import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Don't use standalone output on Vercel — Vercel handles this automatically
  // output: "standalone",  // Uncomment for Docker/self-hosted only
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
};

export default nextConfig;
