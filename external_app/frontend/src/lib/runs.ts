// What the import page knows about a run. Pure helpers, no React.

import type { GeneratedContact, Kickoff } from "@/lib/external-app-api";

// A run is a row of our backend: its stage (`outcome`), its contacts and its review. AMP keeps it up to
// date with webhooks, and the backend sends every change to the page (see hooks/useKickoffStream.ts).
export type Run = Kickoff;

// Can the user review this run right now? The flow is paused (the webhook brought the contacts) and the
// answer was not sent yet.
export const isReviewable = (run: Run) =>
  run.outcome === "generated" && !!run.request_id && !run.answered_at && !!run.contacts?.length;

// Is there a result to show? While the flow imports the selected contacts (the answer was sent), each
// contact changes by itself as the flow reports it; once the flow finishes, all of them are final.
export const hasImportResult = (run: Run) =>
  run.outcome === "imported" || (run.outcome === "generated" && !!run.answered_at);

// What is happening to one contact of the result. "pending" has two meanings: it was not selected (skipped), or
// it is selected and the flow did not get to it yet (waiting).
export type ContactStatus = "waiting" | "skipped" | "imported" | "failed";

export function contactStatus(run: Run, contact: GeneratedContact): ContactStatus {
  if (contact.import_status !== "pending") return contact.import_status;
  const selected = run.selected_refs?.includes(contact.ref) ?? false;
  return run.outcome === "generated" && selected ? "waiting" : "skipped";
}

// The text of a run's row. The badge is the `outcome` of the run itself.
export function describe(run: Run): { title: string; detail?: string } {
  switch (run.outcome) {
    case "failed":
      return { title: "The flow failed", detail: run.error ?? "No error message was reported" };
    case "imported":
      return { title: `${count(run, "imported")} imported · ${count(run, "failed")} failed · ${count(run, "skipped")} skipped` };
    case "generated":
      if (run.answered_at) {
        const total = run.selected_refs?.length;
        const done = count(run, "imported") + count(run, "failed");
        return { title: total ? `Importing the selected contacts... ${done} of ${total}` : "Importing the selected contacts..." };
      }
      return { title: isReviewable(run) ? `${run.contacts?.length} contacts to review` : "Waiting for the review request..." };
    default:
      return { title: "Generating contacts..." };
  }
}

// ---------- helpers (used by the functions above) ----------

const count = (run: Run, status: ContactStatus) =>
  (run.contacts ?? []).filter((contact) => contactStatus(run, contact) === status).length;
