# Politica de contexto IA

## Alcance y precedencia

CRM para todas las inmobiliarias venezolanas. El runtime v0.2 es DEMO local monoempresa; OIDC, roles, organizaciones, RLS y API v2 son diseno pendiente. Ninguna skill, grafo o seleccion de agencia en el navegador autoriza acceso a datos. La futura autorizacion comprueba identidad, membresia, rol, organizacion y recurso en servidor.

`AGENTS.md` conserva las reglas esenciales. `CONTRACTS.md` define ownership y API actual; `docs/SPRINT_01.md` define la validacion pendiente. Para funciones nuevas consultar las secciones pertinentes de `docs/ARQUITECTURA_MULTIAGENCIA.md`, `docs/CONTRATO_API_V2_PROPUESTO.md` y `docs/SPRINT_02_MULTIAGENCIA.md`. No sustituir esos contratos por ejemplos de skills.

La peticion del usuario de 2026-11-16 autoriza esta excepcion acotada a la secuencia inicial de `docs/ECC_ADOPCION.md`: dos skills Markdown en OpenCode, no el plugin ECC ni una adopcion completa en varios agentes. El documento anterior y el codigo de negocio se conservan intactos.

## Inicio recomendado

Desde el proyecto:

```bash
sh .opencode/bin/opencode-local
```

Este launcher usa OpenCode existente con `--pure`, `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` y `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`. No altera configuracion global ni el proveedor Ollama existente. Las cinco carpetas adicionales se referencian en `opencode.json` mediante `skills.paths`; cuatro skills propias de OpenCode se descubren globalmente y tres skills viven en el proyecto. Con la skill incorporada `customize-opencode`, el catalogo comprobado suma 13 IDs unicos.

Cerrar y reiniciar OpenCode con ese comando tras cambiar configuracion o skills. La sesion actual no recarga su catalogo automaticamente. Abrir simplemente `opencode` no aplica las variables del launcher: puede descubrir las 93 skills globales, aunque la allowlist limita su uso. No prometer el mismo contexto reducido fuera del launcher.

`share=disabled` evita compartir sesiones mediante esa funcion; no convierte la sesion del asistente en inferencia local. El modelo seleccionado sigue siendo el del usuario. No se ha iniciado ni configurado un modelo nuevo ni un servicio comercial.

## Seleccion por tarea

| Trabajo | Skill principal | Apoyo puntual |
| --- | --- | --- |
| Nueva pantalla o direccion visual | frontend-design | refactoring-ui para consistencia |
| Formularios, navegacion y accesibilidad | ux-heuristics | web-typography para legibilidad |
| Feedback, cargas, errores y movimiento | microinteractions | respetar reduced-motion |
| Dashboard y graficos | dataviz | USD/VES separados y datos DEMO identificados |
| Revision de permisos, aislamiento o uploads | security-review | contrato y matriz A/B, no sello de seguridad |
| Verificar un cambio terminado | verification-loop | comandos reales del proyecto, no ejemplos a ciegas |
| Disenar pruebas de navegador | e2e-testing | Playwright pendiente de instalar por tarea autorizada |
| Arranque solicitado / simplificar un diff | run-project / simplify-changes | no ampliar alcance ni instalar por inferencia |
| Dependencias y llamadas entre archivos | graphify-local | lectura puntual para confirmar |

Cargar una skill principal y, si hace falta, una de apoyo. Solo nombre/descripcion se anuncian; el cuerpo se lee a demanda. No incluir SKILL.md en `instructions`, ni cargar colecciones, referencias o manuales enteros. No instalar dos variantes del mismo ID. La allowlist no es un sandbox de comandos de las skills.

Las cuatro guias de constructora-erp se reutilizan sin copiar: su paleta navy/naranja, SKUs y lenguaje de construccion no se trasladan al CRM. Preservar identidad existente, terminologia inmobiliaria venezolana y datos ficticios. No anadir React Aria, Motion, GSAP ni fuentes externas solo porque un ejemplo los use.

