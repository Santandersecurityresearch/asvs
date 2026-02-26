import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "OWASP ASVS 5.0",
  description: "OWASP Application Security Verification Standard v5.0 Compliance Tracker",
  icons: { icon: "/img/logoicon.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div id="wrapper" className="min-h-screen bg-gray-50 dark:bg-gray-900 dark:text-white">
            <Navbar />
            <main className="pt-16">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
