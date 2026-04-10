"""In-process event bus with typed events, subscription filters, and dead-letter handling.

Production: swap IdempotencyStore for Redis, EventBus dispatch for Pub/Sub.
The in-process implementation is sufficient for single-instance deployments.
"""

import asyncio
import logging
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from app.models.actor import Actor
from app.models.events import Event, EventActor, EventType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Idempotency store (in-memory, swappable for Redis)
# ---------------------------------------------------------------------------


@dataclass
class IdempotencyEntry:
    """A recorded side-effect result with TTL.

    Attributes:
        result: The cached result of the side-effect.
        created_at: Timestamp when the entry was recorded.
        ttl_seconds: Time-to-live in seconds.
    """

    result: Any
    created_at: float
    ttl_seconds: float = 604800  # 7 days default


class IdempotencyStore:
    """In-memory idempotency store with TTL-based expiry.

    Thread-safe for single-threaded async usage (Python GIL).
    Swap for Redis in production for multi-instance deployments.
    """

    def __init__(self) -> None:
        self._store: dict[str, IdempotencyEntry] = {}

    def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired.

        Args:
            key: The idempotency key to check.

        Returns:
            True if the key exists and hasn't expired.
        """
        entry = self._store.get(key)
        if entry is None:
            return False
        if time.time() - entry.created_at > entry.ttl_seconds:
            del self._store[key]
            return False
        return True

    def get(self, key: str) -> Any:
        """Get the cached result for a key.

        Args:
            key: The idempotency key.

        Returns:
            The cached result, or None if not found/expired.
        """
        if not self.exists(key):
            return None
        return self._store[key].result

    def set(self, key: str, result: Any, ttl_seconds: float = 604800) -> None:
        """Record a side-effect result.

        Args:
            key: The idempotency key.
            result: The result to cache.
            ttl_seconds: Time-to-live in seconds (default 7 days).
        """
        self._store[key] = IdempotencyEntry(
            result=result,
            created_at=time.time(),
            ttl_seconds=ttl_seconds,
        )

    def clear(self) -> None:
        """Clear all entries (for testing)."""
        self._store.clear()

    def prune_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        now = time.time()
        expired_keys = [
            k
            for k, v in self._store.items()
            if now - v.created_at > v.ttl_seconds
        ]
        for k in expired_keys:
            del self._store[k]
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Return the number of entries in the store."""
        return len(self._store)


# ---------------------------------------------------------------------------
# Dead letter entry
# ---------------------------------------------------------------------------


@dataclass
class DeadLetterEntry:
    """A failed event processing record.

    Attributes:
        event: The event that failed processing.
        subscriber_name: Name of the subscriber that failed.
        error: The error message.
        attempts: Number of processing attempts.
        first_failure_at: Timestamp of the first failure.
        last_failure_at: Timestamp of the most recent failure.
    """

    event: Event
    subscriber_name: str
    error: str
    attempts: int = 1
    first_failure_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_failure_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------


