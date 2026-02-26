"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ProjectRecord } from "@/types";

export default function ProjectsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ projectName: "", projectDescription: "", projectLevel: "1" });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
      return;
    }
    if (status === "authenticated" && !session.user.is2faVerified) {
      router.replace("/2fa");
      return;
    }
    if (status === "authenticated") {
      fetchProjects();
    }
  }, [status, session, router]);

  const fetchProjects = async () => {
    setLoading(true);
    const res = await fetch("/api/projects");
    if (res.ok) {
      const data = await res.json();
      setProjects(data);
    }
    setLoading(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    const res = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setCreating(false);
    if (res.ok) {
      setShowModal(false);
      setForm({ projectName: "", projectDescription: "", projectLevel: "1" });
      fetchProjects();
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this project?")) return;
    await fetch(`/api/projects/${id}`, { method: "DELETE" });
    fetchProjects();
  };

  if (loading) return <div className="container mx-auto px-4 py-8 text-center">Loading...</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          + New Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 mb-4">No projects yet.</p>
          <button onClick={() => setShowModal(true)} className="btn-primary">
            Create your first project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <div key={p.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <h2 className="font-bold text-lg">{p.projectName}</h2>
                <span className="text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 px-2 py-0.5 rounded-full">
                  L{p.projectLevel}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{p.projectDescription}</p>
              <p className="text-xs text-gray-400 mb-4">
                Owner: {p.projectOwner} &bull;{" "}
                {new Date(p.projectCreatedAt).toLocaleDateString()}
              </p>
              <div className="flex gap-2">
                <Link href={`/projects/${p.id}`} className="btn-primary text-sm py-1 px-3">
                  View
                </Link>
                <a
                  href={`/api/projects/${p.id}/download`}
                  className="btn-secondary text-sm py-1 px-3"
                  download
                >
                  JSON
                </a>
                {(p.projectOwner === session?.user.username || session?.user.isAdmin) && (
                  <button
                    onClick={() => handleDelete(p.id)}
                    className="btn-danger text-sm py-1 px-3 ml-auto"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Project Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">New Project</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Project Name</label>
                <input
                  type="text"
                  value={form.projectName}
                  onChange={(e) => setForm({ ...form, projectName: e.target.value })}
                  className="input-field"
                  required
                  maxLength={60}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={form.projectDescription}
                  onChange={(e) => setForm({ ...form, projectDescription: e.target.value })}
                  className="input-field"
                  rows={3}
                  required
                  maxLength={255}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">ASVS Level</label>
                <select
                  value={form.projectLevel}
                  onChange={(e) => setForm({ ...form, projectLevel: e.target.value })}
                  className="input-field"
                >
                  <option value="1">Level 1</option>
                  <option value="2">Level 2</option>
                  <option value="3">Level 3</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={creating} className="btn-primary flex-1">
                  {creating ? "Creating..." : "Create"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
