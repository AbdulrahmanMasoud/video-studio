import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");
const API_INTERNAL_URL = process.env.API_INTERNAL_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  // The browser talks to the API through same-origin /api/* so cookies stay first-party and CORS is a non-issue.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_INTERNAL_URL}/:path*` }];
  },
  async headers() {
    return [{ source: "/(.*)", headers: [{ key: "X-Content-Type-Options", value: "nosniff" }, { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" }] }];
  },
};

export default withNextIntl(nextConfig);
