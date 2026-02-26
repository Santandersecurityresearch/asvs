import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { readProjectFile, writeProjectFile, deleteProjectFile } from "@/lib/asvs";
import { projectHash } from "@/lib/hash";

// GET /api/projects/:id
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

  const data = readProjectFile(project.dataHash);
  return NextResponse.json(data);
}

// PUT /api/projects/:id - update requirements
export async function PUT(request: Request, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions);
  if (!session?.user.is2faVerified) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const projectId = parseInt(params.id);
  const project = await prisma.project.findUnique({ where: { id: projectId } });
  if (!project) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const allowed = project.projectAllowedViewers.split(",");
  if (project.projectOwner !== session.user.username && !allowed.includes(session.user.username)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { requirements } = await request.json();
  const data = readProjectFile(project.dataHash);
  data.requirements = requirements;
  writeProjectFile(project.dataHash, data);

  return NextResponse.json({ success: true });
}

// DELETE /api/projects/:id
export async function DELETE(request: Request, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions);
  if (!session?.user.is2faVerified) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const projectId = parseInt(params.id);
  const project = await prisma.project.findUnique({ where: { id: projectId } });
  if (!project) return NextResponse.json({ error: "Not found" }, { status: 404 });

  if (project.projectOwner !== session.user.username && !session.user.isAdmin) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  deleteProjectFile(project.dataHash);
  await prisma.project.delete({ where: { id: projectId } });

  return NextResponse.json({ success: true });
}
