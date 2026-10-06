# External App - Import Flow (CrewAI)

A tutorial project: a **CrewAI Flow** that generates fake contacts, **pauses for a human to select the
contacts to import**, and then imports the selected ones, one by one, through the contacts API of the
External App. It returns every contact with the result of its import.

> **Where it runs.** This project is deployed to **CrewAI AMP**, and runs only there. It has no web server
> and no local copy of the AMP API: the platform hosts it and exposes the endpoints. How to deploy it and
> how the external app talks to it: see the root [README](../README.md#deploy-and-configure).

The flow uses **no LLM and no API key**: contacts are generated with plain Python, and the answer of the
reviewer is read with plain Python too.

## The big picture

```
External App            CrewAI AMP (hosts the flow)              CrewAI Flow
   |                          |                                   |
   |-- POST /kickoff -------->|-- kickoff(count) ---------------->| generate_contacts
   |<-- kickoff_id -----------|                                   | review_contacts  --> PAUSED
   |<-- webhook: flow_started-|                                   |
   |<-- webhook new_request --|  (the flow state, with the contacts, and a callback_url)
   |                          |                                   |
   |  reviewer: select the contacts to import                     |
   |-- POST callback_url ---->|-- resume(answer) ---------------->| process_contacts
   |<-- POST /contacts -------------------------------------------| (one per selected contact)
   |<-- POST /contacts -------------------------------------------|
   |<-- webhook: flow_finished (the final state: outcome, selected_refs, contacts with their result)
```

Everything the External App learns about the run arrives as a webhook (from AMP) or as a `POST /contacts`
(from this flow): it never asks the flow for its status.

## Try it in a terminal

On AMP the platform runs the flow. To try it on your machine:

```bash
cd crewai_flow
cp .env.example .env
uv sync
uv run kickoff 5                                   # count
```

It generates the contacts and then **asks in the terminal** (there is no host to collect the answer).
Answer with the JSON of the selection, for example `{"selected_refs": [1, 3]}`, or with text: `all`, or the
refs (`1, 3`). The flow prints its final output. To save a diagram of the flow, run `uv run plot`.

## Project layout

```
src/crewai_flow/
├── main.py                       # CLI: kickoff, plot (to try the flow in a terminal)
├── config/
│   └── settings.py               # Settings class + cached get_settings()
├── flows/
│   └── import_contacts.py        # THE FLOW: generate, review, import (start here)
├── integrations/                 # The only place that does HTTP
│   └── contacts_api.py           #   creates one contact in the External App (POST /contacts)
├── services/                     # Business logic, plain Python
│   ├── contact_generator.py      #   fake contact generation
│   └── review.py                 #   reads the answer of the reviewer
└── types/                        # Only data (Pydantic), no I/O
    ├── contacts.py               #   GeneratedContact
    ├── review.py                 #   ContactsSelection (what the reviewer sends back)
    └── state.py                  #   ImportContactsState
```

Each folder has one job, and each one has an `__init__.py` that exports its public names,
so you import from the folder (`from crewai_flow.services import generate_contacts`), not from the file.
Dependencies go one way: `flows` -> `integrations` and `services` -> `types` and `config`.

## Concepts you will learn here

**1. Inputs.**
`kickoff(inputs={"count": 5})` fills `self.state`. This is what AMP does with the `inputs` of
`POST /kickoff` (the values arrive as strings, and the state converts them). The `@start()` method just
reads `self.state`.

**2. Human in the loop: the flow does not choose how it waits.**
`@human_feedback` has no `provider` here, on purpose. The host brings its own, through
`flow_config.hitl_provider` (CrewAI uses it when the decorator has no provider of its own):

| Where the flow runs | Who collects the answer |
|---|---|
| CrewAI AMP | the platform: the **Human in the Loop** tab, e-mail, a webhook, or the API |
| a terminal (`uv run kickoff`) | CrewAI asks in the console |

**Do not pass `provider=` in the decorator.** It wins over the provider of the host, so on AMP the
request never reaches the Human in the Loop tab and the run stays "running" forever.

**3. The answer is a selection.**
The reviewer chooses **which contacts to import**. The review API only carries a string (`feedback`), so the
answer travels as **JSON text** of the `ContactsSelection` type (`types/review.py`):

```json
{"selected_refs": [1, 3]}
```

A `@listen(review_contacts)` method (`process_contacts`) receives the `HumanFeedbackResult`, reads its
`feedback` with `parse_review_response` (`services/review.py`) and stores the refs in the state. No LLM and no
`emit` are needed. The reader is forgiving, so a person can also answer in free text in the AMP dashboard
or by e-mail:

| The answer | Result |
|---|---|
| the JSON above | the refs it says. Unknown refs are ignored |
| `all` | every contact |
| text with numbers (`1, 3`) | those refs |
| anything else | nothing selected |

**4. What the reviewer sees is the flow state.**
`review_contacts` returns only a placeholder ("Awaiting Input"). A host that sends a review request (AMP)
delivers the whole flow state as `state`, so the frontend reads the contacts from `state.contacts`.

**5. The side effect is isolated, and one failure does not stop the others.**
`process_contacts` sends each selected contact to the External App (`integrations/contacts_api.py`, the only
module that does HTTP). Each contact has its own result in `import_status` (`imported` with the `external_app_id`,
or `failed` with the `import_error`), and a failure does not stop the next contacts. There is no retry. The final
output has every generated contact with its result, and the `ref`s that were selected.

**6. No local persistence.**
When a flow pauses, its state has to be saved to continue later. On AMP the platform does it. The flow
does not configure `@persist` or any database.

## A failure on purpose

When you generate 2 or more contacts, the **last one reuses the email of the first one**
(`services/contact_generator.py`). The contacts API only accepts unique emails, so when the flow imports both,
the second fails with `HTTP 409 - Email already exists` while the others succeed. This shows how a failure
appears in the report. It is **off in the code** and **on in `.env.example`**: on AMP it only happens if the
variable `FLOW_INCLUDE_DUPLICATE_EMAIL=true` is in the environment variables of the deployment (`crewai deploy
create` copies it from your `.env`). Set it to `false` to turn it off.

## Rules and limits

- `count` must be between **1 and 10** per run (`MAX_CONTACTS_PER_RUN` env var, default 10).
  The flow raises an error otherwise, and the run ends as failed.
- `ref` is a temporary number (1, 2, 3...) valid only inside one run. The database creates the real id.

## Output

The final output of a run (AMP sends it to the External App in the `flow_finished` webhook, as `data.state`;
`GET /status/{kickoff_id}` also returns it in `result`):

```json
{
  "outcome": "imported",
  "selected_refs": [1, 3],
  "contacts": [
    {"ref": 1, "name": "Ana Rocha", "email": "ana.rocha7413@stark.example.com", "instagram": "@ana.rocha",
     "facebook": null, "linkedin": null, "website": null,
     "import_status": "imported", "external_app_id": 12, "import_error": null}
  ]
}
```

`contacts` always has every generated contact, and `selected_refs` says which ones were selected. The
`import_status` of each contact is `imported`, `failed` (see `import_error`), or `pending` when it was not selected. When
`outcome` is `failed` (an invalid `count`), `selected_refs` is empty and `error` says why.

## Settings

Settings live in the `Settings` class (`config/settings.py`). Call `get_settings()` to read them.
It is cached with `@lru_cache`, so the environment and the `.env` file are read only once per process.
Real environment variables win over the `.env` file. On AMP they are the environment variables of the
deployment.

| Variable | Default | What it is |
|---|---|---|
| `EXTERNAL_APP_API_URL` | `http://localhost:8000` | Where the flow sends the selected contacts. **On AMP, set the public (ngrok) address of the backend**: `localhost` there is the flow's own container, and every contact fails with `Connection refused` |
| `FLOW_INCLUDE_DUPLICATE_EMAIL` | `false` (`.env.example` sets `true`) | Repeat one email on purpose, to show a failure when the flow imports the contacts. On AMP, set it to `true` in the deployment to see the demo |
| `MAX_CONTACTS_PER_RUN` | `10` | The most contacts one run may generate. A bigger `count` makes the run fail |
| `FLOW_DEFAULT_COUNT` | `3` | How many contacts to generate when the kickoff has no `count` |

## Docs

- Human feedback in Flows: https://docs.crewai.com/en/learn/human-feedback-in-flows
- Flows: https://docs.crewai.com/en/concepts/flows
