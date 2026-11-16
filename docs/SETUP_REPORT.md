# Informe de configuracion IA

Fecha: 2026-11-16. Alcance: herramientas de desarrollo, Skills y contexto; ningun cambio de codigo de negocio ni activacion de seguridad SaaS. Runtime actual v0.2 monoempresa, solo DEMO local.

## Entorno detectado

| Componente | Resultado ejecutado |
| --- | --- |
| SO | macOS 12.7.6 Monterey, Darwin 21.6.0, x86_64 |
| OpenCode | 1.18.3, `/usr/local/bin/opencode` |
| Python / pip | 3.13.3 / 25.0.1 |
| Node / npm / pnpm | v22.13.1 / 10.9.2 / 9.12.0 |
| Git | 2.37.1 Apple Git-137.1 |
| uv, uvx, pipx, Bun, Yarn | No encontrados en PATH; no instalados por esta tarea |
| Graphify | `graphifyy` 0.9.20 ya instalado; CLI en Python 3.13; proyecto metadata oficial Graphify-Labs/graphify |
| Parsers presentes | tree-sitter 0.25.2, Python 0.25.0, TypeScript 0.23.2; NetworkX 3.6.1 |
| Sandbox | `/usr/bin/sandbox-exec`, disponible; politica de red comprobada |
| Git del proyecto | `git status --short --branch` antes y despues: fatal, no es repositorio Git |

No se inicializo Git, no se hicieron commits/push ni se instalaron herramientas de sistema. Docker existe en PATH, pero no se inicio ni verifico el CRM. No se requieren nuevas credenciales.

## Configuracion anterior preservada

Se leyeron AGENTS, contratos, README, arquitectura y sprints. La configuracion global `~/.config/opencode/opencode.jsonc` referencia sus cuatro skills; `config.json` define Ollama local. `debug config` confirma que ambas siguen efectivas. No habia configuracion OpenCode de proyecto antes de la tarea.

Se creo `opencode.json` sin sobrescribir una configuracion previa. `skills.paths` referencia cinco carpetas concretas; no se copian colecciones globales ni fuentes de otros proyectos. `share` desactivado y allowlist de skills. No se anaden `instructions`, plugins, agentes, MCP ni hooks. El proveedor existente no se reemplaza y no se invoca inferencia Ollama.

El launcher `sh .opencode/bin/opencode-local` desactiva el descubrimiento externo automatico de skills y usa `--pure`. Esto evita incorporar las 93 skills globales y las colisiones con sus aliases. Cerrar y reiniciar OpenCode con ese launcher para aplicar la configuracion; la sesion existente conserva su catalogo anterior. La ejecucion directa de `opencode` sin launcher no garantiza el catalogo reducido.

## Skills reutilizadas

| Fuente | Skills | Accion |
| --- | --- | --- |
| `constructora-erp/.opencode/skills` | refactoring-ui, ux-heuristics, web-typography, microinteractions | Cuatro referencias por carpeta individual; originales intactos |
| `~/.claude/skills/frontend-design` | frontend-design | Referencia individual; licencia Apache-2.0 verificada |
| `~/.config/opencode/skills` | security-review, dataviz, run-project, simplify-changes | Descubrimiento global existente; sin copias |

Son **9 reutilizadas**. Se incorporan ademas **2 ECC**, **graphify-local** propia y **customize-opencode** incorporada en OpenCode: **13 IDs unicos**. No son 13 cuerpos en contexto global: se anuncian metadatos y se cargan cuerpos a demanda. La salida de diagnostico sumo 2901 bytes de nombres/descripciones frente a 46860 bytes de cuerpos; esto no es un benchmark de ahorro de tokens ni una medicion del prompt completo.

Inventario auditado: 93 contenidos globales, 155 rutas, 62 alias symlink; 43 SKILL.md globales completos y metadata de 50. Exploracion adicional en ubicaciones convencionales de 28 proyectos de ProyectosWindows y proyectos identificados en Cursos: 26 rutas, con duplicados. Ver `SKILLS_INVENTORY.md` para compatibilidad, riesgos, licencias y fuentes.

No se reutiliza la paleta ni vocabulario de construccion. React Aria se pospone por dependencias ausentes; las variantes apple-design duplican ID o incorporan reglas nativas no necesarias. Impeccable, taste y Graphify generico tienen scripts o efectos adicionales y no se activan en el perfil.

## ECC selectivo

Fuente oficial fijada: https://github.com/affaan-m/ECC/commit/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b

