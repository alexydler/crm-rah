import { NextRequest, NextResponse } from "next/server";
import * as oidc from "openid-client";
import { USE_MOCKS } from "../../lib/api";
import { callbackUrl, getOidcConfiguration } from "../../lib/server/oidc";
import { appOrigin, cookieOptions, LOGIN_COOKIE, startTransaction } from "../../lib/server/session";

export const runtime = "nodejs";
export async function GET(request: NextRequest) {
  if (USE_MOCKS) return NextResponse.redirect(new URL("/", appOrigin()));
  if (request.headers.get("sec-fetch-site") === "cross-site") return new NextResponse(null, { status: 403 });
  try {
    const config = await getOidcConfiguration();
    const verifier = oidc.randomPKCECodeVerifier();
    const state = oidc.randomState();
    const nonce = oidc.randomNonce();
    const url = oidc.buildAuthorizationUrl(config, {
      redirect_uri: callbackUrl().href, response_type: "code", scope: "openid profile email",
      code_challenge: await oidc.calculatePKCECodeChallenge(verifier), code_challenge_method: "S256", state, nonce,
    });
    const response = NextResponse.redirect(url);
    response.cookies.set(LOGIN_COOKIE, startTransaction({ verifier, state, nonce }), cookieOptions(300));
    response.headers.set("Cache-Control", "no-store");
    response.headers.set("Referrer-Policy", "no-referrer");
    return response;
  } catch {
    return NextResponse.redirect(new URL("/login?error=configuracion", appOrigin()));
  }
}
