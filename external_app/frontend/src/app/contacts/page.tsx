// This is the /contacts page. It owns the state and talks to the API (via lib/external-app-api/contacts.ts).
// "use client" is needed because it uses state and effects, which only run in the browser.
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ContactForm from "@/components/ContactForm";
import ContactTable from "@/components/ContactTable";
import { buttonClass } from "@/components/ui";
import {
  createContact,
  deleteContact,
  listContacts,
  destroyAllContacts,
  updateContact,
  type Contact,
  type ContactInput,
} from "@/lib/external-app-api";

export default function Home() {
  // State = data that, when changed, makes React draw the screen again.
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // showForm controls the modal. editing is the contact being edited (null = new contact).
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Contact | null>(null);

  // Bump this number to load the contacts again.
  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((key) => key + 1);

  // Load the contacts from the API on the first render and after every reload().
  useEffect(() => {
    let cancelled = false;
    // An effect cannot be async itself, so we declare an async function inside it.
    async function load() {
      try {
        const data = await listContacts();
        if (!cancelled) {
          setContacts(data);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("Could not reach the API. Is the backend running?");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    // If the page changes before the request ends, ignore the result.
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  function openNew() {
    setEditing(null);
    setShowForm(true);
  }

  function openEdit(contact: Contact) {
    setEditing(contact);
    setShowForm(true);
  }

  // The form calls this when the user saves.
  // Create or update, depending on whether we are editing. Errors go back to the form.
  async function handleSave(data: ContactInput) {
    if (editing) {
      await updateContact(editing.id, data);
    } else {
      await createContact(data);
    }
    // Close the form and fetch the list again so the table shows the new data.
    setShowForm(false);
    reload();
  }

  async function handleDelete(contact: Contact) {
    // Always confirm before a destructive action.
    if (!window.confirm(`Delete ${contact.name}?`)) return;
    try {
      await deleteContact(contact.id);
      reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the contact");
    }
  }

  // Destroys every contact (the whole table). Destructive, so the user must confirm.
  async function handleDestroyAll() {
    if (!window.confirm("Delete ALL contacts? This cannot be undone.")) return;
    try {
      await destroyAllContacts();
      setError(null);
      reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not destroy the contacts");
    }
  }

  return (
    <main className="w-full p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-zinc-500 hover:underline">
            &larr; External App
          </Link>
          <h1 className="text-2xl font-semibold">Contacts</h1>
        </div>
        <div className="flex gap-2">
        <button
          onClick={handleDestroyAll}
          className={buttonClass("danger")}
        >
          Destroy all contacts
        </button>
        <Link
          href="/contacts/import"
          className={buttonClass("secondary")}
        >
          Import contacts
        </Link>
        <button
          onClick={openNew}
          className={buttonClass("primary")}
        >
          New contact
        </button>
        </div>
      </header>

      {error && (
        <p className="mb-4 rounded-md bg-red-100 p-3 text-sm text-red-700">{error}</p>
      )}

      {loading ? (
        <p className="py-8 text-center text-zinc-500">Loading...</p>
      ) : (
        <ContactTable
          contacts={contacts}
          onEdit={openEdit}
          onDelete={handleDelete}
        />
      )}

      {showForm && (
        <ContactForm
          contact={editing}
          onSave={handleSave}
          onCancel={() => setShowForm(false)}
        />
      )}
    </main>
  );
}
