import { ContactBadge } from "@/components/import/Badge";
import ContactsTable from "@/components/import/ContactsTable";
import { contactStatus, type Run } from "@/lib/runs";

// What the flow did with each contact: waiting, imported, failed (and why) or skipped. While the flow
// imports them, this table changes by itself, one contact at a time.
export default function ImportResult({ run }: { run: Run }) {
  return (
    <ContactsTable
      contacts={run.contacts ?? []}
      firstTitle="Result"
      firstCell={(contact) => (
        <div className="space-y-1">
          <ContactBadge status={contactStatus(run, contact)} />
          {contact.import_error && (
            <p className="text-xs text-red-600 dark:text-red-400">{contact.import_error}</p>
          )}
        </div>
      )}
    />
  );
}
