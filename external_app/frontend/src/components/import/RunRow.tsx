"use client";

import { useState } from "react";
import { RunBadge } from "@/components/import/Badge";
import ImportResult from "@/components/import/ImportResult";
import ReviewSelection from "@/components/import/ReviewSelection";
import { buttonClass } from "@/components/ui";
import type { ReviewAnswer } from "@/lib/flow-api";
import { describe, hasImportResult, isReviewable, type Run } from "@/lib/runs";

type Props = {
  run: Run;
  onAnswer: (kickoffId: string, answer: ReviewAnswer) => Promise<void>;
  onDelete: (kickoffId: string) => void;
};

// One run: its status, and a panel that opens with what the user can do with it at that moment:
// review the contacts the flow paused with, read why it failed, or follow what happens to each contact.
// After the user answers, the panel stays open and turns into the result, which fills in live.
export default function RunRow({ run, onAnswer, onDelete }: Props) {
  const [open, setOpen] = useState(false);
  const { title, detail } = describe(run);
  const reviewable = isReviewable(run);
  const showResult = hasImportResult(run);

  return (
    <li className="space-y-3 px-4 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-900/50">
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <RunBadge outcome={run.outcome} />
          <div className="min-w-0">
            <p className="font-medium">{title}</p>
            <p className="truncate text-xs text-zinc-500">
              {new Date(run.created_at).toLocaleString()} · <span className="font-mono">{run.kickoff_id}</span>
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {(reviewable || showResult || detail) && (
            <button onClick={() => setOpen(!open)} className={buttonClass("secondary", "small")}>
              {open ? "Hide" : reviewable ? "Review" : "Details"}
            </button>
          )}
          <button
            onClick={() => window.confirm("Remove this run from the list?") && onDelete(run.kickoff_id)}
            className={buttonClass("danger", "small")}
          >
            Delete
          </button>
        </div>
      </div>

      {open && reviewable && run.contacts && (
        <ReviewSelection
          contacts={run.contacts}
          onSubmit={(answer) => onAnswer(run.kickoff_id, answer)}
          onCancel={() => setOpen(false)}
        />
      )}
      {open && detail && (
        <p className="rounded-md bg-red-50 p-3 text-red-700 dark:bg-red-950 dark:text-red-300">{detail}</p>
      )}
      {open && showResult && <ImportResult run={run} />}
    </li>
  );
}
