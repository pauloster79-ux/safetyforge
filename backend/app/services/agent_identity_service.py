"""AgentIdentity service — CRUD and lifecycle management for AI agents.

Agents are first-class graph citizens. The BELONGS_TO relationship from
AgentIdentity to Company IS the agent's permission boundary.
"""

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from app.exceptions import AgentNotFoundError, AgentBudgetExceededError
from app.models.agent_identity import (
    AgentIdentity,
    AgentIdentityCreate,
    AgentIdentityUpdate,
    AgentSpendReport,
    AgentStatus,
)
from app.services.base_service import BaseService


class AgentIdentityService(BaseService):
    """Manages AgentIdentity nodes and their company relationships.

    Permission = traversability: an agent can only reach data that
    is traversable from its owning Company via the BELONGS_TO edge.
    """

    def register(
        self, company_id: str, data: AgentIdentityCreate, registered_by: str
    ) -> AgentIdentity:
        """Register a new agent for a company.

        Creates an AgentIdentity node and a BELONGS_TO relationship
        to the company with the agent's scopes.

        Args:
            company_id: The company this agent belongs to.
            data: Validated agent registration data.
            registered_by: User ID of the admin registering the agent.

        Returns:
            The created AgentIdentity.
        """
        agent_id = f"agt_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()
        scopes_json = json.dumps(data.scopes)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:AgentIdentity {
                agent_id: $agent_id,
                name: $name,
                agent_type: $agent_type,
                status: $status,
                scopes: $scopes_json,
                model_tier: $model_tier,
                daily_budget_cents: $daily_budget_cents,
                daily_spend_cents: 0,
                created_at: $now,
                created_by: $registered_by
            })
            CREATE (a)-[:BELONGS_TO {
                scopes: $scopes_json,
                rate_limit_per_minute: 60
            }]->(c)
            CREATE (c)-[:HAS_AGENT]->(a)
            RETURN a {.*, company_id: c.id} AS agent
            """,
            {
                "company_id": company_id,
                "agent_id": agent_id,
                "name": data.name,
                "agent_type": data.agent_type.value,
                "status": AgentStatus.ACTIVE.value,
                "scopes_json": scopes_json,
                "model_tier": data.model_tier.value,
                "daily_budget_cents": data.daily_budget_cents,
                "now": now,
                "registered_by": registered_by,
            },
        )

        if result is None:
            from app.exceptions import CompanyNotFoundError
            raise CompanyNotFoundError(company_id)

        return self._to_model(result["agent"])

    def get(self, agent_id: str, company_id: str) -> AgentIdentity:
        """Fetch an agent by ID within a company scope.

        Args:
            agent_id: The agent's unique identifier.
            company_id: The company the agent belongs to.

        Returns:
            The AgentIdentity.

        Raises:
            AgentNotFoundError: If the agent doesn't exist in this company.
        """
        result = self._read_tx_single(
            """
            MATCH (a:AgentIdentity {agent_id: $agent_id})-[:BELONGS_TO]->(c:Company {id: $company_id})
            RETURN a {.*, company_id: c.id} AS agent
            """,
            {"agent_id": agent_id, "company_id": company_id},
        )

        if result is None:
            raise AgentNotFoundError(agent_id)

        return self._to_model(result["agent"])

    def list_for_company(self, company_id: str) -> list[AgentIdentity]:
        """List all agents belonging to a company.

        Args:
            company_id: The company to list agents for.

        Returns:
            A list of AgentIdentity objects.
        """
        results = self._read_tx(
            """
            MATCH (a:AgentIdentity)-[:BELONGS_TO]->(c:Company {id: $company_id})
            RETURN a {.*, company_id: c.id} AS agent
            ORDER BY a.created_at DESC
            """,
            {"company_id": company_id},
        )

        return [self._to_model(r["agent"]) for r in results]

    def update(
        self, agent_id: str, company_id: str, data: AgentIdentityUpdate
    ) -> AgentIdentity:
        """Update an agent's configuration.

        Args:
            agent_id: The agent's unique identifier.
            company_id: The company the agent belongs to.
            data: Fields to update (None values are skipped).

        Returns:
            The updated AgentIdentity.

        Raises:
            AgentNotFoundError: If the agent doesn't exist in this company.
        """
        updates: dict[str, Any] = {}
        if data.name is not None:
            updates["name"] = data.name
        if data.model_tier is not None:
            updates["model_tier"] = data.model_tier.value
        if data.daily_budget_cents is not None:
            updates["daily_budget_cents"] = data.daily_budget_cents
        if data.status is not None:
            updates["status"] = data.status.value
        if data.scopes is not None:
            updates["scopes"] = json.dumps(data.scopes)

        if not updates:
            return self.get(agent_id, company_id)

        set_clauses = ", ".join(f"a.{k} = ${k}" for k in updates)

        # Also update BELONGS_TO scopes if scopes changed
        scope_update = ""
        if data.scopes is not None:
            scope_update = ", r.scopes = $scopes"

        result = self._write_tx_single(
            f"""
            MATCH (a:AgentIdentity {{agent_id: $agent_id}})-[r:BELONGS_TO]->(c:Company {{id: $company_id}})
            SET {set_clauses}{scope_update}
            RETURN a {{.*, company_id: c.id}} AS agent
            """,
            {"agent_id": agent_id, "company_id": company_id, **updates},
        )

        if result is None:
            raise AgentNotFoundError(agent_id)

        return self._to_model(result["agent"])

    def suspend(self, agent_id: str, company_id: str) -> AgentIdentity:
        """Suspend an agent immediately (kill switch).

        Args:
            agent_id: The agent to suspend.
            company_id: The company the agent belongs to.

        Returns:
            The suspended AgentIdentity.
        """
        return self.update(
            agent_id,
            company_id,
            AgentIdentityUpdate(status=AgentStatus.SUSPENDED),
        )

    def record_spend(self, agent_id: str, cost_cents: int) -> None:
        """Record LLM spend for an agent and check budget.

        Args:
            agent_id: The agent that incurred the cost.
            cost_cents: Cost in cents to add.

        Raises:
            AgentBudgetExceededError: If the agent's daily budget is exceeded.
        """
        result = self._write_tx_single(
            """
            MATCH (a:AgentIdentity {agent_id: $agent_id})
            SET a.daily_spend_cents = coalesce(a.daily_spend_cents, 0) + $cost_cents
            RETURN a.daily_spend_cents AS spent, a.daily_budget_cents AS budget, a.name AS name
            """,
            {"agent_id": agent_id, "cost_cents": cost_cents},
        )

        if result is None:
            raise AgentNotFoundError(agent_id)

        if result["spent"] > result["budget"]:
            raise AgentBudgetExceededError(
                agent_id, result["name"], result["spent"], result["budget"]
            )

    def reset_daily_spend(self, company_id: str) -> int:
        """Reset daily spend for all agents in a company.

        Intended to be called by a daily scheduled job.

        Args:
            company_id: The company to reset spend for.

        Returns:
            Number of agents reset.
        """
        results = self._write_tx(
            """
            MATCH (a:AgentIdentity)-[:BELONGS_TO]->(c:Company {id: $company_id})
            SET a.daily_spend_cents = 0
            RETURN count(a) AS reset_count
            """,
            {"company_id": company_id},
        )
        return results[0]["reset_count"] if results else 0

    def get_spend_report(self, company_id: str) -> list[AgentSpendReport]:
        """Get spend report for all agents in a company.

        Args:
            company_id: The company to report on.

        Returns:
            A list of AgentSpendReport objects.
        """
        results = self._read_tx(
            """
            MATCH (a:AgentIdentity)-[:BELONGS_TO]->(c:Company {id: $company_id})
            RETURN a.agent_id AS agent_id,
                   a.name AS name,
                   a.agent_type AS agent_type,
                   a.daily_budget_cents AS daily_budget_cents,
                   coalesce(a.daily_spend_cents, 0) AS daily_spend_cents
            ORDER BY a.daily_spend_cents DESC
            """,
            {"company_id": company_id},
        )

        reports = []
        for r in results:
            budget = r["daily_budget_cents"]
            spent = r["daily_spend_cents"]
            reports.append(
                AgentSpendReport(
                    agent_id=r["agent_id"],
                    name=r["name"],
                    agent_type=r["agent_type"],
                    daily_budget_cents=budget,
                    daily_spend_cents=spent,
                    budget_remaining_cents=max(0, budget - spent),
                    budget_utilisation_pct=round((spent / budget) * 100, 1) if budget > 0 else 0.0,
                )
            )
        return reports

    def verify_agent_access(self, agent_id: str, company_id: str) -> AgentIdentity:
        """Verify an agent is active and has access to a company.

        Used by the authorization layer to validate agent requests.

        Args:
            agent_id: The agent's identifier.
            company_id: The company to check access for.

        Returns:
            The active AgentIdentity.

        Raises:
            AgentNotFoundError: If the agent doesn't exist or is not active.
        """
        agent = self.get(agent_id, company_id)
        if agent.status != AgentStatus.ACTIVE:
            raise AgentNotFoundError(agent_id)
        return agent

    @staticmethod
    def _to_model(data: dict[str, Any]) -> AgentIdentity:
        """Convert a Neo4j result dict to an AgentIdentity model.

        Args:
            data: Dict of node properties from Neo4j.

        Returns:
            An AgentIdentity instance.
        """
        scopes = data.get("scopes", "[]")
        if isinstance(scopes, str):
            scopes = json.loads(scopes)

        return AgentIdentity(
            agent_id=data["agent_id"],
            name=data["name"],
            agent_type=data["agent_type"],
            status=data["status"],
            scopes=scopes,
            model_tier=data["model_tier"],
            daily_budget_cents=data["daily_budget_cents"],
            daily_spend_cents=data.get("daily_spend_cents", 0) or 0,
            company_id=data["company_id"],
            created_at=data["created_at"],
            created_by=data["created_by"],
        )
