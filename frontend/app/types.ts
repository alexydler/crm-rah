export type Tipo = "apartamento" | "casa" | "quinta" | "townhouse" | "local" | "oficina" | "galpon" | "terreno";
export type Operacion = "venta" | "alquiler";
export type Estado = "borrador" | "disponible" | "reservado" | "cerrado";
export type Moneda = "USD" | "VES";
export interface Inmueble {
  id: string;
  organizacion_id: string;
  titulo: string;
  tipo: Tipo;
  operacion: Operacion;
  precio: string;
  moneda: Moneda;
  direccion?: string | null;
  zona: string;
  estado_ve?: string | null;
  municipio?: string | null;
  parroquia?: string | null;
  urbanizacion?: string | null;
  codigo_referencia?: string | null;
  m2_construidos?: string | null;
  m2_parcela?: string | null;
  habitaciones?: number | null;
  banos?: number | null;
  extras?: Record<string, unknown>;
  descripcion?: string;
  estado: Estado;
}
export interface MediaAsset {
  id: string;
  inmueble_id: string;
  tipo: string;
  etiqueta_estancia: string | null;
  orden: number;
  content_type: string;
  url_temporal: string;
}
export function formatMoney(value: string, currency: string): string {
  if (currency === "USD") return `USD ${new Intl.NumberFormat("es-VE", { maximumFractionDigits: 2 }).format(Number(value))}`;
  if (currency === "VES") return `VES ${new Intl.NumberFormat("es-VE", { maximumFractionDigits: 2 }).format(Number(value))}`;
  return `${currency} ${new Intl.NumberFormat("es-VE").format(Number(value))}`;
}
