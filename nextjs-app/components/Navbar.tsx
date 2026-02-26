"use client";

import Link from "next/link";
import Image from "next/image";
import { useSession, signOut } from "next-auth/react";
import { useTheme } from "./ThemeProvider";
import { useState } from "react";

const HELP_CATEGORIES = [
  { id: 1, label: "Architecture, Design & Threat Modeling" },
  { id: 2, label: "Authentication" },
  { id: 3, label: "Session Management" },
  { id: 4, label: "Access Control" },
  { id: 5, label: "Malicious Input Handling" },
  { id: 7, label: "Cryptography at Rest" },
  { id: 8, label: "Error Handling & Logging" },
  { id: 9, label: "Data Protection" },
  { id: 10, label: "Communications" },
  { id: 11, label: "HTTP Security Configuration" },
  { id: 13, label: "Malicious Controls" },
  { id: 15, label: "Business Logic" },
  { id: 16, label: "Files & Resources" },
  { id: 17, label: "Mobile" },
  { id: 18, label: "Web Services" },
  { id: 19, label: "Configuration" },
];

export function Navbar() {
  const { data: session } = useSession();
  const { theme, toggle } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [levelsOpen, setLevelsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  const show2faNav = !session || session.user.is2faVerified;

  return (
    <nav className="fixed top-0 w-full z-50 bg-blue-900 text-white shadow-lg">
      <div className="container mx-auto px-4 flex items-center justify-between h-14">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 font-bold text-sm">
          <Image src="/img/logoicon.png" alt="OWASP Logo" width={30} height={30} />
          <span className="hidden sm:inline">OWASP ASVS 5.0</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-4">
          {show2faNav && (
            <>
              {/* Levels dropdown */}
              <div className="relative">
                <button
                  className="hover:text-red-300 flex items-center gap-1"
                  onClick={() => { setLevelsOpen(!levelsOpen); setHelpOpen(false); }}
                >
                  Levels <span className="text-xs">▾</span>
                </button>
                {levelsOpen && (
                  <div className="absolute top-full left-0 bg-white text-gray-800 rounded shadow-lg min-w-[120px] z-50">
                    {[1, 2, 3].map((l) => (
                      <Link
                        key={l}
                        href={`/levels/${l}`}
                        className="block px-4 py-2 hover:bg-gray-100"
                        onClick={() => setLevelsOpen(false)}
                      >
                        Level {l}
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              {/* Help dropdown */}
              <div className="relative">
                <button
                  className="hover:text-red-300 flex items-center gap-1"
                  onClick={() => { setHelpOpen(!helpOpen); setLevelsOpen(false); }}
                >
                  Help <span className="text-xs">▾</span>
                </button>
                {helpOpen && (
                  <div className="absolute top-full left-0 bg-white text-gray-800 rounded shadow-lg min-w-[280px] z-50 max-h-80 overflow-y-auto">
                    {HELP_CATEGORIES.map((c) => (
                      <Link
                        key={c.id}
                        href={`/help/${c.id}`}
                        className="block px-4 py-2 hover:bg-gray-100 text-sm"
                        onClick={() => setHelpOpen(false)}
                      >
                        {c.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              {session?.user.is2faVerified && (
                <Link href="/projects" className="hover:text-red-300">
                  Projects
                </Link>
              )}
            </>
          )}

          {/* Right side */}
          <div className="flex items-center gap-3 ml-4">
            {session ? (
              <>
                {!session.user.is2faVerified && (
                  <Link href="/2fa" className="hover:text-red-300 text-sm">
                    2FA Authenticate
                  </Link>
                )}
                <Link href="/profile" className="hover:text-red-300 text-sm">
                  Profile
                </Link>
                <button onClick={() => signOut({ callbackUrl: "/login" })} className="hover:text-red-300 text-sm">
                  Log Out
                </button>
              </>
            ) : (
              <Link href="/login" className="hover:text-red-300 text-sm">
                Log In
              </Link>
            )}
            <button onClick={toggle} className="text-lg" title="Toggle dark mode">
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
          </div>
        </div>

        {/* Mobile hamburger */}
        <button className="md:hidden text-xl" onClick={() => setMobileOpen(!mobileOpen)}>
          ☰
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-blue-900 border-t border-blue-800 px-4 pb-4">
          {show2faNav && (
            <>
              <div className="py-2 font-semibold">Levels</div>
              {[1, 2, 3].map((l) => (
                <Link key={l} href={`/levels/${l}`} className="block py-1 pl-4 hover:text-red-300" onClick={() => setMobileOpen(false)}>
                  Level {l}
                </Link>
              ))}
              <div className="py-2 font-semibold">Help</div>
              {HELP_CATEGORIES.map((c) => (
                <Link key={c.id} href={`/help/${c.id}`} className="block py-1 pl-4 text-sm hover:text-red-300" onClick={() => setMobileOpen(false)}>
                  {c.label}
                </Link>
              ))}
              {session?.user.is2faVerified && (
                <Link href="/projects" className="block py-2 hover:text-red-300" onClick={() => setMobileOpen(false)}>
                  Projects
                </Link>
              )}
            </>
          )}
          {session ? (
            <>
              <Link href="/profile" className="block py-2 hover:text-red-300" onClick={() => setMobileOpen(false)}>Profile</Link>
              <button onClick={() => signOut({ callbackUrl: "/login" })} className="block py-2 hover:text-red-300">Log Out</button>
            </>
          ) : (
            <Link href="/login" className="block py-2 hover:text-red-300" onClick={() => setMobileOpen(false)}>Log In</Link>
          )}
          <button onClick={toggle} className="py-2">
            {theme === "dark" ? "☀️ Light Mode" : "🌙 Dark Mode"}
          </button>
        </div>
      )}
    </nav>
  );
}
