"use client";

import Link from "next/link";
import { ApiError } from "../lib/api";

export function ErrorScreen({ error, retry }: { error: unknown; retry?: () => void }) {
  const status = error instanceof ApiError ? error.status : 0;
  const title = status === 403 ? "Acceso no permitido" : status === 404 ? "Recurso no disponible" : status === 401 ? "Sesión finalizada" : status === 503 ? "Proveedor de identidad no disponible" : "No pudimos completar la solicitud";
  return <section className="panel error-screen" role="alert">
    <p className="eyebrow">{status || "CONEXIÓN"}</p>
    <h1>{title}</h1>
    <p>{error instanceof ApiError ? error.message : "Revisa la conexión e inténtalo de nuevo."}</p>
    <div className="button-row">
      <Link href={status === 401 ? "/login" : "/"} className="button">{status === 401 ? "Ir a iniciar sesión" : "Volver a la cartera"}</Link>
      {retry && ![401, 403, 404].includes(status) && <button className="button primary" onClick={retry}>Reintentar</button>}
    </div>
  </section>;
}
