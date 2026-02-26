import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { readProjectFile, calculateCompletion } from "@/lib/asvs";
import { AsvsRequirement, ProjectData } from "@/types";

// NOTE: PDF is generated client-side using window.print() for now.
// For server-side PDF, install @react-pdf/renderer or pdfkit.
// This endpoint returns the project data for client-side rendering.
export async function GET(request: Request, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions);
  if (!session?.user.is2faVerified) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const projectId = parseInt(params.id);
  const project = await prisma.project.findUnique({ where: { id: projectId } });
  if (!project) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const allowed = project.projectAllowedViewers.split(",");
  if (
    project.projectOwner !== session.user.username &&
    !allowed.includes(session.user.username) &&
    !session.user.isAdmin
  ) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const data: ProjectData = readProjectFile(project.dataHash);
  const completion = calculateCompletion(data.requirements);

  // Build plain-text report content for HTML-based PDF rendering
  const lines: string[] = [];
  lines.push("PROJECT REPORT");
  lines.push("");
  lines.push(`Project Owner: ${data.project_owner}`);
  lines.push(`Project Name: ${data.project_name}`);
  lines.push(`Project ID: ${data.project_id}`);
  lines.push(`Description: ${data.project_description}`);
  lines.push(`Created: ${data.project_created}`);
  lines.push(`Level: ${data.project_level}`);
  lines.push("");
  lines.push(`COMPLETION: ${completion.percentage}% (${completion.enabled}/${completion.total})`);
  lines.push("");
  lines.push("REQUIREMENTS:");

  for (const r of data.requirements) {
    lines.push("");
    lines.push(`[${r.req_id}] ${r.chapter_name}`);
    lines.push(r.req_description);
    if (r.enabled && r.enabled > 0) {
      lines.push("Status: Complete");
    } else if (r.disabled && r.disabled > 0) {
      lines.push("Status: Incomplete");
    } else {
      lines.push("Status: N/A");
    }
    if (r.note) lines.push(`Note: ${r.note}`);
  }

  return NextResponse.json({ report: lines.join("\n"), data, completion });
}
