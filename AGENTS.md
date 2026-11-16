# Reglas Esenciales

- CRM para todas las inmobiliarias venezolanas: Next.js/React/Tailwind, FastAPI, PostgreSQL y MinIO. Runtime v0.2 monoempresa: solo DEMO local y datos ficticios; v0.3 multitenant es diseño pendiente, no seguridad implementada.
- Antes de cambiar código, leer `CONTRACTS.md` y `docs/SPRINT_01.md`. Para funciones nuevas, también `docs/ARQUITECTURA_MULTIAGENCIA.md`, `docs/CONTRATO_API_V2_PROPUESTO.md` y `docs/SPRINT_02_MULTIAGENCIA.md`.
- Respetar ownership de `CONTRACTS.md`: OpenCode frontend; Claude backend/MCP; Antigravity BD/infra. El integrador humano aprueba contratos y resuelve fronteras. No cambiar campos, enums o endpoints sin contrato y pruebas; proponer coordinación fuera del ámbito asignado.
- Aislamiento por organización, membresía y recurso siempre verificado en servidor; el ID del cliente nunca autoriza. Soporte global no implica acceso a otras agencias. No presentar OIDC, RLS o API v2 como existentes.
- Geografía venezolana y USD/VES explícitos, sin conversión implícita. No inventar fotos/ofertas reales ni afiliación o integración oficial con Rent-A-House. No publicar, firmar, gastar ni cambiar estados críticos sin confirmación humana.
- No enviar PII, secretos o código a terceros ni activar IA de pago, APIs, MCP, hooks o scripts remotos sin revisión y autorización. ECC solo apoya desarrollo. Seguridad pendiente: `docs/SEGURIDAD_ANTES_DE_PRODUCCION.md`.
- Contexto mínimo: buscar símbolos/secciones antes de leer archivos completos; Skills solo por tarea; Graphify local para relaciones entre archivos, no búsquedas simples. Política y selección: `docs/AI_CONTEXT_POLICY.md`, `docs/SKILLS_INVENTORY.md`. Guías de otros proyectos no trasladan su paleta ni vocabulario al CRM.
- Verificar e informar pruebas ejecutadas y pendientes. No revertir cambios ajenos ni hacer commits/push sin solicitud; nunca `git add .` en ramas compartidas. Paralelo de código en ramas/worktrees y PR/checks, no ediciones simultáneas sin control.
