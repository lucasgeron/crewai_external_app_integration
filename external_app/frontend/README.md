# External App - Frontend

A simple UI to manage contacts. Built with **Next.js** (App Router), **TypeScript** and **Tailwind CSS**.
It talks to the FastAPI backend in `../backend`. This is an educational project.

## Run it

1. Start the backend first (see `../backend/README.md`).
2. Then:

```bash
npm install
cp .env.example .env.local   # only if .env.local does not exist yet
npm run dev
```

Open http://localhost:3000 and click **Go to /contacts**.

## Pages

| Route | What it shows |
|---|---|
| `/` | The project name and a button to go to `/contacts` |
| `/contacts` | The contacts table, with create, edit, delete and **Destroy all contacts** (deletes all of them) |
| `/contacts/import` | Triggers the CrewAI flow (a count) and follows every run **live**. The run list changes by itself while the flow moves: *initialized* -> *generated* (waiting for you: **Review** the contacts and choose which ones to import) -> *imported* or *failed* (**Details** per contact, or the error). Each run has a **Delete** button, and the runs are stored in the backend, so the list survives a reload |

## How the import page works

The browser does only two things with the flow: it **starts** it (`POST /api/flow/kickoff`) and **answers its
review** (`POST /api/v1/kickoffs/{id}/respond`). Everything else happens between the flow (AMP) and the backend,
through webhooks. The page never asks "what changed?": it opens one connection and the backend pushes.

```
AMP --webhook--> backend (saves the run) --event--> /api/kickoffs/stream (Next.js) --> useKickoffStream --> page
```

- The backend streams the list of runs as Server-Sent Events (`GET /api/v1/kickoffs/stream`).
- `src/app/api/kickoffs/stream/route.ts` passes that stream to the browser (a free ngrok tunnel needs a header
  that `EventSource` cannot send).
- `useKickoffStream` keeps `runs` equal to the last list received, and reconnects if the connection drops.
- After you click **Import**, the panel turns into the result table and each contact changes by itself
  (*waiting* -> *imported* / *failed*) while the flow imports them: the backend sees each `POST /contacts` that
  the flow makes and passes the result to the run.
- The actions (start, answer, delete) do not touch the list: the backend notices the change and sends the new one.

## What you can do (in `/contacts`)

- See all contacts in a table
- Create a contact (**New contact**)
- Edit a contact (**Edit**)
- Delete a contact (**Delete**)

API errors (for example, an email that already exists) are shown in the form.

## Settings

| Variable | Default | What it is |
|---|---|---|
| `CREWAI_FLOW_API_URL` | none | The URL of the flow deployed on CrewAI AMP (`https://<your-flow>.crewai.com`). Needed only for `/contacts/import`. **Server only** |
| `CREWAI_FLOW_API_BEARER_TOKEN` | none | The Bearer token of the deployment. **Server only: it never reaches the browser** |
| `EXTERNAL_APP_API_URL` | `http://localhost:8000` | The backend API. The browser calls it (passed in `next.config.ts`; restart `npm run dev` after changing it), the Next.js server passes on its live stream (`/api/kickoffs/stream`) and AMP sends the start and the end of each run to `<it>/flow-webhook`, so after deploying the flow set the **public (ngrok) address**. With `localhost` a kickoff is refused |
| `CREWAI_KICKOFF_WEBHOOK_SECRET` | none | The secret of the kickoff webhook: any value you choose, the same as in the backend `.env`. The proxy gives it to AMP in each kickoff, and AMP sends it back with the events. **Server only** |

If `CREWAI_FLOW_API_URL` or `CREWAI_FLOW_API_BEARER_TOKEN` is missing, the import page says which one.

The browser does not call the flow directly. It calls `/api/flow/*` (a route handler of this app,
`src/app/api/flow/[...path]/route.ts`), which adds the token and forwards to `CREWAI_FLOW_API_URL`.

## Project layout

```
src/
├── app/
│   ├── api/
│   │   ├── flow/[...path]/route.ts    # Proxy to the flow (adds the Bearer token and the `webhooks` on the server)
│   │   └── kickoffs/stream/route.ts   # Passes the live list of runs from the backend to the browser
│   ├── layout.tsx            # Page shell
│   ├── page.tsx              # Home (/): project name and links
│   └── contacts/
│       ├── page.tsx          # /contacts: loads data and handles the actions
│       └── import/page.tsx   # /contacts/import: only composes the hook and the components
├── hooks/
│   ├── useKickoffStream.ts   # The live list of runs (EventSource)
│   └── useImportRuns.ts      # The import page: the live runs + the actions on them (start, answer, delete)
├── components/
│   ├── ui.ts                 # buttonClass(): the look of the buttons
│   ├── ContactTable.tsx      # The table with Edit and Delete buttons
│   ├── ContactForm.tsx       # The modal form used to create and edit
│   └── import/               # The import page, one component per piece
│       ├── GenerateForm.tsx      #   the count, and the button that starts the flow
│       ├── RunList.tsx           #   the list of runs
│       ├── RunRow.tsx            #   one run: status, and the panel to review / see the result
│       ├── ReviewSelection.tsx   #   the human review: contacts with checkboxes, Import N of M
│       ├── ImportResult.tsx      #   what happened to each contact after the import
│       ├── ContactsTable.tsx     #   the generated contacts as a table (shared by the two above)
│       └── Badge.tsx             #   the colored labels
└── lib/
    ├── http.ts               # `request()` and `ApiError`: every call goes through it
    ├── external-app-api/     # The backend API, one module (import from "@/lib/external-app-api")
    │   ├── contacts.ts       #   contacts: list, create, update, delete
    │   └── kickoffs.ts       #   runs: save, answer the review, forget, and the URL of the stream
    ├── flow-api.ts           # The call to the flow: POST /kickoff (the rest reaches the backend by webhooks)
    └── runs.ts               # The text and the rules of a run, by its `outcome` (pure helpers)
```

`contacts/page.tsx` holds the state and calls `lib/external-app-api`. On the import page, `useImportRuns` holds the
state, and the components only show data and tell the page what the user did.
