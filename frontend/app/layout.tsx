import type { Metadata } from "next";
import "./globals.css";
import { CrmProvider } from "./components/crm-provider";

export const metadata: Metadata = {
  title: "CRM RAH VZLA | Desarrollo local",
  description: "Panel inmobiliario de prueba — datos ficticios",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <CrmProvider>{children}</CrmProvider>
      </body>
    </html>
  );
}
