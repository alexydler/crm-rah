import { ApiError, canCreateInmueble, canEditInmueble, orgPath, writeInput, validatePhoto, type ApiClient, type InmuebleCreate, type Organizacion, type UsuarioActual } from "./api";
import type { Inmueble, MediaAsset } from "../types";

export const CARACAS = "11111111-1111-4111-8111-111111111111";
export const VALENCIA = "22222222-2222-4222-8222-222222222222";
export const DEMO_USER: UsuarioActual = {
  sub: "usuario-ab", email: "usuario-ab@demo.invalid", nombre: "Usuario AB DEMO",
  organizaciones: [
    { id: CARACAS, slug: "demo-caracas", nombre_comercial: "Inmobiliaria DEMO Caracas", rol: "gerente" },
    { id: VALENCIA, slug: "demo-valencia", nombre_comercial: "Inmobiliaria DEMO Valencia", rol: "asesor" },
  ],
};

export function createMockApi(user: UsuarioActual | null = structuredClone(DEMO_USER)): ApiClient {
  const organizaciones: Organizacion[] = structuredClone(DEMO_USER.organizaciones);
  const inmuebles: Inmueble[] = organizaciones.flatMap((org, i) => [{
    id: i ? "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1" : "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
    organizacion_id: org.id, titulo: `DEMO - Apartamento ficticio en ${i ? "Valencia" : "Caracas"}`,
    tipo: "apartamento", operacion: "venta", precio: i ? "3200000.00" : "85000.00", moneda: i ? "VES" : "USD",
    zona: `${i ? "Valencia" : "Caracas"} - ubicación ficticia`, estado_ve: i ? "Carabobo" : "Miranda",
    municipio: i ? "Valencia" : "Baruta", urbanizacion: "Sector DEMO", codigo_referencia: "DEMO-001",
    m2_construidos: "88.00", habitaciones: 3, banos: 2, estado: "borrador",
    descripcion: "Solo datos ficticios para probar el frontend. No es una oferta inmobiliaria.",
  }]);
  const media = new Map<string, { asset: Omit<MediaAsset, "url_temporal">; archivo: File }[]>();
  const urls = new Map<string, string>();
  function session(signal?: AbortSignal) {
    signal?.throwIfAborted();
    if (!user) throw new ApiError(401);
    return user;
  }
  function member(org: string, signal?: AbortSignal, action?: "create" | "edit") {
    const current = session(signal);
    orgPath(org);
    const membership = current.organizaciones.find(m => m.id === org);
    if (!membership || !organizaciones.some(o => o.id === org)) throw new ApiError(403);
    if ((action === "create" && !canCreateInmueble(membership.rol)) || (action === "edit" && !canEditInmueble(membership.rol))) throw new ApiError(403);
    return membership;
  }
  function property(org: string, id: string, signal?: AbortSignal, action?: "edit") {
    member(org, signal, action);
    const item = inmuebles.find(p => p.id === id && p.organizacion_id === org);
    if (!item) throw new ApiError(404);
    return item;
  }
  function validate(org: string, input: InmuebleCreate, id?: string) {
    if (!input.titulo?.trim() || input.titulo.trim().length < 3 || !input.zona?.trim() || typeof input.precio !== "string" || !/^\d{1,12}(\.\d{1,2})?$/.test(input.precio) || !["USD", "VES"].includes(input.moneda)) throw new ApiError(422);
    if ([input.m2_construidos, input.m2_parcela].some(value => value != null && (typeof value !== "string" || !/^\d+(\.\d+)?$/.test(value)))) throw new ApiError(422);
    if (input.codigo_referencia && inmuebles.some(p => p.organizacion_id === org && p.id !== id && p.codigo_referencia === input.codigo_referencia)) throw new ApiError(409);
  }
  function response(org: string, asset: Omit<MediaAsset, "url_temporal">, archivo: File): MediaAsset {
    const url = URL.createObjectURL(archivo);
    urls.set(url, org);
    return { ...structuredClone(asset), url_temporal: url };
  }
  function clearOrganization(org: string) {
    for (const [url, owner] of urls) if (owner === org) { URL.revokeObjectURL(url); urls.delete(url); }
  }
  return {
    async getMe(signal) { return structuredClone(session(signal)); },
    async getOrganizaciones(signal) {
      return structuredClone(session(signal).organizaciones);
    },
    async getOrganizacion(org, signal) { return structuredClone(member(org, signal)); },
    async getInmuebles(org, filtros = {}, signal) {
      member(org, signal);
      return structuredClone(inmuebles.filter(p => p.organizacion_id === org && (!filtros.tipo || p.tipo === filtros.tipo) && (!filtros.estado || p.estado === filtros.estado)));
    },
    async createInmueble(org, input, signal) {
      member(org, signal, "create");
      writeInput(input);
      validate(org, input);
      const item: Inmueble = { ...input, id: crypto.randomUUID(), organizacion_id: org };
      inmuebles.unshift(item);
      return structuredClone(item);
    },
    async getInmueble(org, id, signal) { return structuredClone(property(org, id, signal)); },
    async updateInmueble(org, id, input, signal) {
      const item = property(org, id, signal, "edit");
      const updated = { ...item, ...writeInput(input) };
      validate(org, updated, id);
      Object.assign(item, updated);
      return structuredClone(item);
    },
    async getMedia(org, id, signal) {
      property(org, id, signal);
      clearOrganization(org);
      return (media.get(id) || []).map(({ asset, archivo }) => response(org, asset, archivo));
    },
    async uploadMedia(org, id, archivo, etiqueta, signal) {
      property(org, id, signal, "edit");
      validatePhoto(archivo);
      const asset: Omit<MediaAsset, "url_temporal"> = { id: crypto.randomUUID(), inmueble_id: id, tipo: "foto", etiqueta_estancia: etiqueta || null,
        orden: media.get(id)?.length || 0, content_type: archivo.type };
      media.set(id, [...media.get(id) || [], { asset, archivo }]);
      return response(org, asset, archivo);
    },
    clearOrganization,
    dispose() { for (const url of urls.keys()) URL.revokeObjectURL(url); urls.clear(); },
  };
}
