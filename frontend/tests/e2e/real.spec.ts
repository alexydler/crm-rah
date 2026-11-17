import { test, expect, type Route } from "@playwright/test";
import type { Organizacion, Rol } from "../../app/lib/api";

const org = "11111111-1111-4111-8111-111111111111";
const otherOrg = "22222222-2222-4222-8222-222222222222";
const organizations: Organizacion[] = [
  { id: org, slug: "caracas", nombre_comercial: "Inmobiliaria DEMO Caracas", rol: "gerente" },
  { id: otherOrg, slug: "valencia", nombre_comercial: "Inmobiliaria DEMO Valencia", rol: "asesor" },
];
const property = {
  id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1", organizacion_id: org,
  titulo: "DEMO - Respuesta Caracas", tipo: "casa", operacion: "venta", precio: "100.00", moneda: "USD", zona: "Zona DEMO", estado: "borrador",
};

async function identity(route: Route, orgs = organizations, listed = orgs): Promise<boolean> {
  const path = new URL(route.request().url()).pathname;
  if (path === "/api/v2/me") await route.fulfill({ json: { sub: "usuario-ab", email: "usuario-ab@demo.invalid", nombre: "Usuario AB DEMO", organizaciones: orgs } });
  else if (path === "/api/v2/me/organizaciones") await route.fulfill({ json: listed });
  else {
    const current = orgs.find(item => path === `/api/v2/organizaciones/${item.id}`);
    if (!current) return false;
    await route.fulfill({ json: current });
  }
  return true;
}