- Incorporadas copias exactas Markdown: `verification-loop` y `e2e-testing`.
- Incluidos MIT completo y hashes en `.opencode/vendor/ECC-LICENSE.txt` y `ECC-PROVENANCE.md`.
- Evaluadas las ocho familias: frontend-patterns, backend-patterns, api-design, security-review, tdd-workflow, verification-loop, e2e-testing, strategic-compact.
- security-review no se duplica; frontend/backend/api se posponen; strategic-compact solapa politica y prescribe hooks; tdd-workflow exige un script obligatorio y commits de checkpoint, asi que no se copia incompleta.
- El README oficial permite copia componente por componente. Se descarta el adaptador completo OpenCode: incorpora hooks/plugin y carga 11 skills via instructions. No se ejecutaron instaladores, npm, scripts remotos, hooks ni comandos de ejemplo.

Un intento de clone temporal fallo por DNS de github.com en terminal. Se consultaron documentacion y archivos publicos por webfetch/API de GitHub, sin credenciales y con el commit fijado. No se envio el CRM ni datos a esos servicios.

La carga nativa de ambos SKILL.md esta comprobada. No equivale a ejecutar tests ni a evaluar su comportamiento con un modelo. Playwright, sus navegadores y tests del CRM no se instalan en esta tarea. El frontend solo declara dev/build/start: los ejemplos de test/lint/coverage de ECC no son comandos existentes. La integracion exige lectura por tarea y respeto de la politica, no ejecucion literal.

## Graphify local

Se reutilizo la instalacion existente 0.9.20. Se leyeron `graphify --help`, documentacion oficial actual y fuentes instaladas para compatibilidad real. La skill global es 0.9.15: el CLI avisa del desajuste, pero no se actualizo ni sobrescribio porque su instalador modifica integraciones.

La version instalada no reconoce `GRAPHIFY_BACKEND=none`, aunque la documentacion actual v8 si lo describe. No se invento ese interruptor. La instalacion OpenCode oficial de 0.9.20 tambien escribe un plugin `tool.execute.before`; no tiene modo CLI solo-skill. Se adopta una integracion local propia, no se afirma haber ejecutado el instalador oficial.

`graphify-local` y su wrapper ejecutan el CLI oficial bajo entorno limpio y sandbox macOS `deny network*`. Solo permiten build/query/path/explain/affected/diagnose. El build usa `extract --code-only --force --max-workers 1`; no habilita semantica, deduplicacion LLM, etiquetado LLM, Cloud, base viva, Google, watchers, hooks ni MCP.

Resultado final: **16 archivos de codigo/esquema/configuracion, 123 nodos, 170 aristas, 13 comunidades**, tokens de extraccion LLM **0 entrada / 0 salida**. Documentos y medios no se indexan. El grafo permite SQL estructural de `db/init.sql`; excluye el seed, documentos y datos. No se generan HTML ni informes semanticos.

Primer ensayo `--no-cluster`: 149 nodos/230 aristas y 34 endpoints colgantes. Se sustituyo esa ruta bruta por normalizacion/clustering locales del CLI. El grafo final tiene 0 endpoints colgantes/faltantes, 0 duplicados exactos y 0 self-loops. El diagnostico final no reconstruye relaciones descartadas durante normalizacion: no garantiza exhaustividad ni conserva necesariamente todas las aristas paralelas del AST bruto.

Las primeras sondas socket y un primer build con sandbox agotaron timeout; reintentos de build y todas las consultas posteriores finalizaron. Se comprobo la politica efectiva sin red mediante `libsandbox.sandbox_check` con PID propio: outbound=1, inbound=1, bind=1 (denegado), lectura de archivos=0 (permitida). No hay fallback sin sandbox. No se accedio a servicios externos para el analisis.

`.graphifyignore` excluye dependencias, .next, dist/build, caches, .env/credenciales, datos de clientes, media, dumps/exports, artefactos de tests y herramientas de agentes. `.gitignore` excluye graphify-out y caches. Estos patrones no sustituyen clasificacion de PII bajo nombres arbitrarios; sigue prohibido introducir datos reales. El grafo es generado y local. Query/path/explain pueden escribir un timestamp de cache; logging y memorias Q&A estan desactivados.

## Validaciones ejecutadas