@dataclass
class Subscription:
    """An event subscription with filters.

    Attributes:
        name: Human-readable subscriber name (for logging/debugging).
        handler: Async callable that processes the event.
        event_types: Set of event types this subscriber cares about.
            Empty set means subscribe to all events.
        max_retries: Maximum number of retry attempts on failure.
    """

    name: str
    handler: Callable[[Event], Any]
    event_types: set[EventType] = field(default_factory=set)
    max_retries: int = 3


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class EventBus:
    """In-process async event bus with typed events and dead-letter handling.

    Design:
    - Subscribers register with optional event type filters
    - Events are dispatched to matching subscribers
    - Failed events go to dead-letter after max retries
    - Idempotency store prevents duplicate side-effects

    Attributes:
        idempotency_store: The idempotency store for dedup.
    """

    def __init__(self) -> None:
        self._subscriptions: list[Subscription] = []
        self._dead_letters: list[DeadLetterEntry] = []
        self.idempotency_store = IdempotencyStore()

    def subscribe(
        self,
        name: str,
        handler: Callable[[Event], Any],
        event_types: set[EventType] | None = None,
        max_retries: int = 3,
    ) -> None:
        """Register an event subscriber.

        Args:
            name: Human-readable name for this subscriber.
            handler: Callable that processes events. Can be sync or async.
            event_types: Optional set of event types to filter on.
                If None or empty, subscribes to all events.
            max_retries: Max retry attempts before dead-lettering.
        """
        self._subscriptions.append(
            Subscription(
                name=name,
                handler=handler,
                event_types=event_types or set(),
                max_retries=max_retries,
            )
        )
        logger.info(
            "Subscriber registered: name=%s event_types=%s",
            name,
            [et.value for et in (event_types or set())],
        )

    def unsubscribe(self, name: str) -> bool:
        """Remove a subscriber by name.

        Args:
            name: The subscriber name to remove.

        Returns:
            True if a subscriber was removed, False otherwise.
        """
        before = len(self._subscriptions)
        self._subscriptions = [s for s in self._subscriptions if s.name != name]
        removed = len(self._subscriptions) < before
        if removed:
            logger.info("Subscriber removed: name=%s", name)
        return removed

    def emit(self, event: Event) -> list[str]:
        """Dispatch an event to all matching subscribers (synchronous).

        Subscribers that raise exceptions are retried up to max_retries.
        After exhausting retries, the event is dead-lettered for that subscriber.

        Args:
            event: The event to dispatch.

        Returns:
            List of subscriber names that successfully processed the event.
        """
        successful: list[str] = []

        for sub in self._subscriptions:
            if not self._matches(sub, event):
                continue

            processed = False
            last_error = ""

            for attempt in range(1, sub.max_retries + 1):
                try:
                    sub.handler(event)
                    processed = True
                    successful.append(sub.name)
                    break
                except Exception as exc:
                    last_error = str(exc)
                    logger.warning(
                        "Subscriber %s failed on event %s (attempt %d/%d): %s",
                        sub.name,
                        event.event_id,
                        attempt,
                        sub.max_retries,
                        last_error,
                    )

            if not processed:
                self._dead_letter(event, sub.name, last_error)

        return successful

    def create_event(
        self,
        event_type: EventType,
        entity_id: str,
        entity_type: str,
        company_id: str,
        actor: Actor,
        project_id: str | None = None,
        summary: dict[str, Any] | None = None,
        graph_context: dict[str, Any] | None = None,
    ) -> Event:
        """Create a new Event with a generated event_id.

        Convenience method for services that emit events.

        Args:
            event_type: The coarse event type.
            entity_id: ID of the entity that changed.
            entity_type: Type label of the entity.
            company_id: Tenant scope.
            actor: Who caused this event.
            project_id: Optional project context.
            summary: Optional rich summary payload.
            graph_context: Optional pre-computed graph context.

        Returns:
            A fully populated Event instance.
        """
        return Event(
            event_id=f"evt_{secrets.token_hex(8)}",
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            company_id=company_id,
            project_id=project_id,
            actor=EventActor.from_actor(actor),
            summary=summary or {},
            graph_context=graph_context or {},
        )

    @property
    def dead_letters(self) -> list[DeadLetterEntry]:
        """Return all dead-letter entries."""
        return list(self._dead_letters)

    @property
    def subscriber_count(self) -> int:
        """Return the number of registered subscribers."""
        return len(self._subscriptions)

    def clear_dead_letters(self) -> int:
        """Clear all dead-letter entries.

        Returns:
            Number of entries cleared.
        """
        count = len(self._dead_letters)
        self._dead_letters.clear()
        return count

    def _matches(self, sub: Subscription, event: Event) -> bool:
        """Check if an event matches a subscription's filter.

        Args:
            sub: The subscription to check.
            event: The event to match against.

        Returns:
            True if the event matches the subscription filter.
        """
        if not sub.event_types:
            return True
        return event.event_type in sub.event_types

    def _dead_letter(self, event: Event, subscriber_name: str, error: str) -> None:
        """Send an event to the dead-letter queue.

        Args:
            event: The failed event.
            subscriber_name: Which subscriber failed.
            error: The error message.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Check if this event+subscriber combo already exists
        for entry in self._dead_letters:
            if (
                entry.event.event_id == event.event_id
                and entry.subscriber_name == subscriber_name
            ):
                entry.attempts += 1
                entry.last_failure_at = now
                entry.error = error
                logger.error(
                    "Dead-letter updated: event=%s subscriber=%s attempts=%d error=%s",
                    event.event_id,
                    subscriber_name,
                    entry.attempts,
                    error,
                )
                return

        self._dead_letters.append(
            DeadLetterEntry(
                event=event,
                subscriber_name=subscriber_name,
                error=error,
                first_failure_at=now,
                last_failure_at=now,
            )
        )
        logger.error(
            "Dead-lettered: event=%s subscriber=%s error=%s",
            event.event_id,
            subscriber_name,
            error,
        )
