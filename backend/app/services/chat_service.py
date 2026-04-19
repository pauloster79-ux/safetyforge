"""Chat service — orchestrates Claude with tool use for conversational AI.

Supports two modes:
- 'general': Open-ended graph queries using MCP tools + ad-hoc Cypher
- 'inspection': Guided checklist flow that creates an Inspection on completion

Streams responses via Server-Sent Events using Anthropic's streaming API.
"""

import json
import logging
import secrets
import time
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from typing import Any

from anthropic import Anthropic


def _safe_json_dumps(obj: Any) -> str:
    """JSON-encode with support for Neo4j date/datetime types."""
    def _default(o: object) -> str:
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if hasattr(o, "__str__"):
            return str(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    return json.dumps(obj, default=_default)

from app.config import Settings
from app.models.actor import Actor
from app.models.chat import ChatEvent, ChatSession, InspectionChatState
from app.models.events import EventType
from app.models.inspection import InspectionCreate, InspectionItem
from app.services.conversation_service import ConversationService
from app.services.embedding_service import EmbeddingService
from app.services.event_bus import EventBus
from app.services.inspection_service import InspectionService
from app.services.inspection_template_service import InspectionTemplateService
from app.services.mcp_tools import MCPToolService
from app.services.memory_extraction_service import MemoryExtractionService
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 10
SESSION_TTL_SECONDS = 3600  # 1 hour
CHAT_MODEL = "claude-sonnet-4-20250514"

# Agent identity for the chat agent — stamped on every assistant Message as
# provenance. Versioned so we can attribute decisions to a specific chat
# agent revision and roll back if needed.
CHAT_AGENT_ID = "agent_chat"
CHAT_AGENT_VERSION = "1.0.0"

# Pricing for CHAT_MODEL in cents per million tokens. Mirrors
# llm_service.PRICING_CENTS_PER_MILLION for the STANDARD tier. Kept
# inline here because chat_service uses the Anthropic client directly
# rather than routing through LLMService.
_CHAT_PRICING_CENTS_PER_MILLION: dict[str, float] = {
    "input": 300.0,
    "output": 1500.0,
}


def _calculate_cost_cents(input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost of a single CHAT_MODEL turn in cents."""
    return (
        (input_tokens * _CHAT_PRICING_CENTS_PER_MILLION["input"] / 1_000_000)
        + (output_tokens * _CHAT_PRICING_CENTS_PER_MILLION["output"] / 1_000_000)
    )


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

GENERAL_SYSTEM_PROMPT = """\
You are Kerf, the AI assistant for construction contractors. You help \
foremen, safety officers, and project managers with their projects, \
workers, safety, compliance, financials, and daily operations.

HOW TO ANSWER:
1. Use an intent tool when one fits the question (see list below).
2. Otherwise, use query_graph to traverse the knowledge graph directly. \
You can write any read-only Cypher query. The graph schema is listed below. \
This is powerful — use it freely for questions the intent tools don't cover.
3. When the user mentions a project or worker by name, match it to the \
company data below — you already have the IDs. Use fuzzy matching — \
"the Peachtree job" means the project with Peachtree in its name or address.
4. Keep responses concise. Use bullet points for lists.

CRITICAL RULES:
- When the user talks about an existing project (by name, address, client, or \
context), ALWAYS use that project. Do NOT create a new project with capture_lead \
unless the user is clearly describing work that doesn't match any existing project.
- CONTRACT TYPE: When the user mentions a billing basis — "lump sum", "fixed price", \
"T&M", "time and materials", "cost plus", "open book", "schedule of rates", \
"unit rates" — capture it as data. On new leads pass contract_type to capture_lead. \
On existing projects call set_contract_type. Do NOT just acknowledge it verbally. \
If the user is undecided, recommend a type with brief reasoning, then ask before setting.
- When you recommend contract terms, conditions, or payment structures, ALSO \
create them as data using the appropriate tools (create_payment_milestone, \
create_condition, set_warranty_terms, set_retention_terms). Advice without \
data is incomplete — the contractor needs to see the terms on their Contract tab.
- ALWAYS add exclusions alongside assumptions. Every quote should have both. \
If you've added assumptions but no exclusions, add standard exclusions for the \
trade and work type.
- For small residential jobs (under $10K), keep contract terms simple: deposit + \
balance payment, no retention, standard 12-month warranty. Don't apply commercial \
patterns to residential work.

INTENT TOOLS (use when they fit):
- check_worker_compliance, check_project_compliance, get_project_summary, \
get_worker_profile, generate_morning_brief, report_hazard, report_incident, \
get_daily_log_status, get_changes_since
- capture_lead, qualify_project, check_capacity, set_contract_type
- create_work_item, update_work_item, remove_work_item, create_labour, create_item, \
get_estimate_summary, search_historical_rates
- get_rate_suggestion, suggest_productivity, get_material_history, \
search_material_price, capture_rate, capture_material_price, create_insight
- Knowledge loop: offer_insight_capture, find_applicable_insights, \
apply_insight, reject_insight, correct_insight, \
derive_productivity_from_completion, accept_productivity_update, \
capture_material_price, update_rate_from_purchase, list_contractor_knowledge
- add_assumption, update_assumption, remove_assumption, \
add_exclusion, update_exclusion, remove_exclusion, \
list_assumption_templates, list_exclusion_templates
- create_payment_milestone, update_payment_milestone, remove_payment_milestone, \
create_condition, update_condition, remove_condition, \
set_warranty_terms, set_retention_terms, get_contract_summary, \
suggest_contract_terms
- generate_proposal, update_project_status, update_project_state
- get_schedule, assign_workers, detect_conflicts
- create_daily_log, auto_populate_daily_log, record_time, \
report_quality_observation
- get_job_cost_summary, detect_variation, create_variation, \
get_financial_overview
- generate_invoice, track_payment_status, record_payment
- check_sub_compliance, get_sub_performance, list_subs

GRAPH SCHEMA (for query_graph):
- (Company)-[:OWNS_PROJECT]->(Project)
- (Company)-[:EMPLOYS]->(Worker)
- (Worker)-[:ASSIGNED_TO_PROJECT]->(Project)
- (Worker)-[:HOLDS_CERT]->(Certification) — has expiry_date, status, name
- (Project)-[:HAS_INSPECTION]->(Inspection)
- (Project)-[:HAS_INCIDENT]->(Incident)
- (Project)-[:HAS_HAZARD_REPORT]->(HazardReport)
- (Project)-[:HAS_DAILY_LOG]->(DailyLog)
- (Project)-[:HAS_EQUIPMENT]->(Equipment)
- (Project)-[:HAS_WORK_ITEM]->(WorkItem)
- (WorkItem)-[:HAS_LABOUR]->(Labour) — task, rate_cents, hours, cost_cents
- (WorkItem)-[:HAS_ITEM]->(Item) — description, quantity, unit_cost_cents, total_cents
- (Project)-[:HAS_ASSUMPTION]->(Assumption) — category, statement, variation_trigger
- (Project)-[:HAS_EXCLUSION]->(Exclusion) — category, statement
- (Company)-[:HAS_RATE]->(ResourceRate) — resource_type, rate_cents, unit, source
- (Company)-[:HAS_PRODUCTIVITY]->(ProductivityRate) — rate, rate_unit, time_unit
- (Company)-[:HAS_INSIGHT]->(Insight) — scope, scope_value, statement, adjustment_type, confidence
- (Company)-[:HAS_CATALOG_ENTRY]->(MaterialCatalogEntry) — description, unit_cost_cents, supplier_name, source_url, location, fetched_at
- (IndustryProductivityBaseline) — trade, work_description, rate, rate_unit, time_unit, crew_size, confidence
- (Company)-[:ASSUMPTION_TEMPLATE_OF]->(Assumption {is_template: true})
- (Company)-[:EXCLUSION_TEMPLATE_OF]->(Exclusion {is_template: true})
- (Project)-[:HAS_INVOICE]->(Invoice)
- (Project)-[:HAS_CONTRACT]->(Contract) — retention_pct, payment_terms, value, status
- (Contract)-[:HAS_PAYMENT_MILESTONE]->(PaymentMilestone) — description, percentage or fixed_amount_cents, trigger_condition, sort_order, status
- (Contract)-[:HAS_CONDITION]->(Condition) — category, description, responsible_party
- (Contract)-[:HAS_WARRANTY]->(Warranty) — period_months, scope, start_trigger, terms
- Project has state (lead|quoted|active|completed|closed|lost) and status (normal|on_hold|delayed|suspended)

QUOTING WORKFLOW:
When building a quote: 1) create_work_item for each scope item, 2) call the \
source cascade tools (get_rate_suggestion, suggest_productivity, \
get_material_history, search_material_price) to find rates and prices with \
a source, 3) create_labour and create_item as child nodes — ALWAYS pass the \
source_id, source_type, and source_reasoning from step 2, 4) add_assumption \
for qualifications, 5) add_exclusion for scope boundaries, 6) \
get_estimate_summary to review totals, 7) generate_proposal to assemble the \
document. All monetary values are in cents. Before create_labour or \
create_item, you MUST have a source — call the suggestion tools first.

SOURCE DISCIPLINE (CRITICAL):

Every number in a quote MUST come from a verifiable source. Never invent \
rates, productivity values, or material prices from training data.

Labour rates:
1. ALWAYS check get_rate_suggestion first before calling create_labour
2. If source_type is "resource_rate", pass the rate_source_id to \
create_labour with rate_source_type="resource_rate"
3. If source_type is "not_found", ASK the contractor what their rate is for \
this role, then use capture_rate to store it, then use the new source in \
create_labour
4. NEVER create a labour entry with an invented rate. No exceptions.

Productivity:
1. Call suggest_productivity to get an estimate with source
2. Pass the source_id and source_type to create_labour
3. Explain the source to the contractor in the message: "Based on your \
Peachtree job, 0.38 hrs per receptacle — applying to this quote"
4. If only industry baseline is available, say so clearly and ask if it \
applies

Materials:
1. Call get_material_history first — contractor's own past prices are best
2. If no history, call search_material_price for a current supplier price
3. If search returns pending, ask the contractor or use \
capture_material_price
4. Pass source fields to create_item with proper source_reasoning
5. Always include source_reasoning like "From your Buckhead job, Mar 2026" \
or "Graybar Atlanta, fetched today"

Capturing reasoning:
- When the contractor explains a judgement ("low ceilings add 15%"), create \
an Insight so it applies on future similar jobs
- Use create_insight with appropriate scope and adjustment_type

KNOWLEDGE LOOP (LAYER 4 — MANDATORY):

Kerf learns from every job. The single most important rule: \
**BEFORE you call create_labour or create_item, you MUST call \
find_applicable_insights.** This is non-negotiable. Even if you already \
have a rate from get_rate_suggestion or productivity data from \
search_historical_rates or suggest_productivity, you STILL call \
find_applicable_insights because the Insights may modify the result.

Workflow for every new work item:
1. Call find_applicable_insights with work_type (e.g. "renovation_electrical", \
"commercial_lighting") and trade (e.g. "electrical"). ALWAYS.
2. If combined_productivity_adjustment != 1.0, apply it to any labour hours \
you calculate. Mention the adjustment in source_reasoning: "Your +20% old \
building adjustment applied — 28.8 hrs instead of 24."
3. For high-confidence insights (>= 0.6, appear in surface_to_user), mention \
them to the contractor and call apply_insight after the work item is created \
(this is silent validation).
4. For low-confidence insights (< 0.6, in apply_silently), apply the \
adjustment but only note it in source_reasoning.
5. If multiple insights apply, combine multiplicatively (already computed \
in combined_productivity_adjustment). Show the reasoning chain.

When the contractor explains reasoning (corrections with "because X" or "I \
add Y for Z conditions"):
- Call offer_insight_capture to propose the pattern
- If they accept (yes / sure / save it), call create_insight
- Examples: "Low ceilings in renovations add 15%", "Medical facilities +20% \
for fire alarm device density"

When the contractor corrects an applied Insight ("no, don't add 15% on \
this one — standard ceiling height"):
- Call reject_insight with the reason
- Don't argue — their correction is truth

When the contractor states a material price from an actual purchase:
- Use capture_material_price or update_rate_from_purchase to store it
- Next quote that needs this material will have it in history

