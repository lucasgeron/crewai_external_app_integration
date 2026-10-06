"""Webhooks: the calls that CrewAI AMP makes to us.

They live at the root of the app (outside /api/v1): they are the addresses you give to AMP, and they are not
part of the API that the frontend uses.

- `POST /hitl-webhook`: human review. When a flow waits for a person, AMP sends the request. We keep it in the
  row of the run (the `kickoffs` table), the frontend lists the runs, and when the user answers
  (`POST /kickoffs/{kickoff_id}/respond`) we call the `callback_url` of the webhook. It is signed
  (`X-Crewai-Signature`) with the secret set in the AMP dashboard (Settings -> Human in the Loop).
- `POST /flow-webhook`: Webhook Streaming. When the kickoff has a `webhooks` object (the Next.js proxy adds
  it), AMP sends the events we asked for (`flow_started`, `flow_finished`...) as
  `Authorization: Bearer <CREWAI_KICKOFF_WEBHOOK_SECRET>`. It is not signed, and it is not set in the
  dashboard: it travels in each kickoff.

    {"events": [{"id": "...", "execution_id": "...", "timestamp": "...", "type": "flow_finished", "data": {...}}]}

What we use from the events (checked on real runs, see the README):

- `flow_started`: `data.inputs.id` is the `kickoff_id`. It creates the row of the run. The `flow_started` that
  comes after the review is answered has no `inputs` and is ignored.
- `flow_finished`: `data.state` is the final state of the flow, and `data.state.id` is the `kickoff_id`.
  Its `outcome` (`imported` or `failed`), `error` and `contacts` are saved in the row.

The `execution_id` is the `kickoff_id` only until the flow pauses: after the answer, AMP uses another one.
The order of the events is not guaranteed, and AMP does not retry.
"""

import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import broker
from app.core.config import get_settings
from app.repositories import kickoff as repo

webhook_router = APIRouter(tags=["webhooks"])


@webhook_router.post("/hitl-webhook", summary="Webhook: a flow is waiting for a person")
async def receive_hitl_webhook(request: Request, db: Session = Depends(get_db)):
    """Called by the flow host with a `new_request` event. We keep what the run needs in its `kickoffs` row.

    Real body, the same in the 8 webhooks we captured from a CrewAI AMP deployment (ids shortened). It
    is flat: everything is at the top level. `state` is the whole state of the flow at the pause, as an
    object, and it is what the human has to review. `output` is the return of the review step: do not
    rely on it (it was the contacts as JSON text, and it depends on the version of the flow deployed):

        {
          "event_type": "new_request",
          "id": "774a6c16-...",                  # the review request (not the run)
          "status": "pending",
          "flow_id": "93a06cc0-...",             # the run: it is the `kickoff_id`
          "flow_class": "crewai_flow.flows.import_contacts.ImportContactsFlow",
          "method_name": "review_contacts",
          "message": "Select the contacts to import: ...",
          "output": "...",
          "emit": [],
          "state": {"id": "93a06cc0-...", "count": 5, "outcome": "generated", "error": "",
                    "selected_refs": [], "contacts": [{"ref": 1, "name": "Apollo Nunes", ...}, ...]},
          "metadata": {"otel_trace_context": "cafe6a48...:248dbaff..."},
          "created_at": "2026-10-06T16:46:20Z",
          "callback_url": "https://...",         # where the answer goes (secret, never sent to the frontend)
          "response_token": "...",               # secret too
          "deployment_id": 135826,
          "deployment_name": "crewai_external_app_integration",
          "assigned_to_email": "lucas.geron@codeminer42.com",
          "assigned_at": "2026-10-06T16:46:20Z"
        }

    The host does NOT retry a webhook that gets a 4xx or 5xx answer, so only refuse what must be refused.
    """
    body = await request.body()
    verify_signature(body, request.headers.get("X-Crewai-Signature"), request.headers.get("X-Crewai-Timestamp"))

    try:
        payload = json.loads(body)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "The body is not JSON")
    if payload.get("event_type") != "new_request":
        print(f"[hitl-webhook] Ignoring event_type {payload.get('event_type')!r}")
        return {"status": "ignored"}  # other events are not ours to handle

    callback_url = payload.get("callback_url") or ""
    if not payload.get("id") or not payload.get("flow_id") or not callback_url:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "id, flow_id and callback_url are required")
    if not callback_host_is_allowed(callback_url):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "callback_url host is not allowed")

    # The run may not be saved yet: the webhook can arrive before the frontend saves the id.
    kickoff = repo.get_or_create(db, str(payload["flow_id"]))
    repo.save_review(
        db,
        kickoff,
        request_id=str(payload["id"]),
        method_name=str(payload.get("method_name") or ""),
        callback_url=callback_url,
        state=payload.get("state") or {},
    )
    broker.notify()  # the open pages get the review right away
    return {"status": "saved"}


