import assert from "node:assert/strict";
import test from "node:test";
import { ApiError, ROLES, allowedV2Path, createRealApi, type InmuebleCreate, type InmuebleUpdate } from "../app/lib/api";
import { CARACAS, VALENCIA, createMockApi, DEMO_USER } from "../app/lib/mock-api";

const input: InmuebleCreate = { titulo: "DEMO - Casa ficticia", tipo: "casa", operacion: "venta", precio: "125000.50", moneda: "USD", zona: "Zona ficticia de Venezuela", codigo_referencia: "REF-001", estado: "borrador" };
const rejectsStatus = (status: number) => (error: unknown) => error instanceof ApiError && error.status === status;

test("sesión mock dual y carteras separadas; respuestas no mutan el almacén", async () => {
  const api = createMockApi();
  assert.equal((await api.getMe()).organizaciones.length, 2);
  assert.equal((await api.getMe()).sub, "usuario-ab");
  assert.equal((await api.getOrganizaciones()).length, 2);
  const a = await api.getInmuebles(CARACAS);
  const b = await api.getInmuebles(VALENCIA);
  assert.ok(a.every(p => p.organizacion_id === CARACAS));
  assert.ok(b.every(p => p.organizacion_id === VALENCIA));
  assert.equal(a[0].moneda, "USD"); assert.equal(b[0].moneda, "VES");
  a[0].titulo = "Alterado";
  assert.match((await api.getInmuebles(CARACAS))[0].titulo, /^DEMO/);
});
test("referencia duplicada válida entre organizaciones y 409 dentro de la misma", async () => {
  const api = createMockApi();
  const a = await api.createInmueble(CARACAS, input);
  const b = await api.createInmueble(VALENCIA, input);
  assert.notEqual(a.id, b.id); assert.equal(a.precio, "125000.50");
  await assert.rejects(api.createInmueble(CARACAS, input), rejectsStatus(409));
});
test("inmueble y medios ajenos no se filtran; tampoco una subida", async () => {
  const user = structuredClone(DEMO_USER);
  user.organizaciones[1].rol = "gerente";
  const api = createMockApi(user);
  const [a] = await api.getInmuebles(CARACAS);
  await assert.rejects(api.getInmueble(VALENCIA, a.id), rejectsStatus(404));
  await assert.rejects(api.getMedia(VALENCIA, a.id), rejectsStatus(404));
  await assert.rejects(api.uploadMedia(VALENCIA, a.id, new File(["fixture"], "demo.png", { type: "image/png" })), rejectsStatus(404));
});
test("sin sesión 401; sin membresía 403; consulta escribe 403", async () => {
  await assert.rejects(createMockApi(null).getMe(), rejectsStatus(401));
  await assert.rejects(createMockApi(null).getInmuebles(CARACAS), rejectsStatus(401));
  const user = structuredClone(DEMO_USER);
  user.organizaciones = [{ ...user.organizaciones[0], rol: "consulta" }];
  const api = createMockApi(user);
  assert.equal((await api.getOrganizaciones()).length, 1);
  await assert.rejects(api.getInmuebles(VALENCIA), rejectsStatus(403));
  await assert.rejects(api.createInmueble(CARACAS, input), rejectsStatus(403));
});
test("membresía revocada no permite peticiones posteriores", async () => {
  const user = structuredClone(DEMO_USER);
  const api = createMockApi(user);
  await api.getInmuebles(CARACAS);
  user.organizaciones = user.organizaciones.filter(org => org.id !== CARACAS);
  await assert.rejects(api.getInmuebles(CARACAS), rejectsStatus(403));
});
test("mock rechaza campos de servidor con 422 y filtra tipos", async () => {
  const api = createMockApi();
  for (const key of ["id", "organizacion_id", "creado_por"]) {
    await assert.rejects(api.createInmueble(CARACAS, { ...input, [key]: VALENCIA } as InmuebleCreate), rejectsStatus(422));
  }
  assert.equal((await api.getInmuebles(CARACAS, { tipo: "terreno" })).length, 0);
});
test("subida mock privada, límite de tamaño/MIME y cancelación", async () => {
  const api = createMockApi();
  const [a] = await api.getInmuebles(CARACAS);
  const photo = await api.uploadMedia(CARACAS, a.id, new File(["fixture"], "demo.png", { type: "image/png" }));
  assert.equal((await api.getMedia(CARACAS, a.id))[0].id, photo.id);
  assert.match(photo.url_temporal, /^blob:/);
  await assert.rejects(api.uploadMedia(CARACAS, a.id, new File(["fixture"], "x.svg", { type: "image/svg+xml" })), rejectsStatus(415));
  await assert.rejects(api.uploadMedia(CARACAS, a.id, new File([new Uint8Array(12 * 1024 * 1024 + 1)], "large.png", { type: "image/png" })), rejectsStatus(413));
  const controller = new AbortController(); controller.abort();
  await assert.rejects(api.getInmuebles(CARACAS, {}, controller.signal), { name: "AbortError" });
  api.dispose();
});
test("cliente real usa exactamente rutas v2 sin campos del servidor ni headers inventados", async () => {
  const calls: { path: string; init?: RequestInit }[] = [];
  const item = { ...input, id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1", organizacion_id: CARACAS };
  const transport = (async (url, init) => {
    calls.push({ path: String(url), init });
    return Response.json(init?.method === "POST" ? item : [item]);
  }) as typeof fetch;
  const api = createRealApi(transport);
  await api.getInmuebles(CARACAS, { tipo: "casa", estado: "borrador" });
  await api.createInmueble(CARACAS, input);
  await assert.rejects(api.createInmueble(CARACAS, { ...input, organizacion_id: VALENCIA } as InmuebleCreate), rejectsStatus(422));
  assert.equal(calls.length, 2);
  assert.equal(calls[0].path, `/api/v2/organizaciones/${CARACAS}/inmuebles?tipo=casa&estado=borrador`);
  assert.equal(calls[0].init?.cache, "no-store");
  const payload = JSON.parse(String(calls[1].init?.body));
  assert.equal(payload.organizacion_id, undefined); assert.equal(payload.creado_por, undefined);
  assert.equal(payload.precio, "125000.50");
  assert.deepEqual(calls[1].init?.headers, { "Content-Type": "application/json" });
});
test("cliente real conserva 401/403/404/409/413/422/503 y rechaza respuesta de otra agencia", async () => {
  for (const status of [401, 403, 404, 409, 413, 422, 503]) {
    const api = createRealApi((async () => Response.json({ detail: "No mostrar detalle ajeno" }, { status })) as typeof fetch);
    await assert.rejects(api.getInmuebles(CARACAS), rejectsStatus(status));
  }
  const api = createRealApi((async () => Response.json([{ ...input, id: crypto.randomUUID(), organizacion_id: VALENCIA }])) as typeof fetch);
  await assert.rejects(api.getInmuebles(CARACAS), rejectsStatus(404));
});
test("allowlist BFF no permite rutas ficticias, v1, escalada o IDs inválidos", () => {
  for (const path of ["/api/v2/me", "/api/v2/me/organizaciones", `/api/v2/organizaciones/${CARACAS}`, `/api/v2/organizaciones/${CARACAS}/inmuebles`]) assert.equal(allowedV2Path(path, "GET"), true);
  for (const path of ["/api/v1/inmuebles", "/api/v2/render", "/api/v2/organizaciones", "/api/v2/me/token", "/api/v2/organizaciones/../inmuebles", `/api/v2/organizaciones/${CARACAS}/marca`, `/api/v2/organizaciones/${CARACAS}/miembros`, `/api/v2/organizaciones/${CARACAS}/inmuebles/falso`]) assert.equal(allowedV2Path(path, "GET"), false);
  assert.equal(allowedV2Path(`/api/v2/organizaciones/${CARACAS}/inmuebles`, "DELETE"), false);
  assert.equal(allowedV2Path(`/api/v2/organizaciones/${CARACAS}/membresias/${VALENCIA}`, "DELETE"), false);
});
for (const rol of ROLES) test(`permisos confirmados para ${rol}: alta separada de edición y fotos`, async () => {
  const user = structuredClone(DEMO_USER);
  user.organizaciones[0].rol = rol;
  const api = createMockApi(user);
  const [item] = await api.getInmuebles(CARACAS);
  if (["propietario", "gerente", "asesor"].includes(rol)) await api.createInmueble(CARACAS, input);
  else await assert.rejects(api.createInmueble(CARACAS, input), rejectsStatus(403));
  if (["propietario", "gerente"].includes(rol)) {
    await api.updateInmueble(CARACAS, item.id, { descripcion: "DEMO actualizada" });
    await api.uploadMedia(CARACAS, item.id, new File(["fixture"], "demo.png", { type: "image/png" }));
  } else {
    await assert.rejects(api.updateInmueble(CARACAS, item.id, { descripcion: "DEMO actualizada" }), rejectsStatus(403));
    await assert.rejects(api.uploadMedia(CARACAS, item.id, new File(["fixture"], "demo.png", { type: "image/png" })), rejectsStatus(403));
  }
  api.dispose();
});
test("PATCH rechaza null en campos obligatorios y conserva null opcionales", async () => {
  const mock = createMockApi();
  const [item] = await mock.getInmuebles(CARACAS);
  let calls = 0;
  const real = createRealApi((async () => { calls++; return Response.json(item); }) as typeof fetch);
  for (const key of ["titulo", "tipo", "operacion", "precio", "moneda", "zona", "extras", "descripcion", "estado"]) {
    const update = { [key]: null } as InmuebleUpdate;
    await assert.rejects(mock.updateInmueble(CARACAS, item.id, update), rejectsStatus(422));
    await assert.rejects(real.updateInmueble(CARACAS, item.id, update), rejectsStatus(422));
  }
  assert.equal(calls, 0);
  assert.equal((await mock.updateInmueble(CARACAS, item.id, { codigo_referencia: null })).codigo_referencia, null);
});
test("identidad confirmada acepta sub opaco y organizaciones con rol; no exige id ni membresias", async () => {
  const calls: string[] = [];
  const api = createRealApi((async url => {
    calls.push(String(url));
    return Response.json(String(url).endsWith("/me") ? DEMO_USER : DEMO_USER.organizaciones);
  }) as typeof fetch);
  assert.deepEqual(await api.getMe(), DEMO_USER);
  assert.deepEqual(await api.getOrganizaciones(), DEMO_USER.organizaciones);
  assert.deepEqual(calls, ["/api/v2/me", "/api/v2/me/organizaciones"]);
});
test("limpiar organización revoca URLs anteriores; la nueva lista emite URLs frescas", async () => {
  const api = createMockApi();
  const [item] = await api.getInmuebles(CARACAS);
  await api.uploadMedia(CARACAS, item.id, new File(["fixture"], "demo.png", { type: "image/png" }));
  const [photo] = await api.getMedia(CARACAS, item.id);
  assert.equal((await fetch(photo.url_temporal)).status, 200);
  api.clearOrganization(CARACAS);
  await assert.rejects(fetch(photo.url_temporal));
  const [fresh] = await api.getMedia(CARACAS, item.id);
  assert.equal(fresh.id, photo.id);
  assert.notEqual(fresh.url_temporal, photo.url_temporal);
  api.dispose();
});
test("no normaliza decimales numéricos del backend ni convierte monedas", async () => {
  for (const malformed of [{ precio: 12.5 }, { m2_construidos: 88 }, { moneda: "EUR" }]) {
    const api = createRealApi((async () => Response.json([{ ...input, id: crypto.randomUUID(), organizacion_id: CARACAS, ...malformed }])) as typeof fetch);
    await assert.rejects(api.getInmuebles(CARACAS), rejectsStatus(502));
  }
});
test("una ficha real no puede responder con otro ID dentro de la misma agencia", async () => {
  const api = createRealApi((async () => Response.json({ ...input, id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1", organizacion_id: CARACAS })) as typeof fetch);
  await assert.rejects(api.getInmueble(CARACAS, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"), rejectsStatus(404));
});
