// The runs of the import flow, kept by our backend (the `kickoffs` table). The flow host has no "list my
// runs" endpoint, so the backend keeps one row per run and AMP keeps it up to date with webhooks.
//
// The page does not ask for the list again and again. It opens ONE connection (see hooks/useKickoffStream.ts)
// and the backend sends the list every time a run changes. The functions here only act on the runs.

import { API_URL, request } from "@/lib/http";

const KICKOFFS_URL = `${API_URL}/api/v1/kickoffs`;

// Where the browser listens to the runs. It is a route of this app (src/app/api/kickoffs/stream/route.ts)
// that passes the stream of the backend through.
export const KICKOFFS_STREAM_URL = "/api/kickoffs/stream";

// A contact the flow generated. Same fields as the backend, plus a temporary `ref` (only
// meaningful inside one run, NOT the database id). After the flow imports the selected contacts,
// `import_status` says what happened to each one ("pending" means it was not selected).
export type GeneratedContact = {
  ref: number;
  name: string;
  email: string;
  instagram: string | null;
  facebook: string | null;
  linkedin: string | null;
  website: string | null;
  import_status: "pending" | "imported" | "failed";
  external_app_id: number | null;
  import_error: string | null;
};

// Where a run is. The same names as `outcome` in the state of the flow: "initialized" when it starts,
// "generated" when it waits for the reviewer, then "imported" or "failed".
export type Outcome = "initialized" | "generated" | "imported" | "failed";

// A saved run of the import flow: everything we know about it in one row (backend/app/schemas/kickoff.py).
// `contacts` arrive with the review webhook (the state of the flow at the pause) and again, with the result
// of the import, when the flow finishes. The review (`request_id`, `method_name`, `answered_at`) is filled
// by the webhook; its callback_url is never returned.
export type Kickoff = {
  kickoff_id: string;
  outcome: Outcome;
  error: string | null;
  contacts: GeneratedContact[] | null;
  selected_refs: number[] | null;
  request_id: string | null;
  method_name: string | null;
  answered_at: string | null;
  created_at: string;
};

// POST /kickoffs (save the id returned by the flow's /kickoff, so the run is listed right away: the
// first webhook of AMP can take a few seconds)
export const saveKickoff = (kickoffId: string) =>
  request<Kickoff>(KICKOFFS_URL, {
    method: "POST",
    body: JSON.stringify({ kickoff_id: kickoffId }),
  });

// POST /kickoffs/{kickoff_id}/respond (the reviewer's answer to a paused run). The API posts it to the
// callback_url of the review, which is how the flow host receives the answer of a flow.
// `feedback` is the JSON text of ReviewAnswer (see lib/flow-api.ts).
export const respondToReview = (kickoffId: string, feedback: string) =>
  request<{ status: string }>(`${KICKOFFS_URL}/${kickoffId}/respond`, {
    method: "POST",
    body: JSON.stringify({ feedback }),
  });

// DELETE /kickoffs/{kickoff_id} (forget a run id; the run itself is untouched)
export const forgetKickoff = (kickoffId: string) =>
  request<void>(`${KICKOFFS_URL}/${kickoffId}`, { method: "DELETE" });

// DELETE /kickoffs (forget ALL run ids; the runs themselves are untouched)
export const destroyAllKickoffs = () => request<void>(KICKOFFS_URL, { method: "DELETE" });
