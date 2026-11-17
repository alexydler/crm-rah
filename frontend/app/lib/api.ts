import type { Estado, Inmueble, MediaAsset, Tipo } from "../types";

export const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export const ROLES = ["propietario", "gerente", "asesor", "marketing", "consulta"] as const;
export type Rol = typeof ROLES[number];
export interface Organizacion { id: string; slug: string; nombre_comercial: string; rol: Rol }
export interface UsuarioActual { sub: string; email: string | null; nombre: string | null; organizaciones: Organizacion[] }
export const canCreateInmueble = (rol: Rol) => ["propietario", "gerente", "asesor"].includes(rol);
export const canEditInmueble = (rol: Rol) => ["propietario", "gerente"].includes(rol);
export type InmuebleCreate = Omit<Inmueble, "id" | "organizacion_id">;
export type InmuebleUpdate = Partial<InmuebleCreate>;
export interface Filtros { tipo?: Tipo; estado?: Estado }
export interface ApiClient {
  getMe(signal?: AbortSignal): Promise<UsuarioActual>;
  getOrganizaciones(signal?: AbortSignal): Promise<Organizacion[]>;
  getOrganizacion(org: string, signal?: AbortSignal): Promise<Organizacion>;
  getInmuebles(org: string, filtros?: Filtros, signal?: AbortSignal): Promise<Inmueble[]>;
  createInmueble(org: string, input: InmuebleCreate, signal?: AbortSignal): Promise<Inmueble>;
  getInmueble(org: string, id: string, signal?: AbortSignal): Promise<Inmueble>;
  updateInmueble(org: string, id: string, input: InmuebleUpdate, signal?: AbortSignal): Promise<Inmueble>;
  getMedia(org: string, id: string, signal?: AbortSignal): Promise<MediaAsset[]>;
  uploadMedia(org: string, id: string, archivo: File, etiqueta?: string, signal?: AbortSignal): Promise<MediaAsset>;
  clearOrganization(org: string): void;
  dispose(): void;
}

export class ApiError extends Error {
  constructor(public readonly status: number) {
    const messages: Record<number, string> = {
      0: "No se pudo conectar. Revisa la conexión e inténtalo de nuevo.",
      401: "Tu sesión terminó. Inicia sesión de nuevo.",
      403: "No tienes permiso para realizar esta acción en esta inmobiliaria.",
      404: "El recurso no existe o no está disponible en esta inmobiliaria.",
      409: "La referencia interna ya existe en esta inmobiliaria.",
      413: "La fotografía supera el máximo de 12 MiB.",
      415: "Solo se admiten fotografías JPG, PNG o WEBP.",
      422: "Revisa los campos: hay datos incompletos o no válidos.",
      502: "La respuesta de la API no coincide con el contrato esperado.",
      503: "El proveedor de identidad no está disponible. Tu sesión no se ha cerrado. Inténtalo de nuevo.",
    };
    super(messages[status] || "No se pudo completar la operación. Inténtalo de nuevo.");
    this.name = "ApiError";
  }
}

export function orgPath(org: string): string {
  if (!UUID.test(org)) throw new ApiError(404);
  return `/api/v2/organizaciones/${org}`;
}
export function inmueblePath(org: string, id: string): string {
  if (!UUID.test(id)) throw new ApiError(404);
  return `${orgPath(org)}/inmuebles/${id}`;
}
export function writeInput<T extends object>(input: T): T {
  if (["id", "organizacion_id", "creado_por"].some(key => key in input)) throw new ApiError(422);
  const nonNullable = ["titulo", "tipo", "operacion", "precio", "moneda", "zona", "extras", "descripcion", "estado"];
  if (Object.entries(input).some(([key, value]) => nonNullable.includes(key) && value === null)) throw new ApiError(422);
  return Object.fromEntries(Object.entries(input).filter(([, value]) => value !== undefined)) as T;
}
export function validatePhoto(file: File): void {
  if (file.size > 12 * 1024 * 1024) throw new ApiError(413);
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) throw new ApiError(415);
}

