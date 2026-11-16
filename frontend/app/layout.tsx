import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CRM RAH VZLA | Desarrollo local",
  description: "Panel inmobiliario de prueba — datos ficticios",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <header className="header">
          <div className="wrap header-inner">
            <a href="/" className="brand"><span className="brand-logo">R</span> CRM <span className="brand-muted">RAH VZLA</span></a>
            <span className="env-chip">ENTORNO LOCAL · DEMO</span>
          </div>
        </header>
        <main className="wrap main">{children}</main>
        <footer className="wrap footer">CRM RAH VZLA v0.2 · Solo datos ficticios · No publicar información real</footer>
      </body>
    </html>
  );
}
