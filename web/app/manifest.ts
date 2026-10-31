import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "REGIONAL_SEK signalmonitor",
    short_name: "Signalmonitor",
    description: "Regelbaserad månadssignal med datatransparens. Ingen automatisk handel.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#f6f6f4",
    theme_color: "#ffffff",
    lang: "sv",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
