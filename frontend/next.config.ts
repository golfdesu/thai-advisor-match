import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.ac.th",
      },
      {
        protocol: "http",
        hostname: "**.ac.th",
      },
      {
        protocol: "https",
        hostname: "**.edu",
      },
      {
        protocol: "http",
        hostname: "**.edu",
      },
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "ui-avatars.com",
      },
    ],
  },
};

export default nextConfig;

