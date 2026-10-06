# External App - Backend

A simple API to manage contacts, and to follow the runs of the CrewAI import flow. Built with **FastAPI** and
**SQLite** (a database in one file, no server to install). This is an educational project.

## Run it

```bash
uv venv && uv pip install -r requirements.txt
.venv/bin/uvicorn app.server:app --reload
```

- API: http://localhost:8000 (the root redirects to `/api/v1/contacts`)
- Interactive docs (try the endpoints here): http://localhost:8000/docs

To change the settings, copy `.env.example` to `.env`.

The database is the file `data/external_app.db`. The app creates it on the first start (so it is not
versioned: `data/` is in `.gitignore`). To reset the database (this deletes all data), stop the app and
delete the file.

## Project layout

```
app/
├── server.py              # Entry point: builds the app, runs startup code
├── core/
│   ├── broker.py          # Tells the open streams that a run changed (see GET /kickoffs/stream)
│   ├── config.py          # Settings read from environment variables
│   └── database.py        # SQLite connection and session
├── models/                # Database tables (SQLAlchemy)
├── schemas/               # JSON shapes for requests and responses (Pydantic)
├── repositories/          # Database access: one module per model (get, create, update, ...)
└── api/
    ├── deps.py            # Shared dependencies (like the database session)
    ├── webhook.py         # The two calls AMP makes to us: /hitl-webhook and /flow-webhook
    └── v1/
        └── endpoints/     # One file per resource (contacts.py, kickoffs.py, ...)
```

How a request flows: `endpoints` (HTTP) -> `repositories` (database) -> `models` (tables).
`schemas` validate the data that goes in and out.

To add a new resource (for example `companies`), create a file in each of
`models/`, `schemas/`, `repositories/` and `api/v1/endpoints/`, then include its router
in `app/server.py` (the `for resource in (contacts, kickoffs)` loop).

## Contact fields

| Field | Required | Notes |
|---|---|---|
| `id` | auto | Created by the database |
| `name` | yes | |
| `email` | yes | Must be valid and unique |
| `instagram`, `facebook`, `linkedin`, `website` | no | |
| `created_at` | auto | When the contact was created |
| `updated_at` | auto | Changes every time the contact is updated |

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/contacts` | Create a contact |
| GET | `/api/v1/contacts` | List contacts (`skip` and `limit` for pages) |
| GET | `/api/v1/contacts/{id}` | Get one contact |
| PATCH | `/api/v1/contacts/{id}` | Update some fields of a contact |
| DELETE | `/api/v1/contacts/{id}` | Delete a contact |
| DELETE | `/api/v1/contacts` | Destroy all contacts: delete **every** contact and restart the ids from 1 |

Kickoffs (the runs of the import flow, see the frontend `/contacts/import`):

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/kickoffs` | Save a run: `{"kickoff_id": "..."}`. If it is already saved (its review webhook can arrive first), the saved run is returned |
| GET | `/api/v1/kickoffs/stream` | The same list, **live** (Server-Sent Events): it is sent when you connect and again every time a run changes (webhooks, save, answer, delete). This is what the import page listens to, instead of asking again and again. Try it: `curl -N http://localhost:8000/api/v1/kickoffs/stream` |
| GET | `/api/v1/kickoffs` | List the saved runs, newest first. Each one has everything: `outcome`, `error`, `contacts`, `selected_refs` and its review (`request_id`, `method_name`, `answered_at`). The `callback_url` is never returned |
| DELETE | `/api/v1/kickoffs` | Forget **all** runs (the runs on the flow host are untouched). Cannot be undone. `204` |
| DELETE | `/api/v1/kickoffs/{kickoff_id}` | Forget a run. `404` if it is not saved |

The `kickoffs` table has one row per run, with everything about it. `outcome` has the names of the state of the
flow: `initialized` when the run is saved, `generated` when the webhook says it waits for the reviewer (the
webhook also fills `contacts`, `request_id`, `method_name` and `callback_url`), then `imported` or `failed`
when AMP sends the end of the run (`flow_finished`, see below), with the result of the import in `contacts`. `answered_at` is set when the answer is sent. The flow host has no "list my runs" endpoint,
so this table is what makes the list possible.

