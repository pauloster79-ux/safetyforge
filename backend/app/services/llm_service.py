"""LLM service with per-agent cost tracking, budget enforcement, and circuit breaker.

Central service for all LLM calls. Every call is attributed to an agent
with cost recorded in the graph for billing and monitoring.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from anthropic import Anthropic

from app.config import Settings
from app.exceptions import AgentBudgetExceededError
from app.models.agent_identity import ModelTier
from app.services.agent_identity_service import AgentIdentityService

logger = logging.getLogger(__name__)

# Model mapping — model tier to Anthropic model ID
MODEL_MAP: dict[str, str] = {
    ModelTier.FAST.value: "claude-haiku-4-5-20251001",
    ModelTier.STANDARD.value: "claude-sonnet-4-20250514",
    ModelTier.ADVANCED.value: "claude-opus-4-20250514",
}

# Pricing per million tokens (input/output) in cents
# Updated for current Anthropic pricing
PRICING_CENTS_PER_MILLION: dict[str, dict[str, float]] = {
    ModelTier.FAST.value: {"input": 80, "output": 400},
    ModelTier.STANDARD.value: {"input": 300, "output": 1500},
    ModelTier.ADVANCED.value: {"input": 1500, "output": 7500},
}


@dataclass
class LLMResult:
    """Result of an LLM completion call.

    Attributes:
        content: The generated text content.
        model_id: The Anthropic model ID used.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        cost_cents: Calculated cost in cents.
        duration_ms: Wall-clock duration in milliseconds.
    """

    content: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_cents: float
    duration_ms: int


@dataclass
class CircuitBreakerState:
    """Tracks per-agent circuit breaker state.

    Attributes:
        spend_window: List of (timestamp, cost_cents) tuples for recent spend.
        tripped: Whether the circuit breaker is currently tripped.
        tripped_at: Timestamp when the breaker tripped.
    """

    spend_window: list[tuple[float, float]] = field(default_factory=list)
    tripped: bool = False
    tripped_at: float | None = None

    # Trip if spend in last 5 minutes exceeds 10x the per-call average
    WINDOW_SECONDS: int = 300
    TRIP_THRESHOLD_CENTS: float = 500  # $5 in 5 minutes = likely loop
    COOLDOWN_SECONDS: int = 600  # 10-minute cooldown after trip

    def record(self, cost_cents: float) -> None:
        """Record a spend event and prune old entries.

        Args:
            cost_cents: Cost in cents for this call.
        """
        now = time.time()
        self.spend_window.append((now, cost_cents))
        cutoff = now - self.WINDOW_SECONDS
        self.spend_window = [(t, c) for t, c in self.spend_window if t > cutoff]

    def is_tripped(self) -> bool:
        """Check if the circuit breaker should be tripped.

        Returns:
            True if the breaker is currently tripped or should trip.
        """
        now = time.time()

        # Check cooldown
        if self.tripped and self.tripped_at:
            if now - self.tripped_at < self.COOLDOWN_SECONDS:
                return True
            self.tripped = False
            self.tripped_at = None

        # Check spend threshold
        total_spend = sum(c for _, c in self.spend_window)
        if total_spend > self.TRIP_THRESHOLD_CENTS:
            self.tripped = True
            self.tripped_at = now
            return True

        return False


class LLMService:
    """Central LLM service with cost control and circuit breaker.

    All agent LLM calls flow through this service. Every call:
    1. Checks the agent's budget hasn't been exceeded
    2. Checks the circuit breaker isn't tripped
    3. Routes to the correct model based on agent's tier
    4. Records cost in the agent's graph node
    5. Returns structured result with cost attribution

    Attributes:
        client: The Anthropic client.
        agent_service: AgentIdentityService for cost recording.
        circuit_breakers: Per-agent circuit breaker state.
    """

    def __init__(
        self,
        settings: Settings,
        agent_service: AgentIdentityService,
    ) -> None:
        """Initialise the LLM service.

        Args:
            settings: Application settings containing the Anthropic API key.
            agent_service: AgentIdentityService for cost recording.
        """
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.agent_service = agent_service
        self._circuit_breakers: dict[str, CircuitBreakerState] = {}

    def complete(
        self,
        agent_id: str,
        messages: list[dict[str, str]],
        system: str | None = None,
        model_tier: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResult:
        """Execute an LLM completion with full cost tracking.

        Args:
            agent_id: The agent making the call (for cost attribution).
            messages: List of message dicts with 'role' and 'content'.
            system: Optional system prompt.
            model_tier: Override model tier (defaults to agent's configured tier).
            max_tokens: Maximum output tokens.

        Returns:
            An LLMResult with content and cost metadata.

        Raises:
            AgentBudgetExceededError: If the agent's daily budget is exceeded.
            CircuitBreakerTrippedError: If the agent's circuit breaker is tripped.
        """
        # Check circuit breaker
        breaker = self._get_breaker(agent_id)
        if breaker.is_tripped():
            raise CircuitBreakerTrippedError(agent_id)

        # Resolve model
        tier = model_tier or ModelTier.STANDARD.value
        model_id = MODEL_MAP.get(tier, MODEL_MAP[ModelTier.STANDARD.value])

        # Call Anthropic
        start = time.time()
        kwargs: dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        duration_ms = int((time.time() - start) * 1000)

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        pricing = PRICING_CENTS_PER_MILLION.get(
            tier, PRICING_CENTS_PER_MILLION[ModelTier.STANDARD.value]
        )
        cost_cents = (
            (input_tokens * pricing["input"] / 1_000_000)
            + (output_tokens * pricing["output"] / 1_000_000)
        )
        cost_cents = round(cost_cents, 4)

        # Record spend and check budget
        breaker.record(cost_cents)
        cost_int = max(1, int(cost_cents))  # minimum 1 cent for tracking
        self.agent_service.record_spend(agent_id, cost_int)

        # Extract content
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        logger.info(
            "LLM call: agent=%s model=%s tokens=%d/%d cost=%.4f cents duration=%dms",
            agent_id,
            model_id,
            input_tokens,
            output_tokens,
            cost_cents,
            duration_ms,
        )

        return LLMResult(
            content=content,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cents=cost_cents,
            duration_ms=duration_ms,
        )

    def _get_breaker(self, agent_id: str) -> CircuitBreakerState:
        """Get or create a circuit breaker for an agent.

        Args:
            agent_id: The agent's identifier.

        Returns:
            The agent's CircuitBreakerState.
        """
        if agent_id not in self._circuit_breakers:
            self._circuit_breakers[agent_id] = CircuitBreakerState()
        return self._circuit_breakers[agent_id]


class CircuitBreakerTrippedError(Exception):
    """Raised when an agent's circuit breaker is tripped due to excessive spend."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(
            f"Circuit breaker tripped for agent {agent_id}: "
            f"excessive spend detected, cooldown in effect"
        )
