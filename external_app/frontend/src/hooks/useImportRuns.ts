// The state of the import page: every run of the flow and the actions on them.
//
// The list comes live from the backend (useKickoffStream), because AMP tells the backend about each step with
// webhooks:  initialized -> generated (waits for the review) -> (the user answers) -> imported / failed
// So the actions below do not update the list: they change something, the backend notices, and the stream
// brings the new list.
"use client";

import { useState } from "react";
import { useKickoffStream } from "@/hooks/useKickoffStream";
import { startImport, type ReviewAnswer } from "@/lib/flow-api";
import { destroyAllKickoffs, forgetKickoff, respondToReview, saveKickoff } from "@/lib/external-app-api";

export function useImportRuns() {
  const { runs, loading, connected } = useKickoffStream();
  const [error, setError] = useState<string | null>(null);

  // Trigger the flow. The run appears in the list by itself (see saveKickoff). Returns false on failure.
  const start = (count: number) =>
    attempt("Could not start the import", async () => {
      await saveKickoff(await startImport(count));
    });

  // Send the selection to the flow: our backend posts it to the callback_url of the review.
  // Throws if the flow host refuses it, so the review screen shows why.
  const answer = async (kickoffId: string, answerBody: ReviewAnswer) => {
    await respondToReview(kickoffId, JSON.stringify(answerBody));
  };

  // Remove a run from our database. The run itself (in the flow) is not touched.
  const forget = (kickoffId: string) =>
    attempt("Could not remove the run", () => forgetKickoff(kickoffId));

  // Remove every run from our database (the runs in the flow are not touched).
  const destroyAll = () => attempt("Could not remove the runs", destroyAllKickoffs);

  return { runs, loading, connected, error, start, answer, forget, destroyAll };

  // ---------- helpers (used by the actions above) ----------

  // Run an action. If it fails, show its message in the page and return false.
  async function attempt(fallback: string, action: () => Promise<unknown>): Promise<boolean> {
    setError(null);
    try {
      await action();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : fallback);
      return false;
    }
  }
}
