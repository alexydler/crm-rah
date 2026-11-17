# CRM RAH VZLA · Infraestructura y Base de Datos (Sprint 02)

Guía de puesta en marcha, gestión de identidad local (Keycloak OIDC), migraciones Alembic y verificación de Row Level Security (RLS) para la arquitectura multiinmobiliaria.

---

## 1. Servicios de la Infraestructura (`compose.yaml`)

Todos los puertos están estrictamente vinculados a `127.0.0.1` para desarrollo local seguro:

* **PostgreSQL 16:** `127.0.0.1:5432` (Base de datos relacional con RLS activado).
* **MinIO Storage & Console:** `127.0.0.1:9000` (API S3) y `127.0.0.1:9001` (Consola web).
* **Keycloak 24 (IdP OIDC):** `127.0.0.1:8080` (Realm `crm-rah-dev` autoimportado).
* **Backend FastAPI:** `127.0.0.1:8000` (`/docs` Swagger local).
* **Frontend Next.js:** `127.0.0.1:3000` (Centro de operaciones).

---

## 2. Puesta en Marcha

### Paso 1: Configurar variables de entorno
```bash
cp .env.example .env
```

Las credenciales por defecto son exclusivamente para entorno de desarrollo local ficticio.

### Paso 2: Iniciar los contenedores
```bash
docker compose up --build -d
```

Verificar estado:
```bash
docker compose ps
```

---

## 3. Identidad y Cuentas de Prueba (Keycloak OIDC)

Keycloak levanta en `http://localhost:8080` e importa automáticamente el realm `infra/keycloak-realm-dev.json`.

* **Consola de administración:** `http://localhost:8080`
  * Usuario: `admin` (o `${KEYCLOAK_ADMIN}`)
  * Contraseña: `dev_only_change_me_kc` (o `${KEYCLOAK_ADMIN_PASSWORD}`)
* **Realm de desarrollo:** `crm-rah-dev`
* **Cliente frontend OIDC:** `crm-rah-app` (Público, PKCE habilitado).

### Organizaciones DEMO configuradas:
1. **Organización Caracas:** UUID `11111111-1111-4111-8111-111111111111` (Slug: `demo-caracas`)
2. **Organización Valencia:** UUID `22222222-2222-4222-8222-222222222222` (Slug: `demo-valencia`)

### Usuarios de prueba:
| Usuario | Contraseña | Organizaciones asignadas | Rol principal |
| :--- | :--- | :--- | :--- |
| `usuario-a` | `dev_password_123` | Solo Org Caracas (`11111111-...`) | `asesor` |
| `usuario-b` | `dev_password_123` | Solo Org Valencia (`22222222-...`) | `asesor` |
| `usuario-ab` | `dev_password_123` | Ambas: Caracas y Valencia | `gerente` |
| `usuario-propietario` | `dev_password_123` | Solo Org Caracas (`11111111-...`) | `propietario` |
| `usuario-marketing` | `dev_password_123` | Solo Org Caracas (`11111111-...`) | `marketing` |

### Obtención de Tokens JWT para los usuarios de prueba (Solo Desarrollo)

> [!WARNING]
> Estas credenciales y el flujo `grant_type=password` son exclusivamente para pruebas locales en desarrollo. En producción, la autenticación debe realizarse mediante OIDC Authorization Code con PKCE.

#### 1. Token para `usuario-a` (Org Caracas):
```bash
TOKEN_A=$(curl -s -X POST "http://localhost:8080/realms/crm-rah-dev/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=crm-rah-app" \
  -d "username=usuario-a" \
  -d "password=dev_password_123" | jq -r .access_token)
echo "$TOKEN_A"
```

#### 2. Token para `usuario-b` (Org Valencia):
```bash
TOKEN_B=$(curl -s -X POST "http://localhost:8080/realms/crm-rah-dev/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=crm-rah-app" \
  -d "username=usuario-b" \
  -d "password=dev_password_123" | jq -r .access_token)
echo "$TOKEN_B"
```

