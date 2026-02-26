import { NextResponse } from "next/server";
import { loadRequirementsByLevel } from "@/lib/asvs";

export async function GET(request: Request, { params }: { params: { level: string } }) {
  const level = parseInt(params.level);
  if (![1, 2, 3].includes(level)) {
    return NextResponse.json({ error: "Invalid level" }, { status: 400 });
  }
  const requirements = loadRequirementsByLevel(level);
  return NextResponse.json(requirements);
}
