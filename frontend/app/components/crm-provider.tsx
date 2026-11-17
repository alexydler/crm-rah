"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError, createRealApi, USE_MOCKS, type ApiClient, type Organizacion, type UsuarioActual } from "../lib/api";
import { createMockApi } from "../lib/mock-api";
import { ErrorScreen } from "./error-screen";

interface CrmContext {
  api: ApiClient;
  usuario: UsuarioActual;
  organizaciones: Organizacion[];
  organizacion: Organizacion;
  selectOrganizacion(id: string): void;
  reportError(error: unknown): void;
}
const Context = createContext<CrmContext | null>(null);
export function useCrm() {
  const value = useContext(Context);
  if (!value) throw new Error("La pantalla requiere una sesión y una organización");
  return value;
}
export function CrmProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [api] = useState(() => USE_MOCKS ? createMockApi() : createRealApi());
  const [identity, setIdentity] = useState<{ usuario: UsuarioActual; organizaciones: Organizacion[] } | null>(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [attempt, setAttempt] = useState(0);
  const [validating, setValidating] = useState(true);
  const login = pathname === "/login";

  function reportError(cause: unknown) {
    if (cause instanceof ApiError && cause.status === 401) {
      setIdentity(null);
      setSelected("");
      try { if (identity) sessionStorage.removeItem(`crm:organizacion:${USE_MOCKS ? "mock" : "real"}:${identity.usuario.sub}`); } catch {}
      router.replace("/login?motivo=sesion");
    }
  }
  useEffect(() => {
    if (login) return;
    const controller = new AbortController();
    setValidating(true);
    setError(null);
    Promise.all([api.getMe(controller.signal), api.getOrganizaciones(controller.signal)]).then(([usuario, items]) => {
      if (controller.signal.aborted) return;
      const organizaciones = usuario.organizaciones.filter(org => items.some(item => item.id === org.id));
      if (!organizaciones.length) throw new ApiError(403);
      const key = `crm:organizacion:${USE_MOCKS ? "mock" : "real"}:${usuario.sub}`;
      let saved = "";
      try { saved = sessionStorage.getItem(key) || ""; } catch {}
      const org = organizaciones.find(o => o.id === saved) || organizaciones[0];
      try { sessionStorage.setItem(key, org.id); } catch {}
      setSelected(org.id);
      setIdentity({ usuario, organizaciones });
    }).catch(cause => {
      if (controller.signal.aborted) return;
      setError(cause);
      if (cause instanceof ApiError && [401, 403].includes(cause.status)) { setIdentity(null); setSelected(""); }
      if (cause instanceof ApiError && cause.status === 401) router.replace("/login?motivo=sesion");
    }).finally(() => { if (!controller.signal.aborted) setValidating(false); });
    return () => controller.abort();
  }, [api, login, attempt, router]);
  useEffect(() => {
    const refresh = () => setAttempt(v => v + 1);
    window.addEventListener("focus", refresh);
    return () => window.removeEventListener("focus", refresh);
  }, []);
  useEffect(() => () => api.dispose(), [api]);

  if (login) return <>{children}</>;
  if (error) return <main className="wrap main"><ErrorScreen error={error} retry={() => setAttempt(v => v + 1)} /></main>;
  if (!identity) return <main className="wrap main"><p role="status">Comprobando sesión y membresías…</p></main>;
  const org = identity.organizaciones.find(item => item.id === selected);
  if (!org) return <main className="wrap main"><ErrorScreen error={new ApiError(403)} /></main>;
  const context: CrmContext = {
    api, ...identity, organizacion: org, reportError,
    selectOrganizacion(id) {
      if (!identity.organizaciones.some(o => o.id === id)) return;
      api.clearOrganization(selected);
      try { sessionStorage.setItem(`crm:organizacion:${USE_MOCKS ? "mock" : "real"}:${identity.usuario.sub}`, id); } catch {}
      setSelected(id);
      router.replace("/");
    },
  };
  // Remontar todo el ámbito descarta fichas, formularios y peticiones de la otra agencia.
  return <Context.Provider value={context}>
    {validating && <p className="wrap" role="status">Comprobando sesión y membresías…</p>}
    <div hidden={validating} inert={validating}><OrganizationFrame key={`${identity.usuario.sub}:${org.id}:${org.rol}`}>{children}</OrganizationFrame></div>
  </Context.Provider>;
}

function OrganizationFrame({ children }: { children: ReactNode }) {
  const { api, organizacion, organizaciones, selectOrganizacion, reportError } = useCrm();
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setReady(false); setError(null);
    api.getOrganizacion(organizacion.id, controller.signal).then(() => {
      if (!controller.signal.aborted) setReady(true);
    }).catch(cause => { if (!controller.signal.aborted) { setError(cause); reportError(cause); } });
    return () => { controller.abort(); api.clearOrganization(organizacion.id); };
  }, [api, organizacion.id, attempt]);
  return <div>
    <header className="header"><div className="wrap header-inner">
      <Link href="/" className="brand"><span className="brand-logo" aria-hidden="true">R</span><span>{organizacion.nombre_comercial}</span></Link>
      <div className="session-controls">
        {organizaciones.length > 1 && <label className="field">Inmobiliaria<select value={organizacion.id} onChange={e => selectOrganizacion(e.target.value)}>{organizaciones.map(org => <option key={org.id} value={org.id}>{org.nombre_comercial}</option>)}</select></label>}
        <span className="env-chip">{USE_MOCKS ? "DEMO · MOCK" : "DEMO · API V2"}</span>
        <span className="status" aria-label={`Rol en esta inmobiliaria: ${organizacion.rol}`}>{organizacion.rol}</span>
        {!USE_MOCKS && <form action="/auth/logout" method="post"><button className="button" type="submit">Cerrar sesión local</button></form>}
      </div>
    </div></header>
    <main className="wrap main">
      <p className="warning">{USE_MOCKS ? "Simulación local: sesión y dos inmobiliarias ficticias. No acredita seguridad multitenant." : "Integración v2 en pruebas: utiliza solo datos y fotografías ficticios."}</p>
      {error ? <ErrorScreen error={error} retry={() => setAttempt(v => v + 1)} /> : !ready ? <p role="status">Cargando inmobiliaria…</p> : children}
    </main>
    <footer className="wrap footer">CRM RAH VZLA · DEMO · Sin afiliación oficial a Rent-A-House · USD/VES sin conversión automática</footer>
  </div>;
}
