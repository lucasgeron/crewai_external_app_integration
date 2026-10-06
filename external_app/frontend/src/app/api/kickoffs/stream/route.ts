// Passes the live list of runs from our backend to the browser.
//
// The backend sends Server-Sent Events at GET /api/v1/kickoffs/stream (the whole list, every time a run
// changes). The browser could open it directly, but a free ngrok tunnel only lets a request through if it
// carries a header, and `EventSource` cannot set headers. Here, on the server, we can:
//
//   browser (EventSource)  ->  /api/kickoffs/stream  ->  <EXTERNAL_APP_API_URL>/api/v1/kickoffs/stream
//
// The events are not read or changed: the body is passed through as it arrives.

import { NextRequest } from "next/server";

const API_URL = process.env.EXTERNAL_APP_API_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const upstream = await fetch(`${API_URL}/api/v1/kickoffs/stream`, {
      headers: { "ngrok-skip-browser-warning": "1" },
      cache: "no-store",
      // The browser closed the page: close the connection to the backend too.
      signal: request.signal,
    });
    if (!upstream.ok || !upstream.body) throw new Error(`HTTP ${upstream.status}`);

    return new Response(upstream.body, {
      headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform" },
    });
  } catch {
    return Response.json(
      { detail: "Could not reach the backend. Check EXTERNAL_APP_API_URL and that the backend is running." },
      { status: 502 },
    );
  }
}
