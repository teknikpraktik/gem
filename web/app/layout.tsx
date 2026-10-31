import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";
import ServiceWorkerRegister from "@/components/ServiceWorkerRegister";
import { DISCLAIMER } from "@/lib/api";

export const metadata: Metadata = {
  title: "REGIONAL_SEK – signalmonitor",
  description: "Regelbaserad månadssignal (REGIONAL_SEK) med full datatransparens. Ingen automatisk handel.",
  applicationName: "Signalmonitor",
  appleWebApp: { capable: true, title: "Signalmonitor", statusBarStyle: "default" },
  icons: { icon: "/icons/icon-192.png", apple: "/icons/apple-touch-icon.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#1b1b1a" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sv">
      <body>
        <header className="top">
          <div className="wrap">
            <Link href="/" className="brand">REGIONAL_SEK<small>signalmonitor</small></Link>
            <nav className="main" aria-label="Huvudmeny">
              <Link href="/">Signal</Link>
              <Link href="/history">Historik</Link>
              <Link href="/backtest">Backtest</Link>
              <Link href="/research">Research</Link>
            </nav>
          </div>
        </header>
        <main className="wrap">{children}</main>
        <footer className="wrap foot">{DISCLAIMER}</footer>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
