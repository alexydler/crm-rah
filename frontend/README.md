# Frontend Sprint 02

Trabajo en `sprint02-frontend`, worktree `crm-rah-vzla-frontend`. Todos los cambios de esta entrega pertenecen a `frontend/`. No implementa ni modifica FastAPI, Keycloak, PostgreSQL, RLS, MinIO o Compose. No utilizar datos reales ni desplegar como SaaS seguro hasta integrar y ejecutar la matriz A/B del Sprint 02.

## Arranque DEMO

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm run dev
```

Abrir `http://localhost:3000`. Sin variables, `NEXT_PUBLIC_USE_MOCKS` se considera `true`: sesión simulada, dos membresías de gerente, inmobiliarias ficticias Caracas y Valencia, USD/VES sin conversión. No se contacta con FastAPI ni Keycloak. Cada recarga reinicia inmuebles y fotos mock; solo la organización seleccionada se conserva en `sessionStorage`, separada por usuario y modo.

Los scripts dev/start escuchan en loopback. El Dockerfile mantiene el bind interno `0.0.0.0` requerido por un contenedor; el puerto del host sigue dependiendo de Compose, que esta entrega no cambia.

## Cliente intercambiable

- `app/lib/api.ts`: tipos, errores HTTP, rutas permitidas y `createRealApi`.
- `app/lib/mock-api.ts`: `createMockApi` implementa la misma interfaz con datos DEMO en memoria. Valida pertenencia, rol, referencia por agencia y recurso al simular operaciones; no es autorización del producto real.
- `app/components/crm-provider.tsx`: sesión, membresías, selección, branding y ámbito por usuario/organización/rol. Al cambiar agencia se desmontan fichas/formularios y se abortan solicitudes. La revalidación por foco oculta y bloquea temporalmente el ámbito sin perder sus formularios; un cambio de identidad o rol lo reinicia.
- Las lecturas de páginas tienen generación para impedir que una respuesta anterior sobrescriba la última. El adaptador real también comprueba organización e ID de las fichas y pertenencia de medios antes de mostrarlos.

Funciones disponibles: identidad y organizaciones, consulta y actualización de marca, lista/alta/lectura/actualización de inmuebles y lista/subida de medios. Solo se utilizan rutas documentadas de `/api/v2/me`, `/api/v2/me/organizaciones` y `/api/v2/organizaciones/{org_id}/...`. Invitaciones quedan fuera del primer corte, como indica el contrato. La UI crea borradores y no permite cambios críticos de estado.

La organización siempre está en la URL; no existe `X-Organization-ID` ni autorización derivada de `sessionStorage`. `id`, `organizacion_id` y `creado_por` se eliminan de payloads ordinarios. El backend debe validar identidad/membresía/rol y recurso en cada petición, incluso si el frontend ya lo comprobó.

## Configuración real y OIDC

Variables documentadas en `.env.example`; configurar valores locales en un archivo no versionado:

| Variable | Ámbito / uso |
| --- | --- |
| `NEXT_PUBLIC_USE_MOCKS=false` | Selección de adaptador, fijada durante build; no hay fallback automático a mock |
| `APP_URL` | Origen canónico del navegador, por defecto `http://localhost:3000`; no se deriva de Host/X-Forwarded-Host |
| `API_BASE_URL` | Solo servidor, por defecto `http://localhost:8000`; en Docker puede ser `http://backend:8000` |
| `OIDC_ISSUER` | Issuer del realm Keycloak, no URL directa de `.well-known` |
| `OIDC_CLIENT_ID` | ID del cliente registrado en Keycloak |
| `OIDC_CLIENT_SECRET` | Opcional, solo servidor para cliente confidencial, nunca `NEXT_PUBLIC_*` ni Git |
| `OIDC_ALLOW_INSECURE_LOCALHOST=true` | Excepción explícita HTTP solo con issuer y aplicación en loopback; no sustituye HTTPS |

