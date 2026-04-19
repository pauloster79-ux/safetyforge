// ============================================================================
// Kerf Ontology — Validation Queries
// ============================================================================
// Run AFTER 06-sample-data.cypher
// Tests CQ coverage, structural integrity, and permission model
// ============================================================================


// ============================================================================
// CQ VALIDATION — Proving key questions are answerable
// ============================================================================

// CQ-001: Who is this client and what's our history?
MATCH (c:Company {id: "comp_jake01"})-[:OWNS_PROJECT]->(p:Project)-[:CLIENT_IS]->(contact:Contact)
RETURN contact.name, p.name, p.status, p.contract_value;
// Expected: Mrs Johnson, Kitchen remodel electrics, active, 240000

// CQ-023: What work remains on this job?
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
WHERE wi.state IN ['draft', 'scheduled', 'in_progress', 'on_hold']
RETURN wi.description, wi.state, wi.status,
       wi.labour_hours * wi.labour_rate AS labour_cost;
// Expected: 3 work items, showing state and calculated cost

// CQ-024: How much of specific work is complete?
MATCH (wi:WorkItem {id: "wi_sarah01"})-[:HAS_TIME_ENTRY]->(te:TimeEntry)
WITH wi, sum(duration.between(te.clock_in, te.clock_out).hours - te.break_minutes / 60.0) AS actual_hours
RETURN wi.description, wi.labour_hours AS estimated_hours, actual_hours;
// Expected: receptacles work item with estimated vs actual hours

// CQ-028: Who was on site today?
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_DAILY_LOG]->(dl:DailyLog {log_date: date("2026-04-21")})
MATCH (te:TimeEntry)-[:RECORDED_ON]->(dl)
MATCH (te)-[:LOGGED_BY]->(w:Worker)
RETURN w.name, te.clock_in, te.clock_out;
// Expected: Marco, 06:00 to 15:30

// CQ-036: Is this job on budget?
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
OPTIONAL MATCH (wi)-[ui:USES_ITEM]->()
WITH wi, sum(ui.quantity * ui.unit_cost) AS item_costs
RETURN
  sum(wi.labour_hours * wi.labour_rate + coalesce(wi.materials_allowance, 0) + coalesce(item_costs, 0)) AS total_estimated;
// Expected: sum of all work item costs

// CQ-043: What deficiency items are open? (Would work once DeficiencyList data added)
// MATCH (p:Project)-[:HAS_DEFICIENCY_LIST]->(dl)-[:HAS_DEFICIENCY]->(di:DeficiencyItem)
// WHERE di.status <> 'closed'
// RETURN di.description, di.status;

// CQ-050: Did we make money? (Simplified — shows contract value vs estimated cost)
MATCH (p:Project {id: "proj_dave01"})
MATCH (p)-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
RETURN p.name, p.contract_value,
       sum(coalesce(wi.labour_hours * wi.labour_rate, 0) + coalesce(wi.materials_allowance, 0)) AS total_cost;
// Note: Dave's sub work items have null labour (lump sum subs) — cost comes from sub contracts

// CQ-054: Which subs perform best?
MATCH (c:Company)-[:GC_OVER]->(sub:Company)
OPTIONAL MATCH (sub)<-[:PERFORMED_BY]-(wi:WorkItem)
RETURN sub.name, count(wi) AS work_items_assigned;

// CQ-055: What regulations apply to this activity?
MATCH (a:Activity {id: "act_working_at_height"})-[:REGULATED_BY]->(reg:Regulation)
WHERE reg.valid_until > date()
RETURN reg.reference, reg.title, reg.source;
// Expected: WAH_2005

// CQ-056: What certs does a worker need?
MATCH (a:Activity {id: "act_working_at_height"})-[:REGULATED_BY]->(reg)-[:REQUIRES_CONTROL]->(cert:CertificationType)
RETURN cert.name, reg.reference;
// Expected: Working at Height Trained, WAH_2005

// CQ-070: What jurisdiction is this company in?
MATCH (c:Company {id: "comp_jake01"})-[:IN_JURISDICTION]->(j:Jurisdiction)
RETURN j.code, j.name, j.default_currency, j.measurement_system, j.languages;
// Expected: UK, GBP, metric, [en, pl, ro]


// ============================================================================
// STRUCTURAL VALIDATION — Data integrity checks
// ============================================================================

// Every Project must be owned by a Company
MATCH (p:Project)
WHERE NOT (p)<-[:OWNS_PROJECT]-(:Company)
RETURN p.id AS orphan_project, "Project not owned by any Company" AS violation;
// Expected: empty (no orphans)

