// Proxy from the browser to the CrewAI flow deployed on CrewAI AMP.
//
// Why a proxy? The flow requires a Bearer token. If the browser called it directly, the token
// would be visible to anyone using the page. Here the token is read on the SERVER (no
// NEXT_PUBLIC_ prefix, so it never reaches the browser) and added to every request.
// Bonus: the browser only talks to this app, so the flow needs no CORS settings.
//
//   browser  ->  /api/flow/kickoff  ->  <CREWAI_FLOW_API_URL>/kickoff  (Authorization: Bearer ..., plus `webhooks`)

import { NextRequest } from "next/server";

const FLOW_URL = process.env.CREWAI_FLOW_API_URL ?? "";
const BEARER_TOKEN = process.env.CREWAI_FLOW_API_BEARER_TOKEN ?? "";

// Webhook Streaming: every kickoff asks AMP to send the start and the end of the run to our backend
// (`webhooks` in the kickoff request, received by POST /flow-webhook in the backend). AMP calls that address
// from the internet, so EXTERNAL_APP_API_URL must be the public one (the ngrok tunnel), not localhost.
const API_URL = process.env.EXTERNAL_APP_API_URL ?? "";
const KICKOFF_SECRET = process.env.CREWAI_KICKOFF_WEBHOOK_SECRET ?? "";
// Only events listed in "Supported Events" of the Webhook Streaming docs. The ones of the human review
// (flow_paused, human_feedback_*) are not there: the review comes from the webhook of the AMP dashboard.
const EVENTS = ["flow_started", "flow_finished", "method_execution_failed"];

const isLocal = (url: string) => ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"].includes(new URL(url).hostname);

// What is missing for AMP to be able to tell our backend about a run.
function eventsProblem() {
  if (!KICKOFF_SECRET) return "CREWAI_KICKOFF_WEBHOOK_SECRET is not set (any secret, the same one as in the backend .env).";
  if (!API_URL || isLocal(API_URL)) {
    return "EXTERNAL_APP_API_URL is localhost, and AMP cannot reach it. Set it to the public address of the backend (the ngrok tunnel).";
  }
  return null;
}

// The body of the kickoff, with the `webhooks` object added.
function kickoffBody(text: string) {
  const body = JSON.parse(text);
  body.webhooks = {
    events: EVENTS,
    url: `${API_URL}/flow-webhook`,
    realtime: true,
    authentication: { strategy: "bearer", token: KICKOFF_SECRET },
  };
  return JSON.stringify(body);
}

// The endpoints every flow deployed to AMP has. Anything else is refused.
const ALLOWED = new Set(["healthcheck", "inputs", "kickoff", "status"]);

async function proxy(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  if (!ALLOWED.has(path[0])) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }

  // Say what is missing instead of letting the flow answer "Not authenticated" (or the call fail).
  // /healthcheck needs no token, so it only needs the URL.
  const missing = [
    !FLOW_URL && "CREWAI_FLOW_API_URL",
    !BEARER_TOKEN && path[0] !== "healthcheck" && "CREWAI_FLOW_API_BEARER_TOKEN",
  ].filter(Boolean);
  if (missing.length > 0) {
    return Response.json(
      {
        detail:
          `${missing.join(" and ")} not set. Add ${missing.length > 1 ? "them" : "it"} to ` +
          "external_app/frontend/.env.local (the URL and the Bearer token of the AMP deployment) and restart the app.",
      },
      { status: 500 },
    );
  }

  const problem = path[0] === "kickoff" && eventsProblem();
  if (problem) {
    return Response.json(
      { detail: `${problem} Without it the app never learns that a run finished. See external_app/frontend/.env.example.` },
      { status: 500 },
    );
  }

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  let body = hasBody ? await request.text() : undefined;
  if (body && path[0] === "kickoff") body = kickoffBody(body);
  try {
    const response = await fetch(`${FLOW_URL}/${path.join("/")}${request.nextUrl.search}`, {
      method: request.method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${BEARER_TOKEN}`,
      },
      body,
      cache: "no-store",
    });
    // Pass the answer through as it is (status code and JSON body).
    return new Response(await response.text(), {
      status: response.status,
      headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/json" },
    });
  } catch {
    return Response.json(
      { detail: "Could not reach the flow. Check CREWAI_FLOW_API_URL and that the flow is running." },
      { status: 502 },
    );
  }
}

export { proxy as GET, proxy as POST };
