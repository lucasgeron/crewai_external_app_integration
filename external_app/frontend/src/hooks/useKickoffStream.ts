// The runs of the import flow, live. Opens one connection to the backend (Server-Sent Events) and keeps
// `runs` equal to the last list it sent: first when it connects, then every time a run changes.
//
// So there is no polling: when AMP calls a webhook, the backend writes to this connection and the page
// updates by itself. `EventSource` is built into the browser, and it reconnects alone when the connection drops.
"use client";

import { useEffect, useState } from "react";
import { KICKOFFS_STREAM_URL } from "@/lib/external-app-api";
import type { Run } from "@/lib/runs";

// How long to wait before opening the connection again, when the server refused it (see onerror).
const RETRY_MS = 3000;

export function useKickoffStream() {
  // null = the first list did not arrive yet.
  const [runs, setRuns] = useState<Run[] | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let source: EventSource;
    let retry: ReturnType<typeof setTimeout>;

    function connect() {
      source = new EventSource(KICKOFFS_STREAM_URL);
      source.onopen = () => setConnected(true);
      source.onmessage = (event) => setRuns(JSON.parse(event.data));
      source.onerror = () => {
        setConnected(false);
        // While the state is CONNECTING, the browser tries again by itself. CLOSED means the server answered
        // with an error (the backend is down), and then it gives up: we try again later.
        if (source.readyState === EventSource.CLOSED) retry = setTimeout(connect, RETRY_MS);
      };
    }

    connect();
    return () => {
      clearTimeout(retry);
      source.close();
    };
  }, []);

  return { runs: runs ?? [], loading: runs === null, connected };
}