When a project completes:
- Call derive_productivity_from_completion
- Present proposed rate updates with reasoning
- After 5+ data points the system auto-updates (needs_confirmation=False); \
below that, ask first via accept_productivity_update

When the contractor asks what Kerf knows about their business:
- Call list_contractor_knowledge and summarise rates, productivity, insights

DON'T clutter: only mention insights to the contractor when confidence is \
high enough to matter (>= 0.6) OR multiple insights agree. Silent \
application is fine — source_reasoning on the Labour/Item captures it.

CONTRACT TERMS WORKFLOW:
After building an estimate with work items, ALWAYS call suggest_contract_terms to \
generate recommended contract terms. Present the suggestions to the contractor and \
explain each one. The contractor can accept, modify, or reject each suggestion.

Key tools: create_payment_milestone, create_condition, set_warranty_terms, \
set_retention_terms, get_contract_summary, suggest_contract_terms

Important behaviours:
- After WorkItems are created, proactively suggest payment milestones appropriate \
for the project value and type
- Suggest relevant conditions based on the work type (e.g., site access for \
renovation, weather for outdoor work)
- Ask about warranty and retention if not yet set
- Remember the contractor's preferences — if they always use 50/25/25 payment \
splits, apply that by default
- For commercial work over $50K, always suggest retention terms
- For residential work, suggest simpler payment structures (deposit + balance)
- Explain WHY each term matters, especially for less experienced contractors

Note: query_graph auto-injects $company_id as a parameter. Always filter \
by company_id in your queries for data isolation."""

INSPECTION_SYSTEM_PROMPT_TEMPLATE = """\
You are Kerf, guiding a foreman through a {inspection_type} inspection \
on their construction site. This is a voice conversation — keep responses \
SHORT and conversational (1-2 sentences max).

INSPECTION STATE:
- Total items: {total_items}
- Completed: {completed_count}
- Current item ({current_index}/{total_items}): {current_item}
- Category: {current_category}

COMPLETED ITEMS:
{completed_summary}

