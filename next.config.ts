import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = {
  // In development, proxy /api/* to the local FastAPI server on port 8000.
  // On Vercel, /api/* is served directly by the Python serverless function —
  // no rewrite needed (Vercel routes it via vercel.json).
  ...(isDev && {
    async rewrites() {
      return [
        {
          source: "/api/:path*",
          destination: "http://127.0.0.1:8000/api/:path*",
        },
      ];
    },
  }),
};

export default nextConfig;