The flow host calls us (webhooks, they are not part of the API the frontend uses):

| Method | Path | Description |
|---|---|---|
| POST | `/flow-webhook` | Webhook Streaming: `{"events": [...]}`, as `Authorization: Bearer <CREWAI_KICKOFF_WEBHOOK_SECRET>`. `flow_started` saves the run (`data.inputs.id`) and `flow_finished` registers how it ended (`data.state`: `outcome`, `error`, `contacts`, `selected_refs`). Other events are ignored. `401` wrong secret, `503` no `CREWAI_KICKOFF_WEBHOOK_SECRET` set |
| POST | `/hitl-webhook` | The review webhook. Receives the event `new_request` and saves it in the row of the run (created if it does not exist yet) |
| POST | `/api/v1/kickoffs/{kickoff_id}/respond` | `{"feedback": "..."}`. Sends the answer to the `callback_url` of the run. `404` unknown run, `409` no review is waiting or it was already answered, `502` the host refused it |

The webhook is checked by its signature: `X-Crewai-Signature: sha256=<hex>` is the HMAC-SHA256 of
`"{X-Crewai-Timestamp}.{body}"` with `CREWAI_HITL_WEBHOOK_SECRET`, and a request older than 5 minutes is refused. The
body is flat (`event_type`, `id`, `flow_id`, `state`, `callback_url`...). The `callback_url` is kept
but never returned by `GET /api/v1/kickoffs`, and the `response_token` is not kept. AMP does
**not** retry a webhook that gets an error, so only invalid requests get a 4xx.

Settings (`.env`): `CREWAI_HITL_WEBHOOK_SECRET` (the secret of the webhook, `whsec_...`; an unsigned or wrongly signed
request gets `401`, and without the secret every webhook gets `503`) and
`CREWAI_KICKOFF_WEBHOOK_SECRET` (the secret of `/flow-webhook`, the kickoff webhook: any value you choose, the same one as in the frontend;
it is not `CREWAI_HITL_WEBHOOK_SECRET`).

The `callback_url` of the review must be on `crewai.com` or a subdomain (`app.crewai.com` for AMP), so nobody can
make this API call an arbitrary address. It is the constant `CALLBACK_DOMAIN` in `webhook.py`, not a setting.

**Live import progress.** The flow creates the selected contacts one by one with `POST /api/v1/contacts`, and the
backend uses that to follow the import without any change in the flow: when the answer is sent
(`/respond`) the run keeps the `selected_refs`, and each contact that arrives at `POST /contacts` (created, or
refused with `409`) that matches a still-`pending` selected contact of a waiting run (same email) is saved in that
run's `contacts` (`import_status`, `external_app_id`, `import_error`) and sent through the stream. The final state
of the flow (`flow_finished`) still has the last word.

Other routes: `GET /` redirects to the contacts list, and `GET /health` checks that the app is running.

Errors: `404` when the contact is not found, `409` when the email already exists.

## Example

```bash
# Create
curl -X POST http://localhost:8000/api/v1/contacts \
  -H "Content-Type: application/json" \
  -d '{"name": "Ana Silva", "email": "ana@example.com", "instagram": "@ana.silva"}'

# List
curl http://localhost:8000/api/v1/contacts

# Update only the website
curl -X PATCH http://localhost:8000/api/v1/contacts/1 \
  -H "Content-Type: application/json" \
  -d '{"website": "https://ana.dev"}'

# Delete
curl -X DELETE http://localhost:8000/api/v1/contacts/1
```

## CORS

The frontend runs on another address (`http://localhost:3000`), so the API must allow it.
This is set by `CORS_ORIGINS` (a JSON list, for example `["http://localhost:3000"]`).
The default already allows `http://localhost:3000`.

## Changing the port

The API listens on port `8000` of your machine. To change it, set `API_PORT` in `.env`
(copy `.env.example` first). Then update `EXTERNAL_APP_API_URL` in the frontend and in `crewai_flow`.
See the root `README.md` for the full list of connected settings.