Registrar en Keycloak Standard Flow / Authorization Code, PKCE S256 y redirect URI exacto `${APP_URL}/auth/callback`. Para cliente público usar autenticación `none`; para confidencial se usa `client_secret_basic`. Acordar con backend el audience del access token y configurar el mapper de Keycloak; no se inventan parámetros de audience ni cabeceras de identidad.

```bash
NEXT_PUBLIC_USE_MOCKS=false npm run build
npm run start
```

La variable pública requiere reconstrucción y reinicio. Las variables de servidor deben estar presentes al ejecutar Next.js. En contenedores hay que hacer alcanzable el mismo issuer canónico desde navegador y BFF; esta entrega no añade redes, aliases, realms ni secretos a Compose. HTTP OIDC solo admite localhost/127.0.0.1/::1, no un nombre Docker arbitrario; no desactivar esas comprobaciones para solventar networking.

### Rutas internas de Next.js

| Ruta | Función local del BFF, no endpoint nuevo de FastAPI |
| --- | --- |
| `/login` | Pantalla española de acceso, simulación o error |
| `GET /auth/login` | Discovery diferido y Authorization Code + PKCE S256, state y nonce aleatorios |
| `GET /auth/callback` | Consume una transacción de cinco minutos ligada a cookie; valida intercambio, issuer/audience, nonce y firma de ID token mediante JWKS con openid-client 6.9.0 |
| `POST /auth/logout` | Cierra la sesión local; exige Origin canónico. No cierra SSO global de Keycloak |
| `/api/v2/[...path]` | Proxy con allowlist de métodos y rutas del contrato; obtiene bearer del servidor, no del cliente |

El BFF guarda tokens únicamente en un almacén en memoria de servidor; el navegador recibe una cookie aleatoria HttpOnly/SameSite=Lax, Secure con HTTPS. La sesión vence al expirar el access token, con máximo de una hora; no se solicitan offline tokens ni se implementa refresh silencioso. Estado/nonce/verifier no se guardan en almacenamiento JavaScript del navegador. No se registran tokens ni respuestas sensibles en logs.

El almacén local está limitado a 1000 entradas por tipo y caducidad, sirve para un proceso DEMO y se pierde al reiniciar. No es adecuado para múltiples réplicas, serverless, persistencia ni revocación distribuida: acordar un almacén compartido antes de producción. Si se deshabilitan mocks con configuración ausente, no se simula autenticación: se muestra error.

El proxy conserva errores HTTP, no devuelve detalles privados del upstream y desactiva caché. Mutaciones y logout comprueban Origin; hay límites de body y timeout. Un 401 upstream revoca solo la sesión capturada en servidor, sin un Set-Cookie tardío que pudiera borrar otro login. Un 401 del cliente limpia el ámbito y redirige a login; 403/404 muestran pantallas propias sin título, precio ni galería ajenos.

## Coordinación pendiente del contrato

El documento v2 fija endpoints, ejemplo de inmueble y marca, pero **no define los JSON completos de identidad ni organizaciones ni enum de estatus de membresía**. Esta entrega NO modifica ese contrato ni afirma que el backend ya devuelve estos DTO. El adaptador tipado usa la siguiente **propuesta provisional para el integrador**, basada en las entidades del ADR:

```ts
// GET /api/v2/me
type UsuarioActual = {
  id: string; // UUID interno, no el subject OIDC
  membresias: {
    organizacion_id: string;
    rol: "propietario" | "gerente" | "asesor" | "marketing" | "consulta";
    estatus: "activa"; // propuesta para la membresía habilitada
  }[];
};

// GET /api/v2/me/organizaciones -> Organizacion[]
// GET /api/v2/organizaciones/{org_id} -> Organizacion
type Organizacion = { id: string; nombre_comercial: string };
```

