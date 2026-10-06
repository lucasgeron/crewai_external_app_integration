// Client for the CrewAI flow, which runs on CrewAI AMP. It is separate from the other clients because it
// talks to a different service: the flow, not the contacts API.
//
// The browser only starts a run here: POST /kickoff, through our own proxy at /api/flow/*
// (src/app/api/flow/[...path]/route.ts), which adds the Bearer token on the server. Everything that happens
// afterwards reaches the backend by itself, as webhooks sent by AMP: the review request
// and the start and the end of the run (both in the backend's api/webhook.py).
// There is no /resume for a flow: the answer goes to the callback_url of the review (see respondToReview
// in lib/external-app-api/kickoffs.ts).

import { ApiError, request } from "@/lib/http";

const FLOW_URL = "/api/flow";

// What the reviewer sends back: which contacts to import. It travels as JSON text in the
// `feedback` of the answer (respondToReview in lib/external-app-api/kickoffs.ts). Same shape as `ContactsSelection` in crewai_flow.
export type ReviewAnswer = {
  selected_refs: number[];
};

// POST /kickoff: start a run. It returns right away with the id (the `kickoff_id`).
// The inputs are the ones the flow asks for (just `count`), sent as strings, as in AMP.
export async function startImport(count: number): Promise<string> {
  try {
    const body = JSON.stringify({ inputs: { count: String(count) } });
    const run = await request<{ kickoff_id: string }>(`${FLOW_URL}/kickoff`, { method: "POST", body });
    return run.kickoff_id;
  } catch (err) {
    if (!(err instanceof ApiError)) throw err;
    // The flow refused our token: say where to look.
    const reason =
      err.status === 401
        ? "The flow refused the token (Not authenticated). Check CREWAI_FLOW_API_BEARER_TOKEN in external_app/frontend/.env.local and restart the app."
        : err.message;
    // Keep the HTTP status in the message, so a failed call can be told apart (401, 500, 502...).
    throw new ApiError(`${reason} (HTTP ${err.status})`, err.status);
  }
}
