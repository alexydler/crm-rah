import { NextRequest, NextResponse } from "next/server";
import * as oidc from "openid-client";
import { USE_MOCKS } from "../../lib/api";
import { callbackUrl, getOidcConfiguration } from "../../lib/server/oidc";
import { appOrigin, consumeTransaction, cookieOptions, createSession, deleteSession, LOGIN_COOKIE, SESSION_COOKIE } from "../../lib/server/session";

export const runtime = "nodejs";
export async function GET(request: NextRequest) {
  let response: NextResponse;
  if (USE_MOCKS) return NextResponse.redirect(new URL("/", appOrigin()));
  const transaction = consumeTransaction(request.cookies.get(LOGIN_COOKIE)?.value);
  try {
    if (!transaction) throw new Error("Transacción inválida o expirada");
    const currentUrl = callbackUrl();
    currentUrl.search = request.nextUrl.search;
    const tokens = await oidc.authorizationCodeGrant(await getOidcConfiguration(), currentUrl, {
      pkceCodeVerifier: transaction.verifier, expectedState: transaction.state, expectedNonce: transaction.nonce, idTokenExpected: true,
    });
    if (!tokens.claims() || !tokens.access_token || !tokens.expires_in || tokens.expires_in <= 0) throw new Error("Respuesta OIDC incompleta");
    const ttl = Math.min(tokens.expires_in, 3600);
    deleteSession(request.cookies.get(SESSION_COOKIE)?.value);
    response = NextResponse.redirect(new URL("/", appOrigin()));
    response.cookies.set(SESSION_COOKIE, createSession(tokens.access_token, ttl), cookieOptions(ttl));
  } catch {
    response = NextResponse.redirect(new URL("/login?error=autenticacion", appOrigin()));
  }
  response.cookies.set(LOGIN_COOKIE, "", cookieOptions(0));
  response.headers.set("Cache-Control", "no-store");
  response.headers.set("Referrer-Policy", "no-referrer");
  return response;
}