Confirmar también arrays directos frente a paginación, campos opcionales heredados v1 en inmueble v2 y la presencia de `inmueble_id` en MediaAsset. Si backend acuerda otra forma, adaptar y probar la decodificación en `app/lib/api.ts`, no añadir endpoints alternativos, omitir autorización o usar silenciosamente mocks. El adaptador falla de forma cerrada ante datos estructurales incompatibles.

La propiedad se marca DEMO al crearla. Fotografías mock usan object URLs locales, conservan bytes y se revocan al destruir el cliente; no prueban almacenamiento ni expiración S3. El backend real debe comprobar MIME real, tamaño, pertenencia y autorización antes de emitir URLs firmadas.

## Pruebas reproducibles

```bash
npm run typecheck
npm test
npm run build
npm run test:e2e
```

Playwright usa Chrome instalado (`channel: chrome`), sin descargar navegadores durante esta tarea. Inicia y detiene Next en `localhost:3100`; necesita ese puerto libre. Ejecuta cinco escenarios en escritorio y móvil: cambio de agencia y persistencia de selección, alta DEMO, ficha ajena 404, imagen sintética y layout sin overflow, filtro vacío/login. No hay fotos reales ni credenciales en fixtures.

Para probar el cliente real sin depender de agentes en paralelo:

```bash
NEXT_PUBLIC_USE_MOCKS=false npm run build
E2E_REAL=true npm run test:e2e
# Restaurar el artefacto DEMO predeterminado al terminar.
npm run build
```

La suite real comprueba contra el BFF real el 401 sin sesión, redirección a login, callback sin transacción, ausencia de fallback, configuración OIDC ausente, rechazo CSRF y ruta no permitida. Sus escenarios visuales 403 y carrera de respuesta usan respuestas interceptadas exclusivamente en el navegador de prueba, no un backend ficticio desplegado. La prueba unitaria OIDC levanta un IdP efímero de loopback con claves RSA generadas para comprobar PKCE/state/nonce/JWKS, no sustituye una prueba con Keycloak real.

No afirmar aislamiento PostgreSQL/RLS, permisos FastAPI ni MinIO verificados por estos tests. Quedan pendientes el walkthrough con Keycloak y API v2 reales, contratos aprobados, usuario de dos agencias, revocación efectiva, aislamiento de medios y matriz A/B completa. No se hicieron commits ni push.

## Resultado de esta entrega

- `npm run build`: PASS con Next.js 16.4.6 y el modo mock predeterminado. También compiló con `NEXT_PUBLIC_USE_MOCKS=false`; el artefacto final quedó restaurado a mock.
- `npm run typecheck`: PASS.
- `npm test`: 17/17 PASS. Incluye cliente real con transporte controlado, mock A/B, referencia por agencia, 401/403/404/409, medios, cancelación, sesión/transacción, proxy/CSRF/401 tardío y OIDC/JWKS con IdP local efímero.
- `npm run test:e2e`: 10/10 PASS con Chrome local, escritorio y viewport móvil de 390 px.
- `E2E_REAL=true npm run test:e2e` tras build real: 8/8 PASS, con el alcance de BFF real e interceptación visual descrito arriba.
- `git diff --check`: PASS. Los cambios están exclusivamente en frontend; el worktree backend no se cambia de rama.

La primera instalación agotó timeout y dejó SWC truncado; se regeneró el lockfile completo de dependencias opcionales y se ejecutó `npm ci --ignore-scripts`. El build pasó después, sin desactivar TypeScript ni cambiar el compilador. Next actualizó automáticamente `next-env.d.ts`. Los primeros ensayos también corrigieron una API de tests no disponible en Node 22, selectores ambiguos de Playwright y carreras de lectura/sesión detectadas por revisión. No hay tests omitidos ni retries para ocultar fallos.

No se ejecutaron Keycloak real, backend v2, Docker, PostgreSQL/RLS o MinIO. No se enviaron datos del CRM a servicios de IA; los únicos datos de prueba son ficticios.
