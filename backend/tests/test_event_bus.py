"""Tests for the in-process event bus, idempotency store, and dead-letter handling."""

import time

import pytest

from app.models.actor import Actor
from app.models.events import Event, EventActor, EventType
from app.services.event_bus import (
    DeadLetterEntry,
    EventBus,
    IdempotencyStore,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def event_bus() -> EventBus:
    """Return a fresh EventBus instance."""
    return EventBus()


@pytest.fixture()
def idempotency_store() -> IdempotencyStore:
    """Return a fresh IdempotencyStore instance."""
    return IdempotencyStore()


@pytest.fixture()
def sample_actor() -> Actor:
    """Return a test actor."""
    return Actor.human("test_user_001", company_id="comp_test_000001")


@pytest.fixture()
def sample_event(sample_actor: Actor) -> Event:
    """Return a sample event for testing."""
    return Event(
        event_id="evt_test_001",
        event_type=EventType.INSPECTION_COMPLETED,
        entity_id="insp_test_001",
        entity_type="Inspection",
        company_id="comp_test_000001",
        project_id="proj_test_000001",
        actor=EventActor.from_actor(sample_actor),
        summary={"total_items": 10, "passed": 8, "failed": 2},
        graph_context={"affected_workers": ["wkr_001"]},
    )


# ---------------------------------------------------------------------------
# IdempotencyStore tests
# ---------------------------------------------------------------------------


class TestIdempotencyStore:
    """Tests for the in-memory idempotency store."""

    def test_set_and_exists(self, idempotency_store: IdempotencyStore) -> None:
        """Stored keys should be retrievable."""
        idempotency_store.set("key1", {"result": "ok"})
        assert idempotency_store.exists("key1") is True

    def test_get_returns_cached_result(self, idempotency_store: IdempotencyStore) -> None:
        """Get should return the cached result."""
        idempotency_store.set("key1", {"status": "done"})
        assert idempotency_store.get("key1") == {"status": "done"}

    def test_nonexistent_key_returns_false(self, idempotency_store: IdempotencyStore) -> None:
        """Exists should return False for unknown keys."""
        assert idempotency_store.exists("missing") is False

    def test_get_nonexistent_returns_none(self, idempotency_store: IdempotencyStore) -> None:
        """Get should return None for unknown keys."""
        assert idempotency_store.get("missing") is None

    def test_ttl_expiry(self, idempotency_store: IdempotencyStore) -> None:
        """Entries with expired TTL should not be found."""
        idempotency_store.set("key1", "value", ttl_seconds=0.01)
        time.sleep(0.02)
        assert idempotency_store.exists("key1") is False
        assert idempotency_store.get("key1") is None

    def test_clear(self, idempotency_store: IdempotencyStore) -> None:
        """Clear should remove all entries."""
        idempotency_store.set("a", 1)
        idempotency_store.set("b", 2)
        idempotency_store.clear()
        assert idempotency_store.size == 0

    def test_prune_expired(self, idempotency_store: IdempotencyStore) -> None:
        """Prune should remove only expired entries."""
        idempotency_store.set("keep", "yes", ttl_seconds=3600)
        idempotency_store.set("expire", "no", ttl_seconds=0.01)
        time.sleep(0.02)
        removed = idempotency_store.prune_expired()
        assert removed == 1
        assert idempotency_store.exists("keep") is True
        assert idempotency_store.exists("expire") is False

    def test_size(self, idempotency_store: IdempotencyStore) -> None:
        """Size should reflect current entry count."""
        assert idempotency_store.size == 0
        idempotency_store.set("a", 1)
        assert idempotency_store.size == 1


# ---------------------------------------------------------------------------
# Event model tests
# ---------------------------------------------------------------------------


class TestEventModel:
    """Tests for the Event Pydantic model."""

    def test_idempotency_key(self, sample_event: Event) -> None:
        """Idempotency key should combine event_id, entity_id, and type."""
        key = sample_event.idempotency_key
        assert "evt_test_001" in key
        assert "insp_test_001" in key
        assert "inspection.completed" in key

    def test_event_actor_from_actor(self) -> None:
        """EventActor should correctly convert from Actor dataclass."""
        actor = Actor.agent("agt_001", company_id="comp_001", scopes=("read:safety",))
        ea = EventActor.from_actor(actor)
        assert ea.type == "agent"
        assert ea.id == "agt_001"
        assert ea.agent_id == "agt_001"

    def test_event_has_timestamp(self, sample_event: Event) -> None:
        """Events should have an ISO timestamp."""
        assert sample_event.timestamp is not None
        assert "T" in sample_event.timestamp


# ---------------------------------------------------------------------------
# EventBus tests
# ---------------------------------------------------------------------------


class TestEventBus:
    """Tests for the in-process event bus."""

    def test_subscribe_and_emit(self, event_bus: EventBus, sample_event: Event) -> None:
        """Subscribers should receive matching events."""
        received: list[Event] = []
        event_bus.subscribe("test_sub", lambda e: received.append(e))
        event_bus.emit(sample_event)
        assert len(received) == 1
        assert received[0].event_id == sample_event.event_id

    def test_filtered_subscription(self, event_bus: EventBus, sample_event: Event) -> None:
        """Subscribers should only receive events matching their filter."""
        received: list[Event] = []
        event_bus.subscribe(
            "incident_only",
            lambda e: received.append(e),
            event_types={EventType.INCIDENT_REPORTED},
        )
        # Emit an inspection event — should NOT be received
        event_bus.emit(sample_event)
        assert len(received) == 0

    def test_all_events_subscription(self, event_bus: EventBus, sample_event: Event) -> None:
        """Empty filter set should receive all events."""
        received: list[Event] = []
        event_bus.subscribe("catch_all", lambda e: received.append(e))
        event_bus.emit(sample_event)
        assert len(received) == 1

    def test_multiple_subscribers(self, event_bus: EventBus, sample_event: Event) -> None:
        """Multiple subscribers should each receive the event."""
        received_a: list[Event] = []
        received_b: list[Event] = []
        event_bus.subscribe("sub_a", lambda e: received_a.append(e))
        event_bus.subscribe("sub_b", lambda e: received_b.append(e))
        event_bus.emit(sample_event)
        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_emit_returns_successful_subscribers(
        self, event_bus: EventBus, sample_event: Event
    ) -> None:
        """Emit should return names of successful subscribers."""
        event_bus.subscribe("good_sub", lambda e: None)
        successful = event_bus.emit(sample_event)
        assert "good_sub" in successful

    def test_failed_subscriber_dead_lettered(
        self, event_bus: EventBus, sample_event: Event
    ) -> None:
        """Subscribers that fail all retries should be dead-lettered."""

        def always_fail(event: Event) -> None:
            raise ValueError("processing failed")

        event_bus.subscribe("bad_sub", always_fail, max_retries=2)
        successful = event_bus.emit(sample_event)

        assert "bad_sub" not in successful
        assert len(event_bus.dead_letters) == 1
        assert event_bus.dead_letters[0].subscriber_name == "bad_sub"
        assert "processing failed" in event_bus.dead_letters[0].error

    def test_partial_failure(self, event_bus: EventBus, sample_event: Event) -> None:
        """One failing subscriber should not prevent others from receiving."""
        received: list[Event] = []
        event_bus.subscribe("good_sub", lambda e: received.append(e))

        def fail_sub(event: Event) -> None:
            raise RuntimeError("boom")

        event_bus.subscribe("bad_sub", fail_sub, max_retries=1)

        successful = event_bus.emit(sample_event)
        assert "good_sub" in successful
        assert "bad_sub" not in successful
        assert len(received) == 1

    def test_unsubscribe(self, event_bus: EventBus, sample_event: Event) -> None:
        """Unsubscribed handlers should no longer receive events."""
        received: list[Event] = []
        event_bus.subscribe("removable", lambda e: received.append(e))
        assert event_bus.unsubscribe("removable") is True
        event_bus.emit(sample_event)
        assert len(received) == 0

    def test_unsubscribe_nonexistent(self, event_bus: EventBus) -> None:
        """Unsubscribing a non-existent subscriber should return False."""
        assert event_bus.unsubscribe("ghost") is False

    def test_subscriber_count(self, event_bus: EventBus) -> None:
        """Subscriber count should reflect registrations."""
        assert event_bus.subscriber_count == 0
        event_bus.subscribe("a", lambda e: None)
        assert event_bus.subscriber_count == 1
        event_bus.subscribe("b", lambda e: None)
        assert event_bus.subscriber_count == 2

    def test_create_event(self, event_bus: EventBus, sample_actor: Actor) -> None:
        """create_event should generate a valid Event with unique ID."""
        event = event_bus.create_event(
            event_type=EventType.HAZARD_REPORTED,
            entity_id="haz_001",
            entity_type="HazardReport",
            company_id="comp_001",
            actor=sample_actor,
            project_id="proj_001",
            summary={"severity": "high"},
        )
        assert event.event_id.startswith("evt_")
        assert event.event_type == EventType.HAZARD_REPORTED
        assert event.entity_id == "haz_001"
        assert event.summary == {"severity": "high"}

    def test_clear_dead_letters(self, event_bus: EventBus, sample_event: Event) -> None:
        """Clearing dead letters should empty the queue."""
        event_bus.subscribe("bad", lambda e: (_ for _ in ()).throw(ValueError("fail")), max_retries=1)
        event_bus.emit(sample_event)
        assert len(event_bus.dead_letters) > 0
        cleared = event_bus.clear_dead_letters()
        assert cleared > 0
        assert len(event_bus.dead_letters) == 0

    def test_retry_before_dead_letter(self, event_bus: EventBus, sample_event: Event) -> None:
        """Handler should be retried before dead-lettering."""
        call_count = 0

        def fail_twice(event: Event) -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient error")

        event_bus.subscribe("retry_sub", fail_twice, max_retries=3)
        successful = event_bus.emit(sample_event)

        assert "retry_sub" in successful
        assert call_count == 3
        assert len(event_bus.dead_letters) == 0
