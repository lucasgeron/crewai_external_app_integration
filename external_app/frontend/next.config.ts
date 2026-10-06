import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Makes EXTERNAL_APP_API_URL available in the browser code (see src/lib/http.ts). The Next.js server reads it too:
  // it is the address AMP sends the events to (src/app/api/flow/[...path]/route.ts) and the backend whose live
  // stream it passes on (src/app/api/kickoffs/stream/route.ts).
  // Its value is copied into the code at build time, so restart `npm run dev` after changing it.
  // CREWAI_FLOW_API_URL and CREWAI_FLOW_API_BEARER_TOKEN are NOT listed on purpose: only the server
  // reads them (src/app/api/flow/[...path]/route.ts), so the token never reaches the browser.
  env: {
    EXTERNAL_APP_API_URL: process.env.EXTERNAL_APP_API_URL,
  },
};

export default nextConfig;
