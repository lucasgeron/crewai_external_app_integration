"""A tiny broker: it tells the open streams that the runs changed, so they send the new list to the browsers.

The flow talks to this API through webhooks, and the page has no way to know when one arrives. Instead of the
page asking again and again (polling), the page keeps one connection open (`GET /kickoffs/stream`, see
api/v1/endpoints/kickoffs.py) and we write to it when something changes:

    webhook / route that changes a run  ->  notify()  ->  every open stream wakes up  ->  sends the list

The broker only says "something changed". It carries no data: each stream reads the list from the database.
Everything lives in the memory of this process, which is enough for one `uvicorn` worker. With more than one
worker, a webhook would only wake the streams of its own worker, and you would need Redis (or similar) here.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

# One queue per open stream, with the event loop that owns it (see `notify`).
_subscribers: set[tuple[asyncio.AbstractEventLoop, asyncio.Queue[None]]] = set()


@asynccontextmanager
async def subscribe() -> AsyncIterator[asyncio.Queue[None]]:
    """Listen to the changes while the `with` block runs. Each `notify()` puts one item in the queue."""
    entry = (asyncio.get_running_loop(), asyncio.Queue[None]())
    _subscribers.add(entry)
    try:
        yield entry[1]
    finally:
        _subscribers.discard(entry)  # the browser closed the page: nobody is listening anymore


def notify() -> None:
    """Tell every open stream that the runs changed. Call it after saving to the database.

    It works from any route. FastAPI runs `def` routes in a thread, and a queue can only be touched by the
    thread of its event loop, so we ask each loop to do it (`call_soon_threadsafe`).
    """
    for loop, queue in list(_subscribers):
        loop.call_soon_threadsafe(queue.put_nowait, None)
