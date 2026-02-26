import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { readProjectFile } from "@/lib/asvs";

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
  const json = JSON.stringify(data, null, 2);

  return new NextResponse(json, {
    headers: {
      "Content-Type": "application/json",
      "Content-Disposition": `attachment; filename="${project.dataHash}.json"`,
    },
  });
}
