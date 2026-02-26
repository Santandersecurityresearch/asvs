import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { readProjectFile, writeProjectFile } from "@/lib/asvs";

// PATCH /api/projects/:id/viewers - update allowed viewers
export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions);
  if (!session?.user.is2faVerified) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const projectId = parseInt(params.id);
  const project = await prisma.project.findUnique({ where: { id: projectId } });
  if (!project) return NextResponse.json({ error: "Not found" }, { status: 404 });

  if (project.projectOwner !== session.user.username) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { viewers } = await request.json();
  await prisma.project.update({
    where: { id: projectId },
    data: { projectAllowedViewers: viewers },
  });

  // Update the JSON file too
  const data = readProjectFile(project.dataHash);
  data.project_allowed_viewers = viewers;
  writeProjectFile(project.dataHash, data);

  return NextResponse.json({ success: true });
}