export function allowedV2Path(path: string, method: string): boolean {
  if (method === "GET" && ["/api/v2/me", "/api/v2/me/organizaciones"].includes(path)) return true;
  const parts = path.split("/");
  if (parts.slice(0, 4).join("/") !== "/api/v2/organizaciones" || !UUID.test(parts[4] || "")) return false;
  if (parts.length === 5) return method === "GET";
  if (parts[5] !== "inmuebles") return false;
  if (parts.length === 6) return ["GET", "POST"].includes(method);
  if (!UUID.test(parts[6] || "")) return false;
  if (parts.length === 7) return ["GET", "PATCH"].includes(method);
  return parts.length === 8 && parts[7] === "media" && ["GET", "POST"].includes(method);
}

export function createRealApi(transport: typeof fetch = fetch): ApiClient {
  async function request<T>(path: string, signal?: AbortSignal, init?: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await transport(path, { ...init, signal, cache: "no-store", credentials: "same-origin" });
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new ApiError(0);
    }
    if (!response.ok) throw new ApiError(response.status);
    try { return await response.json() as T; } catch { throw new ApiError(502); }
  }
  const body = (method: string, input: object): RequestInit => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(writeInput(input)) });
  function organization(item: Organizacion): Organizacion {
    if (!item || !UUID.test(item.id) || typeof item.slug !== "string" || typeof item.nombre_comercial !== "string" || !ROLES.includes(item.rol)) throw new ApiError(502);
    return item;
  }
  function property(item: Inmueble, org: string, id?: string): Inmueble {
    if (item?.organizacion_id !== org || (id && item.id !== id)) throw new ApiError(404);
    if (!UUID.test(item.id) || typeof item.precio !== "string" || !["USD", "VES"].includes(item.moneda) || [item.m2_construidos, item.m2_parcela].some(value => value != null && typeof value !== "string")) throw new ApiError(502);
    return item;
  }
  function asset(item: MediaAsset, id: string): MediaAsset {
    if (item?.inmueble_id !== id) throw new ApiError(404);
    return item;
  }
  return {
    async getMe(signal) {
      const me = await request<UsuarioActual>("/api/v2/me", signal);
      if (!me || typeof me.sub !== "string" || !me.sub || (me.email !== null && typeof me.email !== "string") || (me.nombre !== null && typeof me.nombre !== "string") || !Array.isArray(me.organizaciones)) throw new ApiError(502);
      me.organizaciones.forEach(organization);
      return me;
    },
    async getOrganizaciones(signal) {
      const orgs = await request<Organizacion[]>("/api/v2/me/organizaciones", signal);
      if (!Array.isArray(orgs)) throw new ApiError(502);
      return orgs.map(organization);
    },
    async getOrganizacion(org, signal) {
      const item = await request<Organizacion>(orgPath(org), signal);
      if (item?.id !== org) throw new ApiError(404);
      return organization(item);
    },
    async getInmuebles(org, filtros = {}, signal) {
      const query = new URLSearchParams();
      if (filtros.tipo) query.set("tipo", filtros.tipo);
      if (filtros.estado) query.set("estado", filtros.estado);
      const items = await request<Inmueble[]>(`${orgPath(org)}/inmuebles${query.size ? `?${query}` : ""}`, signal);
      if (!Array.isArray(items)) throw new ApiError(502);
      return items.map(item => property(item, org));
    },
    createInmueble: async (org, input, signal) => property(await request(`${orgPath(org)}/inmuebles`, signal, body("POST", input)), org),
    getInmueble: async (org, id, signal) => property(await request(inmueblePath(org, id), signal), org, id),
    updateInmueble: async (org, id, input, signal) => property(await request(inmueblePath(org, id), signal, body("PATCH", input)), org, id),
    async getMedia(org, id, signal) {
      const items = await request<MediaAsset[]>(`${inmueblePath(org, id)}/media`, signal);
      if (!Array.isArray(items)) throw new ApiError(502);
      return items.map(item => asset(item, id));
    },
    async uploadMedia(org, id, archivo, etiqueta, signal) {
      validatePhoto(archivo);
      const form = new FormData();
      form.append("archivo", archivo);
      if (etiqueta) form.append("etiqueta_estancia", etiqueta);
      return asset(await request(`${inmueblePath(org, id)}/media`, signal, { method: "POST", body: form }), id);
    },
    clearOrganization() {},
    dispose() {},
  };
}
