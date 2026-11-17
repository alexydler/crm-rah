import { test, expect } from "@playwright/test";

const caracas = "11111111-1111-4111-8111-111111111111";
const valencia = "22222222-2222-4222-8222-222222222222";
const selectionKey = "crm:organizacion:mock:usuario-ab";

test("cambia inmobiliaria, borra formulario/ficha anterior y persiste solo selección", async ({ page }) => {
  const apiCalls: string[] = [];
  page.on("request", request => { if (new URL(request.url()).pathname.startsWith("/api/v2/")) apiCalls.push(request.url()); });
  await page.goto("/");
  const selector = page.getByRole("combobox", { name: "Inmobiliaria", exact: true });
  await expect(selector).toHaveValue(caracas);
  await expect(page.getByText("DEMO - Apartamento ficticio en Caracas", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "+ Nuevo inmueble" }).click();
  await page.getByLabel("Título", { exact: true }).fill("Dato sin guardar de Caracas");
  await page.getByRole("combobox", { name: "Filtrar", exact: true }).selectOption("casa");
  await selector.selectOption(valencia);
  await expect(page.getByText("DEMO - Apartamento ficticio en Valencia", { exact: true })).toBeVisible();
  await expect(page.getByText("DEMO - Apartamento ficticio en Caracas", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Título", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("combobox", { name: "Filtrar", exact: true })).toHaveValue("todos");
  await page.reload();
  await expect(selector).toHaveValue(valencia);
  await page.getByRole("button", { name: "+ Nuevo inmueble" }).click();
  await expect(page.getByLabel("Título", { exact: true })).toHaveValue("");
  const stored = await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }));
  expect(stored.local).toEqual({});
  expect(stored.session).toEqual({ [selectionKey]: valencia });
  expect(apiCalls).toEqual([]);
});
test("cambio de agencia limpia galería, errores y URLs emitidas; asesor no sube fotos", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link").filter({ hasText: "DEMO - Apartamento ficticio en Caracas" }).click();
  await page.getByLabel("Subir fotografía ficticia").setInputFiles({ name: "DEMO.png", mimeType: "image/png", buffer: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==", "base64") });
  const image = page.getByRole("img", { name: "Fotografía DEMO del inmueble" });
  await expect(image).toBeVisible();
  const previousUrl = await image.getAttribute("src");
  await page.getByLabel("Subir fotografía ficticia").setInputFiles({ name: "DEMO.svg", mimeType: "image/svg+xml", buffer: Buffer.from("fixture") });
  await expect(page.getByRole("alert").filter({ hasText: "Solo se admiten fotografías" })).toBeVisible();
  const selector = page.getByRole("combobox", { name: "Inmobiliaria", exact: true });
  await selector.selectOption(valencia);
  await expect(page.getByRole("alert").filter({ hasText: "Solo se admiten fotografías" })).toHaveCount(0);
  await page.getByRole("link").filter({ hasText: "DEMO - Apartamento ficticio en Valencia" }).click();
  await expect(page.getByRole("heading", { name: "DEMO - Apartamento ficticio en Valencia" })).toBeVisible();
  await expect(page.getByRole("img")).toHaveCount(0);
  await expect(page.getByLabel("Subir fotografía ficticia")).toHaveCount(0);
  expect(await page.evaluate(async url => { try { await fetch(url!); return false; } catch { return true; } }, previousUrl)).toBe(true);
  await selector.selectOption(caracas);
  await page.getByRole("link").filter({ hasText: "DEMO - Apartamento ficticio en Caracas" }).click();
  await expect(image).toBeVisible();
  expect(await image.getAttribute("src")).not.toBe(previousUrl);
});
test("crea borrador DEMO y muestra precio con moneda explícita", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "+ Nuevo inmueble" }).click();
  await page.getByLabel("Título", { exact: true }).fill("Casa ficticia de prueba");
  await page.getByLabel("Precio", { exact: true }).fill("125000.50");
  await page.getByLabel("Zona", { exact: true }).fill("Caracas - sector ficticio");
  await page.getByLabel("Referencia interna", { exact: true }).fill("PRUEBA-001");
  await page.getByRole("button", { name: "Guardar inmueble", exact: true }).click();
  await page.getByRole("link").filter({ hasText: "DEMO - Casa ficticia de prueba" }).click();
  await expect(page.getByRole("heading", { name: "DEMO - Casa ficticia de prueba" })).toBeVisible();
  await expect(page.locator(".detail-price")).toContainText("USD");
  await expect(page.locator(".heading-row .status")).toHaveText("borrador");
  await expect(page.getByText("Superficie construida", { exact: true })).toHaveCount(0);
});
test("ficha ajena muestra 404 sin título, precio ni galería de Caracas", async ({ page }) => {
  await page.addInitScript(({ key, id }) => sessionStorage.setItem(key, id), { key: selectionKey, id: valencia });
  await page.goto("/inmuebles/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1");
  await expect(page.getByRole("heading", { name: "Recurso no disponible" })).toBeVisible();
  await expect(page.locator(".error-screen .eyebrow")).toHaveText("404");
  await expect(page.getByText("DEMO - Apartamento ficticio en Caracas", { exact: true })).toHaveCount(0);
  await expect(page.locator(".detail-price,.gallery")).toHaveCount(0);
});
test("galería acepta imagen ficticia, sin desbordamiento horizontal en móvil", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link").filter({ hasText: "DEMO - Apartamento ficticio en Caracas" }).click();
  await page.getByLabel("Subir fotografía ficticia").setInputFiles({
    name: "DEMO-pixel.png", mimeType: "image/png",
    buffer: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==", "base64"),
  });
  await expect(page.getByRole("img", { name: "Fotografía DEMO del inmueble" })).toBeVisible();
  await expect(page.getByRole("img")).toHaveAttribute("src", /^blob:/);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
});
test("filtro vacío y login explican claramente que es simulación", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("combobox", { name: "Filtrar", exact: true }).selectOption("terreno");
  await expect(page.getByText("No hay inmuebles para este filtro.")).toBeVisible();
  await page.goto("/login?motivo=sesion");
  await expect(page.getByRole("alert").filter({ hasText: "Tu sesión terminó" })).toBeVisible();
  await expect(page.getByText(/Modo mock: la sesión se simula iniciada/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Entrar a la DEMO" })).toBeVisible();
});