| Comprobacion | Resultado |
| --- | --- |
| Versiones, rutas y `graphify --help` | PASS, versiones arriba; ningun flag inventado |
| OpenCode `debug config` mediante launcher | PASS: esquema aceptado, share disabled, 0 instructions, 0 plugins y 0 MCP; Ollama global preservado |
| OpenCode `debug skill` mediante launcher | PASS: 13 IDs unicos, fuentes exactas seleccionadas y cuerpos presentes; ambas ECC cargadas |
| OpenCode `debug agent build` | PASS: reglas deny/allow de skills y rutas externas seleccionadas resueltas |
| `sh -n` de los dos launchers | PASS |
| SHA-256 de copias ECC y licencia | PASS; coinciden con pin y blobs oficiales |
| SHA-256 de 30 archivos protegidos | PASS repetido tras generar grafo; negocio, Compose, SQL, contratos y documentos protegidos intactos |
| Graphify build y diagnostico final | PASS: 123 nodos/170 aristas, ningun endpoint faltante/colgante |
| Graphify path Home a formatMoney | PASS: Home() --calls EXTRACTED--> formatMoney() |
| Graphify explain subir_foto | PASS: backend/app/main.py:L105; llamadas a guard, S3, modelo y respuesta |
| Graphify query InmuebleMedia/s3_client | PASS: subgrafo local acotado con ubicaciones y confianza |
| Graphify affected formatMoney | PASS: lista Home e InmuebleDetail y sus dos paginas |
| Wrapper rechaza label | PASS negativo: salida 2, sin iniciar operacion |
| Politica sandbox efectiva | PASS: red entrante, saliente y bind denegados |
| `verify-setup.py` reproducible | PASS: configuracion, 13 IDs/fuentes, 30 hashes, ECC exacto, 29 exclusiones sinteticas, integridad de grafo y escaneo local limitado |
| Fuentes externas y configuracion global | PASS: 14 huellas SHA-256 antes/despues coinciden (10 skills de constructora, frontend-design global y 3 archivos de configuracion/instrucciones globales) |

Las verificaciones de carga no lanzan sesiones de modelo. Un diagnostico inicial de todas las skills globales produjo JSON truncado por volumen; el catalogo reducido permite parseo y validacion completos. El primer test sintetico de ignores detecto una diferencia `/var` frente a `/private/var` en la fixture temporal de macOS: se corrigio con resolve() y los 29 casos pasan. Una revision independiente pidio comprobar rutas exactas de todas las skills, no solo IDs/subcadenas; el verificador final lo exige. No se realizo benchmark A/B ni se afirma porcentaje de ahorro o mejora de calidad sin medir.

## Archivos y preservacion

Nuevos: `opencode.json`, `.graphifyignore`, dos launchers en `.opencode/bin`, `.opencode/scripts/verify-setup.py`, tres skills locales (2 ECC + graphify-local), licencia/procedencia/manifest de integridad en `.opencode/vendor`, y los tres documentos solicitados. OpenCode creo automaticamente `.opencode/.gitignore` durante su diagnostico. Graphify genero solo artefactos locales ignorados en `graphify-out/`.

Modificados intencionalmente: `AGENTS.md` para reglas esenciales/enlaces y `.gitignore` para artefactos IA. `CONTRACTS.md`, `docs/ECC_ADOPCION.md`, README, frontend, backend, SQL e infraestructura permanecen iguales segun el manifest `.opencode/vendor/CRM-BASELINE.sha256`. No se borraron archivos existentes, configuraciones globales ni proyectos fuente.

## Pendientes y recomendacion

1. Reiniciar OpenCode usando el launcher indicado, no reusar el catalogo de la sesion actual. Las rutas compartidas son absolutas y propias de esta maquina; si se mueve un proyecto fuente, ajustar skills.paths tras revision.
2. Esta carpeta no es Git: no puede acreditarse staging, diff ni historial libre de secretos. Se usa integridad SHA-256 y escaneo local limitado de archivos nuevos; no se inicializa ni se versiona sin solicitud.
3. El CRM no se arranco: build, tests unitarios, E2E, Docker y matriz multitenant A/B siguen pendientes. La skill E2E no instala ni sustituye esos tests.
4. Conservar las skills compartidas sin redistribuir las de licencia no aclarada. ECC esta fijado; actualizar solo tras revisar cambios, dependencias y permisos. No actualizar Graphify por el simple aviso de skill antigua.
5. Mantener Graphify como ayuda estructural puntual, busqueda directa para consultas simples y una skill principal por tarea. No activar Cloud, MCP, hooks ni servicios comerciales.
6. No usar datos reales ni desplegar hasta completar autenticacion, autorizacion por recurso, migraciones/RLS, medios privados, auditoria, backups y pruebas de aislamiento del Sprint 02.

## Repetir las comprobaciones

```bash
sh .opencode/bin/opencode-local debug config
sh .opencode/bin/opencode-local debug skill
sh .opencode/bin/graphify-local build
sh .opencode/bin/graphify-local diagnose
PYTHONDONTWRITEBYTECODE=1 python3 .opencode/scripts/verify-setup.py
shasum -a 256 -c .opencode/vendor/CRM-BASELINE.sha256
```

El manifest documenta el estado anterior a esta tarea; si despues se cambia codigo legitimamente, el fallo de integridad es esperado. No regenerarlo automaticamente para ocultar diferencias. Fuentes oficiales consultadas: https://opencode.ai/config.json, https://opencode.ai/docs/skills/, https://github.com/affaan-m/ECC y https://github.com/Graphify-Labs/graphify; comportamiento de Graphify contrastado con el paquete instalado, no solo con documentacion viva.