@webhook_router.post("/flow-webhook", summary="Webhook Streaming: the events of a run")
async def receive_flow_webhook(request: Request, db: Session = Depends(get_db)):
    """Called by AMP with the events of a run. Returns `ignored` for the ones we do not use."""
    check_secret(request.headers.get("Authorization", ""))

    try:
        events = (await request.json())["events"]
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "The body is not {\"events\": [...]}")

    for event in events:
        data = event.get("data") or {}
        if event.get("type") == "flow_started":
            # Only the first one (before the review) has the inputs, and `inputs.id` is the kickoff_id.
            kickoff_id = (data.get("inputs") or {}).get("id")
            if kickoff_id:
                repo.get_or_create(db, str(kickoff_id))
                broker.notify()
        elif event.get("type") == "flow_finished":
            state = data.get("state") or {}
            if state.get("id"):
                repo.finish(db, repo.get_or_create(db, str(state["id"])), state)
                broker.notify()
        elif event.get("type") == "method_execution_failed":
            # It does not say which run failed (the data has no state): only the log can tell.
            print(f"[flow-webhook] method_execution_failed: {data.get('method_name')}: {data.get('error')}")
    return {"status": "ok"}


# ---------- helpers (used by the endpoints above) ----------


# A signed webhook older than this is refused, so a captured request cannot be replayed later.
SIGNATURE_MAX_AGE_SECONDS = 300

# The webhook brings a callback_url that we call to send the human's answer. Only CrewAI's own domain is
# accepted (`app.crewai.com` for AMP), so nobody can make this API call an arbitrary address.
CALLBACK_DOMAIN = "crewai.com"


def verify_signature(body: bytes, signature: str | None, timestamp: str | None) -> None:
    """Check the HMAC-SHA256 signature of the webhook.

    The webhook URL is public (a tunnel), so this is what tells a real AMP request from anyone else's.
    AMP sends `X-Crewai-Signature: sha256=<hex>`, the HMAC of `"{X-Crewai-Timestamp}.{body}"` with the
    secret of the webhook (the whole `whsec_...` text), and the timestamp is a Unix timestamp.
    """
    secret = get_settings().crewai_hitl_webhook_secret
    if not secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "CREWAI_HITL_WEBHOOK_SECRET is not set in the backend .env")
    if not signature or not timestamp:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-Crewai-Signature or X-Crewai-Timestamp")
    try:
        age = abs(time.time() - float(timestamp))
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid X-Crewai-Timestamp")
    if age > SIGNATURE_MAX_AGE_SECONDS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "The webhook is too old")

    expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    received = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, received):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

def callback_host_is_allowed(url: str) -> bool:
    """True if the callback_url points to CrewAI's domain (or a subdomain of it)."""
    host = urlparse(url).hostname or ""
    return host == CALLBACK_DOMAIN or host.endswith(f".{CALLBACK_DOMAIN}")


def check_secret(authorization: str) -> None:
    """The events are authenticated by the secret we gave AMP in the kickoff (`Authorization: Bearer <secret>`)."""
    expected = get_settings().crewai_kickoff_webhook_secret
    if not expected:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "CREWAI_KICKOFF_WEBHOOK_SECRET is not set in the backend .env")
    scheme, _, token = authorization.partition(" ")
    if scheme != "Bearer" or not secrets.compare_digest(token, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid secret")
