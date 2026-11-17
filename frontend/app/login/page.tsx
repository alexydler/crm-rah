import Link from "next/link";
import { USE_MOCKS } from "../lib/api";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string; motivo?: string }> }) {
  const params = await searchParams;
  const message = params.error === "configuracion" ? "Keycloak no está disponible o faltan variables OIDC. Revisa la configuración local e inténtalo de nuevo."
    : params.error === "autenticacion" ? "No se pudo verificar el inicio de sesión. Vuelve a intentarlo desde esta página."
    : params.motivo === "sesion" ? "Tu sesión terminó. Inicia sesión para continuar." : "";
  return <main className="wrap main login-main"><section className="panel login-panel">
    <p className="eyebrow">CRM INMOBILIARIO · VENEZUELA</p><h1>Accede a tu inmobiliaria</h1>
    <p className="subtitle">Carteras separadas por organización. Solo entorno local y datos DEMO.</p>
    {message && <p className="error" role="alert">{message}</p>}
    {USE_MOCKS ? <><p className="warning">Modo mock: la sesión se simula iniciada. No se contacta con Keycloak ni con FastAPI.</p><Link className="button primary" href="/">Entrar a la DEMO</Link></>
      : <><p>Usa tu cuenta del Keycloak local. El CRM no solicita ni guarda tu contraseña.</p><a className="button primary" href="/auth/login">Iniciar sesión con Keycloak</a></>}
  </section></main>;
}
