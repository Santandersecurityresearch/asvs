"use client";

import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ProfilePage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/login");
  }, [status, router]);

  if (!session) return null;

  return (
    <div className="container mx-auto px-4 py-8 max-w-md">
      <div className="card shadow-md">
        <h1 className="text-2xl font-bold mb-6">Profile</h1>

        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b dark:border-gray-700">
            <span className="text-sm text-gray-500 dark:text-gray-400">Username</span>
            <span className="font-medium">{session.user.username}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b dark:border-gray-700">
            <span className="text-sm text-gray-500 dark:text-gray-400">Email</span>
            <span className="font-medium">{session.user.email}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b dark:border-gray-700">
            <span className="text-sm text-gray-500 dark:text-gray-400">2FA Status</span>
            <span className={`text-sm font-medium px-2 py-0.5 rounded ${
              session.user.is2faVerified
                ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
            }`}>
              {session.user.is2faVerified ? "Verified" : "Not Verified"}
            </span>
          </div>
          {session.user.isAdmin && (
            <div className="flex justify-between items-center py-2 border-b dark:border-gray-700">
              <span className="text-sm text-gray-500 dark:text-gray-400">Role</span>
              <span className="text-sm font-medium px-2 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">
                Admin
              </span>
            </div>
          )}
        </div>

        <div className="mt-6 space-y-2">
          {!session.user.is2faVerified && (
            <a href="/2fa" className="btn-primary block text-center w-full">
              Set Up 2FA
            </a>
          )}
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="btn-danger w-full"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
