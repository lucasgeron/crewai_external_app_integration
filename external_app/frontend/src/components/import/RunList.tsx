"use client";

import RunRow from "@/components/import/RunRow";
import { buttonClass } from "@/components/ui";
import type { ReviewAnswer } from "@/lib/flow-api";
import type { Run } from "@/lib/runs";

type Props = {
  runs: Run[];
  loading: boolean;
  onAnswer: (kickoffId: string, answer: ReviewAnswer) => Promise<void>;
  onDelete: (kickoffId: string) => void;
  onDestroyAll: () => void;
};

// Every run, newest first. The list is live: it changes by itself as the flow moves.
export default function RunList({ runs, loading, onAnswer, onDelete, onDestroyAll }: Props) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Runs{loading ? "" : ` (${runs.length})`}</h2>
        <button
          onClick={() => window.confirm("Delete ALL runs from the list? This cannot be undone.") && onDestroyAll()}
          disabled={loading || runs.length === 0}
          className={buttonClass("danger", "small")}
        >
          Destroy all runs
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-zinc-500">Loading...</p>
      ) : runs.length === 0 ? (
        <p className="text-sm text-zinc-500">No import yet.</p>
      ) : (
        <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-200 text-sm dark:divide-zinc-800 dark:border-zinc-800">
          {runs.map((run) => (
            <RunRow key={run.kickoff_id} run={run} onAnswer={onAnswer} onDelete={onDelete} />
          ))}
        </ul>
      )}
    </section>
  );
}
