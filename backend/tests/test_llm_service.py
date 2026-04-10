"""Tests for LLMService — circuit breaker and cost calculation logic.

The LLM service depends on Anthropic's API, so we test the internal
mechanics (circuit breaker, cost calculation) without making real API calls.
External dependency mocking is allowed per test conventions.
"""

import time

import pytest

from app.services.llm_service import CircuitBreakerState


# ---------------------------------------------------------------------------
# Circuit breaker tests
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    """Tests for the CircuitBreakerState circuit breaker."""

    def test_not_tripped_initially(self) -> None:
        """New circuit breaker is not tripped."""
        breaker = CircuitBreakerState()
        assert breaker.is_tripped() is False

    def test_trips_on_high_spend(self) -> None:
        """Circuit breaker trips when spend exceeds threshold."""
        breaker = CircuitBreakerState()
        # Record spend that exceeds the $5 threshold
        for _ in range(10):
            breaker.record(60.0)  # 10 * 60 = $6 > $5 threshold

        assert breaker.is_tripped() is True

    def test_does_not_trip_on_normal_spend(self) -> None:
        """Circuit breaker stays open on normal spend levels."""
        breaker = CircuitBreakerState()
        for _ in range(5):
            breaker.record(10.0)  # 5 * 10 = 50 cents, well under $5

        assert breaker.is_tripped() is False

    def test_old_entries_pruned(self) -> None:
        """Old spend entries are pruned from the window."""
        breaker = CircuitBreakerState()

        # Record high spend with old timestamps
        old_time = time.time() - 400  # older than 5-minute window
        breaker.spend_window = [(old_time, 600.0)]

        # Record a small new entry to trigger pruning
        breaker.record(1.0)

        # Old entry should be pruned, total should be just 1.0
        assert breaker.is_tripped() is False
        assert len(breaker.spend_window) == 1

    def test_cooldown_period(self) -> None:
        """Tripped breaker stays tripped during cooldown."""
        breaker = CircuitBreakerState()
        breaker.tripped = True
        breaker.tripped_at = time.time()  # just now

        assert breaker.is_tripped() is True

    def test_resets_after_cooldown(self) -> None:
        """Tripped breaker resets after cooldown period."""
        breaker = CircuitBreakerState()
        breaker.tripped = True
        breaker.tripped_at = time.time() - 700  # 700s > 600s cooldown

        assert breaker.is_tripped() is False
        assert breaker.tripped is False
