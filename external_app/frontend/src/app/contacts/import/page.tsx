// The /contacts/import page. The browser only does two things with the CrewAI flow: it starts it (the
// form) and answers its human review (inside the run list). Everything else happens between the flow and
// the backend, by webhooks, and the backend sends each change to this page, live. State lives in useImportRuns.
"use client";

import Link from "next/link";
import GenerateForm from "@/components/import/GenerateForm";
import RunList from "@/components/import/RunList";
import { useImportRuns } from "@/hooks/useImportRuns";

export default function ImportPage() {
  const imports = useImportRuns();

  return (
    <main className="w-full space-y-8 p-6">
      <header className="relative">
        <LiveStatus connected={imports.connected} />
        <Link
          href="/contacts"
          className="text-sm text-zinc-500 hover:underline"
        >
          &larr; Contacts
        </Link>
        <h1 className="text-2xl font-semibold">Import contacts</h1>
        <p className="text-sm text-zinc-500">
          A CrewAI flow generates contacts. You select which ones to import, and
          the flow imports them.
        </p>
      </header>

      {imports.error && (
        <p className="rounded-md bg-red-100 p-3 text-sm text-red-700">
          {imports.error}
        </p>
      )}

      <GenerateForm onStart={imports.start} />
      <RunList
        runs={imports.runs}
        loading={imports.loading}
        onAnswer={imports.answer}
        onDelete={imports.forget}
        onDestroyAll={imports.destroyAll}
      />
    </main>
  );
}

// ---------- helpers (used by the page above) ----------

// Shows if the connection that brings the runs is open. While it is not, the list may be out of date.
function LiveStatus({ connected }: { connected: boolean }) {
  return (
    <span className="absolute right-0 top-0 flex items-center gap-2 text-xs text-zinc-500">
      <span className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-amber-500"}`} />
      {connected ? "Live" : "Reconnecting..."}
    </span>
  );
}
