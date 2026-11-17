import assert from "node:assert/strict";
import { createHash, generateKeyPairSync, sign } from "node:crypto";
import { createServer } from "node:http";
import test from "node:test";
import * as oidc from "openid-client";
import { getOidcConfiguration } from "../app/lib/server/oidc";

test("OIDC local de prueba: PKCE S256, state, nonce y firma JWKS reales", async t => {
  const keys = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const otherKeys = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const jwk = { ...keys.publicKey.export({ format: "jwk" }), kid: "demo-key", use: "sig", alg: "RS256" };
  let issuer = "";
  let nonce = "";
  let challenge = "";
  let exchanges = 0;
  const server = createServer(async (req, res) => {
    res.setHeader("Content-Type", "application/json");
    if (req.url?.includes(".well-known")) {
      res.end(JSON.stringify({ issuer, authorization_endpoint: `${issuer}/authorize`, token_endpoint: `${issuer}/token`, jwks_uri: `${issuer}/jwks`, response_types_supported: ["code"], subject_types_supported: ["public"], id_token_signing_alg_values_supported: ["RS256"], token_endpoint_auth_methods_supported: ["none"], code_challenge_methods_supported: ["S256"] }));
    } else if (req.url?.endsWith("/jwks")) {
      res.end(JSON.stringify({ keys: [jwk] }));
    } else if (req.url?.endsWith("/token")) {
      exchanges++;
      const chunks: Buffer[] = [];
      for await (const chunk of req) chunks.push(Buffer.from(chunk));
      const body = new URLSearchParams(Buffer.concat(chunks).toString());
      if (createHash("sha256").update(body.get("code_verifier") || "").digest("base64url") !== challenge) {
        res.statusCode = 400; res.end(JSON.stringify({ error: "invalid_grant" })); return;
      }
      const now = Math.floor(Date.now() / 1000);
      const header = Buffer.from(JSON.stringify({ alg: "RS256", kid: "demo-key" })).toString("base64url");
      const payload = Buffer.from(JSON.stringify({ iss: issuer, aud: "crm-test", sub: "usuario-demo", iat: now, exp: now + 60, nonce })).toString("base64url");
      const unsigned = `${header}.${payload}`;
      const signature = sign("RSA-SHA256", Buffer.from(unsigned), body.get("code") === "bad-signature" ? otherKeys.privateKey : keys.privateKey).toString("base64url");
      res.end(JSON.stringify({ token_type: "Bearer", access_token: "DEMO-access-token-no-real", expires_in: 60, id_token: `${unsigned}.${signature}` }));
    } else { res.statusCode = 404; res.end("{}"); }
  });
  await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
  t.after(() => server.close());
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  issuer = `http://127.0.0.1:${address.port}/realms/demo`;
  const environment = { OIDC_ISSUER: issuer, OIDC_CLIENT_ID: "crm-test", OIDC_ALLOW_INSECURE_LOCALHOST: "true", APP_URL: "http://localhost:3000", OIDC_CLIENT_SECRET: undefined };
  const previous = Object.fromEntries(Object.keys(environment).map(key => [key, process.env[key]]));
  for (const [key, value] of Object.entries(environment)) {
    if (value === undefined) delete process.env[key]; else process.env[key] = value;
  }
  t.after(() => { for (const [key, value] of Object.entries(previous)) { if (value === undefined) delete process.env[key]; else process.env[key] = value; } });
  const config = await getOidcConfiguration();
  const verifier = oidc.randomPKCECodeVerifier();
  challenge = await oidc.calculatePKCECodeChallenge(verifier);
  const state = oidc.randomState(); nonce = oidc.randomNonce();
  const auth = oidc.buildAuthorizationUrl(config, { redirect_uri: "http://localhost:3000/auth/callback", response_type: "code", scope: "openid", code_challenge: challenge, code_challenge_method: "S256", state, nonce });
  assert.equal(auth.searchParams.get("code_challenge_method"), "S256");
  assert.equal(auth.searchParams.get("state"), state);
  const url = (code: string, callbackState = state) => new URL(`http://localhost:3000/auth/callback?code=${code}&state=${callbackState}`);
  const checks = { pkceCodeVerifier: verifier, expectedState: state, expectedNonce: nonce, idTokenExpected: true };
  const tokens = await oidc.authorizationCodeGrant(config, url("valid"), checks);
  assert.equal(tokens.claims()?.sub, "usuario-demo");
  assert.equal(exchanges, 1);
  await assert.rejects(oidc.authorizationCodeGrant(config, url("valid", "estado-ajeno"), checks));
  assert.equal(exchanges, 1, "state incorrecto se rechaza antes de enviar el verifier");
  await assert.rejects(oidc.authorizationCodeGrant(config, url("valid"), { ...checks, expectedNonce: "nonce-ajeno" }));
  await assert.rejects(oidc.authorizationCodeGrant(config, url("valid"), { ...checks, pkceCodeVerifier: "verifier-ajeno" }));
  await assert.rejects(oidc.authorizationCodeGrant(config, url("bad-signature"), checks));
});