#### 3. Token para `usuario-ab` (Dual: Caracas y Valencia):
```bash
TOKEN_AB=$(curl -s -X POST "http://localhost:8080/realms/crm-rah-dev/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=crm-rah-app" \
  -d "username=usuario-ab" \
  -d "password=dev_password_123" | jq -r .access_token)
echo "$TOKEN_AB"
```

#### Inspección del Payload del Token (sin verificar firma):
```bash
# Decodificar el payload Base64 del JWT:
echo "$TOKEN_A" | cut -d'.' -f2 | base64 --decode 2>/dev/null | jq .
# Verificar:
# iss: http://localhost:8080/realms/crm-rah-dev
# aud: ["crm-rah-api", ...] o "crm-rah-api"
# sub: e0000000-0000-4000-8000-000000000001
```

---

## 4. Migraciones de Base de Datos (Alembic)

La configuración de Alembic reside en `db/alembic.ini` y `db/alembic/`.

### Migraciones disponibles:
1. `0001_sprint02_multiagencia`: Esquema inicial multi-tenant, tablas base, `organizacion_id NOT NULL`, FK compuestas, RLS y rol `rah_app`.
2. `0002_rls_usuario_lectura`: Políticas RLS `PERMISSIVE` de lectura por usuario (`app.usuario_sub`) para `membresias` y `organizaciones`, y corrección idempotente de `usuarios.subject` para bases donde `0001` ya se aplicó.

### Corrección de `usuarios.subject` en volúmenes existentes:
Si un volumen de base de datos ya había ejecutado la migración `0001` con el subject antiguo (username en vez de UUID), la migración `0002` incluye automáticamente la actualización idempotente:
```sql
UPDATE usuarios SET subject = 'e0000000-0000-4000-8000-000000000001' WHERE email = 'usuario-a@ejemplo.com';
UPDATE usuarios SET subject = 'e0000000-0000-4000-8000-000000000002' WHERE email = 'usuario-b@ejemplo.com';
UPDATE usuarios SET subject = 'e0000000-0000-4000-8000-000000000003' WHERE email = 'usuario-ab@ejemplo.com';
```

### Aplicar migraciones con Alembic:
```bash
# Estando en el directorio db/ o con DATABASE_URL configurada:
cd db
alembic upgrade head
```

### Aplicar migración vía SQL directo (PostgreSQL en Docker):
Si no dispones del entorno Python/Alembic en tu máquina anfitriona:
```bash
docker compose exec -T postgres psql -U rah_dev -d rah_vzla < db/migrations/0001_sprint02_multiagencia.sql
docker compose exec -T postgres psql -U rah_dev -d rah_vzla < db/migrations/0002_rls_usuario_lectura.sql
docker compose exec -T postgres psql -U rah_dev -d rah_vzla < db/seeds/0001_sprint02_seeds.sql
```

### Reversión (Rollback):
```bash
# Con Alembic:
cd db
alembic downgrade -1

# O con SQL:
docker compose exec -T postgres psql -U rah_dev -d rah_vzla < db/migrations/0002_rls_usuario_lectura_down.sql
docker compose exec -T postgres psql -U rah_dev -d rah_vzla < db/migrations/0001_sprint02_multiagencia_down.sql
```

---

## 5. Verificación de Row Level Security (RLS) a Mano

### Concepto de seguridad implementado:
1. **Rol de aplicación no privilegiado (`rah_app`):** Tiene permisos de DML sobre las tablas, pero **NO** tiene el atributo `BYPASSRLS` ni es propietario de las tablas.
2. **Variable de sesión `app.organizacion_id`:** En cada transacción, la aplicación debe ejecutar `SET LOCAL app.organizacion_id = '<uuid_organizacion_verificada>';`.
3. **Aislamiento por defecto:** Si no se establece la variable de sesión, PostgreSQL no devuelve filas (0 filas), previniendo fugas accidentales por consultas no filtradas.

### Procedimiento de prueba manual en terminal con `psql`:

Inicia una sesión interactiva como el rol de aplicación `rah_app`:
```bash
docker compose exec -it postgres psql -U rah_app -d rah_vzla
```
*(Contraseña por defecto en desarrollo: `dev_only_change_me_app`)*