// Every WorkItem must belong to a Project (directly or via WorkPackage)
MATCH (wi:WorkItem)
WHERE NOT (wi)<-[:HAS_WORK_ITEM]-(:Project)
  AND NOT (wi)<-[:CONTAINS]-(:WorkPackage)<-[:HAS_WORK_PACKAGE]-(:Project)
RETURN wi.id AS orphan_work_item, "WorkItem not linked to any Project" AS violation;
// Expected: empty

// No cross-tenant paths (companies should not reach each other's data)
MATCH (c1:Company)-[:OWNS_PROJECT]->(p1:Project)-[:HAS_WORK_ITEM|HAS_WORK_PACKAGE*1..2]->(wi:WorkItem)<-[:HAS_WORK_ITEM|CONTAINS*1..2]-(p2:Project)<-[:OWNS_PROJECT]-(c2:Company)
WHERE c1 <> c2
RETURN c1.name, c2.name, "Cross-tenant work item detected" AS violation;
// Expected: empty

// Every Inspection has a conductor
MATCH (i:Inspection)
WHERE NOT (i)-[:CONDUCTED_BY]->()
RETURN i.id AS inspection_without_conductor, "Inspection missing CONDUCTED_BY" AS violation;
// Expected: empty

// Every WorkItem has a required state
MATCH (wi:WorkItem)
WHERE wi.state IS NULL OR NOT wi.state IN ['draft', 'scheduled', 'in_progress', 'complete', 'invoiced', 'on_hold', 'cancelled']
RETURN wi.id, wi.state, "Invalid or missing WorkItem state" AS violation;
// Expected: empty

// Every Invoice has a direction
MATCH (inv:Invoice)
WHERE inv.direction IS NULL OR NOT inv.direction IN ['receivable', 'payable']
RETURN inv.id, "Invoice missing direction" AS violation;
// Expected: empty

// Regulations have valid temporal data
MATCH (r:Regulation)
WHERE r.valid_from IS NULL OR r.valid_until IS NULL
RETURN r.reference, "Regulation missing temporal validity" AS violation;
// Expected: empty


// ============================================================================
// PERMISSION MODEL VALIDATION
// ============================================================================

// Can Jake reach his own project?
MATCH (m:Member {id: "mem_jake01"})<-[:HAS_MEMBER]-(c:Company)-[:OWNS_PROJECT]->(p:Project)
RETURN m.name, m.access_role, p.name;
// Expected: Jake, owner, Kitchen remodel

// Can Jake reach Sarah's project? (Should return nothing)
MATCH (m:Member {id: "mem_jake01"})<-[:HAS_MEMBER]-(c:Company)-[:OWNS_PROJECT]->(p:Project {id: "proj_sarah01"})
RETURN p.name AS should_be_empty;
// Expected: empty (no cross-tenant access)

// Can Dave see ABC Electric's insurance? (Via GC_OVER relationship)
MATCH (dave_co:Company {id: "comp_dave01"})-[:GC_OVER]->(sub:Company)-[:HAS_INSURANCE]->(cert:InsuranceCertificate)
RETURN sub.name, cert.carrier, cert.expiration_date;
// Expected: ABC Electric, State Farm, 2027-01-01


// ============================================================================
// WORK MODEL VALIDATION — Two-layer spine
// ============================================================================

// Jake: flat structure (Project → WorkItem directly)
MATCH (p:Project {id: "proj_jake01"})-[:HAS_WORK_ITEM]->(wi:WorkItem)
RETURN p.name, count(wi) AS work_items, "flat (no work packages)" AS structure;
// Expected: 3 work items, flat

// Sarah: grouped structure (Project → WorkPackage → WorkItem)
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_WORK_PACKAGE]->(wp:WorkPackage)-[:CONTAINS]->(wi:WorkItem)
RETURN p.name, wp.name, count(wi) AS items_in_package;
// Expected: Rough-In: 2 items, Trim: 1 item

// Dave: grouped with sub-performed items
MATCH (p:Project {id: "proj_dave01"})-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
OPTIONAL MATCH (wi)-[:PERFORMED_BY]->(sub:Company)
RETURN wp.name, wi.description, wi.state, sub.name AS performed_by;
// Expected: framing by own crew (null), electrical by ABC Electric, plumbing by Reliable Plumbing


// ============================================================================
// CONVERSATION & MESSAGE PROVENANCE (Phase 1)
// ============================================================================
// These queries enforce the AGENTIC_INFRASTRUCTURE provenance contract on
// assistant Messages. Any row returned indicates a structural violation.

