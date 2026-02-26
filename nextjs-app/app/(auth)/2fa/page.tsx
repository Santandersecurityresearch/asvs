"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Image from "next/image";

type Step = "setup" | "verify";

export default function TwoFAPage() {
  const { data: session, update: updateSession } = useSession();
  const router = useRouter();
  const [step, setStep] = useState<Step>("setup");
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (session?.user.is2faVerified) {
      router.replace("/projects");
    }
  }, [session, router]);

  const handleSetup = async () => {
    setLoading(true);
    setError("");
    const res = await fetch("/api/totp/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userAgent: navigator.userAgent }),
    });
    setLoading(false);

    if (res.ok) {
      const data = await res.json();
      setQrCode(data.qrCode);
      setSecret(data.secret);
      setStep("verify");
    } else {
      setError("Failed to set up 2FA");
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const res = await fetch("/api/totp/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    setLoading(false);

    if (res.ok) {
      await updateSession({ is2faVerified: true });
      router.push("/projects");
    } else {
      setError("Invalid authentication code. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <Image src="/img/logoicon.png" alt="OWASP Logo" width={60} height={60} className="mx-auto mb-3" />
          <h1 className="text-2xl font-bold">Two-Factor Authentication</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
            Secure your account with 2FA
          </p>
        </div>

        <div className="card shadow-md">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-3 py-2 rounded text-sm mb-4">
              {error}
            </div>
          )}

          {step === "setup" && (
            <div className="text-center space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-300">
                You need to set up two-factor authentication to continue. Use an authenticator app
                like Google Authenticator or Authy.
              </p>
              <button onClick={handleSetup} disabled={loading} className="btn-primary w-full">
                {loading ? "Setting up..." : "Set Up 2FA"}
              </button>
            </div>
          )}

          {step === "verify" && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-300 text-center">
                Scan the QR code with your authenticator app, then enter the 6-digit code below.
              </p>

              {qrCode && (
                <div className="text-center">
                  <Image src={qrCode} alt="QR Code" width={200} height={200} className="mx-auto" />
                </div>
              )}

              {secret && (
                <div className="bg-gray-100 dark:bg-gray-700 rounded p-2 text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Or enter this secret manually:
                  </p>
                  <code className="text-sm font-mono break-all">{secret}</code>
                </div>
              )}

              <form onSubmit={handleVerify} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Authentication Code</label>
                  <input
                    type="text"
                    value={token}
                    onChange={(e) => setToken(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    className="input-field text-center text-2xl tracking-widest"
                    placeholder="000000"
                    maxLength={6}
                    required
                    autoFocus
                  />
                </div>
                <button type="submit" disabled={loading || token.length !== 6} className="btn-primary w-full">
                  {loading ? "Verifying..." : "Verify"}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
