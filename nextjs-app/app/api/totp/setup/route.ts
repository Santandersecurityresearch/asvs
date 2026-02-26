import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { authenticator } from "otplib";
import QRCode from "qrcode";

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = parseInt(session.user.id);
  const { userAgent } = await request.json();

  // Generate a new TOTP secret
  const secret = authenticator.generateSecret();

  // Save the device (unconfirmed)
  await prisma.totpDevice.create({
    data: {
      userId,
      secret,
      name: userAgent ?? "unknown",
      confirmed: false,
    },
  });

  const user = await prisma.user.findUnique({ where: { id: userId } });
  const otpauth = authenticator.keyuri(user!.username, "OWASP ASVS v5", secret);
  const qrCode = await QRCode.toDataURL(otpauth);

  return NextResponse.json({ secret, qrCode });
}
