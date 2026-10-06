import type { ReactNode } from "react";
import type { GeneratedContact } from "@/lib/external-app-api";

// The generated contacts as a table. The first column changes with the moment: the checkbox to
// choose what to import (review) or what happened to each contact (after the import).
export default function ContactsTable({
  contacts,
  firstTitle,
  firstCell,
}: {
  contacts: GeneratedContact[];
  firstTitle: string;
  firstCell: (contact: GeneratedContact) => ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-100 dark:bg-zinc-900">
          <tr>
            {[firstTitle, "Name", "Email", "Instagram", "Facebook", "LinkedIn", "Website"].map((title) => (
              <th key={title} className="px-4 py-3 font-medium">
                {title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {contacts.map((contact) => (
            <tr key={contact.ref} className="border-t border-zinc-200 dark:border-zinc-800">
              <td className="px-4 py-3">{firstCell(contact)}</td>
              <td className="whitespace-nowrap px-4 py-3 font-medium">{contact.name}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.email}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.instagram ?? "-"}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.facebook ?? "-"}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.linkedin ?? "-"}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.website ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
