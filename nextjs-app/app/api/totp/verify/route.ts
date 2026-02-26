import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { authenticator } from "otplib";

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { token } = await request.json();
  const userId = parseInt(session.user.id);

  const devices = await prisma.totpDevice.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
  });

  if (devices.length === 0) {
    return NextResponse.json({ error: "No 2FA device found" }, { status: 400 });
  }

  for (const device of devices) {
    const isValid = authenticator.verify({ token, secret: device.secret });
    if (isValid) {
      await prisma.totpDevice.update({
        where: { id: device.id },
        data: { confirmed: true },
      });
      return NextResponse.json({ success: true });
    }
  }

  return NextResponse.json({ error: "Invalid token" }, { status: 400 });
}
