# ECC minimo para OpenCode CRM

## Fuente y alcance

- Repositorio oficial: https://github.com/affaan-m/ECC
- Commit fijado: `d2ef2680594f9a17526a6e1a2e18b3d242c5d17b`.
- Commit URL: https://github.com/affaan-m/ECC/commit/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b
- SHA resuelto sin credenciales mediante `https://api.github.com/repos/affaan-m/ECC/commits/main`, consultado el 2026-11-16. Las lecturas posteriores usan el SHA, no `main`.
- Base de las copias: `https://raw.githubusercontent.com/affaan-m/ECC/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b/`.
- Copias exactas, sin adaptar nombres, frontmatter, ejemplos, Unicode ni saltos de linea. Licencia MIT completa: `ECC-LICENSE.txt`, Copyright (c) 2026 Affaan Mustafa.
- Solo cuatro archivos nuevos: dos skills, licencia y esta procedencia. Sin cambios de negocio, contratos, configuracion global, npm installs, ejecutables, scripts, hooks, plugins, agentes, reglas, MCP, proveedores ni tokens LLM/API adicionales.

Se leyeron `README.md` y `.opencode/README.md` del commit. El README principal admite copia manual componente por componente. Se descarta la configuracion completa OpenCode: carga 11 skills mediante `instructions` e incorpora integraciones de plugin/hooks. No se ejecutaron instaladores ni scripts remotos.

## Ocho familias evaluadas

Se leyeron los ocho `skills/<familia>/SKILL.md` oficiales; los tres candidatos de testing se leyeron completos.

| Familia | Decision | Motivo |
| --- | --- | --- |
| `frontend-patterns` | Posponer | Patrones React/Next, estado y rendimiento; solapan skills existentes y exceden la brecha testing. |
| `backend-patterns` | Posponer | Patrones Node/Express/Next y datos; backend CRM FastAPI de otro propietario. |
| `api-design` | Posponer | Convenciones REST, respuestas y versionado; no sustituir contratos CRM ni ampliar alcance. |
| `security-review` | No copiar | Ya existe `~/.config/opencode/skills/security-review/SKILL.md`, leida y conservada; evitar colision de nombre y alcance. |
| `tdd-workflow` | Excluir en este pin | Step 0 exige ejecutar `scripts/setup-package-manager.js`; depende de `scripts/lib/package-manager`. No es independiente dentro de los archivos autorizados. Tambien prescribe commits de checkpoint no autorizados aqui. |
| `verification-loop` | Copiar exacta | Checklist y reporte de verificacion autocontenidos; sus comandos son ejemplos sujetos a disponibilidad y permiso. |
| `e2e-testing` | Copiar exacta | Patrones Playwright autocontenidos; no instala ni configura el runner. |
| `strategic-compact` | Posponer | Solapa gestion de contexto; describe hooks y `suggest-compact.js`, fuera de alcance. |

No se copia TDD incompleta ni se crea una variante derivada `ecc-*`: esas rutas no estan autorizadas. La seleccion se reduce de tres candidatos a dos skills.

## Recursos y compatibilidad

- Se inspeccionaron por API `contents/skills/{tdd-workflow,verification-loop,e2e-testing}?ref=<SHA>`: cada directorio contiene solo `SKILL.md`. Se leyo `scripts/setup-package-manager.js`, sin ejecutarlo; su `require('./lib/package-manager')` confirma la dependencia externa del paso obligatorio TDD.
- `verification-loop` no importa scripts ECC. La mencion de PostToolUse es complementaria; `/verify` es una referencia, no un comando instalado. `e2e-testing` no exige recursos hermanos ECC: `ItemsPage`, fixtures, configuracion, workflows y artefactos son ejemplos a implementar en una tarea posterior autorizada.
- Entorno comprobado durante esta tarea: OpenCode 1.18.3, Python 3.13, Node 22. Descubrimiento en `.opencode/skills/<nombre>/SKILL.md`, sin agregar cuerpos a `instructions`. Fuente de ubicacion/formato: https://opencode.ai/docs/skills/. La carga nativa se verifico posteriormente como se indica abajo.
- `frontend/package.json` solo declara `dev`, `build` y `start`; no existen scripts npm `test`, `test:coverage`, `lint` o `typecheck`. No inventar comandos ni informar cobertura o PASS ficticios. El script `build` existe, pero no se ejecuto.
- Playwright no esta instalado en el frontend inspeccionado: no figura en dependencias ni se encontro `frontend/node_modules/@playwright`. Tampoco se encontraron configuracion Playwright o archivos test/spec en el frontend. Jest/Vitest, Testing Library, Bun, Supabase, Redis y OpenAI del TDD excluido son ejemplos, no dependencias instaladas por esta operacion. No se presupone disponibilidad de pyright/ruff ni de runners del backend.
- Los ejemplos E2E requieren `@playwright/test`, navegadores, servidor y tests reales antes de ejecutarse; ninguno se instala aqui. Sus ejemplos CI, wallets, trading y staging no son funcionalidades ni destinos del CRM. Revisar compatibilidad de APIs/opciones con la version de Playwright que se apruebe; registrar esperas de respuesta antes de disparar acciones para evitar carreras.