CRITICAL RULES:
1. ONLY call update_inspection_item when the foreman gives a CLEAR pass/fail/na \
answer. Words like "good", "fine", "pass", "yes" = pass. Words like "failed", \
"issue", "problem", "broken", "missing" = fail.
2. If the foreman asks a QUESTION (contains "?", starts with "what", "how", \
"where", "why", "which", "can you", "tell me", "explain"), DO NOT call any \
tool. Answer their question about the checklist item and then re-ask for \
the status.
3. If the message is UNCLEAR or ambiguous, ask for clarification. Do NOT \
guess pass/fail.
4. If they say "go back" or "previous", call go_back.
5. If they say "skip" or "not applicable" or "n/a", call skip_item.
6. If they say "add a note", call add_note.
7. When all items are done, summarise results and call complete_inspection.
8. Be friendly but efficient — this is a busy construction site.
9. Keep responses under 2 sentences when acknowledging a pass/fail. \
Longer answers are OK when explaining what to look for."""


# ---------------------------------------------------------------------------
# Tool definitions for Anthropic API
# ---------------------------------------------------------------------------

GENERAL_TOOLS: list[dict[str, Any]] = [
    {
        "name": "check_worker_compliance",
        "description": "Check if a worker meets all certification requirements for a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "worker_id": {"type": "string", "description": "Worker ID"},
            },
            "required": ["project_id", "worker_id"],
        },
    },
    {
        "name": "check_project_compliance",
        "description": "Get full compliance overview for a project — workers, equipment, inspections, hazards, incidents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_project_summary",
        "description": "Get project overview — workers, equipment count, recent activity in last 7 days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_worker_profile",
        "description": "Get a worker's profile — certifications, project assignments, contact info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "worker_id": {"type": "string", "description": "Worker ID"},
            },
            "required": ["worker_id"],
        },
    },
    {
        "name": "generate_morning_brief",
        "description": "Generate a morning safety brief for a project — alerts, expired certs, open hazards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "report_hazard",
        "description": "Report a hazard on a project. Creates a HazardReport node.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "description": {"type": "string", "description": "Hazard description"},
                "location": {"type": "string", "description": "Location on site"},
                "severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Severity level",
                },
            },
            "required": ["project_id", "description"],
        },
    },
    {
        "name": "report_incident",
        "description": "Report an incident on a project. Creates an Incident node.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "title": {"type": "string", "description": "Short incident title"},
                "description": {"type": "string", "description": "Full description"},
                "severity": {
                    "type": "string",
                    "enum": ["minor", "moderate", "serious", "critical", "fatality"],
                },
                "incident_type": {
                    "type": "string",
                    "enum": ["near_miss", "first_aid", "medical_treatment", "lost_time", "property_damage"],
                },
            },
            "required": ["project_id", "title", "description"],
        },
    },
    {
        "name": "get_daily_log_status",
        "description": "Check daily log submission status — which dates have/haven't submitted.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_changes_since",
        "description": "Get all changes on a project since a timestamp — new inspections, incidents, hazards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "since": {"type": "string", "description": "ISO 8601 timestamp"},
            },
            "required": ["project_id", "since"],
        },
    },
    {
        "name": "query_graph",
        "description": "Run a read-only Cypher query against the Neo4j knowledge graph. Use for ad-hoc queries not covered by other tools. Always scope queries to the current company.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cypher": {
                    "type": "string",
                    "description": "Read-only Cypher query. Must include company_id filter.",
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters",
                },
            },
            "required": ["cypher"],
        },
    },
    # ── Find & Qualify ──────────────────────────────────────────────────
    {
        "name": "capture_lead",
        "description": "Capture a new lead — creates a Project in lead state. Address can be empty at this stage (placeholder is used). If the user mentions a billing basis (lump sum / fixed price, T&M, cost plus, schedule of rates), set contract_type accordingly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Project description"},
                "project_type": {"type": "string", "description": "Type: residential, commercial, industrial, infrastructure"},
                "address": {"type": "string", "description": "Site address (optional at lead stage)"},
                "client_name": {"type": "string", "description": "Client name"},
                "client_email": {"type": "string", "description": "Client email"},
                "client_phone": {"type": "string", "description": "Client phone"},
                "contract_type": {
                    "type": "string",
                    "enum": ["lump_sum", "schedule_of_rates", "cost_plus", "time_and_materials"],
                    "description": "Contract/billing basis — 'lump_sum' (fixed price), 'time_and_materials' (T&M, hours+materials billed), 'cost_plus' (cost + fee, open book), 'schedule_of_rates' (priced unit rates). Set when user specifies."
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "qualify_project",
        "description": "Qualify a lead project — checks certs, capacity, and GC payment history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID to qualify"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "check_capacity",
        "description": "Check if the company has capacity for new work — active projects, worker utilisation, availability.",
        "input_schema": {"type": "object", "properties": {}},
    },
    # ── Plan & Mobilise ─────────────────────────────────────────────────
    {
        "name": "get_schedule",
        "description": "Get rolling schedule for a project — work items with dates, grouped by week.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "weeks_ahead": {"type": "integer", "description": "Weeks to look ahead (default 4)"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "assign_workers",
        "description": "Assign workers or a crew to a work item on a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "work_item_id": {"type": "string", "description": "Work item ID"},
                "worker_ids": {"type": "array", "items": {"type": "string"}, "description": "Worker IDs to assign"},
                "crew_id": {"type": "string", "description": "Crew ID to assign (alternative to worker_ids)"},
            },
            "required": ["project_id", "work_item_id"],
        },
    },
    {
        "name": "detect_conflicts",
        "description": "Detect scheduling conflicts — cert expirations, equipment overlaps, worker double-bookings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    # ── Sub Management ──────────────────────────────────────────────────
    {
        "name": "check_sub_compliance",
        "description": "Check subcontractor compliance — insurance, certifications, safety performance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sub_company_id": {"type": "string", "description": "Subcontractor company ID"},
            },
            "required": ["sub_company_id"],
        },
    },
    {
        "name": "get_sub_performance",
        "description": "Get subcontractor performance — inspection pass rates, incident frequency, corrective actions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sub_company_id": {"type": "string", "description": "Subcontractor company ID"},
            },
            "required": ["sub_company_id"],
        },
    },
    {
        "name": "list_subs",
        "description": "List all subcontractors with compliance summary.",
        "input_schema": {"type": "object", "properties": {}},
    },
    # ── Estimate & Price ────────────────────────────────────────────────
    {
        "name": "create_work_item",
        "description": "Create a work item on a project — a scope line for quoting. After creation, use create_labour and create_item to add cost breakdown. STRONGLY RECOMMENDED: supply work_category_id from the canonical taxonomy for the contractor's jurisdiction (MasterFormat for US/CA, NRM 2 for UK/IE, NATSPEC for AU/NZ). Categorisation enables rate/productivity lookup, regulatory bridging, and cross-project benchmarks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "description": {"type": "string", "description": "Work item description"},
                "quantity": {"type": "number", "description": "Scope quantity (e.g. 2 floor boxes, 15 LF cable)"},
                "unit": {"type": "string", "description": "Unit: EA, LF, SF, CY, LS, etc."},
                "margin_pct": {"type": "number", "description": "Markup percentage (0-100)"},
                "work_package_id": {"type": "string", "description": "Optional work package ID"},
                "work_category_id": {"type": "string", "description": "Canonical WorkCategory ID (e.g. wcat_us_26_24_16) or company-scoped Extension ID. Writes (wi)-[:CATEGORISED_AS]->(cat)."},
            },
            "required": ["project_id", "description"],
        },
    },
    {
        "name": "create_labour",
        "description": "Add a labour task to a work item — rate and hours. All amounts in cents. STRONGLY RECOMMENDED: call get_rate_suggestion and suggest_productivity first, then pass the rate_source_id/rate_source_type/productivity_source_id/productivity_source_type/source_reasoning through so the estimate is traceable back to its source. Never invent a rate from training data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "work_item_id": {"type": "string", "description": "Work item ID"},
                "task": {"type": "string", "description": "Labour task description (e.g. 'Install receptacles')"},
                "rate_cents": {"type": "integer", "description": "Hourly rate in cents (e.g. 15000 = $150/hr)"},
                "hours": {"type": "number", "description": "Estimated hours"},
                "notes": {"type": "string", "description": "Optional notes"},
                "rate_source_id": {"type": "string", "description": "ResourceRate ID the rate came from. REQUIRED when rate_source_type='resource_rate'."},
                "rate_source_type": {"type": "string", "enum": ["resource_rate", "contractor_stated", "inherited_from_similar_project"], "description": "Where the hourly rate came from. 'resource_rate' = from company rate library; 'contractor_stated' = contractor gave it verbally; 'inherited_from_similar_project' = reused from a past job."},
                "productivity_source_id": {"type": "string", "description": "ID of the ProductivityRate / Insight / IndustryProductivityBaseline the hours were derived from."},
                "productivity_source_type": {"type": "string", "enum": ["productivity_rate", "insight", "industry_baseline", "contractor_estimate"], "description": "Where the productivity (hours) came from."},
                "source_reasoning": {"type": "string", "description": "Human-readable explanation of the source — e.g. 'Based on your Peachtree job: 0.38 hrs per receptacle' or 'Industry baseline, adjusted per contractor for low ceilings'."},
            },
            "required": ["project_id", "work_item_id", "task", "rate_cents", "hours"],
        },
    },
    {
        "name": "create_item",
        "description": "Add a material/equipment/fixture item to a work item. All amounts in cents. STRONGLY RECOMMENDED: call get_material_history or search_material_price first, then pass price_source_id/price_source_type/source_reasoning/source_url through so the price is traceable back to its source. Never invent a price from training data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "work_item_id": {"type": "string", "description": "Work item ID"},
                "description": {"type": "string", "description": "Item description (e.g. 'Floor box (Arlington FLBR5420)')"},
                "quantity": {"type": "number", "description": "Number of units"},
                "unit_cost_cents": {"type": "integer", "description": "Cost per unit in cents (e.g. 4500 = $45)"},
                "unit": {"type": "string", "description": "Unit: EA, LF, SF, etc. (default EA)"},
                "product": {"type": "string", "description": "Product name/model number"},
                "notes": {"type": "string", "description": "Optional notes"},
                "price_source_id": {"type": "string", "description": "MaterialCatalogEntry ID or past Item ID the price came from."},
                "price_source_type": {"type": "string", "enum": ["material_catalog", "purchase_history", "contractor_stated", "estimate"], "description": "Where the price came from."},
                "source_reasoning": {"type": "string", "description": "Human-readable explanation — e.g. 'From your Buckhead job, Mar 2026' or 'Graybar Atlanta, fetched today'."},
                "source_url": {"type": "string", "description": "URL the price was looked up from, if applicable."},
            },
            "required": ["project_id", "work_item_id", "description", "quantity", "unit_cost_cents"],
        },
    },
    {
        "name": "update_work_item",
        "description": "Update a work item — change description, quantity, margin, state. When quantity changes (and unit is unchanged), child Labour hours and Item quantities are scaled proportionally by default so the cost tracks the new scope. Pass scale_children=false only when the user is renaming a unit (e.g. EA -> SF) rather than rescaling the work.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "work_item_id": {"type": "string", "description": "Work item ID"},
                "description": {"type": "string", "description": "Updated description"},
                "quantity": {"type": "number", "description": "Updated scope quantity"},
                "unit": {"type": "string", "description": "Updated unit"},
                "margin_pct": {"type": "number", "description": "Updated markup percentage"},
                "state": {"type": "string", "description": "New state: draft, scheduled, in_progress, complete"},
                "scale_children": {"type": "boolean", "description": "Default true. When true and only quantity changes, labour hours and item quantities scale proportionally."},
            },
            "required": ["project_id", "work_item_id"],
        },
    },
    {
        "name": "remove_work_item",
        "description": "Soft-delete a work item from a project. Removes it (and its labour/items) from the estimate and any generated proposals. Use this when the user wants to delete a line, remove a duplicate, or drop scope.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "work_item_id": {"type": "string", "description": "Work item ID to remove"},
            },
            "required": ["project_id", "work_item_id"],
        },
    },
    {
        "name": "get_estimate_summary",
        "description": "Get estimate summary — labour, items, margin, totals (in cents), plus assumption/exclusion counts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "search_historical_rates",
        "description": "Search past projects and company rate library for similar work — returns historical costs, ResourceRates, and ProductivityRates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Work description to search for"},
                "work_category_id": {"type": "string", "description": "Work category ID to filter by"},
            },
        },
    },
    # ── Source cascade (Layer 3) ──────────────────────────────────────
    {
        "name": "get_rate_suggestion",
        "description": "Cascade lookup for a labour rate. Returns the matching ResourceRate with a source_id the agent can pass into create_labour. Returns source_type='not_found' when there is no match — in that case ask the contractor for the rate and use capture_rate. Never fall back to a training-data guess for labour rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID the estimate is for"},
                "trade": {"type": "string", "description": "Trade name, e.g. 'electrical'"},
                "role": {"type": "string", "description": "Role description, e.g. 'journeyman electrician'"},
            },
            "required": ["project_id", "trade", "role"],
        },
    },
    {
        "name": "suggest_productivity",
        "description": "Cascade lookup for a productivity rate. Tries company ProductivityRate first, then applicable Insights as refinement signals, then IndustryProductivityBaseline as low-confidence fallback. Pass the returned source_id + source_type into create_labour.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID the estimate is for"},
                "trade": {"type": "string", "description": "Trade name, e.g. 'electrical'"},
                "work_description": {"type": "string", "description": "What the crew is doing, e.g. 'install receptacles'"},
            },
            "required": ["project_id", "trade", "work_description"],
        },
    },
    {
        "name": "get_material_history",
        "description": "Find prior unit costs for a material from the contractor's own completed projects. Always prefer this over web search — the contractor's own history is the most trusted source.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID the estimate is for"},
                "description": {"type": "string", "description": "Material description, e.g. 'duplex receptacle'"},
            },
            "required": ["project_id", "description"],
        },
    },
    {
        "name": "search_material_price",
        "description": "Look up a current material price. Checks the contractor's MaterialCatalogEntry library first (location-aware via project city/state). If nothing fresh matches, returns source_type='search_pending' — in that case ask the contractor or use capture_material_price. Web search integration is not yet wired up.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID the estimate is for"},
                "description": {"type": "string", "description": "Material description, e.g. 'duplex receptacle 20A spec grade'"},
                "unit": {"type": "string", "description": "Expected unit of measurement (EA, LF, SF, ...)"},
            },
            "required": ["project_id", "description", "unit"],
        },
    },
    {
        "name": "capture_rate",
        "description": "Store a labour rate the contractor just stated. Creates a ResourceRate so future estimates can reuse it. Use this immediately after the contractor answers 'what's your rate for X'. After capture, the returned rate_id can be passed into create_labour as rate_source_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID the rate was stated on"},
                "trade": {"type": "string", "description": "Trade name, e.g. 'electrical'"},
                "role": {"type": "string", "description": "Role description, e.g. 'journeyman electrician'"},
                "rate_cents": {"type": "integer", "description": "Hourly rate in cents (e.g. 15000 = $150/hr)"},
                "description": {"type": "string", "description": "Optional richer description for the library entry"},
            },
            "required": ["project_id", "trade", "role", "rate_cents"],
        },
    },
    {
        "name": "capture_material_price",
        "description": "Store a material price the contractor stated or that was researched. Creates a MaterialCatalogEntry tagged with the project's location so future location-aware lookups can prefer it. Returned entry_id can be passed into create_item as price_source_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID the price was stated on"},
                "description": {"type": "string", "description": "Material description"},
                "unit": {"type": "string", "description": "Unit of measurement (EA, LF, SF, ...)"},
                "unit_cost_cents": {"type": "integer", "description": "Price per unit in cents"},
                "supplier_name": {"type": "string", "description": "Supplier name, if known"},
                "source_url": {"type": "string", "description": "URL the price was looked up from, if any"},
            },
            "required": ["project_id", "description", "unit", "unit_cost_cents"],
        },
    },
    {
        "name": "create_insight",
        "description": "Capture contractor reasoning as a reusable Insight. Use this when the contractor explains a judgement that should apply on similar future jobs — e.g. 'low ceilings add 15% to rough-in hours' or 'residential always needs sub-floor drilling'. Scope + scope_value define where the insight applies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["work_type", "trade", "jurisdiction", "client_type", "project_size", "other"], "description": "Dimension the insight scopes to"},
                "scope_value": {"type": "string", "description": "Concrete value for the scope (e.g. 'low_ceiling_renovation' or 'electrical')"},
                "statement": {"type": "string", "description": "Human-readable insight text"},
                "adjustment_type": {"type": "string", "enum": ["productivity_multiplier", "rate_adjustment", "qualitative"], "description": "Kind of adjustment the insight encodes"},
                "adjustment_value": {"type": "number", "description": "Numeric adjustment where applicable (e.g. 1.15 for +15%)"},
                "confidence": {"type": "number", "description": "Confidence 0-1, default 0.5"},
                "source_context": {"type": "string", "description": "Optional origin (e.g. conversation ID or project ID)"},
            },
            "required": ["scope", "scope_value", "statement", "adjustment_type"],
        },
    },
    # ── Layer 4: Knowledge accumulation ─────────────────────────────────
    {
        "name": "apply_insight",
        "description": "Record that an Insight was applied during a quote. Call this when you've used an insight to adjust a productivity rate or rate estimate. Increments validation_count and raises confidence (+0.05, capped at 0.95). Silence is consent — if the contractor doesn't correct the applied adjustment, it counts as validated.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_id": {"type": "string", "description": "The Insight ID being applied"},
                "context": {"type": "string", "description": "Optional — where it was applied, e.g. 'wi_abc123 receptacle rough-in'"},
            },
            "required": ["insight_id"],
        },
    },
    {
        "name": "correct_insight",
        "description": "Record that the contractor pushed back on a previously-applied Insight. Decreases confidence (-0.1, floor 0.1), decrements validation_count, appends the correction to source_context. If confidence drops below 0.3, the Insight is marked deprecated and will not be applied on future quotes. The contractor always wins — don't argue, adjust.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_id": {"type": "string", "description": "The Insight ID being corrected"},
                "correction_note": {"type": "string", "description": "Why the contractor disagreed or clarified (required)"},
            },
            "required": ["insight_id", "correction_note"],
        },
    },
    {
        "name": "find_applicable_insights_for_work",
        "description": "Find Insights relevant to a specific work item and bucket them for surfacing. Returns high_confidence (>= 0.6, apply silently), medium_confidence (0.3-0.6, mention and ask), low_confidence (< 0.3, usually skip). Also returns combined_productivity_adjustment — a multiplicative combination of all high-confidence productivity_multiplier insights — plus combined_reasoning narrating the math. Call this BEFORE create_labour or create_item so the estimate can be adjusted with source.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID for scope context"},
                "work_description": {"type": "string", "description": "What the work item is, e.g. 'install receptacles in open ceiling'"},
                "trade": {"type": "string", "description": "Trade name, e.g. 'electrical'"},
            },
            "required": ["project_id", "work_description", "trade"],
        },
    },
    {
        "name": "derive_productivity_from_actuals",
        "description": "Compare estimated hours vs actual TimeEntry hours for a completed WorkItem. Returns implied rate (units per hour from actuals), the library rate that was used, variance, and a recommendation. Called automatically on project completion but can also be invoked on demand when closing out a work item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "work_item_id": {"type": "string", "description": "Work item to derive actuals for"},
            },
            "required": ["project_id", "work_item_id"],
        },
    },
    {
        "name": "update_productivity_rate_from_actuals",
        "description": "Apply a new data point to a ProductivityRate, weighted-averaging the implied actual rate into the library rate. Increments sample_size. Use after derive_productivity_from_actuals recommends an update. Rule: ask the contractor before updating if sample_size < 5; auto-update with notification once sample_size >= 5.",
        "input_schema": {
            "type": "object",
            "properties": {
                "productivity_rate_id": {"type": "string", "description": "The ProductivityRate to update"},
                "new_data_point_rate": {"type": "number", "description": "Implied rate from actuals (output units per hour)"},
                "new_data_point_sample_size": {"type": "integer", "description": "How many data points this represents (default 1)"},
            },
            "required": ["productivity_rate_id", "new_data_point_rate"],
        },
    },
    {
        "name": "update_material_price_from_purchase",
        "description": "Record an actual material purchase price. If a MaterialCatalogEntry with matching description + supplier + location exists, updates it; otherwise creates a new entry. Sets last_verified_at to now so future staleness checks know the price is fresh. Use when the contractor states a real purchase price (not a quote or search result).",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "What the material is (matched case-insensitively)"},
                "unit_cost_cents": {"type": "integer", "description": "Price paid per unit, in cents"},
                "unit": {"type": "string", "description": "Unit of measurement (EA, LF, SF, ...)"},
                "supplier_name": {"type": "string", "description": "Supplier the purchase was from (matched exactly)"},
                "location": {"type": "string", "description": "City/region where the price applies (matched exactly)"},
                "source_url": {"type": "string", "description": "Optional receipt/invoice URL"},
            },
            "required": ["description", "unit_cost_cents"],
        },
    },
    {
        "name": "list_contractor_knowledge",
        "description": "Summary read for the Knowledge page. Returns the contractor's accumulated rate library, productivity rates (with derived confidence), insights (sorted by confidence), plus counts for material catalog entries and completed projects. Use when the contractor asks 'what do you know about my business' or 'what are my rates'.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    # Layer 4 (extended): contractor-confirmation knowledge tools
    {
        "name": "offer_insight_capture",
        "description": "Propose an Insight for the contractor to confirm BEFORE saving. Use when the contractor gives reasoning during a correction (e.g. 'I add 15% for low ceilings', 'this GC pays slow so I want a bigger deposit'). Does NOT write — returns a confirmation prompt. After the contractor accepts (yes/sure/save it), call create_insight with the same fields. After they reject or edit, follow their lead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project the reasoning came from (for source_context)"},
                "statement": {"type": "string", "description": "Human-readable insight text"},
                "scope": {"type": "string", "enum": ["work_type", "trade", "jurisdiction", "client_type", "project_size", "other"], "description": "Dimension the insight scopes to"},
                "scope_value": {"type": "string", "description": "Concrete value for the scope (e.g. 'low_ceiling_renovation' or 'electrical')"},
                "adjustment_type": {"type": "string", "enum": ["productivity_multiplier", "rate_adjustment", "qualitative"], "description": "Kind of adjustment"},
                "adjustment_value": {"type": "number", "description": "Numeric adjustment where applicable (e.g. 1.15 for +15%)"},
                "confidence": {"type": "number", "description": "Initial confidence 0-1, default 0.5"},
            },
            "required": ["project_id", "statement", "scope", "scope_value", "adjustment_type"],
        },
    },
    {
        "name": "find_applicable_insights",
        "description": "Find Insights applicable to the current work and split them into surface-to-user vs apply-silently. Returns combined_productivity_adjustment (multiplicative product of all productivity_multiplier insights), reasoning_chain narrating the math, combined_confidence (lowest of inputs), and the buckets. Surface-to-user insights have confidence >= surface_threshold (default 0.6) OR multiple insights agree. Apply silent insights without interrupting the contractor. Filters out deprecated/inactive automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID for scope context (jurisdiction, client_type)"},
                "work_type": {"type": "string", "description": "Work type tag to match (e.g. 'rough_in', 'low_ceiling_renovation')"},
                "trade": {"type": "string", "description": "Trade name (e.g. 'electrical')"},
                "surface_threshold": {"type": "number", "description": "Confidence at/above which to surface to user (default 0.6)"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "reject_insight",
        "description": "Record contractor rejection of an applied Insight. Decreases confidence by 0.10 (floor 0.0), logs reason in source_context. If confidence drops below 0.2, the insight is marked active=false and won't surface on future quotes. Use this when the contractor says 'no, don't add 15% on this one' or similar pushback. The contractor always wins — don't argue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_id": {"type": "string", "description": "The Insight ID being rejected"},
                "reason": {"type": "string", "description": "Why the contractor pushed back (required)"},
            },
            "required": ["insight_id", "reason"],
        },
    },
    {
        "name": "derive_productivity_from_completion",
        "description": "Compare estimated vs actual hours across ALL work items on a completed project. Returns proposed_updates — a list of ProductivityRate refinements where actuals differ from library by >10%. needs_confirmation is False if the rate already has 5+ data points (auto-update is safe). Call this when a project transitions to 'completed'. For each proposed update with needs_confirmation=true, ask the contractor before calling accept_productivity_update.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "The completed project to analyse"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "accept_productivity_update",
        "description": "Apply a proposed productivity update directly. Sets the rate to new_rate (no weighted averaging — caller decided), increments sample_size by 1, sets last_derived_at to now, stamps source='derived_from_actuals'. Use after derive_productivity_from_completion when the contractor confirms (or when sample_size >= 5 so confirmation isn't needed).",
        "input_schema": {
            "type": "object",
            "properties": {
                "productivity_rate_id": {"type": "string", "description": "ProductivityRate to update"},
                "new_rate": {"type": "number", "description": "Accepted new rate value"},
            },
            "required": ["productivity_rate_id", "new_rate"],
        },
    },
    {
        "name": "update_rate_from_purchase",
        "description": "Update an existing MaterialCatalogEntry with a fresh purchase price — avoids creating duplicates. Sets last_verified_at and fetched_at to now. Use when the contractor captures a new price for a material we already track (you have its material_catalog_entry_id from a prior get_material_history or search_material_price call).",
        "input_schema": {
            "type": "object",
            "properties": {
                "material_catalog_entry_id": {"type": "string", "description": "MaterialCatalogEntry ID to update"},
                "new_price_cents": {"type": "integer", "description": "New price in cents"},
                "source_url": {"type": "string", "description": "Optional receipt/invoice URL"},
            },
            "required": ["material_catalog_entry_id", "new_price_cents"],
        },
    },
    {
        "name": "add_assumption",
        "description": "Add an assumption to a project quote — a qualification that, if violated, may trigger a variation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "category": {"type": "string", "enum": ["schedule", "quantities", "access", "coordination", "site_conditions", "design_completeness", "pricing", "regulatory"], "description": "Assumption type"},
                "statement": {"type": "string", "description": "Assumption text for the quote document"},
                "variation_trigger": {"type": "boolean", "description": "Whether violation triggers a variation claim"},
                "trigger_description": {"type": "string", "description": "What would violate this assumption"},
                "relied_on_value": {"type": "string", "description": "Specific value relied upon (e.g. '19')"},
                "relied_on_unit": {"type": "string", "description": "Unit for the value (e.g. 'weeks')"},
            },
            "required": ["project_id", "category", "statement"],
        },
    },
    {
        "name": "add_exclusion",
        "description": "Add an exclusion to a project quote — states what is NOT included in the price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "category": {"type": "string", "enum": ["scope", "trade_boundary", "conditions", "risk", "regulatory"], "description": "Exclusion type"},
                "statement": {"type": "string", "description": "Exclusion text for the quote document"},
                "partial_inclusion": {"type": "string", "description": "What IS included despite the exclusion"},
            },
            "required": ["project_id", "category", "statement"],
        },
    },
    {
        "name": "update_assumption",
        "description": "Update an existing assumption on a project quote.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assumption_id": {"type": "string", "description": "Assumption ID to update"},
                "statement": {"type": "string", "description": "Updated assumption text"},
                "category": {"type": "string", "enum": ["schedule", "quantities", "access", "coordination", "site_conditions", "design_completeness", "pricing", "regulatory"], "description": "Updated category"},
                "variation_trigger": {"type": "boolean", "description": "Whether violation triggers a variation claim"},
                "trigger_description": {"type": "string", "description": "What would violate this assumption"},
                "relied_on_value": {"type": "string", "description": "Specific value relied upon"},
                "relied_on_unit": {"type": "string", "description": "Unit for the value"},
            },
            "required": ["assumption_id"],
        },
    },
    {
        "name": "remove_assumption",
        "description": "Remove an assumption from a project quote.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assumption_id": {"type": "string", "description": "Assumption ID to remove"},
            },
            "required": ["assumption_id"],
        },
    },
    {
        "name": "update_exclusion",
        "description": "Update an existing exclusion on a project quote.",
        "input_schema": {
            "type": "object",
            "properties": {
                "exclusion_id": {"type": "string", "description": "Exclusion ID to update"},
                "statement": {"type": "string", "description": "Updated exclusion text"},
                "category": {"type": "string", "enum": ["scope", "trade_boundary", "conditions", "risk", "regulatory"], "description": "Updated category"},
                "partial_inclusion": {"type": "string", "description": "What IS included despite the exclusion"},
            },
            "required": ["exclusion_id"],
        },
    },
    {
        "name": "remove_exclusion",
        "description": "Remove an exclusion from a project quote.",
        "input_schema": {
            "type": "object",
            "properties": {
                "exclusion_id": {"type": "string", "description": "Exclusion ID to remove"},
            },
            "required": ["exclusion_id"],
        },
    },
    {
        "name": "list_assumption_templates",
        "description": "List company assumption templates that can be reused on projects.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trade_type": {"type": "string", "description": "Filter by trade (e.g. 'electrical')"},
            },
        },
    },
    {
        "name": "list_exclusion_templates",
        "description": "List company exclusion templates that can be reused on projects.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trade_type": {"type": "string", "description": "Filter by trade (e.g. 'electrical')"},
            },
        },
    },
    # ── Propose & Win ───────────────────────────────────────────────────
    {
        "name": "generate_proposal",
        "description": "Generate a proposal document — includes work items, assumptions, exclusions, pricing, and terms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "terms": {"type": "string", "description": "Payment terms"},
                "timeline": {"type": "string", "description": "Timeline/schedule info"},
                "notes": {"type": "string", "description": "Additional notes"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "update_project_status",
        "description": "Update project lifecycle state — lead, quoted, active, completed, closed, lost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "new_status": {"type": "string", "description": "New state: lead, quoted, active, completed, closed, lost"},
            },
            "required": ["project_id", "new_status"],
        },
    },
    {
        "name": "update_project_state",
        "description": "Update project lifecycle state (same as update_project_status) — lead, quoted, active, completed, closed, lost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "new_state": {"type": "string", "description": "New state: lead, quoted, active, completed, closed, lost"},
            },
            "required": ["project_id", "new_state"],
        },
    },
    {
        "name": "set_contract_type",
        "description": "Set the contract/billing basis on a project. Use when the user says 'T&M', 'lump sum', 'fixed price', 'cost plus', 'open book', 'schedule of rates', 'unit rates', or similar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "contract_type": {
                    "type": "string",
                    "enum": ["lump_sum", "schedule_of_rates", "cost_plus", "time_and_materials"],
                    "description": "Billing basis — 'lump_sum' (fixed price), 'time_and_materials' (hours + materials), 'cost_plus' (costs + fee, open book), 'schedule_of_rates' (priced unit rates)."
                },
            },
            "required": ["project_id", "contract_type"],
        },
    },
    # ── Execute & Document ──────────────────────────────────────────────
    {
        "name": "create_daily_log",
        "description": "Create a daily log for a project on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "log_date": {"type": "string", "description": "Date (YYYY-MM-DD, default today)"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "auto_populate_daily_log",
        "description": "Auto-populate a daily log from inspections, time entries, incidents, weather data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "log_date": {"type": "string", "description": "Date (YYYY-MM-DD, default today)"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "record_time",
        "description": "Record a time entry — worker clock in/out on a work item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "worker_id": {"type": "string", "description": "Worker ID"},
                "work_item_id": {"type": "string", "description": "Work item ID"},
                "clock_in": {"type": "string", "description": "Clock in time (HH:MM or ISO)"},
                "clock_out": {"type": "string", "description": "Clock out time (HH:MM or ISO)"},
                "date": {"type": "string", "description": "Date (YYYY-MM-DD, default today)"},
            },
            "required": ["project_id", "worker_id", "work_item_id", "clock_in"],
        },
    },
    {
        "name": "report_quality_observation",
        "description": "Report a quality observation — creates an Inspection with category 'quality'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "description": {"type": "string", "description": "Quality observation description"},
                "location": {"type": "string", "description": "Location on site"},
                "result_status": {"type": "string", "enum": ["pass", "fail", "partial"], "description": "Result status"},
                "score": {"type": "integer", "description": "Quality score (0-100)"},
            },
            "required": ["project_id", "description"],
        },
    },
    # ── Manage Money ────────────────────────────────────────────────────
    {
        "name": "get_job_cost_summary",
        "description": "Get job cost summary — actual vs estimated costs, margin, burn rate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "detect_variation",
        "description": "Detect potential variations — compare daily log work against original scope.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "create_variation",
        "description": "Create a variation (change order) with evidence chain.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "description": {"type": "string", "description": "Variation description"},
                "amount": {"type": "number", "description": "Variation amount ($)"},
                "work_item_ids": {"type": "string", "description": "Comma-separated affected work item IDs"},
                "evidence_ids": {"type": "string", "description": "Comma-separated evidence entity IDs"},
            },
            "required": ["project_id", "description"],
        },
    },
    {
        "name": "get_financial_overview",
        "description": "Get project financial overview — contract value, costs, variations, invoiced, paid, profit/loss.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    # ── Get Paid ────────────────────────────────────────────────────────
    {
        "name": "generate_invoice",
        "description": "Generate an invoice from selected work items or percentage of project progress.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "work_item_ids": {"type": "array", "items": {"type": "string"}, "description": "Specific work item IDs to invoice"},
                "progress_pct": {"type": "number", "description": "Percentage of project progress to invoice (0-100)"},
                "due_date": {"type": "string", "description": "Invoice due date (YYYY-MM-DD)"},
                "notes": {"type": "string", "description": "Invoice notes"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "track_payment_status",
        "description": "Track outstanding invoices — amounts, aging, overdue status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "record_payment",
        "description": "Record a payment received against an invoice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "invoice_id": {"type": "string", "description": "Invoice ID"},
                "amount": {"type": "number", "description": "Payment amount"},
                "payment_date": {"type": "string", "description": "Payment date (YYYY-MM-DD)"},
                "method": {"type": "string", "description": "Payment method (check, ach, wire, credit_card)"},
                "reference": {"type": "string", "description": "Payment reference/check number"},
            },
            "required": ["project_id", "invoice_id", "amount"],
        },
    },
    # ── Contract Terms ─────────────────────────────────────────────────
    {
        "name": "create_payment_milestone",
        "description": "Create a payment milestone on a project's contract. Auto-creates the contract if needed. Provide exactly one of percentage or fixed_amount_cents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "description": {"type": "string", "description": "Milestone description (e.g. 'Deposit on signing')"},
                "percentage": {"type": "number", "description": "Percentage of contract value (0-100). Mutually exclusive with fixed_amount_cents."},
                "fixed_amount_cents": {"type": "integer", "description": "Fixed amount in cents. Mutually exclusive with percentage."},
                "trigger_condition": {"type": "string", "description": "What triggers this payment (e.g. 'Contract execution', 'Rough-in inspection passed')"},
                "sort_order": {"type": "integer", "description": "Display ordering (0 = first)"},
            },
            "required": ["project_id", "description", "trigger_condition"],
        },
    },
    {
        "name": "update_payment_milestone",
        "description": "Update a payment milestone — change description, amount, trigger, status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "milestone_id": {"type": "string", "description": "Payment milestone ID to update"},
                "description": {"type": "string", "description": "Updated description"},
                "percentage": {"type": "number", "description": "Updated percentage (0-100)"},
                "fixed_amount_cents": {"type": "integer", "description": "Updated fixed amount in cents"},
                "trigger_condition": {"type": "string", "description": "Updated trigger condition"},
                "sort_order": {"type": "integer", "description": "Updated display ordering"},
                "status": {"type": "string", "enum": ["pending", "invoiced", "paid"], "description": "Updated status"},
            },
            "required": ["project_id", "milestone_id"],
        },
    },
    {
        "name": "remove_payment_milestone",
        "description": "Remove a payment milestone from a project's contract.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "milestone_id": {"type": "string", "description": "Payment milestone ID to remove"},
            },
            "required": ["project_id", "milestone_id"],
        },
    },
    {
        "name": "create_condition",
        "description": "Create a contract condition on a project — prerequisites or obligations. Auto-creates contract if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "category": {
                    "type": "string",
                    "enum": ["site_access", "working_hours", "permits", "materials", "client_obligations", "insurance", "other"],
                    "description": "Condition category",
                },
                "description": {"type": "string", "description": "Condition text for the contract"},
                "responsible_party": {"type": "string", "description": "Who is responsible (e.g. 'Client', 'Contractor')"},
            },
            "required": ["project_id", "category", "description"],
        },
    },
    {
        "name": "update_condition",
        "description": "Update a contract condition — change category, description, or responsible party.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "condition_id": {"type": "string", "description": "Condition ID to update"},
                "category": {
                    "type": "string",
                    "enum": ["site_access", "working_hours", "permits", "materials", "client_obligations", "insurance", "other"],
                    "description": "Updated category",
                },
                "description": {"type": "string", "description": "Updated condition text"},
                "responsible_party": {"type": "string", "description": "Updated responsible party"},
            },
            "required": ["project_id", "condition_id"],
        },
    },
    {
        "name": "remove_condition",
        "description": "Remove a contract condition from a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "condition_id": {"type": "string", "description": "Condition ID to remove"},
            },
            "required": ["project_id", "condition_id"],
        },
    },
    {
        "name": "set_warranty_terms",
        "description": "Set warranty terms on a project's contract. Upserts — replaces any existing warranty. Auto-creates contract if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "period_months": {"type": "integer", "description": "Warranty duration in months (e.g. 12)"},
                "scope": {"type": "string", "description": "What the warranty covers (e.g. 'All workmanship and materials')"},
                "start_trigger": {
                    "type": "string",
                    "enum": ["practical_completion", "handover", "other"],
                    "description": "What starts the warranty period (default: practical_completion)",
                },
                "terms": {"type": "string", "description": "Additional warranty terms and conditions"},
            },
            "required": ["project_id", "period_months", "scope"],
        },
    },
    {
        "name": "set_retention_terms",
        "description": "Set retention percentage and payment terms on a project's contract. Auto-creates contract if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "retention_pct": {"type": "number", "description": "Retention percentage (0-100, e.g. 5 = 5%)"},
                "payment_terms_days": {"type": "integer", "description": "Payment terms in days (e.g. 30 = Net 30)"},
            },
            "required": ["project_id", "retention_pct"],
        },
    },
    {
        "name": "get_contract_summary",
        "description": "Get full contract terms overview — payment milestones, conditions, warranty, retention.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "suggest_contract_terms",
        "description": "Suggest contract terms based on project type, value, and the company's history. Returns recommended payment milestones, conditions, retention, and warranty with reasoning. Call this after building a quote to set up appropriate contract terms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        },
    },
]

INSPECTION_TOOLS: list[dict[str, Any]] = [
    {
        "name": "update_inspection_item",
        "description": "Record the result of the current checklist item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Checklist item ID"},
                "status": {
                    "type": "string",
                    "enum": ["pass", "fail", "na"],
                    "description": "Item result",
                },
                "notes": {
                    "type": "string",
                    "description": "Inspector notes for this item",
                },
            },
            "required": ["item_id", "status"],
        },
    },
    {
        "name": "skip_item",
        "description": "Skip the current checklist item (marks as N/A).",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "go_back",
        "description": "Go back to the previous checklist item.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "add_note",
        "description": "Add a note to a previously completed checklist item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Item ID to add note to"},
                "note": {"type": "string", "description": "Note text to append"},
            },
            "required": ["item_id", "note"],
        },
    },
    {
        "name": "complete_inspection",
        "description": "Finish the inspection and save all results. Call when all items are reviewed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "overall_notes": {
                    "type": "string",
                    "description": "Summary notes for the overall inspection",
                },
                "corrective_actions": {
                    "type": "string",
                    "description": "Required corrective actions",
                },
            },
        },
    },
]


class ChatService:
    """Orchestrates Claude with tool use for conversational AI.

    Manages in-memory chat sessions, streams Claude responses via SSE,
    and dispatches tool calls to MCPToolService or inspection state handlers.
    Persists all conversations and messages to Neo4j for memory.
    """

    def __init__(
        self,
        settings: Settings,
        mcp_tools: MCPToolService,
        template_service: InspectionTemplateService,
        inspection_service: InspectionService,
        event_bus: EventBus,
        conversation_service: ConversationService | None = None,
        message_service: MessageService | None = None,
        embedding_service: EmbeddingService | None = None,
        memory_extraction_service: MemoryExtractionService | None = None,
    ) -> None:
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.mcp_tools = mcp_tools
        self.template_service = template_service
        self.inspection_service = inspection_service
        self.event_bus = event_bus
        self.conversation_service = conversation_service
        self.message_service = message_service
        self.embedding_service = embedding_service
        self.memory_extraction_service = memory_extraction_service
        self._sessions: dict[str, ChatSession] = {}
        self._bg_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="chat_persist")

    # ------------------------------------------------------------------
    # Main streaming entry point
    # ------------------------------------------------------------------

    async def stream_response(
        self,
        session_id: str | None,
        message: str,
        company_id: str,
        project_id: str | None,
        mode: str,
        inspection_type: str | None,
        user_id: str,
    ) -> AsyncGenerator[ChatEvent, None]:
        """Stream a chat response as SSE events.

        Yields ChatEvent objects that the router serialises as SSE data lines.
        """
        self._cleanup_expired_sessions()

        # Get or create session
        sid = session_id or f"chat_{secrets.token_hex(8)}"
        session = self._get_or_create_session(
            sid, mode, company_id, project_id, user_id, inspection_type
        )

        # Ensure a Conversation node exists in Neo4j
        self._ensure_conversation(session)

        # Append user message
        session.messages.append({"role": "user", "content": message})
        session.last_active = datetime.now(timezone.utc).isoformat()

        # Persist user message (non-blocking)
        self._persist_message_bg(
            session, role="user", content=message,
            sender_id=user_id, sender_type="member",
            provenance=self._human_provenance(),
        )

        # Build tools once — they don't change per iteration.
        tools = self._get_tools(session.mode)

        # Two actors: the human actor for guardrail bypass (the user is
        # already authenticated via Clerk) and the agent actor for entity
        # provenance so mutations record the chat agent, not the human.
        guardrail_actor = Actor.human(user_id, company_id)
        actor = Actor.agent(
            agent_id=CHAT_AGENT_ID,
            company_id=company_id,
            agent_version=CHAT_AGENT_VERSION,
            model_id=CHAT_MODEL,
        )

        # Tool-use loop
        for iteration in range(MAX_TOOL_ITERATIONS):
            try:
                # Rebuild the system prompt at the top of each iteration so
                # the active project contents (work items, assumptions, etc.)
                # reflect the latest graph state after any mutations from the
                # previous turn. This prevents the agent from hallucinating
                # stale quantities or descriptions.
                system_prompt = self._build_system_prompt(session)

                # Stream Claude's response
                collected_text = ""
                tool_use_blocks: list[dict[str, Any]] = []
                turn_start = time.monotonic()

                with self.client.messages.stream(
                    model=CHAT_MODEL,
                    max_tokens=8192,
                    system=system_prompt,
                    messages=session.messages,
                    tools=tools,
                ) as stream:
                    for event in stream:
                        if event.type == "content_block_start":
                            if hasattr(event.content_block, "type"):
                                if event.content_block.type == "tool_use":
                                    tool_use_blocks.append({
                                        "id": event.content_block.id,
                                        "name": event.content_block.name,
                                        "input": {},
                                    })
                                    yield ChatEvent(
                                        type="tool_call",
                                        data={"tool": event.content_block.name},
                                    )

                        elif event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                collected_text += event.delta.text
                                yield ChatEvent(
                                    type="text_delta",
                                    data={"text": event.delta.text},
                                )
                            elif hasattr(event.delta, "partial_json"):
                                # Accumulate tool input JSON
                                if tool_use_blocks:
                                    block = tool_use_blocks[-1]
                                    block.setdefault("_partial", "")
                                    block["_partial"] += event.delta.partial_json

                    # Finalise tool inputs from partial JSON
                    for block in tool_use_blocks:
                        partial = block.pop("_partial", "")
                        if partial:
                            try:
                                block["input"] = json.loads(partial)
                            except json.JSONDecodeError:
                                block["input"] = {}

                    # Capture usage + latency from the completed turn.
                    # get_final_message() is the Anthropic SDK's stable way
                    # to fetch the assembled Message (with .usage) after a
                    # stream. Guarded because older SDK versions may miss it.
                    input_tokens: int | None = None
                    output_tokens: int | None = None
                    try:
                        final = stream.get_final_message()
                        usage = getattr(final, "usage", None)
                        if usage is not None:
                            input_tokens = getattr(usage, "input_tokens", None)
                            output_tokens = getattr(usage, "output_tokens", None)
                    except Exception:
                        logger.debug("Could not read final message usage", exc_info=True)

                latency_ms = int((time.monotonic() - turn_start) * 1000)
                assistant_provenance = self._agent_provenance(
                    model_id=CHAT_MODEL,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                )

                # If no tool calls, we're done
                if not tool_use_blocks:
                    # Append assistant response to history
                    session.messages.append({
                        "role": "assistant",
                        "content": collected_text,
                    })

                    # Persist assistant message (non-blocking)
                    self._persist_message_bg(
                        session, role="assistant", content=collected_text,
                        sender_id=CHAT_AGENT_ID, sender_type="agent",
                        provenance=assistant_provenance,
                    )

                    # Run memory extraction in background
                    self._run_memory_extraction_bg(session, message, collected_text)

                    yield ChatEvent(type="done", data={"session_id": sid})
                    return

                # Build assistant message with content blocks
                assistant_content: list[dict[str, Any]] = []
                if collected_text:
                    assistant_content.append({"type": "text", "text": collected_text})
                for block in tool_use_blocks:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block["id"],
                        "name": block["name"],
                        "input": block["input"],
                    })

                session.messages.append({
                    "role": "assistant",
                    "content": assistant_content,
                })

                # Persist assistant message with tool calls (non-blocking)
                tool_text = collected_text or json.dumps(
                    [{"tool": b["name"], "input": b["input"]} for b in tool_use_blocks]
                )
                self._persist_message_bg(
                    session, role="assistant", content=tool_text,
                    sender_id=CHAT_AGENT_ID, sender_type="agent",
                    tool_calls=tool_use_blocks,
                    content_blocks=assistant_content,
                    provenance=assistant_provenance,
                )

                # Execute tool calls and build tool results
                tool_result_content: list[dict[str, Any]] = []
                for block in tool_use_blocks:
                    result = self._handle_tool_call(
                        block["name"], block["input"],
                        actor, guardrail_actor, company_id, session,
                    )

                    yield ChatEvent(
                        type="tool_result",
                        data={"tool": block["name"], "result": result},
                    )

                    # Emit inspection progress if in inspection mode
                    if session.mode == "inspection" and session.inspection_state:
                        state = session.inspection_state
                        yield ChatEvent(
                            type="inspection_progress",
                            data={
                                "current_index": state.current_index,
                                "total_items": len(state.template_items),
                                "completed_count": len(state.responses),
                                "current_item": (
                                    state.template_items[state.current_index]
                                    if state.current_index < len(state.template_items)
                                    else None
                                ),
                                "completed": state.completed,
                                "responses": state.responses,
                            },
                        )

                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": _safe_json_dumps(result),
                    })

                session.messages.append({
                    "role": "user",
                    "content": tool_result_content,
                })

                # Persist tool result message (non-blocking).
                # Tool-result messages are synthesised by the runtime, not
                # typed by the user, but they appear in the chat as
                # role="user" for the Anthropic API. We mark actor_type
                # "agent" so the Knowledge view can distinguish these
                # synthetic turns from real user typing.
                tool_result_provenance = {
                    **self._human_provenance(),
                    "actor_type": "agent",
                    "agent_id": CHAT_AGENT_ID,
                    "agent_version": CHAT_AGENT_VERSION,
                }
                self._persist_message_bg(
                    session, role="user",
                    content=json.dumps([{"tool_use_id": b["tool_use_id"], "summary": b["content"][:200]} for b in tool_result_content]),
                    sender_id=user_id, sender_type="member",
                    content_blocks=tool_result_content,
                    provenance=tool_result_provenance,
                )

                # System prompt (including inspection state and active
                # project contents) is rebuilt at the top of the next
                # iteration — no need to rebuild here.

                # If inspection completed, stop the loop
                if (
                    session.mode == "inspection"
                    and session.inspection_state
                    and session.inspection_state.completed
                ):
                    # Let Claude generate one final summary message
                    continue

            except Exception as exc:
                err_str = str(exc).lower()
                # Auto-retry on overloaded/rate-limit (up to 2 retries with backoff)
                if ("overloaded" in err_str or "rate_limit" in err_str) and iteration < 2:
                    wait_secs = 3 * (iteration + 1)
                    logger.warning(
                        "API overloaded/rate-limited, retrying in %ds (attempt %d)",
                        wait_secs, iteration + 1,
                    )
                    time.sleep(wait_secs)
                    continue

                logger.exception("Chat stream error: %s", exc)
                if "overloaded" in err_str:
                    friendly = "The AI service is temporarily busy. Please try again in a moment."
                elif "rate_limit" in err_str:
                    friendly = "Rate limit reached. Please wait a moment and try again."
                else:
                    friendly = "Something went wrong. Please try again."
                yield ChatEvent(
                    type="error",
                    data={"message": friendly},
                )
                return

        yield ChatEvent(type="done", data={"session_id": sid})

    # ------------------------------------------------------------------
    # System prompt builders
    # ------------------------------------------------------------------

    def _build_system_prompt(self, session: ChatSession) -> str:
        if session.mode == "inspection" and session.inspection_state:
            return self._build_inspection_prompt(session.inspection_state)
        prompt = GENERAL_SYSTEM_PROMPT

        # Inject company context: projects + workers
        company_id = session.company_id
        try:
            driver = self.mcp_tools.driver
            with driver.session() as db_session:
                # Fetch projects
                proj_result = db_session.run(
                    "MATCH (c:Company {id: $cid})-[:OWNS_PROJECT]->(p:Project) "
                    "WHERE p.deleted = false "
                    "RETURN p.id AS id, p.name AS name, p.status AS status "
                    "ORDER BY p.status, p.name",
                    cid=company_id,
                )
                projects = [dict(r) for r in proj_result]

                # Fetch workers
                wkr_result = db_session.run(
                    "MATCH (c:Company {id: $cid})-[:EMPLOYS]->(w:Worker) "
                    "WHERE w.deleted = false "
                    "RETURN w.id AS id, w.first_name + ' ' + w.last_name AS name, "
                    "w.role AS role ORDER BY w.role, w.last_name",
                    cid=company_id,
                )
                workers = [dict(r) for r in wkr_result]

            if projects:
                prompt += "\n\nCOMPANY PROJECTS:"
                for p in projects:
                    prompt += f"\n- {p['name']} (id: {p['id']}, status: {p['status']})"

            if workers:
                prompt += f"\n\nCOMPANY WORKERS ({len(workers)} total):"
                for w in workers:
                    prompt += f"\n- {w['name']} (id: {w['id']}, role: {w['role']})"
        except Exception:
            pass  # Degrade gracefully — prompt still works without context

        if session.project_id:
            # Resolve project name for context clarity
            active_project_name = next(
                (p["name"] for p in projects if p.get("id") == session.project_id),
                None,
            )
            active_label = (
                f"{active_project_name} (id: {session.project_id})"
                if active_project_name
                else session.project_id
            )
            prompt += (
                f"\n\nACTIVE PROJECT CONTEXT: The user is currently viewing "
                f"{active_label} in the right-hand canvas pane. "
                "When the user's message uses pronouns ('it', 'this', 'that', 'the project'), "
                "demonstratives ('this project', 'this quote', 'this job'), or otherwise refers "
                "to something without naming it, assume they mean THIS project. "
                "Use this project_id as the default for all tool calls unless the user explicitly "
                "names a different project. Do not ask the user which project they mean — they "
                "are looking at it."
            )

            prompt += self._build_active_project_contents(company_id, session.project_id)

        prompt += self._build_recent_actions(session)

        return prompt

    def _build_recent_actions(self, session: ChatSession) -> str:
        """Summarise the agent's recent write actions in this session.

        Stops the agent hallucinating prior state ("it was already 5000") by
        explicitly listing the before/after values from the last handful of
        mutating tool calls. Only the most recent 8 write actions are
        included to keep the prompt bounded.
        """
        actions: list[str] = []
        MUTATING_PREFIXES = (
            "update_", "create_", "add_", "remove_", "delete_",
            "generate_", "set_",
        )
        # Map tool_use_id -> (tool_name, input) so we can pair with results.
        tool_use_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
        for msg in session.messages:
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    tool_use_by_id[block.get("id", "")] = (
                        block.get("name", ""),
                        block.get("input", {}) or {},
                    )
                elif block.get("type") == "tool_result":
                    tuid = block.get("tool_use_id", "")
                    pair = tool_use_by_id.get(tuid)
                    if not pair:
                        continue
                    tool_name, tool_input = pair
                    if not tool_name.startswith(MUTATING_PREFIXES):
                        continue
                    result_content = block.get("content", "")
                    if isinstance(result_content, list):
                        result_text = "".join(
                            c.get("text", "") for c in result_content if isinstance(c, dict)
                        )
                    else:
                        result_text = str(result_content)
                    try:
                        result = json.loads(result_text) if result_text else {}
                    except Exception:
                        result = {}
                    summary = self._summarise_tool_action(tool_name, tool_input, result)
                    if summary:
                        actions.append(summary)

        if not actions:
            return ""

        # Keep only the last 8 actions, most recent last.
        recent = actions[-8:]
        numbered = "\n".join(f"  {i + 1}. {a}" for i, a in enumerate(recent))
        return (
            "\n\nYOUR ACTION LOG THIS SESSION (ordered oldest → newest, last "
            f"{len(recent)} mutations):\n"
            f"{numbered}\n"
            "\nRules for interpreting this log:\n"
            "- Entries already reflect work YOU completed in this session. "
            "When you just called a tool and the user is now asking about "
            "what happened, the latest entry IS that action — do not describe "
            "it as 'earlier in our session' or 'you asked me to do X again'.\n"
            "- Use the 'qty A → B' notation as the authoritative before/after "
            "for that work item. Never claim 'was already at X' unless the "
            "log shows two consecutive identical states.\n"
            "- If the current graph state disagrees with the log's last "
            "write for a given entity, trust the log — the user or another "
            "agent may have changed it outside this conversation and you "
            "should flag that rather than silently override.\n"
            "- When the user questions a value, quote the specific log entry "
            "(e.g. 'Per my log, entry 3: update_work_item wi_abc quantity 3000 → 5000')."
        )

    @staticmethod
    def _summarise_tool_action(
        tool_name: str, tool_input: dict[str, Any], result: dict[str, Any]
    ) -> str:
        """Produce a one-line before/after summary of a mutating tool call."""
        if result.get("error"):
            return f"{tool_name} — ERROR: {result['error']}"
        target_id = (
            result.get("work_item_id")
            or result.get("assumption_id")
            or result.get("exclusion_id")
            or result.get("milestone_id")
            or result.get("condition_id")
            or tool_input.get("work_item_id")
            or tool_input.get("assumption_id")
            or tool_input.get("exclusion_id")
            or ""
        )
        desc = (
            result.get("description")
            or result.get("task")
            or result.get("statement")
            or tool_input.get("description")
            or tool_input.get("statement")
            or ""
        )
        prev_qty = result.get("previous_quantity")
        new_qty = result.get("quantity")
        ratio = result.get("scale_ratio")
        if tool_name == "update_work_item" and prev_qty is not None and new_qty is not None:
            scaled = ""
            if ratio and abs(ratio - 1.0) > 1e-6:
                scaled = f" (scaled children ×{ratio:.3g})"
            return (
                f"update_work_item {target_id} '{desc}': "
                f"quantity {prev_qty} → {new_qty}{scaled}"
            )
        if tool_name == "remove_work_item":
            return f"remove_work_item {target_id} '{desc}' — deleted"
        if tool_name == "create_work_item":
            q = tool_input.get("quantity")
            u = tool_input.get("unit") or ""
            qty_str = f" ({q} {u})" if q is not None else ""
            return f"create_work_item {target_id} '{desc}'{qty_str}"
        if tool_name in ("add_assumption", "update_assumption"):
            return f"{tool_name} {target_id}: {desc[:80]}"
        if tool_name in ("add_exclusion", "update_exclusion"):
            return f"{tool_name} {target_id}: {desc[:80]}"
        if tool_name == "remove_assumption":
            return f"remove_assumption {target_id} — deleted"
        if tool_name == "remove_exclusion":
            return f"remove_exclusion {target_id} — deleted"
        if tool_name == "create_labour":
            hours = tool_input.get("hours")
            return f"create_labour on wi {tool_input.get('work_item_id','')}: {desc} ({hours}h)"
        if tool_name == "create_item":
            q = tool_input.get("quantity")
            return f"create_item on wi {tool_input.get('work_item_id','')}: {desc} (qty {q})"
        if tool_name == "generate_proposal":
            return f"generate_proposal for project {tool_input.get('project_id','')}"
        # Generic fallback
        args = ", ".join(f"{k}={v}" for k, v in tool_input.items() if k != "notes")[:120]
        return f"{tool_name}({args})"

    def _build_active_project_contents(self, company_id: str, project_id: str) -> str:
        """Load the active project's work items, assumptions, exclusions, and
        contract terms so the agent knows what already exists and can update
        existing entities instead of creating duplicates.
        """
        section = ""
        try:
            driver = self.mcp_tools.driver
            with driver.session() as db_session:
                meta = db_session.run(
                    """
                    MATCH (c:Company {id: $cid})-[:OWNS_PROJECT]->(p:Project {id: $pid})
                    WHERE p.deleted = false
                    RETURN p.state AS state, p.status AS status,
                           p.contract_type AS contract_type,
                           p.project_type AS project_type
                    """,
                    cid=company_id, pid=project_id,
                ).single()
                if meta:
                    ct = meta.get("contract_type")
                    ct_label = ct.replace("_", " ") if ct else "not yet set"
                    section += (
                        f"\n\nACTIVE PROJECT METADATA: state={meta.get('state')}, "
                        f"status={meta.get('status')}, "
                        f"project_type={meta.get('project_type') or 'unspecified'}, "
                        f"contract_type={ct_label}. "
                    )
                    if not ct:
                        section += (
                            "Contract type is not set — when the user next "
                            "discusses pricing or billing, help them choose and "
                            "call set_contract_type."
                        )
                wi_rows = [dict(r) for r in db_session.run(
                    """
                    MATCH (c:Company {id: $cid})-[:OWNS_PROJECT]->(p:Project {id: $pid})
                          -[:HAS_WORK_ITEM]->(wi:WorkItem)
                    WHERE p.deleted = false AND coalesce(wi.deleted, false) = false
                    RETURN wi.id AS id, wi.description AS description,
                           wi.quantity AS quantity, wi.unit AS unit,
                           wi.state AS state,
                           wi.sell_price_cents AS sell_price_cents
                    ORDER BY wi.created_at
                    """,
                    cid=company_id, pid=project_id,
                )]
                assumption_rows = [dict(r) for r in db_session.run(
                    """
                    MATCH (c:Company {id: $cid})-[:OWNS_PROJECT]->(p:Project {id: $pid})
                          -[:HAS_ASSUMPTION]->(a:Assumption)
                    WHERE p.deleted = false AND coalesce(a.deleted, false) = false
                    RETURN a.id AS id, a.category AS category, a.statement AS statement
                    ORDER BY a.category
                    """,
                    cid=company_id, pid=project_id,
                )]
                exclusion_rows = [dict(r) for r in db_session.run(
                    """
                    MATCH (c:Company {id: $cid})-[:OWNS_PROJECT]->(p:Project {id: $pid})
                          -[:HAS_EXCLUSION]->(e:Exclusion)
                    WHERE p.deleted = false AND coalesce(e.deleted, false) = false
                    RETURN e.id AS id, e.category AS category, e.statement AS statement
                    ORDER BY e.category
                    """,
                    cid=company_id, pid=project_id,
                )]
                milestone_rows = [dict(r) for r in db_session.run(
                    """
                    MATCH (c:Company {id: $cid})-[:OWNS_PROJECT]->(p:Project {id: $pid})
                          -[:HAS_CONTRACT]->(:Contract)
                          -[:HAS_PAYMENT_MILESTONE]->(m:PaymentMilestone)
                    WHERE p.deleted = false
                    RETURN m.id AS id, m.description AS description,
                           m.percentage AS percentage,
                           m.fixed_amount_cents AS fixed_amount_cents,
                           m.trigger_condition AS trigger_condition
                    ORDER BY coalesce(m.sort_order, 0)
                    """,
                    cid=company_id, pid=project_id,
                )]
                condition_rows = [dict(r) for r in db_session.run(
                    """
                    MATCH (c:Company {id: $cid})-[:OWNS_PROJECT]->(p:Project {id: $pid})
                          -[:HAS_CONTRACT]->(:Contract)
                          -[:HAS_CONDITION]->(cond:Condition)
                    WHERE p.deleted = false
                    RETURN cond.id AS id, cond.category AS category,
                           cond.description AS description
                    ORDER BY cond.category
                    """,
                    cid=company_id, pid=project_id,
                )]
        except Exception:
            return ""  # Degrade gracefully — prompt still works without contents

        if wi_rows:
            section += f"\n\nEXISTING WORK ITEMS ON THIS PROJECT ({len(wi_rows)}):"
            for wi in wi_rows:
                qty_str = (
                    f"{wi['quantity']} {wi['unit']}"
                    if wi.get("quantity") is not None and wi.get("unit")
                    else "—"
                )
                price_str = (
                    f"${wi['sell_price_cents'] / 100:,.2f}"
                    if wi.get("sell_price_cents")
                    else "$0.00"
                )
                section += (
                    f"\n- {wi['description']} "
                    f"(id: {wi['id']}, qty: {qty_str}, price: {price_str}, "
                    f"state: {wi.get('state') or 'draft'})"
                )
            section += (
                "\n\nCRITICAL — MATCH EXISTING ITEMS BEFORE CREATING: When the user "
                "refers to changing, updating, or adjusting an item (e.g. 'make the LED one 4000', "
                "'change the panel quantity', 'update the concrete price', 'now going to be X'), "
                "match their reference to one of the work items above and use update_work_item "
                "with its id. Use fuzzy matching on descriptions — 'LED lights', 'LED lighting', "
                "'the LEDs', 'lighting system' all refer to any existing work item with 'LED' "
                "or 'lighting' in its description. Do NOT call create_work_item when the user is "
                "describing a change to something that already exists — that creates duplicates. "
                "Only call create_work_item when the user is adding genuinely new scope."
            )

        if assumption_rows:
            section += f"\n\nEXISTING ASSUMPTIONS ON THIS PROJECT ({len(assumption_rows)}):"
            for a in assumption_rows:
                section += f"\n- [{a.get('category') or 'general'}] {a['statement']} (id: {a['id']})"

        if exclusion_rows:
            section += f"\n\nEXISTING EXCLUSIONS ON THIS PROJECT ({len(exclusion_rows)}):"
            for e in exclusion_rows:
                section += f"\n- [{e.get('category') or 'general'}] {e['statement']} (id: {e['id']})"

        if milestone_rows:
            section += f"\n\nEXISTING PAYMENT MILESTONES ({len(milestone_rows)}):"
            for m in milestone_rows:
                if m.get("percentage") is not None:
                    amt = f"{m['percentage']}%"
                elif m.get("fixed_amount_cents") is not None:
                    amt = f"${m['fixed_amount_cents'] / 100:,.2f}"
                else:
                    amt = "—"
                trigger = m.get("trigger_condition") or "—"
                section += (
                    f"\n- {m['description']}: {amt} @ {trigger} (id: {m['id']})"
                )

        if condition_rows:
            section += f"\n\nEXISTING CONTRACT CONDITIONS ({len(condition_rows)}):"
            for c in condition_rows:
                section += (
                    f"\n- [{c.get('category') or 'general'}] {c['description']} "
                    f"(id: {c['id']})"
                )

        return section

    def _build_inspection_prompt(self, state: InspectionChatState) -> str:
        total = len(state.template_items)
        completed_count = len(state.responses)
        idx = state.current_index

        if idx < total:
            current = state.template_items[idx]
            current_item = current["description"]
            current_category = current["category"]
        else:
            current_item = "ALL ITEMS COMPLETE"
            current_category = "N/A"

        # Build completed summary
        completed_lines = []
        for item in state.template_items[:idx]:
            item_id = item["item_id"]
            if item_id in state.responses:
                resp = state.responses[item_id]
                status = resp.get("status", "?")
                notes = resp.get("notes", "")
                icon = {"pass": "PASS", "fail": "FAIL", "na": "N/A"}.get(status, status)
                line = f"  - [{icon}] {item['category']}: {item['description']}"
                if notes:
                    line += f" — {notes}"
                completed_lines.append(line)

        completed_summary = "\n".join(completed_lines) if completed_lines else "  (none yet)"

        return INSPECTION_SYSTEM_PROMPT_TEMPLATE.format(
            inspection_type=state.inspection_type.replace("_", " "),
            total_items=total,
            completed_count=completed_count,
            current_index=idx + 1,
            current_item=current_item,
            current_category=current_category,
            completed_summary=completed_summary,
        )

    # ------------------------------------------------------------------
    # Tool routing
    # ------------------------------------------------------------------

    def _get_tools(self, mode: str) -> list[dict[str, Any]]:
        if mode == "inspection":
            return INSPECTION_TOOLS
        return GENERAL_TOOLS

    def _handle_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        actor: Actor,
        guardrail_actor: Actor,
        company_id: str,
        session: ChatSession,
    ) -> dict[str, Any]:
        """Route a tool call to the correct handler.

        Args:
            tool_name: The MCP tool name.
            tool_input: The tool invocation parameters.
            actor: Agent actor for entity provenance (type='agent').
            guardrail_actor: Human actor for guardrail bypass (type='human').
            company_id: Tenant scope.
            session: The chat session.

        Returns:
            The tool result dict.
        """
        # Inspection-mode tools
        if tool_name in {
            "update_inspection_item", "skip_item", "go_back",
            "add_note", "complete_inspection",
        }:
            return self._handle_inspection_tool(tool_name, tool_input, actor, company_id, session)

        # Ad-hoc Cypher query
        if tool_name == "query_graph":
            return self._handle_query_graph(tool_input, company_id)

        # MCP tools — pass guardrail_actor so the human user's
        # authentication bypasses agent-specific guardrails (scope,
        # rate limit, budget), while the invoke_tool dispatch uses
        # actor for entity provenance on any mutations.
        return self.mcp_tools.invoke_tool(
            tool_name, actor, company_id, tool_input,
            guardrail_actor=guardrail_actor,
        )

    def _handle_query_graph(
        self, tool_input: dict[str, Any], company_id: str
    ) -> dict[str, Any]:
        cypher = tool_input.get("cypher", "")
        params = tool_input.get("params", {})

        # Safety: reject writes
        cypher_upper = cypher.upper().strip()
        for keyword in ("CREATE", "MERGE", "DELETE", "SET ", "REMOVE", "DROP", "DETACH"):
            if keyword in cypher_upper:
                return {"error": f"Write operations not allowed. Found: {keyword}"}

        # Inject company_id for safety
        params["company_id"] = company_id

        try:
            driver = self.mcp_tools.driver
            with driver.session() as db_session:
                result = db_session.run(cypher, **params)
                records = [dict(record) for record in result]

                # Serialise neo4j types
                serialised = []
                for record in records[:50]:  # Cap results
                    row = {}
                    for key, value in record.items():
                        if hasattr(value, "isoformat"):
                            row[key] = value.isoformat()
                        elif hasattr(value, "__dict__"):
                            row[key] = str(value)
                        else:
                            row[key] = value
                    serialised.append(row)

                return {
                    "results": serialised,
                    "count": len(serialised),
                    "truncated": len(records) > 50,
                }
        except Exception as exc:
            return {"error": f"Cypher query failed: {exc}"}

    # ------------------------------------------------------------------
    # Inspection tool handlers
    # ------------------------------------------------------------------

    def _handle_inspection_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        actor: Actor,
        company_id: str,
        session: ChatSession,
    ) -> dict[str, Any]:
        state = session.inspection_state
        if state is None:
            return {"error": "No active inspection session"}

        if tool_name == "update_inspection_item":
            item_id = tool_input.get("item_id", "")
            status = tool_input.get("status", "pass")
            notes = tool_input.get("notes", "")

            state.responses[item_id] = {"status": status, "notes": notes}

            # Advance to next item if updating the current one
            if state.current_index < len(state.template_items):
                current = state.template_items[state.current_index]
                if current["item_id"] == item_id:
                    state.current_index += 1

            remaining = len(state.template_items) - len(state.responses)
            return {
                "updated": item_id,
                "status": status,
                "notes": notes,
                "remaining_items": remaining,
                "all_complete": remaining == 0,
            }

        elif tool_name == "skip_item":
            if state.current_index < len(state.template_items):
                current = state.template_items[state.current_index]
                state.responses[current["item_id"]] = {"status": "na", "notes": "Skipped"}
                state.current_index += 1
            return {"skipped": True, "current_index": state.current_index}

        elif tool_name == "go_back":
            if state.current_index > 0:
                state.current_index -= 1
            current = state.template_items[state.current_index]
            return {
                "moved_to": state.current_index,
                "item": current,
                "previous_response": state.responses.get(current["item_id"]),
            }

        elif tool_name == "add_note":
            item_id = tool_input.get("item_id", "")
            note = tool_input.get("note", "")
            if item_id in state.responses:
                existing = state.responses[item_id].get("notes", "")
                state.responses[item_id]["notes"] = (
                    f"{existing}; {note}" if existing else note
                )
                return {"added_note": True, "item_id": item_id}
            return {"error": f"Item {item_id} not found in responses"}

        elif tool_name == "complete_inspection":
            return self._complete_inspection(
                state, actor, company_id, session.user_id,
                tool_input.get("overall_notes", ""),
                tool_input.get("corrective_actions", ""),
            )

        return {"error": f"Unknown inspection tool: {tool_name}"}

    def _complete_inspection(
        self,
        state: InspectionChatState,
        actor: Actor,
        company_id: str,
        user_id: str,
        overall_notes: str,
        corrective_actions: str,
    ) -> dict[str, Any]:
        # Build InspectionCreate from accumulated state
        items = []
        for template_item in state.template_items:
            item_id = template_item["item_id"]
            response = state.responses.get(item_id, {"status": "na", "notes": ""})
            items.append(InspectionItem(
                item_id=item_id,
                category=template_item["category"],
                description=template_item["description"],
                status=response["status"],
                notes=response.get("notes", ""),
                photo_url=None,
            ))

        inspection_data = InspectionCreate(
            inspection_type=state.inspection_type,
            inspection_date=date.today(),
            inspector_name=state.inspector_name or user_id,
            items=items,
            overall_notes=overall_notes,
            corrective_actions_needed=corrective_actions,
        )

        try:
            inspection = self.inspection_service.create(
                company_id=company_id,
                project_id=state.project_id,
                data=inspection_data,
                user_id=user_id,
            )

            # Emit event
            event = self.event_bus.create_event(
                event_type=EventType.INSPECTION_COMPLETED,
                entity_id=inspection.id,
                entity_type="Inspection",
                company_id=company_id,
                project_id=state.project_id,
                actor=actor,
                summary={
                    "inspection_type": state.inspection_type,
                    "overall_status": inspection.overall_status.value,
                    "total_items": len(items),
                    "passed": sum(1 for i in items if i.status == "pass"),
                    "failed": sum(1 for i in items if i.status == "fail"),
                },
            )
            self.event_bus.emit(event)

            state.completed = True

            return {
                "inspection_id": inspection.id,
                "overall_status": inspection.overall_status.value,
                "total_items": len(items),
                "passed": sum(1 for i in items if i.status == "pass"),
                "failed": sum(1 for i in items if i.status == "fail"),
                "na": sum(1 for i in items if i.status == "na"),
                "saved": True,
            }
        except Exception as exc:
            logger.exception("Failed to create inspection: %s", exc)
            return {"error": f"Failed to save inspection: {exc}"}

    # ------------------------------------------------------------------
    # Graph persistence (non-blocking)
    # ------------------------------------------------------------------

    def _ensure_conversation(self, session: ChatSession) -> None:
        """Create a Conversation node for this session if not already created.

        Stores the conversation_id on the session for subsequent message writes.
        Failures are logged but do not interrupt streaming.

        Args:
            session: The in-memory chat session.
        """
        if session.conversation_id or not self.conversation_service:
            return

        try:
            conv = self.conversation_service.create(
                company_id=session.company_id,
                data={
                    "mode": "chat",
                    "title": None,
                    "project_id": session.project_id,
                    "session_id": session.session_id,
                },
                user_id=session.user_id,
            )
            session.conversation_id = conv["id"]
            logger.info(
                "Created conversation %s for session %s",
                conv["id"],
                session.session_id,
            )
        except Exception:
            logger.warning(
                "Failed to create conversation for session %s",
                session.session_id,
                exc_info=True,
            )

    def _persist_message_bg(
        self,
        session: ChatSession,
        role: str,
        content: str,
        sender_id: str,
        sender_type: str = "member",
        tool_calls: list[dict[str, Any]] | None = None,
        content_blocks: list[dict[str, Any]] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> None:
        """Persist a message to Neo4j in the background thread pool.

        Fire-and-forget — does not block the streaming response.

        Args:
            session: The in-memory chat session.
            role: Message role (user/assistant/system).
            content: Message text content.
            sender_id: ID of the sender (Member or AgentIdentity).
            sender_type: Label of the sender node.
            tool_calls: Optional tool call blocks for entity linking.
            content_blocks: Structured Anthropic content blocks (for tool_use/tool_result).
            provenance: Optional per-turn provenance (actor_type, agent_id,
                agent_version, model_id, input_tokens, output_tokens,
                cost_cents, latency_ms, confidence). Persisted as
                properties on the Message node.
        """
        if not session.conversation_id or not self.message_service:
            return

        conv_id = session.conversation_id
        # Serialise structured blocks for Neo4j storage
        blocks_json = json.dumps(content_blocks) if content_blocks else None

        def _persist() -> None:
            try:
                msg = self.message_service.create(
                    conversation_id=conv_id,
                    data={
                        "role": role,
                        "content": content,
                        "content_blocks": blocks_json,
                    },
                    sender_id=sender_id,
                    sender_type=sender_type,
                    provenance=provenance,
                )
                msg_id = msg["id"]
                session.last_message_id = msg_id

                # Entity linking from tool calls
                if tool_calls:
                    self._link_entities_from_tools(msg_id, tool_calls)

                # Embedding generation
                if self.embedding_service and content:
                    self.embedding_service.embed_and_store_message(msg_id, content)

            except Exception:
                logger.warning(
                    "Failed to persist %s message for conversation %s",
                    role,
                    conv_id,
                    exc_info=True,
                )

        self._bg_pool.submit(_persist)

    @staticmethod
    def _human_provenance() -> dict[str, Any]:
        """Provenance block for a user-authored message."""
        return {
            "actor_type": "human",
            "agent_id": None,
            "agent_version": None,
            "model_id": None,
            "input_tokens": None,
            "output_tokens": None,
            "cost_cents": None,
            "latency_ms": None,
            "confidence": None,
        }

    @staticmethod
    def _agent_provenance(
        model_id: str,
        input_tokens: int | None,
        output_tokens: int | None,
        latency_ms: int | None,
        confidence: float | None = None,
    ) -> dict[str, Any]:
        """Provenance block for an assistant-authored turn."""
        cost_cents = None
        if input_tokens is not None and output_tokens is not None:
            cost_cents = _calculate_cost_cents(input_tokens, output_tokens)
        return {
            "actor_type": "agent",
            "agent_id": CHAT_AGENT_ID,
            "agent_version": CHAT_AGENT_VERSION,
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_cents": cost_cents,
            "latency_ms": latency_ms,
            "confidence": confidence,
        }

    def _run_memory_extraction_bg(
        self,
        session: ChatSession,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Run decision/insight extraction in the background.

        Args:
            session: The chat session.
            user_message: The user's message text.
            assistant_message: The assistant's response text.
        """
        if not session.conversation_id or not self.memory_extraction_service:
            return

        conv_id = session.conversation_id

        def _extract() -> None:
            self.memory_extraction_service.extract_and_persist(
                conversation_id=conv_id,
                user_message=user_message,
                assistant_message=assistant_message,
            )

        self._bg_pool.submit(_extract)

    def _link_entities_from_tools(
        self, message_id: str, tool_calls: list[dict[str, Any]]
    ) -> None:
        """Create REFERENCES relationships from a Message to entities mentioned in tool calls.

        Parses tool call parameters for entity IDs (patterns like 'xxx_hexhex')
        and creates (Message)-[:REFERENCES {entity_type}]->(entity) relationships.

        Args:
            message_id: The Message node ID.
            tool_calls: List of tool call dicts with 'name' and 'input'.
        """
        # Map parameter names to entity labels
        param_to_label = {
            "project_id": "Project",
            "worker_id": "Worker",
            "inspection_id": "Inspection",
            "equipment_id": "Equipment",
            "incident_id": "Incident",
            "hazard_report_id": "HazardReport",
            "daily_log_id": "DailyLog",
        }

        entity_refs: list[tuple[str, str]] = []  # (entity_id, entity_type)

        for tool_call in tool_calls:
            tool_input = tool_call.get("input", {})
            if not isinstance(tool_input, dict):
                continue

            for param, label in param_to_label.items():
                entity_id = tool_input.get(param)
                if entity_id and isinstance(entity_id, str):
                    entity_refs.append((entity_id, label))

        if not entity_refs:
            return

        try:
            driver = self.mcp_tools.driver
            with driver.session() as db_session:
                for entity_id, entity_type in entity_refs:
                    db_session.run(
                        f"""
                        MATCH (msg:Message {{id: $message_id}})
                        MATCH (target:{entity_type} {{id: $entity_id}})
                        MERGE (msg)-[:REFERENCES {{entity_type: $entity_type}}]->(target)
                        """,
                        {
                            "message_id": message_id,
                            "entity_id": entity_id,
                            "entity_type": entity_type,
                        },
                    )
        except Exception:
            logger.warning(
                "Failed to link entities for message %s",
                message_id,
                exc_info=True,
            )

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _get_or_create_session(
        self,
        session_id: str,
        mode: str,
        company_id: str,
        project_id: str | None,
        user_id: str,
        inspection_type: str | None,
    ) -> ChatSession:
        if session_id in self._sessions:
            return self._sessions[session_id]

        inspection_state = None
        if mode == "inspection" and inspection_type and project_id:
            template_items = self.template_service.get_template_dicts(inspection_type)
            inspection_state = InspectionChatState(
                template_items=template_items,
                inspection_type=inspection_type,
                project_id=project_id,
            )

        session = ChatSession(
            session_id=session_id,
            mode=mode,
            company_id=company_id,
            project_id=project_id,
            user_id=user_id,
            inspection_state=inspection_state,
        )

        # Recover conversation history from Neo4j (survives backend restarts)
        try:
            recovered = self._recover_messages_from_graph(session_id)
            if recovered:
                recovered = self._validate_recovered_messages(recovered)
                if recovered:
                    session.messages = recovered
                    logger.info(
                        "Recovered %d messages for session %s from Neo4j",
                        len(recovered), session_id,
                    )
        except Exception as exc:
            logger.warning("Message recovery failed for %s: %s", session_id, exc)

        self._sessions[session_id] = session
        return session

    def _recover_messages_from_graph(self, session_id: str) -> list[dict[str, Any]]:
        """Recover conversation messages from Neo4j for a session.

        Queries the Conversation node by session_id, then retrieves
        all linked Message nodes in order.  When structured content_blocks
        are available (tool_use / tool_result messages), the original
        Anthropic API format is reconstructed so Claude maintains context.

        Args:
            session_id: The chat session ID.

        Returns:
            A list of Anthropic-compatible message dicts or empty list.
        """
        if not self.message_service:
            return []
        with self.message_service.driver.session() as db_session:
            result = db_session.run(
                """
                MATCH (conv:Conversation {session_id: $sid})
                WHERE conv.deleted = false
                OPTIONAL MATCH (conv)<-[:PART_OF]-(m:Message)
                WITH m ORDER BY m.timestamp ASC
                WHERE m IS NOT NULL
                RETURN m.role AS role, m.content AS content,
                       m.content_blocks AS content_blocks
                """,
                {"sid": session_id},
            )
            messages: list[dict[str, Any]] = []
            for record in result:
                role = record["role"]
                content_blocks = record["content_blocks"]
                content = record["content"]
                if not role:
                    continue

                if content_blocks:
                    # Structured message — restore exact Anthropic format
                    try:
                        messages.append({
                            "role": role,
                            "content": json.loads(content_blocks),
                        })
                    except (json.JSONDecodeError, TypeError):
                        # Fallback to flat text if JSON is corrupt
                        if content:
                            messages.append({"role": role, "content": content})
                elif content:
                    # Plain text message
                    messages.append({"role": role, "content": content})
            return messages

    @staticmethod
    def _validate_recovered_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate that recovered messages form a valid Anthropic conversation.

        Ensures every tool_use block has a matching tool_result in the next
        message.  If the conversation is malformed (e.g. tool results were
        not persisted before the fix), truncate to the last valid point.
        """
        valid: list[dict[str, Any]] = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            # Check if this assistant message contains tool_use blocks
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                has_tool_use = any(
                    isinstance(b, dict) and b.get("type") == "tool_use"
                    for b in msg["content"]
                )
                if has_tool_use:
                    # Next message must be a user message with tool_result blocks
                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        if (
                            next_msg.get("role") == "user"
                            and isinstance(next_msg.get("content"), list)
                            and any(
                                isinstance(b, dict) and b.get("type") == "tool_result"
                                for b in next_msg["content"]
                            )
                        ):
                            # Valid pair — keep both
                            valid.append(msg)
                            valid.append(next_msg)
                            i += 2
                            continue
                    # Malformed — tool_use without tool_result. Truncate here.
                    logger.warning(
                        "Truncating recovered messages at index %d: "
                        "tool_use without matching tool_result",
                        i,
                    )
                    break
            valid.append(msg)
            i += 1
        return valid

    def _cleanup_expired_sessions(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, session in self._sessions.items()
            if (now - datetime.fromisoformat(session.last_active)).total_seconds()
            > SESSION_TTL_SECONDS
        ]
        for sid in expired:
            del self._sessions[sid]
