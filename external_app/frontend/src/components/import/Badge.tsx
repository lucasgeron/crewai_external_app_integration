import type { Outcome } from "@/lib/external-app-api";
import type { ContactStatus } from "@/lib/runs";

// The small colored label. Two kinds: where a run is, and what happened to a contact.
export function RunBadge({ outcome }: { outcome: Outcome }) {
  return <Badge className={`w-28 shrink-0 text-center ${runColors[outcome]}`}>{outcome}</Badge>;
}

export function ContactBadge({ status }: { status: ContactStatus }) {
  return <Badge className={contactColors[status]}>{status}</Badge>;
}

// ---------- helpers (used by the badges above) ----------

const runColors: Record<Outcome, string> = {
  initialized: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  generated: "bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300",
  imported: "bg-green-100 text-green-800 dark:bg-green-500/15 dark:text-green-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-500/15 dark:text-red-300",
};

const contactColors: Record<ContactStatus, string> = {
  skipped: runColors.initialized,
  waiting: runColors.generated,
  imported: runColors.imported,
  failed: runColors.failed,
};

function Badge({ className, children }: { className: string; children: React.ReactNode }) {
  return (
    <span
      className={`inline-block rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wider ${className}`}
    >
      {children}
    </span>
  );
}