// V-MSG-01: Every Message must have an actor_type.
MATCH (m:Message)
WHERE m.actor_type IS NULL
RETURN m.id AS missing_actor_type, "Message missing actor_type" AS violation
LIMIT 10;
// Expected: 0 rows

// V-MSG-02: Every assistant-authored Message must carry model_id.
MATCH (m:Message)
WHERE m.actor_type = "agent" AND m.model_id IS NULL
  AND NOT coalesce(m.content, "") STARTS WITH "[{\"tool_use_id\""
RETURN m.id AS missing_model, "Agent Message missing model_id" AS violation
LIMIT 10;
// Expected: 0 rows (tool_result synthetic messages are excluded)

// V-MSG-03: Every assistant-authored Message must carry agent_id + agent_version.
MATCH (m:Message)
WHERE m.actor_type = "agent" AND (m.agent_id IS NULL OR m.agent_version IS NULL)
RETURN m.id AS missing_agent_identity,
       m.agent_id AS agent_id, m.agent_version AS agent_version,
       "Agent Message missing agent identity" AS violation
LIMIT 10;
// Expected: 0 rows

// V-MSG-04: Cost must be non-negative when present.
MATCH (m:Message)
WHERE m.cost_cents IS NOT NULL AND m.cost_cents < 0
RETURN m.id AS bad_cost, m.cost_cents AS cost_cents,
       "Message has negative cost_cents" AS violation
LIMIT 10;
// Expected: 0 rows

// V-MSG-05: Every Message must belong to a Conversation via PART_OF.
MATCH (m:Message)
WHERE NOT (m)-[:PART_OF]->(:Conversation)
RETURN m.id AS orphan_message, "Message not attached to any Conversation" AS violation
LIMIT 10;
// Expected: 0 rows

// V-MSG-06: Every Conversation must belong to a Company via HAS_CONVERSATION.
MATCH (c:Conversation)
WHERE c.deleted = false AND NOT (:Company)-[:HAS_CONVERSATION]->(c)
RETURN c.id AS orphan_conversation, "Conversation not attached to any Company" AS violation
LIMIT 10;
// Expected: 0 rows

// V-MSG-07: Every Conversation must have a created_by actor.
MATCH (c:Conversation)
WHERE c.created_by IS NULL
RETURN c.id AS missing_creator, "Conversation missing created_by" AS violation
LIMIT 10;
// Expected: 0 rows

// V-MSG-08: scope_project_id, when set, must reference an existing Project
// owned by the same Company as the Message's Conversation. Prevents
// cross-tenant scope leaks.
MATCH (m:Message)-[:PART_OF]->(conv:Conversation)<-[:HAS_CONVERSATION]-(co:Company)
WHERE m.scope_project_id IS NOT NULL
  AND NOT EXISTS {
    MATCH (co)-[:OWNS_PROJECT]->(p:Project {id: m.scope_project_id})
  }
RETURN m.id AS bad_scope, m.scope_project_id AS scope_project_id,
       co.id AS company_id, "Message scope_project_id does not belong to its Company" AS violation
LIMIT 10;
// Expected: 0 rows


// ============================================================================
// CANONICAL WORK CATEGORIES VALIDATION
// ============================================================================

// V-CAT-01: Every Canonical WorkCategory must have code, jurisdiction_code, and level
MATCH (c:WorkCategory:Canonical)
WHERE c.code IS NULL OR c.jurisdiction_code IS NULL OR c.level IS NULL
RETURN c.id AS violation, "Canonical WorkCategory missing required property (code, jurisdiction_code, or level)" AS reason
LIMIT 10;
// Expected: 0 rows

// V-CAT-02: Every Extension WorkCategory must have PARENT_CATEGORY pointing to a Canonical
MATCH (c:WorkCategory:Extension)
WHERE NOT (c)-[:PARENT_CATEGORY]->(:WorkCategory:Canonical)
RETURN c.id AS violation, "Extension must have Canonical parent" AS reason
LIMIT 10;
// Expected: 0 rows

// V-CAT-03: No two Canonicals share the same jurisdiction_code + code
MATCH (c1:WorkCategory:Canonical), (c2:WorkCategory:Canonical)
WHERE c1.id < c2.id
  AND c1.jurisdiction_code = c2.jurisdiction_code
  AND c1.code = c2.code
RETURN [c1.id, c2.id] AS violation,
       c1.jurisdiction_code + " " + c1.code AS duplicated,
       "Duplicate canonical code within jurisdiction" AS reason
LIMIT 10;
// Expected: 0 rows