#### Test 1: Consulta sin filtro y sin contexto de organización
```sql
SELECT id, titulo, organizacion_id FROM inmuebles;
```
**Resultado esperado:**
```text
 id | titulo | organizacion_id 
----+--------+-----------------
(0 rows)
```
*Ninguna fila es visible sin fijar un contexto de tenant verificado.*

#### Test 2: Simular sesión de Organización Caracas
```sql
BEGIN;
SET LOCAL app.organizacion_id = '11111111-1111-4111-8111-111111111111';

SELECT id, codigo_referencia, titulo, organizacion_id FROM inmuebles;
```
**Resultado esperado:**
Devuelve únicamente los 3 inmuebles DEMO pertenecientes a la organización Caracas. Ningún registro de Valencia es accesible.
```sql
COMMIT;
```

#### Test 3: Simular sesión de Organización Valencia
```sql
BEGIN;
SET LOCAL app.organizacion_id = '22222222-2222-4222-8222-222222222222';

SELECT id, codigo_referencia, titulo, organizacion_id FROM inmuebles;
```
**Resultado esperado:**
Devuelve únicamente el inmueble perteneciente a Valencia (`DEMO · Local comercial en Valencia Centro`, código `DEMO-RAH-001`). Ningún registro de Caracas es accesible.
```sql
COMMIT;
```

#### Test 4: Intento de inserción cruzada (Cross-Tenant Attack)
Estando autenticado en el contexto de Caracas, intentar insertar un registro con el `organizacion_id` de Valencia:
```sql
BEGIN;
SET LOCAL app.organizacion_id = '11111111-1111-4111-8111-111111111111';

INSERT INTO inmuebles (
    titulo, tipo, operacion, precio, moneda, zona, organizacion_id
) VALUES (
    'Intento Ilegal', 'apartamento', 'venta', 50000, 'USD', 'Caracas',
    '22222222-2222-4222-8222-222222222222'
);
```
**Resultado esperado:**
```text
ERROR:  new row violates row-level security policy for table "inmuebles"
```
*La cláusula `WITH CHECK` rechaza la transacción de forma inmediata.*
```sql
ROLLBACK;
```

### Ejecutar Suite Automatizada de Validación RLS:
Hemos provisto un script SQL que ejecuta y valida automáticamente todas las aserciones de aislamiento:
```bash
docker compose exec -T postgres psql -U rah_dev -d rah_vzla -f /db/test_rls.sql
```
O desde la máquina anfitriona si `psql` está disponible localmente:
```bash
PGPASSWORD=dev_only_change_me psql -h 127.0.0.1 -U rah_dev -d rah_vzla -f db/test_rls.sql
```

---

## 6. Notas para el Integrador y otros Agentes

### Para Claude Code (`backend/`):
1. **Alembic:** Se recomienda añadir `alembic>=1.13,<2` a `backend/requirements.txt` para permitir que el backend ejecute `alembic upgrade head` en su flujo de arranque si se desea.
2. **Conexión a BD:** El backend debe conectarse usando el rol `rah_app` (`APP_DB_USER` / `APP_DB_PASSWORD`) en lugar del superusuario `rah_dev`.
3. **Sesión RLS en FastAPI:** En el middleware o dependencia de base de datos (`get_db`), tras validar el token OIDC y la membresía del usuario para la organización solicitada, ejecutar:
   ```python
   session.execute(text("SET LOCAL app.organizacion_id = :org_id"), {"org_id": str(org_id)})
   ```
4. **Validación OIDC:** Consumir los certificados JWKS desde `http://keycloak:8080/realms/crm-rah-dev/protocol/openid-connect/certs`.

### Para OpenCode (`frontend/`):
1. **BFF / OIDC Client:** Conectar Next.js BFF al issuer `http://localhost:8080/realms/crm-rah-dev` usando el client id `crm-rah-app`.
2. **Selector de Organización:** El usuario `usuario-ab` tiene membresías en ambas organizaciones; la interfaz debe proveer un selector accesible que altere la ruta activa a `/organizaciones/{org_id}/...`.
