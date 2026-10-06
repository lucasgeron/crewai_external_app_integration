// The External App API (the FastAPI backend), as one module: import everything from "@/lib/external-app-api".
//
//   contacts.ts  - the contacts table (create, edit, delete)
//   kickoffs.ts  - the runs of the import flow (save, answer the review, forget) and the URL of their live stream
//
// The flow itself (CrewAI AMP) is another service, so it is NOT here: see lib/flow-api.ts.

export * from "@/lib/external-app-api/contacts";
export * from "@/lib/external-app-api/kickoffs";
