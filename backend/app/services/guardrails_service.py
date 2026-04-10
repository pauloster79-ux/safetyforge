"""Guardrails service — action classification, rate limiting, approval queue.

Pre-execution guard that checks scopes, rate limits, and budget before
tool execution. High-risk writes go to an approval queue stored in Neo4j.
"""

import logging
import secrets
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from neo4j import Driver

from app.exceptions import AgentBudgetExceededError, AgentNotFoundError
from app.models.actor import Actor
from app.models.guardrails import (
    ActionClass,
    ApprovalRequest,
    ApprovalStatus,
    GuardrailCheckResult,
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool → action class mapping
# ---------------------------------------------------------------------------

TOOL_ACTION_MAP: dict[str, ActionClass] = {
    # Read-only tools
    "check_worker_compliance": ActionClass.READ_ONLY,
    "check_project_compliance": ActionClass.READ_ONLY,
    "get_project_summary": ActionClass.READ_ONLY,
    "get_worker_profile": ActionClass.READ_ONLY,
    "generate_morning_brief": ActionClass.READ_ONLY,
    "get_changes_since": ActionClass.READ_ONLY,
    "get_inspection_results": ActionClass.READ_ONLY,
    "get_regulatory_requirements": ActionClass.READ_ONLY,
    "query_graph": ActionClass.READ_ONLY,
    # Low-risk write tools
    "report_hazard": ActionClass.LOW_RISK_WRITE,
    "report_incident": ActionClass.LOW_RISK_WRITE,
    "create_inspection": ActionClass.LOW_RISK_WRITE,
    "generate_toolbox_talk": ActionClass.LOW_RISK_WRITE,
    "generate_safety_plan": ActionClass.LOW_RISK_WRITE,
    "assign_worker_to_project": ActionClass.LOW_RISK_WRITE,
    # High-risk write tools
    "resolve_corrective_action": ActionClass.HIGH_RISK_WRITE,
    "update_worker_certification": ActionClass.HIGH_RISK_WRITE,
    "override_compliance_flag": ActionClass.HIGH_RISK_WRITE,
}

# Scope required per tool — maps tool name to required scope prefix
TOOL_SCOPE_MAP: dict[str, str] = {
    "check_worker_compliance": "read:compliance",
    "check_project_compliance": "read:compliance",
    "get_project_summary": "read:projects",
    "get_worker_profile": "read:workers",
    "generate_morning_brief": "read:briefings",
    "get_changes_since": "read:projects",
    "get_inspection_results": "read:inspections",
    "get_regulatory_requirements": "read:compliance",
    "query_graph": "read:all",
    "report_hazard": "write:hazards",
    "report_incident": "write:incidents",
    "create_inspection": "write:inspections",
    "resolve_corrective_action": "write:safety",
    "update_worker_certification": "write:workers",
    "override_compliance_flag": "write:compliance",
    "generate_toolbox_talk": "write:safety",
    "generate_safety_plan": "write:documents",
    "assign_worker_to_project": "write:projects",
}


# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per-agent)
# ---------------------------------------------------------------------------


class AgentRateLimiter:
    """In-memory rate limiter using sliding window counters.

    Each agent has a per-minute call limit stored on the BELONGS_TO
    relationship. This limiter tracks calls in a 60-second window.
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, agent_id: str, limit: int) -> tuple[bool, int]:
        """Check if an agent is within its rate limit.

        Args:
            agent_id: The agent to check.
            limit: Maximum calls per minute.

        Returns:
            Tuple of (allowed, remaining_calls).
        """
        now = time.time()
        window = self._windows[agent_id]

        # Prune entries older than 60 seconds
        cutoff = now - 60.0
        window[:] = [t for t in window if t > cutoff]

        remaining = max(0, limit - len(window))
        if len(window) >= limit:
            return False, 0

        return True, remaining

    def record(self, agent_id: str) -> None:
        """Record a call for rate limiting.

        Args:
            agent_id: The agent that made the call.
        """
        self._windows[agent_id].append(time.time())

    def clear(self) -> None:
        """Clear all rate limit state (for testing)."""
        self._windows.clear()


# ---------------------------------------------------------------------------
# GuardrailsService
# ---------------------------------------------------------------------------


class GuardrailsService(BaseService):
    """Pre-execution guard for agent tool invocations.

    Checks in order:
    1. Agent exists and is active
    2. Agent has required scope for the tool
    3. Agent is within rate limits
    4. Agent hasn't exceeded budget
    5. Action class determines whether to proceed or queue for approval

    Approval queue is stored in Neo4j as ApprovalRequest nodes.
    """

    def __init__(self, driver: Driver) -> None:
        """Initialise the guardrails service.

        Args:
            driver: Neo4j driver instance.
        """
        super().__init__(driver)
        self._rate_limiter = AgentRateLimiter()

    def classify_tool(self, tool_name: str) -> ActionClass:
        """Classify a tool's action class.

        Args:
            tool_name: The MCP tool name.

        Returns:
            The action classification. Defaults to HIGH_RISK_WRITE for unknown tools.
        """
        return TOOL_ACTION_MAP.get(tool_name, ActionClass.HIGH_RISK_WRITE)

    def check_scope(self, tool_name: str, agent_scopes: tuple[str, ...] | list[str]) -> bool:
        """Check if an agent has the required scope for a tool.

        A scope of 'read:all' or 'write:all' grants universal access
        for that action type.

        Args:
            tool_name: The MCP tool name.
            agent_scopes: The agent's granted scopes.

        Returns:
            True if the agent has sufficient scope.
        """
        required = TOOL_SCOPE_MAP.get(tool_name)
        if required is None:
            return False

        action, domain = required.split(":")
        scopes = list(agent_scopes)

        # Direct match
        if required in scopes:
            return True

        # Wildcard domain
        if f"{action}:all" in scopes:
            return True

        # Write scope implies read for the same domain
        if action == "read" and f"write:{domain}" in scopes:
            return True
        if action == "read" and "write:all" in scopes:
            return True

        return False

    def pre_execution_check(
        self,
        agent_id: str,
        company_id: str,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
        reasoning: str = "",
        confidence: float | None = None,
    ) -> GuardrailCheckResult:
        """Run all pre-execution guardrail checks.

        Args:
            agent_id: The agent requesting the action.
            company_id: The company context.
            tool_name: The MCP tool being invoked.
            parameters: Tool invocation parameters.
            reasoning: Agent's reasoning for the action.
            confidence: Agent's confidence level.

        Returns:
            A GuardrailCheckResult indicating whether to proceed.
        """
        action_class = self.classify_tool(tool_name)

        # 1. Verify agent exists, is active, and get scopes + rate limit
        agent_data = self._get_agent_data(agent_id, company_id)
        if agent_data is None:
            return GuardrailCheckResult(
                allowed=False,
                action_class=action_class,
                reason=f"Agent {agent_id} not found or not active in company {company_id}",
            )

        # 2. Check scope
        scopes = agent_data["scopes"]
        if not self.check_scope(tool_name, scopes):
            return GuardrailCheckResult(
                allowed=False,
                action_class=action_class,
                reason=f"Agent lacks required scope for tool '{tool_name}'. "
                       f"Has: {scopes}. Needs: {TOOL_SCOPE_MAP.get(tool_name, 'unknown')}",
            )

        # 3. Check rate limit
        rate_limit = agent_data["rate_limit"]
        allowed, remaining = self._rate_limiter.check(agent_id, rate_limit)
        if not allowed:
            return GuardrailCheckResult(
                allowed=False,
                action_class=action_class,
                reason=f"Rate limit exceeded: {rate_limit} calls/minute",
                rate_limit_remaining=0,
            )

        # 4. Check budget
        if agent_data["daily_spend_cents"] >= agent_data["daily_budget_cents"]:
            return GuardrailCheckResult(
                allowed=False,
                action_class=action_class,
                reason=f"Daily budget exceeded: spent {agent_data['daily_spend_cents']} "
                       f"of {agent_data['daily_budget_cents']} cents",
            )

        # 5. Action class routing
        if action_class == ActionClass.HIGH_RISK_WRITE:
            # Queue for approval
            request_id = self._create_approval_request(
                agent_id=agent_id,
                agent_name=agent_data["name"],
                company_id=company_id,
                tool_name=tool_name,
                parameters=parameters or {},
                reasoning=reasoning,
                confidence=confidence,
            )
            return GuardrailCheckResult(
                allowed=False,
                action_class=action_class,
                reason="High-risk write requires human approval",
                approval_request_id=request_id,
                rate_limit_remaining=remaining,
            )

        # Read-only or low-risk write — proceed
        self._rate_limiter.record(agent_id)
        return GuardrailCheckResult(
            allowed=True,
            action_class=action_class,
            rate_limit_remaining=remaining - 1,
        )

    def get_pending_approvals(self, company_id: str) -> list[ApprovalRequest]:
        """List pending approval requests for a company.

        Args:
            company_id: The company to list approvals for.

        Returns:
            List of pending ApprovalRequest objects.
        """
        results = self._read_tx(
            """
            MATCH (ar:ApprovalRequest {company_id: $company_id, status: $status})
            RETURN ar {.*} AS request
            ORDER BY ar.created_at DESC
            """,
            {"company_id": company_id, "status": ApprovalStatus.PENDING.value},
        )
        return [self._to_approval_request(r["request"]) for r in results]

    def review_approval(
        self,
        request_id: str,
        company_id: str,
        reviewer_id: str,
        approved: bool,
        comment: str = "",
    ) -> ApprovalRequest | None:
        """Review (approve or reject) an approval request.

        Args:
            request_id: The approval request ID.
            company_id: The company context.
            reviewer_id: User ID of the reviewer.
            approved: Whether to approve the request.
            comment: Optional reviewer comment.

        Returns:
            The updated ApprovalRequest, or None if not found.
        """
        new_status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        now = datetime.now(timezone.utc).isoformat()

        result = self._write_tx_single(
            """
            MATCH (ar:ApprovalRequest {
                request_id: $request_id,
                company_id: $company_id,
                status: $pending_status
            })
            SET ar.status = $new_status,
                ar.reviewed_by = $reviewer_id,
                ar.reviewed_at = $now,
                ar.review_comment = $comment
            RETURN ar {.*} AS request
            """,
            {
                "request_id": request_id,
                "company_id": company_id,
                "pending_status": ApprovalStatus.PENDING.value,
                "new_status": new_status.value,
                "reviewer_id": reviewer_id,
                "now": now,
                "comment": comment,
            },
        )

        if result is None:
            return None

        return self._to_approval_request(result["request"])

    def _get_agent_data(self, agent_id: str, company_id: str) -> dict[str, Any] | None:
        """Fetch agent data including scopes and rate limit from graph.

        Args:
            agent_id: The agent's identifier.
            company_id: The company context.

        Returns:
            Dict with agent data, or None if not found/inactive.
        """
        import json

        result = self._read_tx_single(
            """
            MATCH (a:AgentIdentity {agent_id: $agent_id, status: 'active'})
                  -[r:BELONGS_TO]->(c:Company {id: $company_id})
            RETURN a.name AS name,
                   a.scopes AS scopes,
                   a.daily_budget_cents AS daily_budget_cents,
                   coalesce(a.daily_spend_cents, 0) AS daily_spend_cents,
                   coalesce(r.rate_limit_per_minute, 60) AS rate_limit
            """,
            {"agent_id": agent_id, "company_id": company_id},
        )

        if result is None:
            return None

        scopes = result["scopes"]
        if isinstance(scopes, str):
            scopes = json.loads(scopes)

        return {
            "name": result["name"],
            "scopes": scopes,
            "daily_budget_cents": result["daily_budget_cents"],
            "daily_spend_cents": result["daily_spend_cents"],
            "rate_limit": result["rate_limit"],
        }

    def _create_approval_request(
        self,
        agent_id: str,
        agent_name: str,
        company_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        reasoning: str = "",
        confidence: float | None = None,
    ) -> str:
        """Create an approval request node in Neo4j.

        Args:
            agent_id: The requesting agent.
            agent_name: Human-readable agent name.
            company_id: Tenant scope.
            tool_name: The tool being invoked.
            parameters: Tool parameters.
            reasoning: Agent's reasoning.
            confidence: Agent's confidence.

        Returns:
            The generated request_id.
        """
        import json

        request_id = f"apr_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()

        self._write_tx(
            """
            CREATE (ar:ApprovalRequest {
                request_id: $request_id,
                agent_id: $agent_id,
                agent_name: $agent_name,
                company_id: $company_id,
                tool_name: $tool_name,
                action_class: $action_class,
                parameters_json: $parameters_json,
                reasoning: $reasoning,
                confidence: $confidence,
                status: $status,
                created_at: $now,
                timeout_hours: 24
            })
            """,
            {
                "request_id": request_id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "company_id": company_id,
                "tool_name": tool_name,
                "action_class": ActionClass.HIGH_RISK_WRITE.value,
                "parameters_json": json.dumps(parameters),
                "reasoning": reasoning,
                "confidence": confidence,
                "status": ApprovalStatus.PENDING.value,
                "now": now,
            },
        )

        logger.info(
            "Approval request created: request_id=%s agent=%s tool=%s",
            request_id,
            agent_id,
            tool_name,
        )
        return request_id

    @staticmethod
    def _to_approval_request(data: dict[str, Any]) -> ApprovalRequest:
        """Convert a Neo4j result dict to an ApprovalRequest model.

        Args:
            data: Dict of node properties.

        Returns:
            An ApprovalRequest instance.
        """
        import json

        params = data.get("parameters_json", "{}")
        if isinstance(params, str):
            params = json.loads(params)

        return ApprovalRequest(
            request_id=data["request_id"],
            agent_id=data["agent_id"],
            agent_name=data.get("agent_name", ""),
            company_id=data["company_id"],
            tool_name=data["tool_name"],
            action_class=data.get("action_class", ActionClass.HIGH_RISK_WRITE.value),
            parameters=params,
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence"),
            status=data["status"],
            created_at=data.get("created_at", ""),
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=data.get("reviewed_at"),
            review_comment=data.get("review_comment"),
            timeout_hours=data.get("timeout_hours", 24),
        )
