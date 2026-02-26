import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { loadRequirementsByLevel, writeProjectFile } from "@/lib/asvs";
import { projectHash } from "@/lib/hash";
import { ProjectData } from "@/types";

// GET /api/projects - list projects for the current user
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user.is2faVerified) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const projects = session.user.isAdmin
    ? await prisma.project.findMany({ orderBy: { projectCreatedAt: "desc" } })
    : await prisma.project.findMany({
        where: {
          OR: [
            { projectOwner: session.user.username },
            { projectAllowedViewers: { contains: session.user.username } },
          ],
        },
        orderBy: { projectCreatedAt: "desc" },
      });

  // Filter strictly (SQLite case-insensitive workaround)
  const filtered = session.user.isAdmin
    ? projects
    : projects.filter(
        (p) =>
          p.projectOwner === session.user.username ||
          p.projectAllowedViewers.split(",").includes(session.user.username)
      );

  return NextResponse.json(filtered);
}

// POST /api/projects - create a new project
export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user.is2faVerified) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { projectName, projectDescription, projectLevel } = await request.json();
  const level = parseInt(projectLevel);

  const project = await prisma.project.create({
    data: {
      projectName,
      projectOwner: session.user.username,
      projectDescription,
      projectLevel: level,
      projectAllowedViewers: session.user.username,
      dataHash: "temp",
    },
  });

  const hash = projectHash(projectName, project.id);

  await prisma.project.update({
    where: { id: project.id },
    data: { dataHash: hash },
  });

  const requirements = loadRequirementsByLevel(level);
  const data: ProjectData = {
    project_owner: session.user.username,
    project_name: projectName,
    project_id: project.id,
    project_description: projectDescription,
    project_created: project.projectCreatedAt.toISOString(),
    project_level: level,
    project_allowed_viewers: session.user.username,
    requirements,
  };

  writeProjectFile(hash, data);

  return NextResponse.json({ id: project.id }, { status: 201 });
}
