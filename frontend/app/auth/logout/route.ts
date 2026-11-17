import { NextRequest, NextResponse } from "next/server";
import { appOrigin, cookieOptions, deleteSession, SESSION_COOKIE, sameOrigin } from "../../lib/server/session";

export const runtime = "nodejs";
export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Origen no permitido" }, { status: 403 });
  deleteSession(request.cookies.get(SESSION_COOKIE)?.value);
  const response = NextResponse.redirect(new URL("/login", appOrigin()), 303);
  response.cookies.set(SESSION_COOKIE, "", cookieOptions(0));
  response.headers.set("Cache-Control", "no-store");
  return response;
}