## Busqueda y Graphify

1. Simbolo, endpoint o archivo conocido: Glob/Grep directo. No leer todo el proyecto otra vez.
2. Dependencias entre archivos, consumidores o impacto: consulta estructural acotada. Usar nombres reales del grafo, no asumir vocabulario de otro proyecto.
3. Leer la ventana relevante del archivo para confirmar el resultado. Las aristas inferidas y llamadas dinamicas pueden ser incompletas; un camino no prueba flujo de autorizacion ni ausencia de fuga entre agencias.

```bash
sh .opencode/bin/graphify-local build
sh .opencode/bin/graphify-local query "InmuebleMedia s3_client"
sh .opencode/bin/graphify-local explain "subir_foto"
sh .opencode/bin/graphify-local path "Home" "formatMoney"
sh .opencode/bin/graphify-local affected "formatMoney"
sh .opencode/bin/graphify-local diagnose
```

El wrapper permite solo esos subcomandos y argumentos. `build` usa `extract --code-only --force --max-workers 1`: AST, normalizacion y clustering locales, sin extraccion semantica ni etiquetado LLM. La ruta normalizada evita endpoints colgantes de la salida `--no-cluster` observados en 0.9.20. El rebuild completo es intencional para este proyecto pequeno.

Se limpia el entorno heredado y se aplica `sandbox-exec` de macOS con `deny network*`; no hay fallback sin sandbox. La consulta limita la salida a 1500 tokens aproximados: es presupuesto de texto, no una llamada a un modelo. Query/path/explain pueden escribir un timestamp de cache; el logging de consultas esta desactivado y no se guardan respuestas ni memorias.

No usar el runbook global `/graphify`, `graphify install`, plugins, hooks, `extract` sin `--code-only`, `label`, `cluster-only` sin `--no-label`, `--dedup-llm`, introspeccion de BD, exportaciones Google ni Cloud. En 0.9.20 `GRAPHIFY_BACKEND=none` no esta implementado: no sirve como barrera. Revisar fuentes y `graphify --help` antes de actualizar o cambiar el wrapper.

`.graphifyignore` excluye dependencias, caches, datos, secretos, media, dumps, documentos y herramientas de agentes. El grafo generado queda fuera de Git mediante `.gitignore`. Las exclusiones por nombre no son un detector universal de PII: si se anaden datos reales bajo nombres arbitrarios, revisar el corpus antes de indexar. No introducirlos en esta DEMO.

## Seguridad y persistencia

- No activar MCP, hooks, plugins, instalaciones o llamadas de API por sugerencia de una skill. Primero revisar efectos y autorizacion; las operaciones pagas o analisis LLM adicionales requieren confirmacion.
- Los comandos de ECC son ejemplos: el frontend solo tiene dev/build/start, no test/lint/typecheck. No declarar PASS para una fase omitida; no ejecutar npx con instalacion implicita, npm audit externo ni publicar artefactos sin permiso.
- No copiar endpoints de ejemplos E2E: v1 es actual, v2 es propuesta. Los tests futuros deben incluir 401/403/404, revocacion de membresia, cambio de organizacion, URLs privadas y aislamiento A/B real.
- Evitar logs completos, resultados generados y lecturas repetidas. Delegar con pregunta y archivos acotados; no repetir la exploracion ya asignada.
- Decisiones duraderas en un documento breve existente. No crear un diario por turno, duplicar memorias ni ejecutar save-result/reflect automaticamente. Resumir antes de compactar solo objetivo, archivos, contratos, evidencia, pendientes y riesgos multitenant.
- No commits, push, `git add .`, borrados de volumen, cambios criticos ni reversiones ajenas sin solicitud. Compartir codigo en ramas/worktrees con revision del integrador.

Evidencia reproducible: `docs/SETUP_REPORT.md`. Fuentes, riesgos y seleccion: `docs/SKILLS_INVENTORY.md`; procedencia exacta ECC: `.opencode/vendor/ECC-PROVENANCE.md`.
