"""Async wrappers for synchronous Firestore operations."""

import asyncio
from typing import Any, Callable


async def run_sync(fn: Callable, *args: Any, **kwargs: Any) -> Any:
    """Run a synchronous function in a thread pool to avoid blocking the event loop.

    This wraps blocking Firestore SDK calls so they can be awaited without
    stalling the async event loop.

    Args:
        fn: The synchronous callable to execute.
        *args: Positional arguments forwarded to *fn*.
        **kwargs: Keyword arguments forwarded to *fn*.

    Returns:
        The return value of *fn*.
    """
    return await asyncio.to_thread(fn, *args, **kwargs)
