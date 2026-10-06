"use client";

import { useState } from "react";
import type { GeneratedContact } from "@/lib/external-app-api";
import type { ReviewAnswer } from "@/lib/flow-api";
import ContactsTable from "@/components/import/ContactsTable";
import { buttonClass } from "@/components/ui";

type Props = {
  contacts: GeneratedContact[];
  // Sends the answer to the flow. It can throw, and the message is shown here.
  onSubmit: (answer: ReviewAnswer) => Promise<void>;
  onCancel: () => void;
};

// The human step of the flow: look at the generated contacts and choose which ones to import.
export default function ReviewSelection({ contacts, onSubmit, onCancel }: Props) {
  // Every contact starts selected. The reviewer unchecks the ones to discard.
  const [selected, setSelected] = useState<Set<number>>(() => new Set(contacts.map((contact) => contact.ref)));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggle(ref: number) {
    const next = new Set(selected);
    if (next.has(ref)) next.delete(ref);
    else next.add(ref);
    setSelected(next);
  }

  async function send() {
    setSending(true);
    setError(null);
    try {
      await onSubmit({ selected_refs: [...selected] });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setSending(false);
    }
  }

  return (
    <div className="space-y-4">
      <ContactsTable
        contacts={contacts}
        firstTitle="Import"
        firstCell={(contact) => (
          <input
            type="checkbox"
            checked={selected.has(contact.ref)}
            onChange={() => toggle(contact.ref)}
            className="h-4 w-4 cursor-pointer"
          />
        )}
      />

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex justify-end gap-2">
        <button
          onClick={onCancel}
          disabled={sending}
          className={buttonClass("secondary")}
        >
          Back
        </button>
        <button
          onClick={send}
          disabled={sending || selected.size === 0}
          className={buttonClass("primary")}
        >
          {sending ? "Sending..." : `Import ${selected.size} of ${contacts.length}`}
        </button>
      </div>
    </div>
  );
}
