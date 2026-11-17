import { NextRequest, NextResponse } from "next/server";
import { allowedV2Path, USE_MOCKS } from "../../../lib/api";
import { deleteSession, getSession, sameOrigin, SESSION_COOKIE } from "../../../lib/server/session";

export const runtime = "nodejs";
const jsonError = (status: number) => NextResponse.json({ detail: "No se pudo completar la solicitud" }, { status, headers: { "Cache-Control": "no-store" } });

async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  if (!allowedV2Path(path, request.method)) return jsonError(404);
  // El mock vive solo en el cliente. Nunca autentica solicitudes contra FastAPI.
  if (USE_MOCKS) return jsonError(503);
  const sessionId = request.cookies.get(SESSION_COOKIE)?.value;
  const session = getSession(sessionId);
  if (!session) return jsonError(401);
  if (request.method !== "GET" && !sameOrigin(request)) return jsonError(403);
  try {
    const base = new URL(process.env.API_BASE_URL || "http://localhost:8000");
    if (!["http:", "https:"].includes(base.protocol) || base.username || base.password || base.pathname !== "/" || base.search || base.hash) return jsonError(503);
    if (base.protocol === "http:" && !["localhost", "127.0.0.1", "[::1]", "backend"].includes(base.hostname)) return jsonError(503);
    const target = new URL(path, base);
    for (const [key, value] of request.nextUrl.searchParams) {
      if (!["tipo", "estado"].includes(key) || !path.endsWith("/inmuebles") || request.method !== "GET") return jsonError(422);
      target.searchParams.set(key, value);
    }
    const headers: Record<string, string> = { Accept: "application/json", Authorization: `Bearer ${session.accessToken}` };
    let body: Buffer | undefined;
    if (request.method !== "GET") {
      const contentType = request.headers.get("content-type") || "";
      const isMedia = path.endsWith("/media");
      if (isMedia ? !contentType.startsWith("multipart/form-data; boundary=") : !contentType.startsWith("application/json")) return jsonError(415);
      const limit = isMedia ? 13 * 1024 * 1024 : 128 * 1024;
      const reader = request.body?.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      if (reader) {
        while (true) {
          const part = await reader.read();
          if (part.done) break;
          size += part.value.length;
          if (size > limit) { await reader.cancel(); return jsonError(413); }
          chunks.push(part.value);
        }
      }
      body = Buffer.concat(chunks);
      headers["Content-Type"] = contentType;
    }
    const upstream = await fetch(target, { method: request.method, headers, body: body as BodyInit | undefined,
      cache: "no-store", redirect: "error", signal: AbortSignal.timeout(15000) });
    if (!upstream.ok) {
      const response = jsonError(upstream.status);
      if (upstream.status === 401) {
        deleteSession(sessionId);
        // No borrar la cookie: esta respuesta antigua podría llegar después de otro login.
      }
      return response;
    }
    return NextResponse.json(await upstream.json(), { status: upstream.status, headers: { "Cache-Control": "no-store" } });
  } catch { return jsonError(502); }
}
export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
