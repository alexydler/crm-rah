import assert from "node:assert/strict";
import test from "node:test";
import { appOrigin, consumeTransaction, cookieOptions, createSession, deleteSession, getSession, sameOrigin, startTransaction } from "../app/lib/server/session";

test("transacción OIDC opaca de un solo uso, ligada al ID del navegador", () => {
  const input = { verifier: "verificador-ficticio", state: "estado-ficticio", nonce: "nonce-ficticio" };
  const id = startTransaction(input);
  assert.ok(!id.includes(input.verifier));
  assert.equal(consumeTransaction("otro-navegador"), undefined);
  assert.deepEqual(consumeTransaction(id), input);
  assert.equal(consumeTransaction(id), undefined);
});
test("transacción expirada y sesiones vencidas no se aceptan", t => {
  let now = 1000;
  t.mock.method(Date, "now", () => now);
  const login = startTransaction({ verifier: "demo", state: "demo", nonce: "demo" });
  const session = createSession("token-ficticio-no-real", 30);
  assert.equal(getSession(session)?.accessToken, "token-ficticio-no-real");
  now += 301000;
  assert.equal(consumeTransaction(login), undefined);
  assert.equal(getSession(session), undefined);
});
test("sesión revocable y cookie HttpOnly sin token en su identificador", () => {
  const session = createSession("token-ficticio-no-real", 30);
  assert.ok(!session.includes("token"));
  deleteSession(session); assert.equal(getSession(session), undefined);
  assert.deepEqual(cookieOptions(30), { httpOnly: true, sameSite: "lax", secure: false, path: "/", maxAge: 30 });
});
test("el origen canónico no se deriva de Host; mutaciones cross-origin se rechazan", () => {
  assert.equal(appOrigin(), "http://localhost:3000");
  assert.equal(sameOrigin(new Request("http://localhost:3000/auth/logout", { headers: { origin: "http://localhost:3000" } })), true);
  assert.equal(sameOrigin(new Request("http://localhost:3000/auth/logout", { headers: { origin: "https://ajeno.invalid" } })), false);
  assert.equal(sameOrigin(new Request("http://localhost:3000/auth/logout")), false);
});