test("sin sesión real: 401, redirección a login y ningún fallback DEMO", async ({ page, request }) => {
  const response = await request.get("/api/v2/me");
  expect(response.status()).toBe(401);
  expect(await response.text()).not.toContain("access_token");
  await page.goto("/");
  await expect(page).toHaveURL(/\/login\?motivo=sesion/);
  await expect(page.getByRole("link", { name: "Iniciar sesión con Keycloak" })).toBeVisible();
  await expect(page.getByText("DEMO - Apartamento ficticio en Caracas", { exact: true })).toHaveCount(0);
});
test("OIDC no configurado o callback sin transacción falla de forma cerrada", async ({ request }) => {
  const login = await request.get("/auth/login", { maxRedirects: 0 });
  expect(login.headers().location).toBe("http://localhost:3100/login?error=configuracion");
  const callback = await request.get("/auth/callback?code=DEMO-code&state=falso", { maxRedirects: 0 });
  expect(callback.headers().location).toBe("http://localhost:3100/login?error=autenticacion");
  expect(callback.headers()["set-cookie"] || "").not.toContain("crm_bff_session=");
  expect((await request.post("/auth/logout", { headers: { Origin: "https://ajeno.invalid" } })).status()).toBe(403);
  for (const path of ["/api/v2/render", "/api/v2/organizaciones", `/api/v2/organizaciones/${org}/marca`]) expect((await request.get(path)).status()).toBe(404);
  expect((await request.delete(`/api/v2/organizaciones/${org}/membresias/${otherOrg}`)).status()).toBe(405);
});
test("cliente real presenta 403 sin mostrar la cartera", async ({ page }) => {
  await page.route("**/api/v2/**", async route => {
    if (await identity(route)) return;
    expect(new URL(route.request().url()).pathname).toBe(`/api/v2/organizaciones/${org}/inmuebles`);
    await route.fulfill({ status: 403, json: { detail: "No autorizado" } });
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Acceso no permitido" })).toBeVisible();
  await expect(page.locator(".error-screen .eyebrow")).toHaveText("403");
  await expect(page.locator(".property-list,.stats")).toHaveCount(0);
});
test("respuesta tardía de Caracas no aparece después de cambiar a Valencia", async ({ page }) => {
  let release: (() => void) | undefined;
  const delayed = new Promise<void>(resolve => { release = resolve; });
  let caracasRequested = false;
  await page.route("**/api/v2/**", async route => {
    if (await identity(route)) return;
    const path = new URL(route.request().url()).pathname;
    const current = path.includes(otherOrg) ? otherOrg : org;
    expect(path).toBe(`/api/v2/organizaciones/${current}/inmuebles`);
    if (current === org) { caracasRequested = true; await delayed; }
    const json = [{ ...property, organizacion_id: current, titulo: `DEMO - Respuesta ${current === org ? "Caracas" : "Valencia"}` }];
    try { await route.fulfill({ json }); } catch { /* La petición anterior puede estar cancelada. */ }
  });
  await page.goto("/");
  await expect.poll(() => caracasRequested).toBe(true);
  await page.getByRole("combobox", { name: "Inmobiliaria", exact: true }).selectOption(otherOrg);
  await expect(page.getByText("DEMO - Respuesta Valencia", { exact: true })).toBeVisible();
  release!();
  await expect(page.getByText("DEMO - Respuesta Caracas", { exact: true })).toHaveCount(0);
  await expect(page.getByText("DEMO - Respuesta Valencia", { exact: true })).toBeVisible();
});
for (const rol of ["propietario", "gerente", "asesor", "marketing", "consulta"] as Rol[]) {
  test(`acciones visibles para ${rol} usan el rol de /me`, async ({ page }) => {
    const meOrgs = [{ ...organizations[0], rol }];
    await page.route("**/api/v2/**", async route => {
      // Un rol inflado en el listado no prevalece sobre /me.
      if (await identity(route, meOrgs, [{ ...meOrgs[0], rol: "propietario" }])) return;
      const path = new URL(route.request().url()).pathname;
      if (path === `/api/v2/organizaciones/${org}/inmuebles`) await route.fulfill({ json: [property] });
      else if (path === `/api/v2/organizaciones/${org}/inmuebles/${property.id}`) await route.fulfill({ json: property });
      else {
        expect(path).toBe(`/api/v2/organizaciones/${org}/inmuebles/${property.id}/media`);
        await route.fulfill({ json: [] });
      }
    });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Tu cartera inmobiliaria" })).toBeVisible();
    await expect(page.getByRole("button", { name: "+ Nuevo inmueble" })).toHaveCount(["propietario", "gerente", "asesor"].includes(rol) ? 1 : 0);
    await page.getByRole("link").filter({ hasText: property.titulo }).click();
    await expect(page.getByRole("heading", { name: property.titulo })).toBeVisible();
    await expect(page.getByLabel("Subir fotografía ficticia")).toHaveCount(["propietario", "gerente"].includes(rol) ? 1 : 0);
  });
}
test("503 conserva cookie y selección; reintentar recupera sin re-login", async ({ page, context }) => {
  await context.addCookies([{ name: "crm_bff_session", value: "DEMO-sesion-no-real", url: "http://localhost:3100", httpOnly: true, sameSite: "Lax" }]);
  let down = false;
  await page.route("**/api/v2/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (down && path === "/api/v2/me") { await route.fulfill({ status: 503, json: { detail: "IdP no disponible" } }); return; }
    if (await identity(route)) return;
    expect(path).toBe(`/api/v2/organizaciones/${org}/inmuebles`);
    await route.fulfill({ json: [property] });
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Tu cartera inmobiliaria" })).toBeVisible();
  const before = await page.evaluate(() => ({ ...sessionStorage }));
  down = true;
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByRole("heading", { name: "Proveedor de identidad no disponible" })).toBeVisible();
  await expect(page).toHaveURL("http://localhost:3100/");
  expect((await context.cookies()).find(cookie => cookie.name === "crm_bff_session")?.value).toBe("DEMO-sesion-no-real");
  expect(await page.evaluate(() => ({ ...sessionStorage }))).toEqual(before);
  down = false;
  await page.getByRole("button", { name: "Reintentar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Tu cartera inmobiliaria" })).toBeVisible();
});
test("404 de ficha no muestra datos del listado ni acciones privadas", async ({ page }) => {
  await page.route("**/api/v2/**", async route => {
    if (await identity(route)) return;
    await route.fulfill({ status: 404, json: { detail: "No disponible" } });
  });
  await page.goto(`/inmuebles/${property.id}`);
  await expect(page.getByRole("heading", { name: "Recurso no disponible" })).toBeVisible();
  await expect(page.locator(".detail-price,.gallery")).toHaveCount(0);
});
test("URLs temporales se renuevan antes de 900 s, reintentan un 503 y no se persisten", async ({ page }) => {
  await page.clock.install();
  let mediaCalls = 0;
  await page.route("**/api/v2/**", async route => {
    if (await identity(route)) return;
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/media")) {
      mediaCalls++;
      if (mediaCalls === 2) { await route.fulfill({ status: 503, json: { detail: "IdP no disponible" } }); return; }
      await route.fulfill({ json: [{ id: "dddddddd-dddd-4ddd-8ddd-ddddddddddd1", inmueble_id: property.id, tipo: "foto", etiqueta_estancia: "DEMO", orden: 0, content_type: "image/png", url_temporal: `http://localhost:3100/media-demo.png?firma=${mediaCalls}` }] });
    } else {
      expect(path).toBe(`/api/v2/organizaciones/${org}/inmuebles/${property.id}`);
      await route.fulfill({ json: property });
    }
  });
  await page.route("**/media-demo.png?*", route => route.fulfill({ contentType: "image/png", body: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==", "base64") }));
  await page.goto(`/inmuebles/${property.id}`);
  await expect.poll(() => mediaCalls).toBe(1);
  await expect(page.getByRole("img", { name: "DEMO", exact: true })).toHaveAttribute("src", /firma=1$/);
  await page.clock.fastForward(14 * 60 * 1000);
  await expect.poll(() => mediaCalls).toBe(2);
  await expect(page.getByRole("alert").filter({ hasText: "Tu sesión no se ha cerrado" })).toBeVisible();
  await page.clock.fastForward(15000);
  await expect.poll(() => mediaCalls).toBe(3);
  await expect(page.getByRole("img", { name: "DEMO", exact: true })).toHaveAttribute("src", /firma=3$/);
  await expect(page.getByRole("heading", { name: property.titulo })).toBeVisible();
  expect(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).not.toContain("firma=");
});
