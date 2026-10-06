import { buttonClass } from "@/components/ui";
import type { Contact } from "@/lib/external-app-api";

// This component only displays data. It never calls the API:
// it tells the parent page what happened (onEdit / onDelete) and the page decides what to do.
type Props = {
  contacts: Contact[];
  onEdit: (contact: Contact) => void;
  onDelete: (contact: Contact) => void;
};

const formatDate = (iso: string) => new Date(iso).toLocaleString();

export default function ContactTable({ contacts, onEdit, onDelete }: Props) {
  // Show a friendly message instead of an empty table.
  if (contacts.length === 0) {
    return <p className="py-8 text-center text-zinc-500">No contacts yet.</p>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-100 dark:bg-zinc-900">
          <tr>
            {["Name", "Email", "Instagram", "Facebook", "LinkedIn", "Website", "Updated", ""].map(
              (title) => (
                <th key={title} className="px-4 py-3 font-medium">
                  {title}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {/* key helps React track each row when the list changes. Use a stable id. */}
          {contacts.map((contact) => (
            <tr
              key={contact.id}
              className="border-t border-zinc-200 dark:border-zinc-800"
            >
              <td className="whitespace-nowrap px-4 py-3 font-medium">{contact.name}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.email}</td>
              {/* ?? shows "-" when the optional value is null */}
              <td className="px-4 py-3 wrap-anywhere">{contact.instagram ?? "-"}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.facebook ?? "-"}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.linkedin ?? "-"}</td>
              <td className="px-4 py-3 wrap-anywhere">{contact.website ?? "-"}</td>
              <td className="whitespace-nowrap px-4 py-3">
                {formatDate(contact.updated_at)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right">
                <button
                  onClick={() => onEdit(contact)}
                  className={`mr-2 ${buttonClass("secondary", "small")}`}
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(contact)}
                  className={buttonClass("danger", "small")}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
