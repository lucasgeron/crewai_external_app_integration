// The one `request` function every API call goes through (the contacts API, the flow proxy), so headers and
// error handling exist in one place. Components never build URLs or parse errors by themselves.

// Set EXTERNAL_APP_API_URL in .env.local. Normally Next.js hides variables without the
// NEXT_PUBLIC_ prefix from the browser, so next.config.ts passes this one through.
export const API_URL = process.env.EXTERNAL_APP_API_URL ?? "http://localhost:8000";

// The error of a failed request. It keeps the HTTP status, so callers can tell a 401 from a 409.
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

// Send a request and return the JSON. Throw an ApiError with a readable message if it fails.
// <T> is the type of data we expect back, so callers get type safety.
export async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      // A free ngrok tunnel answers a browser with a warning page instead of the JSON, unless it gets this header.
      "ngrok-skip-browser-warning": "1",
    },
  });

  if (!response.ok) {
    throw new ApiError(await readError(response), response.status);
  }
  // DELETE returns 204 (no body).
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

// ---------- helpers (used by request above) ----------

// FastAPI and our proxy send errors as { detail: "message" } or { detail: [{ loc, msg }] }.
type ErrorBody = { detail?: string | { loc: (string | number)[]; msg: string }[] };

async function readError(response: Response): Promise<string> {
  const body: ErrorBody | null = await response.json().catch(() => null);

  if (typeof body?.detail === "string") return body.detail;
  if (Array.isArray(body?.detail)) {
    return body.detail.map((item) => `${item.loc[item.loc.length - 1]}: ${item.msg}`).join(", ");
  }
  return `Request failed (${response.status})`;
}
