// "use client" means this component runs in the browser.
// We need it because the form uses state (useState) and handles events.
"use client";

import { useState } from "react";
import { buttonClass } from "@/components/ui";
import type { Contact, ContactInput } from "@/lib/external-app-api";

// Props are the inputs of a component. The parent page decides what to do on save/cancel,
// so this form stays simple and can be reused.
type Props = {
  // When a contact is given, the form edits it. Otherwise it creates a new one.
  contact: Contact | null;
  onSave: (data: ContactInput) => Promise<void>;
  onCancel: () => void;
};

// The optional fields, so we can render them with a loop.
const optionalFields = ["instagram", "facebook", "linkedin", "website"] as const;

const inputClass =
  "w-full rounded-md border border-zinc-300 bg-transparent px-3 py-2 text-sm dark:border-zinc-700";

export default function ContactForm({ contact, onSave, onCancel }: Props) {
  // saving disables the button; error shows a message from the API.
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    // Stop the browser from reloading the page, we send the data with fetch instead.
    event.preventDefault();
    // FormData reads the values of the inputs by their name attribute.
    const form = new FormData(event.currentTarget);
    const text = (name: string) => String(form.get(name) ?? "").trim();

    // Empty optional fields become null, so the API clears them.
    const data: ContactInput = {
      name: text("name"),
      email: text("email"),
      instagram: text("instagram") || null,
      facebook: text("facebook") || null,
      linkedin: text("linkedin") || null,
      website: text("website") || null,
    };

    setSaving(true);
    setError(null);
    try {
      // The parent calls the API. If it throws (for example 409), we show the message.
      await onSave(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/50 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-4 rounded-lg bg-background p-6 shadow-xl"
      >
        <h2 className="text-lg font-semibold">
          {contact ? "Edit contact" : "New contact"}
        </h2>

        {/* defaultValue fills the field but still lets the user type (uncontrolled input). */}
        <label className="block text-sm">
          Name *
          <input
            name="name"
            required
            defaultValue={contact?.name}
            className={inputClass}
          />
        </label>

        <label className="block text-sm">
          Email *
          <input
            name="email"
            type="email"
            required
            defaultValue={contact?.email}
            className={inputClass}
          />
        </label>

        {/* One input per optional field, created with a loop to avoid repeating code. */}
        {optionalFields.map((field) => (
          <label key={field} className="block text-sm capitalize">
            {field}
            <input
              name={field}
              defaultValue={contact?.[field] ?? ""}
              className={inputClass}
            />
          </label>
        ))}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className={buttonClass("secondary")}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className={buttonClass("primary")}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