// V-CAT-04: Company-owned (HAS_WORK_CATEGORY) categories must be Extensions, not top-level Canonicals
MATCH (co:Company)-[:HAS_WORK_CATEGORY]->(cat:WorkCategory)
WHERE NOT cat:Extension
RETURN cat.id AS violation, co.id AS company_id,
       "Company-owned category must be :Extension, not top-level" AS reason
LIMIT 10;
// Expected: 0 rows

// V-CAT-05: CATEGORISED_AS on WorkItem must target a valid WorkCategory
MATCH (wi:WorkItem)-[:CATEGORISED_AS]->(cat)
WHERE NOT cat:WorkCategory
RETURN wi.id AS violation, "WorkItem CATEGORISED_AS target is not a WorkCategory" AS reason
LIMIT 10;
// Expected: 0 rows


// ============================================================================
// METHODOLOGY VALIDATION
// ============================================================================

// V-METH-01: Every Methodology must have an approach map (may be empty but present)
MATCH (m:Methodology)
WHERE m.approach IS NULL
RETURN m.id AS violation, "Methodology missing approach map" AS reason
LIMIT 10;
// Expected: 0 rows

// V-METH-02: Every non-project Methodology must have a CHILD_OF parent
MATCH (m:Methodology)
WHERE m.scope_level IN ["package", "item"]
  AND NOT (m)-[:CHILD_OF]->(:Methodology)
RETURN m.id AS violation, m.scope_level AS scope_level,
       "Non-project methodology missing CHILD_OF parent" AS reason
LIMIT 10;
// Expected: 0 rows

// V-METH-03: Every Methodology must APPLIES_TO_CATEGORY a Canonical WorkCategory
MATCH (m:Methodology)
WHERE NOT (m)-[:APPLIES_TO_CATEGORY]->(:WorkCategory:Canonical)
RETURN m.id AS violation, "Methodology missing APPLIES_TO_CATEGORY anchor" AS reason
LIMIT 10;
// Expected: 0 rows

// V-METH-04: CHILD_OF must go up the scope_level chain (item → package → project)
MATCH (m1:Methodology)-[:CHILD_OF]->(m2:Methodology)
WHERE NOT (
  (m1.scope_level = "package" AND m2.scope_level = "project")
  OR (m1.scope_level = "item" AND m2.scope_level = "package")
)
RETURN [m1.id, m2.id] AS violation,
       m1.scope_level + " -> " + m2.scope_level AS invalid_chain,
       "Invalid CHILD_OF hierarchy (must be item->package->project)" AS reason
LIMIT 10;
// Expected: 0 rows

// V-METH-05: Every active Methodology must have valid_from and valid_until sentinel or date
MATCH (m:Methodology)
WHERE m.valid_from IS NULL OR m.valid_until IS NULL
RETURN m.id AS violation, "Methodology missing valid_from/valid_until temporal metadata" AS reason
LIMIT 10;
// Expected: 0 rows


// ============================================================================
// SOURCE ENFORCEMENT VALIDATION (Labour + Item)
// ============================================================================

// V-SRC-01: Labour must have rate_source_id pointing to a ResourceRate
MATCH (l:Labour)
WHERE l.rate_source_id IS NULL
RETURN l.id AS violation, "Labour missing rate_source_id (fabricated rate)" AS reason
LIMIT 10;
// Expected: 0 rows (once enforcement is live)

// V-SRC-02: Labour rate_source_id must reference an existing active ResourceRate
MATCH (l:Labour)
WHERE l.rate_source_id IS NOT NULL
  AND NOT EXISTS {
    MATCH (rr:ResourceRate {id: l.rate_source_id})
    WHERE rr.active = true
  }
RETURN l.id AS violation, l.rate_source_id AS missing_rate,
       "Labour rate_source_id references non-existent or inactive ResourceRate" AS reason
LIMIT 10;
// Expected: 0 rows

// V-SRC-03: Item must have either price_source_id OR price_source_type="contractor_stated"
MATCH (it:Item)
WHERE it.price_source_id IS NULL
  AND (it.price_source_type IS NULL OR it.price_source_type <> "contractor_stated")
RETURN it.id AS violation, "Item missing price_source_id without contractor_stated tag" AS reason
LIMIT 10;
// Expected: 0 rows (once enforcement is live)

// V-SRC-04: Item price_source_id when set must reference MaterialCatalogEntry or Purchase-derived source
MATCH (it:Item)
WHERE it.price_source_id IS NOT NULL
  AND NOT EXISTS {
    MATCH (mce:MaterialCatalogEntry {id: it.price_source_id})
  }
RETURN it.id AS violation, it.price_source_id AS missing_catalog,
       "Item price_source_id references non-existent MaterialCatalogEntry" AS reason
LIMIT 10;
// Expected: 0 rows
