"use client";

import { useState } from "react";
import { buttonClass } from "@/components/ui";

// The request of an import: how many contacts to generate.
export default function GenerateForm({ onStart }: { onStart: (count: number) => Promise<boolean> }) {
  const [count, setCount] = useState(5);
  const [starting, setStarting] = useState(false);
  const valid = Number.isInteger(count);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!valid || starting) return;
    setStarting(true);
    try {
      await onStart(count);
    } finally {
      setStarting(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
      <label className="text-sm">
        How many contacts?
        <input
          type="number"
          value={Number.isNaN(count) ? "" : count}
          onChange={(event) => setCount(event.target.valueAsNumber)}
          className="mt-1 block w-32 rounded-md border border-zinc-300 bg-transparent px-3 py-2 dark:border-zinc-700"
        />
      </label>
      <button
        type="submit"
        disabled={!valid || starting}
        className={buttonClass("primary")}
      >
        {starting ? "Starting..." : "Generate contacts"}
      </button>
    </form>
  );
}
