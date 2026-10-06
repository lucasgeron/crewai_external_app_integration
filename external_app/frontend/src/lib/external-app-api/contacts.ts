// The contacts API (the FastAPI backend): the contacts table, with create, edit and delete.
// Each function below matches one endpoint, and they are the only ones the pages and components use.

import { API_URL, request } from "@/lib/http";

// All contact routes live under /api/v1/contacts (see the backend's api/v1 folder).
const CONTACTS_URL = `${API_URL}/api/v1/contacts`;

// The contact as the API returns it.
// These types mirror the backend's ContactRead schema (backend/app/schemas/contact.py).
// Dates arrive as ISO strings because JSON has no date type.
export type Contact = {
  id: number;
  name: string;
  email: string;
  instagram: string | null;
  facebook: string | null;
  linkedin: string | null;
  website: string | null;
  created_at: string;
  updated_at: string;
};

// The fields a user can edit (no id and no dates).
export type ContactInput = Omit<Contact, "id" | "created_at" | "updated_at">;

// GET /contacts
export const listContacts = () => request<Contact[]>(CONTACTS_URL);

// POST /contacts
export const createContact = (data: ContactInput) =>
  request<Contact>(CONTACTS_URL, { method: "POST", body: JSON.stringify(data) });

// PATCH /contacts/{id} (changes only the fields we send)
export const updateContact = (id: number, data: ContactInput) =>
  request<Contact>(`${CONTACTS_URL}/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

// DELETE /contacts (deletes ALL contacts and restarts the ids from 1)
export const destroyAllContacts = () => request<void>(CONTACTS_URL, { method: "DELETE" });

// DELETE /contacts/{id}
export const deleteContact = (id: number) =>
  request<void>(`${CONTACTS_URL}/${id}`, { method: "DELETE" });
