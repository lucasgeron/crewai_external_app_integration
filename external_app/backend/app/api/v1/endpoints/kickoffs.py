"""HTTP routes for kickoffs: the saved ids of the import flow runs.

The frontend saves the id after starting a run, and AMP tells us when it finishes and when it waits for a
review (see api/webhook.py). So every run is still listed after a page reload, on another
browser, or after a restart.

The page does not ask for the list again and again: it opens `GET /kickoffs/stream` once and we send the list
every time a run changes (see core/broker.py). Every route that changes a run calls `broker.notify()`.
"""

import asyncio
import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.webhook import callback_host_is_allowed
from app.core import broker
from app.core.database import SessionLocal
from app.repositories import kickoff as repo
from app.schemas.kickoff import KickoffCreate, KickoffRead, ReviewAnswer

router = APIRouter(prefix="/kickoffs", tags=["kickoffs"])

@router.get("/stream", summary="Follow the runs live (Server-Sent Events)")
async def stream_kickoffs():
    """Keep the connection open and send the whole list of runs (the same JSON as `GET /kickoffs`) as soon as it
    connects and every time a run changes. In the browser: `new EventSource(url)`.

    Try it with `curl -N http://localhost:8000/api/v1/kickoffs/stream` (the docs page cannot show a stream).
    """
    return StreamingResponse(
        run_events(),
        media_type="text/event-stream",
        # Tell the browser and the proxies in the middle (nginx, ngrok) not to keep the events waiting.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "",
    response_model=KickoffRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save a kickoff id",
)
def create_kickoff(payload: KickoffCreate, db: Session = Depends(get_db)):
    """Save the id of a run. If it is already saved (the webhook of its review can arrive before this
    call), the saved run is returned."""
    kickoff = repo.get_or_create(db, payload.kickoff_id)
    broker.notify()
    return kickoff


@router.get("", response_model=list[KickoffRead], summary="List kickoffs")
def list_kickoffs(db: Session = Depends(get_db)):
    """List every saved run id, newest first."""
    return repo.list_all(db)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Forget every kickoff id",
)
def destroy_all_kickoffs(db: Session = Depends(get_db)):
    """Forget ALL saved runs. The runs themselves are not touched.
    This cannot be undone."""
    repo.delete_all(db)
    broker.notify()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{kickoff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Forget a kickoff id",
)
def delete_kickoff(kickoff_id: str, db: Session = Depends(get_db)):
    """Forget a run id (it does not touch the run itself). Returns 404 if it is not saved."""
    kickoff = repo.get(db, kickoff_id)
    if kickoff is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kickoff not found")
    repo.delete(db, kickoff)
    broker.notify()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{kickoff_id}/respond", summary="Send the human's answer to the flow")
def respond(kickoff_id: str, answer: ReviewAnswer, db: Session = Depends(get_db)):
    """Send the answer to the `callback_url` of the review of the run. The flow then continues.

    Returns 404 if the run is unknown, 409 if no review is waiting (the webhook did not arrive yet) or it
    was already answered, and 502 if the flow host did not accept the answer.
    """
    kickoff = repo.get(db, kickoff_id)
    if kickoff is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kickoff not found")
    if not kickoff.callback_url:
        raise HTTPException(status.HTTP_409_CONFLICT, "No review is waiting for this run yet")
    if kickoff.answered_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This review was already answered")
    if not callback_host_is_allowed(kickoff.callback_url):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "callback_url host is not allowed")

    try:
        response = httpx.post(
            kickoff.callback_url,
            json={"feedback": answer.feedback, "source": "external_app"},
            timeout=15,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Could not reach the flow host: {exc}")
    if response.status_code >= 400:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"The flow host refused the answer (HTTP {response.status_code}): {response.text[:200]}",
        )

    repo.mark_answered(db, kickoff, selected_refs_of(answer.feedback))
    broker.notify()
    return {"status": "sent"}


# ---------- helpers (used by the routes above) ----------

# A quiet connection is closed by proxies after a while, so we write a comment line every few seconds.
HEARTBEAT_SECONDS = 15

_kickoffs_json = TypeAdapter(list[KickoffRead])


def selected_refs_of(feedback: str) -> list[int] | None:
    """The `selected_refs` inside the answer ({"selected_refs": [1, 3]}), so the page knows which contacts are
    being imported before the flow says so. None if the answer is another text (the flow still understands it)."""
    try:
        refs = json.loads(feedback)["selected_refs"]
    except (ValueError, KeyError, TypeError):
        return None
    return refs if isinstance(refs, list) and all(isinstance(ref, int) for ref in refs) else None


async def run_events():
    """The body of the stream: one Server-Sent Event with the list now, and another one after each change.

    An event is the text `data: <json>` followed by an empty line. A line that starts with `:` is a comment,
    which the browser ignores (it only keeps the connection alive).
    """
    # Subscribe before reading the list, so a change that happens in between is not lost.
    async with broker.subscribe() as changes:
        yield await read_event()
        while True:
            try:
                await asyncio.wait_for(changes.get(), HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            yield await read_event()


async def read_event() -> str:
    """The list of runs as one event. The database call is blocking, so it runs in a thread."""
    return f"data: {await run_in_threadpool(read_runs)}\n\n"


def read_runs() -> str:
    """The runs as JSON text, with its own session (a stream lives longer than a request's `get_db`)."""
    with SessionLocal() as db:
        runs = _kickoffs_json.validate_python(repo.list_all(db), from_attributes=True)
        return _kickoffs_json.dump_json(runs).decode()