## Limites de uso

- Esta procedencia describe limites de integracion, no instala reglas de ejecucion. Las instrucciones de mayor prioridad, `AGENTS.md`, el alcance autorizado y `CONTRACTS.md` prevalecen sobre ejemplos ECC. Una skill de texto no garantiza seguridad ni disponibilidad de herramientas.
- No ejecutar `npm audit`, scanners externos de secretos ni enviar codigo, manifests, secretos o datos personales a servicios externos sin permiso. Para una revision local autorizada, no imprimir valores sensibles; los grep de ejemplo no acreditan una auditoria completa. No ejecutar instalaciones implicitas con `npx` ni los ejemplos CI/descargas sin aprobacion.
- No ejecutar Git commit, stage, rollback ni operaciones destructivas por indicacion de una skill. Este workspace no es repositorio Git; el hashing local de blobs no crea repositorio ni commits. No interpretar `git diff HEAD~1` como diff de la tarea sin verificar contexto.
- API actual: `/health`, `/api/v1/inmuebles`, `/api/v1/inmuebles/{uuid}` y medios segun `CONTRACTS.md`; v0.2 solo DEMO local, sin autenticacion ni aislamiento. API `/api/v2/organizaciones/{organizacion_id}/...` futura, propuesta y no implementada. No usar `/api/search`, `/api/data`, `/markets` ni otros ejemplos ECC como endpoints CRM.
- Mantener datos ficticios venezolanos, USD/VES explicitos y sin conversion implicita. No habilitar datos reales, produccion, integracion oficial con Rent-A-House ni accesos entre agencias. Cualquier futura implementacion respeta ownership y aprobacion del integrador humano.

## Integridad y verificacion

Rutas fuente relativas a la base fijada; destinos relativos al proyecto. SHA-256 calculado localmente con `shasum -a 256`. Los tamanos y Git blob SHA-1 locales tambien coinciden con los publicados por la API del commit, verificando la copia exacta.

| Fuente | Destino | Bytes | SHA-256 local |
| --- | --- | --- | --- |
| `skills/verification-loop/SKILL.md` | `.opencode/skills/verification-loop/SKILL.md` | 3972 | `9ee288d426660b0c785f534a003a4960fb4d8083a21302d8a4fd9b035b2edbb1` |
| `skills/e2e-testing/SKILL.md` | `.opencode/skills/e2e-testing/SKILL.md` | 8170 | `b0e00e7e17cb259101139900816c5528aed18dd10bcf5f9cb42cfc35baf8a755` |
| `LICENSE` | `.opencode/vendor/ECC-LICENSE.txt` | 1071 | `326146379f01bb137c0a5d3c54770c1aa31076705c8b88a7f6b26a460f6221b2` |

- Blobs oficiales, en el mismo orden: `32c1c5da8b6a6bb504396874c750cf34c98ad15c`, `f9ca797a1badc3a85352e14d31e6262dfde535bc`, `b832b6f642312312367c07688dc7426db40a82ed`.
- Formato comprobado con Ruby/Psych estandar (`YAML.safe_load`): frontmatter valido, nombre igual al directorio, descripcion no vacia y metadata ECC; bloques Markdown balanceados. Node/crypto verifico tamanos y hashes de blob sin ejecutar contenido descargado.
- Carga nativa posterior EJECUTADA por el integrador: `sh .opencode/bin/opencode-local debug skill` en OpenCode 1.18.3 devuelve ambos IDs, cuerpos y ubicaciones exactas. El launcher desactiva plugins externos y la carga automatica de colecciones externas. No se ejecutan ejemplos de las skills ni sesiones de modelo. El verificador `.opencode/scripts/verify-setup.py` comprueba su descubrimiento y hashes.
- Sin ejecuciones LLM, tests de negocio, build, lint, coverage, navegador, npm audit ni escaneos de secretos. No se modifican ni ejecutan los ejemplos de las skills.
- Para disponer de las skills en una sesion nueva, cerrar y reiniciar OpenCode desde este proyecto; comprobar descubrimiento/carga sin ejecutar los comandos de ejemplo. La sesion actual puede conservar el catalogo anterior.
