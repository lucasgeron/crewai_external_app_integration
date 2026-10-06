// The home page. It only shows the project name and a link to the contacts page.
// No "use client" here: it has no state, so it can be a Server Component (the default).
import Link from "next/link";
import { buttonClass } from "@/components/ui";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-6">
      <h1 className="text-4xl font-semibold">External App</h1>
      {/* Link navigates between pages without reloading the whole site. */}
      <Link
        href="/contacts/import"
        className={buttonClass("primary")}
      >
        Import Contacts
      </Link>
      <Link
        href="/contacts"
        className={buttonClass("primary")}
      >
        View Contacts
      </Link>
    </main>
  );
}
