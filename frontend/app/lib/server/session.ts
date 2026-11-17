import { randomBytes } from "node:crypto";

type Entry<T> = { value: T; expiresAt: number };
export interface LoginTransaction { verifier: string; state: string; nonce: string }
interface Session { accessToken: string }
const globalStore = globalThis as typeof globalThis & {
  crmSessions?: Map<string, Entry<Session>>;
  crmLogins?: Map<string, Entry<LoginTransaction>>;
};
// DEMO de un solo proceso: reemplazar por un almacén compartido antes de desplegar.
const sessions = globalStore.crmSessions ??= new Map();
const logins = globalStore.crmLogins ??= new Map();
export const SESSION_COOKIE = "crm_bff_session";
export const LOGIN_COOKIE = "crm_oidc_transaction";

function store<T>(map: Map<string, Entry<T>>, value: T, ttlSeconds: number) {
  const now = Date.now();
  for (const [key, entry] of map) if (entry.expiresAt <= now) map.delete(key);
  if (map.size >= 1000) throw new Error("Capacidad de sesiones alcanzada");
  const id = randomBytes(32).toString("base64url");
  map.set(id, { value, expiresAt: now + ttlSeconds * 1000 });
  return id;
}
export function startTransaction(value: LoginTransaction) { return store(logins, value, 300); }
export function consumeTransaction(id?: string): LoginTransaction | undefined {
  if (!id) return;
  const entry = logins.get(id);
  logins.delete(id);
  return entry && entry.expiresAt > Date.now() ? entry.value : undefined;
}
export function createSession(accessToken: string, ttlSeconds: number) {
  return store(sessions, { accessToken }, ttlSeconds);
}
export function getSession(id?: string): Session | undefined {
  if (!id) return;
  const entry = sessions.get(id);
  if (!entry || entry.expiresAt <= Date.now()) { sessions.delete(id); return; }
  return entry.value;
}
export function deleteSession(id?: string) { if (id) sessions.delete(id); }

export function appOrigin(): string {
  const url = new URL(process.env.APP_URL || "http://localhost:3000");
  if (url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("APP_URL no válida");
  if (url.protocol !== "https:" && !(url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname))) throw new Error("APP_URL requiere HTTPS");
  return url.origin;
}
export function cookieOptions(maxAge: number) {
  return { httpOnly: true, sameSite: "lax" as const, secure: appOrigin().startsWith("https:"), path: "/", maxAge };
}
export function sameOrigin(request: Request): boolean { return request.headers.get("origin") === appOrigin(); }
