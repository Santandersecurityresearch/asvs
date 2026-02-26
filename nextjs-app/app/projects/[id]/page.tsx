"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { AsvsRequirement, ProjectData, CompletionStats } from "@/types";

interface Props {
  params: { id: string };
}

const CHAPTER_COLORS: Record<string, string> = {
  Architecture: "bg-orange-100 dark:bg-orange-900",
  Authentication: "bg-teal-100 dark:bg-teal-900",
  Session: "bg-blue-100 dark:bg-blue-900",
  Access: "bg-yellow-100 dark:bg-yellow-900",
  Validation: "bg-green-100 dark:bg-green-900",
  Cryptography: "bg-emerald-100 dark:bg-emerald-900",
  "Stored Cryptography": "bg-emerald-100 dark:bg-emerald-900",
  Error: "bg-red-100 dark:bg-red-900",
  Data: "bg-purple-100 dark:bg-purple-900",
  Communications: "bg-slate-200 dark:bg-slate-700",
  Malicious: "bg-lime-100 dark:bg-lime-900",
  "Business Logic": "bg-orange-200 dark:bg-orange-800",
  Files: "bg-cyan-100 dark:bg-cyan-900",
  API: "bg-green-200 dark:bg-green-800",
  Configuration: "bg-red-200 dark:bg-red-900",
  Encoding: "bg-indigo-100 dark:bg-indigo-900",
};

function getChapterColor(chapterName: string): string {
  for (const [key, cls] of Object.entries(CHAPTER_COLORS)) {
    if (chapterName.startsWith(key)) return cls;
  }
  return "bg-gray-100 dark:bg-gray-700";
}

export default function ProjectViewPage({ params }: Props) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [project, setProject] = useState<ProjectData | null>(null);
  const [requirements, setRequirements] = useState<AsvsRequirement[]>([]);
  const [completion, setCompletion] = useState<CompletionStats>({ total: 0, enabled: 0, percentage: "0.0" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [viewersModal, setViewersModal] = useState(false);
  const [viewers, setViewers] = useState("");

  const fetchProject = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`/api/projects/${params.id}`);
    if (!res.ok) { router.replace("/projects"); return; }
    const data: ProjectData = await res.json();
    setProject(data);
    setRequirements(data.requirements);
    setViewers(data.project_allowed_viewers);
    calculateCompletion(data.requirements);
    setLoading(false);
  }, [params.id, router]);

  useEffect(() => {
    if (status === "unauthenticated") { router.replace("/login"); return; }
    if (status === "authenticated" && !session.user.is2faVerified) { router.replace("/2fa"); return; }
    if (status === "authenticated") fetchProject();
  }, [status, session, router, fetchProject]);

  const calculateCompletion = (reqs: AsvsRequirement[]) => {
    const total = reqs.length;
    const enabled = reqs.filter((r) => r.enabled && r.enabled > 0).length;
    setCompletion({ total, enabled, percentage: total > 0 ? ((enabled / total) * 100).toFixed(1) : "0.0" });
  };

  const setStatus = (reqId: string, status: "enabled" | "disabled" | "na") => {
    setRequirements((prev) =>
      prev.map((r) => {
        if (r.req_id !== reqId) return r;
        return {
          ...r,
          enabled: status === "enabled" ? 1 : 0,
          disabled: status === "disabled" ? 1 : 0,
        };
      })
    );
  };

  const setNote = (reqId: string, note: string) => {
    setRequirements((prev) =>
      prev.map((r) => (r.req_id === reqId ? { ...r, note } : r))
    );
  };

  const handleSave = async () => {
    setSaving(true);
    await fetch(`/api/projects/${params.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ requirements }),
    });
    setSaving(false);
    calculateCompletion(requirements);
  };

  const handleUpdateViewers = async () => {
    await fetch(`/api/projects/${params.id}/viewers`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ viewers }),
    });
    setViewersModal(false);
  };

  const groupedByChapter = requirements.reduce<Record<string, AsvsRequirement[]>>((acc, r) => {
    if (!acc[r.chapter_id]) acc[r.chapter_id] = [];
    acc[r.chapter_id].push(r);
    return acc;
  }, {});

  if (loading) return <div className="container mx-auto px-4 py-8 text-center">Loading...</div>;
  if (!project) return null;

  const percentage = parseFloat(completion.percentage);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Project Header */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">{project.project_name}</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">{project.project_description}</p>
            <div className="flex gap-4 mt-2 text-xs text-gray-400">
              <span>Owner: {project.project_owner}</span>
              <span>Level {project.project_level}</span>
              <span>Created: {new Date(project.project_created).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={handleSave} disabled={saving} className="btn-primary text-sm">
              {saving ? "Saving..." : "Save"}
            </button>
            <a href={`/api/projects/${params.id}/download`} download className="btn-secondary text-sm">
              JSON
            </a>
            {project.project_owner === session?.user.username && (
              <button onClick={() => setViewersModal(true)} className="btn-secondary text-sm">
                Share
              </button>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Completion</span>
            <span>{completion.percentage}% ({completion.enabled}/{completion.total})</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-green-500 h-3 rounded-full transition-all"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Requirements */}
      <div className="space-y-6">
        {Object.entries(groupedByChapter).map(([chapterId, reqs]) => (
          <div key={chapterId} className="card">
            <h2 className={`text-base font-bold px-3 py-2 rounded mb-4 ${getChapterColor(reqs[0].chapter_name)}`}>
              {chapterId}: {reqs[0].chapter_name}
            </h2>
            <div className="space-y-4">
              {reqs.map((r) => {
                const status = r.enabled ? "enabled" : r.disabled ? "disabled" : "na";
                return (
                  <div key={r.req_id} className="border border-gray-100 dark:border-gray-700 rounded p-3">
                    <div className="flex gap-2 items-start mb-2">
                      <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded shrink-0">
                        {r.req_id}
                      </span>
                      <p className="text-sm">{r.req_description}</p>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {(["enabled", "disabled", "na"] as const).map((s) => (
                        <button
                          key={s}
                          onClick={() => setStatus(r.req_id, s)}
                          className={`text-xs px-3 py-1 rounded transition-colors ${
                            status === s
                              ? s === "enabled"
                                ? "bg-green-500 text-white"
                                : s === "disabled"
                                ? "bg-red-500 text-white"
                                : "bg-blue-500 text-white"
                              : "bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
                          }`}
                        >
                          {s === "enabled" ? "Complete" : s === "disabled" ? "Incomplete" : "N/A"}
                        </button>
                      ))}
                    </div>
                    <textarea
                      value={r.note ?? ""}
                      onChange={(e) => setNote(r.req_id, e.target.value)}
                      placeholder="Add a note..."
                      className="mt-2 w-full text-xs border border-gray-200 dark:border-gray-600 rounded px-2 py-1 bg-transparent resize-none focus:outline-none focus:ring-1 focus:ring-red-500"
                      rows={2}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Share Modal */}
      {viewersModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-3">Share Project</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
              Enter comma-separated usernames who can view this project.
            </p>
            <input
              type="text"
              value={viewers}
              onChange={(e) => setViewers(e.target.value)}
              className="input-field mb-4"
            />
            <div className="flex gap-3">
              <button onClick={handleUpdateViewers} className="btn-primary flex-1">Save</button>
              <button onClick={() => setViewersModal(false)} className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
