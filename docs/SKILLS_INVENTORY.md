# Inventario y seleccion de skills locales

## Alcance y evidencia

- Proyecto: `/Users/alexander/Desktop/Cursos/ProyectosWindows/crm-rah-vzla-starter`.
- Auditoria global mediante subagente de solo lectura: **93 contenidos canonicos, 155 rutas a SKILL.md, 62 alias por symlink y 43 SKILL.md leidos completos**; metadata de los otros 50. No sumar alias como instalaciones independientes.
- Los scripts y referencias de candidatas se inspeccionaron estaticamente, sin ejecutarlos. La validacion posterior ejecuta solo tooling local auditado y se detalla en `SETUP_REPORT.md`; no hubo analisis LLM adicional ni uso de Cloud.
- Otro subagente reviso las ubicaciones convencionales de proyectos: 28 proyectos de `ProyectosWindows` y proyectos de desarrollo identificados en `Cursos`, sin recorrer carpetas personales; **26 rutas de skills de proyectos, no 26 skills unicas**.
- Configuracion aplicada: referencias selectivas `skills.paths`, launcher reducido, dos skills ECC Markdown y `graphify-local`. Sin cambios de negocio, contratos, dependencias del CRM, fuentes originales o configuracion global.
- Compatibilidad base auditada: Next.js 16, React 19.2, Tailwind 4.1 y TypeScript. El runtime sigue siendo DEMO local sin autenticacion ni aislamiento multiagencia implementados.
- Aplican `AGENTS.md`, `CONTRACTS.md` y los sprints: datos ficticios, USD/VES explicitos, geografia venezolana, sin conversion implicita, sin afiliacion oficial a Rent-A-House ni acceso de soporte transversal implicito.

## Rutas y estados

Cada ubicacion del inventario termina en `/SKILL.md`. `F` significa lectura completa del SKILL.md global; `M`, metadata. La agrupacion conserva todos los IDs del frontmatter.

| Clave | Raiz o convencion | Estado de evidencia |
| --- | --- | --- |
| O | `~/.config/opencode/skills` | 4 contenidos auditados; reutilizacion sin copiar. |
| A | `~/.agents/skills` | 62 contenidos auditados; todos declaran MIT en frontmatter. |
| C | `~/.claude/skills` | 27 contenidos adicionales y 62 alias hacia A. |
| S | `~/.claude/skills/synced/797e3534-528b-45e3-acdc-95c1ee8e8f7a_fbcabcd4-b682-4f2e-89ad-73c327230f87` | Subraiz de C; no contar otra vez sus 16 contenidos. |
| A/ID y C/ID | `C/ID -> ../../.agents/skills/ID` | Los 62 IDs de A tienen alias confirmado; mismo contenido, no copias divergentes. |
| P/nombre | `/Users/alexander/Desktop/Cursos/ProyectosWindows/<nombre>` | Constructora usa `.opencode/skills`; ProjectmanagerAY, `.claude/skills`; StudioPulse, `.agents/skills` y `frontend/.agents/skills`. |

## Inventario OpenCode

Solo se encontraron SKILL.md en estas cuatro carpetas, sin scripts o manifiestos empaquetados ni licencia local declarada.

| ID y ubicacion | Lectura | Proposito | Compatibilidad | Riesgo concreto | Recomendacion |
| --- | --- | --- | --- | --- | --- |
| `security-review` O/security-review | F | Revisar autorizacion, secretos, dependencias y aislamiento tenant. | Independiente del stack; muy pertinente al CRM multiagencia. | Revision estatica no certifica seguridad; no afirmar vulnerabilidades de dependencias sin evidencia actual. | Reutilizar global sin copiar; solo lectura por defecto. |
| `dataviz` O/dataviz | F | Graficos, escalas, unidades y alternativas accesibles. | Dashboard web responsive, sin biblioteca obligatoria. | No inventar KPIs ni mezclar monedas; distinguir cero, ausente y dato obsoleto. | Reutilizar global sin copiar, solo cuando haya visualizacion. |
| `simplify-changes` O/simplify-changes | F | Simplificar el diff preservando comportamiento y contratos. | Compatible con patrones del proyecto. | Prescribe edicion y verificaciones; necesita un cambio identificable y ownership. | Reutilizar global sin copiar, tras un diff autorizado. |
| `run-project` O/run-project | F | Arrancar y verificar usando infraestructura existente. | Compose y scripts del CRM. | Puede instalar dependencias y iniciar procesos; no es solo lectura. | Reutilizar global sin copiar solo al pedir ejecucion; mantener loopback y DEMO. |

## Inventario Claude

Estas 11 skills, mas las 16 de S, forman los 27 contenidos adicionales de C. Salvo donde se indica, no se encontro licencia local declarada ni archivo de licencia en estas carpetas.

| ID y ubicacion | Lectura | Proposito | Compatibilidad | Riesgo concreto | Recomendacion |
| --- | --- | --- | --- | --- | --- |
| `frontend-design` C/frontend-design | F | Direccion visual, copy, responsive y componentes. | Next/React; sin scripts propios. | Puede inducir reinvencion de marca o claims; Apache-2.0 verificada en LICENSE.txt. | Referenciar solo esta fuente global adicional; preservar marca y contenido veraz. |
| `impeccable` C/impeccable | F | UI, a11y, responsive y sistema de diseno; modo Operate. | Referencias transferibles; integracion del motor con OpenCode no demostrada. | Launcher descarga/ejecuta motor y puede gestionar hooks/configuracion; Apache-2.0 declarada sin texto local encontrado. | Referencias solamente; excluir launcher del flujo normal. |
| `design-taste-frontend` C/taste-skill | F | Direccion, generacion e inspeccion visual; reglas propias para dashboards. | Node 22 y Chrome para inspector; reglas web transferibles. | Historial en home, capturas, servidor local, assets de red y prohibiciones esteticas rigidas; licencia no aclarada. | No base del CRM; consulta puntual, sin scripts ni copia de assets. |
| `ui-ux-pro-max` C/ui-ux-pro-max | F | Catalogo UI/UX, a11y, React, Next y Tailwind. | Datos para React 19, Next 16 y Tailwind 4; Python estandar. | `--persist` escribe; ruta de invocacion depende de CLAUDE_PLUGIN_ROOT; licencia no declarada. | Consulta selectiva de referencias; no persistencia ni autoejecucion. |
| `emil-design-eng` C/emil-design-eng | F | Componentes, feedback y motion. | CSS/WAAPI/React; ejemplos Motion/Framer no instalados en CRM. | Reglas absolutas y nuevas librerias innecesarias; licencia no declarada. | Solo consulta puntual, sin ampliar dependencias por defecto. |
| `apple-design` C/apple-design | F | Gestos, tipografia, springs y reduced-motion. | Web; sin scripts propios. | Blur, gestos y estetica Apple pueden contradecir marca y uso intensivo; licencia no declarada. | Fuente canonica frente al duplicado de ProjectmanagerAY; no seleccion habitual. |
| `animation-vocabulary` C/animation-vocabulary | F | Nombrar efectos, no implementarlos. | Referencia terminologica independiente del stack. | No es implementacion ni prueba; licencia no declarada. | Opcional al describir una interaccion. |
| `find-animation-opportunities` C/find-animation-opportunities | F | Proponer motion solo donde aporta. | Revision de UI, sin implementacion. | Propuestas no verificadas visualmente siguen siendo hipotesis; licencia no declarada. | Opcional; priorizar contencion en uso diario. |
| `review-animations` C/review-animations | F | Revisar un diff de motion. | CSS/React; disable-model-invocation: true. | Criterios rigidos pueden producir falsos positivos; licencia no declarada. | Solo revision explicita, no guia general. |
| `improve-animations` C/improve-animations | F | Auditoria y planes de motion. | Codigo web; delegacion opcional. | Read-only solo sobre fuentes: escribe plans/; execute delega implementacion; licencia no declarada. | No invocar en auditorias sin escrituras. |
| `graphify` C/graphify | F | Grafos, consultas, exportacion y memoria. | CLI instalado 0.9.20; skill global 0.9.15. | AutoGemini, instalaciones y persistencia; no es workflow estrictamente local. | Excluida del launcher; usar graphify-local sin tocar el original. |

## Inventario Agents

Todas las ubicaciones son `A/<ID>/SKILL.md`, con alias `C/<ID>/SKILL.md` para cada ID explicito. No se encontraron scripts empaquetados ni archivos LICENSE/NOTICE; MIT esta declarada en los 62 frontmatters, no documentada con un expediente local completo de redistribucion.

| IDs explicitos | Lectura | Proposito | Compatibilidad | Riesgo concreto | Recomendacion |
| --- | --- | --- | --- | --- | --- |
| `ux-heuristics` | F | Navegacion, formularios, errores y evaluacion UX. | Web/React; checklist WCAG 2.1. | Puntuacion no certifica a11y; completar criterios 2.2 aplicables. | Conservar como consulta global, no duplicar la ligera de proyecto seleccionada. |
| `refactoring-ui` | F | Jerarquia, tokens, componentes y espaciado. | Tailwind con adaptacion a v4. | Referencia confunde px con pt en contraste de texto grande; snippets no son componentes terminados. | Consulta con reserva; flujo habitual usara variante ligera original. |
| `web-typography` | F | Legibilidad, escala fluida y carga de fuentes. | CSS/Next; verificar caracteres del espanol. | Licencias de fuentes y solicitudes externas; no asumir cobertura por la skill. | Consulta profunda ocasional; ligera seleccionada para uso normal. |
| `microinteractions` | F | Estados, validacion y feedback. | UI web, sin runtime propio. | Decoracion y celebraciones pueden ralentizar tareas frecuentes. | Consulta profunda ocasional; ligera seleccionada para uso normal. |
| `design-everyday-things` | F | Affordances, prevencion y recuperacion de errores. | Conceptual, transferible al CRM. | Solapa ux-heuristics; no validar decisiones por una nota numerica. | Opcional ante una confusion concreta. |
| `high-perf-browser` | F | Recursos, cache y Core Web Vitals. | Web/Next; consejos de red dependen de despliegue. | Cache generica de API puede filtrar datos entre agencias si se aplica sin aislamiento. | Usar ante problemas medidos, no optimizar por intuicion. |
| `lean-analytics` | F | Definir KPIs y metricas accionables. | Dashboard y producto, no biblioteca grafica. | Benchmarks SaaS no son datos venezolanos ni del CRM. | Opcional antes de elegir metricas. |
| `top-design` | F | Landing inmersiva, scroll y tipografia dramatica. | Web; sugiere Lenis/GSAP. | Mal encaje en panel operativo; dependencias y motion innecesarios. | Posponer para marketing, no aplicar al CRM. |
| `ios-hig-design` | F | Interfaces SwiftUI/UIKit y accesibilidad nativa. | No corresponde al frontend web actual. | Importar SF Symbols, navegacion y reglas nativas como obligaciones web. | Fuera de seleccion normal. |
| `steve-jobs-design-review` | F | Foco y experiencia completa. | Revision de producto independiente del stack. | Veredictos subjetivos no son controles de entrega. | Opcional, sin reemplazar evidencia ni pruebas. |
| `lean-ux`, `design-sprint` | F | Experimentos, prototipos y pruebas con usuarios. | Metodos de producto transferibles. | Necesitan participantes y evidencia; no sustituyen tests automatizados. | Posponer hasta una decision incierta concreta. |
| `storybrand-messaging`, `made-to-stick`, `obviously-awesome` | F | Mensaje, claridad y posicionamiento. | Marca/copy, no implementacion React. | Convertir ejemplos, ventajas o testimonios en claims reales. | Solo comunicacion autorizada y evidencia verificable. |
| `hooked-ux`, `improve-retention` | F | Habitos, activacion y friccion. | Producto digital con uso observado. | Gamificacion, ansiedad o notificaciones sin necesidad real. | Posponer hasta contar con evidencia. |
| `improve-app`, `grow-app` | F | Orquestar mejora UX y retencion. | Producto existente; multiples skills. | Escriben trackers/docs y ofrecen instalaciones globales. | No activar journeys completos por defecto. |
| `create-website`, `improve-website`, `grow-website` | F | Journeys de diseno, conversion y crecimiento web. | Marketing futuro, no runtime operativo. | Escrituras amplias, instalacion global ofrecida y solapamiento de guias. | Posponer; no reiniciar trabajo del CRM. |
| `cro-methodology` | F | Embudos y experimentos A/B. | Sitios con trafico y evidencia. | Testing de conversion no verifica funcionalidad ni seguridad. | Posponer mientras solo haya DEMO. |
| `working-with-legacy-code` | F | Caracterizacion y cambios seguros sin tests. | React/backend con harness apropiado; no aporta runner. | Scratch refactoring/reverts y compatibilidad por defecto requieren control. | Apoyo puntual antes de cambiar comportamiento existente. |
| `clean-code` | F | Nombres, funciones, errores y tests unitarios. | Transferible, con ejemplos OO. | Extract till you drop y funciones de 4-6 lineas favorecen sobreabstraccion. | Preferir simplify-changes; no convertir heuristicas en reglas absolutas. |
| `improve-code-quality`, `remove-technical-debt` | F | Journeys de testing, estructura y robustez. | Conceptualmente pertinentes al prototipo. | Escrituras, commits/reverts prescritos y alcance amplio. | No activar completos ni autorizar acciones Git implicitamente. |
| `clean-architecture`, `domain-driven-design`, `software-design-philosophy`, `pragmatic-programmer`, `refactoring-patterns` | M | Limites, dominio, complejidad y refactorizacion. | Conceptual frontend/backend. | Nuevas abstracciones, contratos u ownership fuera de alcance. | Consulta bajo necesidad y aprobacion humana de fronteras. |
| `ddia-systems`, `system-design`, `release-it` | M | Datos, escalabilidad y resiliencia. | Backend/infra, no UI directamente. | Introducir cache, colas o servicios sin requisitos. | Puntuales y con propietario correspondiente. |
| `create-app`, `design-code-architecture` | M | Orquestar creacion y arquitectura. | Ya existe arquitectura multiagencia propuesta. | Reiniciar decisiones y crear documentacion paralela. | No usar para redisenar el sistema por defecto. |
| `37signals-way`, `team-topologies`, `high-output-management`, `traction-eos` | M | Alcance, equipos, ownership y operacion. | Organizacion, no stack concreto. | Reemplazar responsabilidades humanas o sprints vigentes. | Consulta organizativa opcional. |
| `jobs-to-be-done`, `mom-test`, `continuous-discovery`, `inspired-product`, `lean-startup` | M | Descubrimiento, entrevistas y validacion. | Producto/mercado. | Presentar hipotesis como hallazgos de clientes. | Opcionales con evidencia y sin datos personales. |
| `good-strategy-bad-strategy`, `blue-ocean-strategy`, `crossing-the-chasm`, `cold-start-problem` | M | Estrategia, diferenciacion, adopcion y redes. | Negocio, no implementacion inmediata. | Desviar alcance o asumir un marketplace inexistente. | Fuera del flujo tecnico normal. |
| `one-page-marketing`, `scorecard-marketing`, `influence-psychology`, `contagious`, `hundred-million-offers`, `predictable-revenue`, `monetizing-innovation` | M | Captacion, persuasion, ventas y precios. | Marketing/comercial futuro. | Ofertas, metricas o pruebas sociales inventadas; captura de PII. | Posponer; no publicar ni comprometer acciones comerciales. |
| `create-business`, `improve-business`, `grow-business` | M | Journeys de negocio. | No necesarios para desarrollo UI. | Documentacion y decisiones amplias sin mandato. | Alcance separado si se solicitan. |
| `drive-motivation` | M | Autonomia, dominio y proposito. | Producto/equipo. | Anadir gamificacion por metodologia. | Opcional, no seleccion habitual. |
| `negotiation` | M | Preparar negociaciones y objeciones. | Comercial, no tecnico. | Compromisos o acciones externas no autorizados. | Fuera del trabajo de implementacion. |

## Inventario Synced

Cada ID tiene ubicacion `S/<ID>/SKILL.md`. Las dependencias de estas familias no se auditaron exhaustivamente; no se proponen para el flujo CRM salvo tarea especifica.

| IDs explicitos | Lectura | Proposito | Compatibilidad | Riesgo y licencia | Recomendacion |
| --- | --- | --- | --- | --- | --- |
| `built-in-browser`, `chrome-browser`, `computer-use` | M | Navegador/escritorio con herramientas especificas Claude. | Herramientas no disponibles en esta sesion. | Propietarias; restricciones explicitas de copia, derivados y distribucion. | No portar a OpenCode ni al repositorio. |
| `docs` | M | Documentos colaborativos via connector. | Connector requerido, no disponible. | Creacion previa a investigacion; licencia no declarada. | Excluir de tareas sin escrituras. |
| `docx`, `pdf`, `pptx`, `xlsx` | M | Documentos Office/PDF y hojas de calculo. | Herramientas y scripts auxiliares, no UI CRM. | Apache-2.0 identificada; dependencias externas no auditadas aqui. | Solo tareas documentales expresas. |
| `google-workspace` | M | Crear/editar archivos Google. | Connectors y acceso a cuenta. | Escritura y transferencia de datos; licencia no declarada. | Fuera del CRM local; sin envio/publicacion implicitos. |
| `skill-creator` | M | Crear y evaluar skills, no probar el CRM. | Harness de evaluacion propio. | Apache-2.0 identificada; scripts de evaluacion/optimizacion. | No necesaria; no ejecutar evaluaciones LLM. |
| `deep-research` | M | Investigacion coordinada. | Requiere agentes/fuentes. | Alcance externo innecesario; licencia no declarada. | Excluir del inventario local operativo. |
| `estefa-brand-brain` | F | Marca personal especifica y Brand DNA. | project_read/project_write ajenos al CRM. | Identidad ajena y reescritura de documentos; licencia no declarada. | Excluir aunque coincida con branding. |
| `import-memory`, `morning` | M | Memoria personal y briefing/recurrencias. | Entorno Claude. | Persistencia/contexto personal; licencia no declarada. | Fuera de ambito. |
| `cerebro-financiero`, `jumbo-check-shopping` | M | Finanzas personales y supermercado. | Sin relacion con CRM. | Supuestos monetarios/promocionales ajenos; licencia no declarada. | Excluir. |

## Hallazgos de proyectos

Los conteos siguientes son adicionales al inventario global y no se suman como contenidos unicos. La igualdad o diferencia comunicada se refiere a lectura de archivos, no a paquetes instalados en el CRM.

| Proyecto / IDs explicitos | Hallazgo comunicado | Compatibilidad y riesgo | Reutilizacion decidida | Configuracion prevista |
| --- | --- | --- | --- | --- |
| P/constructora-erp y P/constructora-erp-demo: `frontend-design`, `refactoring-ui`, `ux-heuristics`, `web-typography`, `microinteractions`, `clean-code`, `security-review`, `clean-architecture`, `system-design`, `run-project` | 10 skills iguales por lectura en ambos proyectos: 20 rutas, no 20 contenidos distintos. | No deducir identidad con las globales por compartir ID; no importar sus reglas sectoriales. | Solo las cuatro originales de la fila siguiente; sin duplicados demo. | Rutas e IDs verificados mediante descubrimiento nativo. |
| P/constructora-erp: `refactoring-ui`, `ux-heuristics`, `web-typography`, `microinteractions` | Variantes ligeras de 17-19 lineas, solo Markdown. | Vocabulario de construccion y paleta navy/naranja NO aplican al CRM; preservar marca existente y semantica inmobiliaria venezolana. | Reutilizadas mediante skills.paths, sin copiar ni editar originales. | Solo estas cuatro carpetas, no toda la raiz de skills. |
| P/ProjectmanagerAY: `apple-design` | Duplicado del contenido global C/apple-design. | Doble ID y doble carga sin beneficio. | No reutilizar esta ruta. | Mantener como referencia canonica C si alguna vez se necesita. |
| P/StudioPulse: `apple-design` | Difiere del global con el mismo ID; 123 referencias y script pull-hig. | Red, escritura y prune; colision de ID no equivale a alias seguro. | NO reutilizar. | Excluir tanto skill como script del launcher normal. |
| P/StudioPulse: `react-aria` en frontend/.agents/skills/react-aria | Documentacion Apache-2.0 de componentes, frameworks y testing; requiere react-aria-components y, para testers, dependencias de testing ausentes en CRM. | No confundir disponibilidad de instrucciones con compatibilidad del runtime. | Pospuesta. | No instalar paquetes ni copiar herramientas implicitamente. |
| Exploracion agregada | 26 rutas de proyectos; 28 proyectos en ProyectosWindows y ubicaciones convencionales Cursos inspeccionados, sin carpetas personales. | No se aportan aqui todos los IDs/rutas exactas de testers; no inventarlos ni afirmar 26 unicas. | Solo las cuatro ligeras anteriores quedan seleccionadas para reutilizacion. | Completar detalle de rutas/testers en procedencia antes de habilitarlos. |

## Riesgos de ejecucion y licencias

- `C/graphify/SKILL.md:65-100,154-161`: prescribe instalaciones/actualizaciones, contempla --break-system-packages y selecciona Gemini si detecta claves; incluso query prescribe vocabulario y save-result en `references/query.md:43,168-182`.
- Version comunicada por el integrador: Graphify ya 0.9.20; skill global 0.9.15 desalineada e insegura por autoGemini. La version del CLI no vuelve seguro el runbook anterior.
- `C/impeccable/scripts/impeccable:42-85,122-203`: ejecuta candidatos de entorno/cache/PATH o descarga a ~/.impeccable; cambia permisos. SHA-256 de nuevas descargas proviene del mismo origen y no autentica candidatos locales ya confiados.
- `C/impeccable/reference/hooks.md:11-21,108`: admite hooks/configuracion por proyecto y en ambito usuario; no autorizar modificaciones globales ni hooks por usar una referencia de diseno.
- `C/taste-skill/scripts/draw.mjs:110-113,206-208` y `scripts/lib/app-draw.mjs:46-48,118-120`: escriben historial en ~/.taste-skill y direccion en el proyecto; inspector abre servidor loopback, crea/elimina perfiles y reemplaza capturas.
- El servidor de archivos del inspector puede servir el directorio de trabajo, no solo el HTML; no ejecutarlo sobre contenido no confiable o carpetas con secretos. Assets incorpora red/descargas y licencias independientes.
- ui-ux-pro-max: search/core/reasoning_contract revisados como busqueda local con Python estandar, sin LLM en lo inspeccionado; design_system --persist escribe y --force sobrescribe. Esto no autoriza ejecutar scripts en este trabajo.
- Las cuatro O y las 62 A no empaquetan ejecutables encontrados. Los journeys A aun pueden inducir escrituras, instalaciones globales ofrecidas y operaciones Git: las instrucciones no son una barrera de permisos.
- Permisos muestreados: archivos 0644, launcher shell Impeccable 0755 y directorios superiores 0755; sin escritura de grupo/otros observada. No constituye sandbox; no se encontraron allowlists allowed-tools en candidatas principales.
- `A/refactoring-ui/references/accessibility-depth.md:118-122` confunde px con pt: 3:1 solo para texto de al menos 24 CSS px normal o aproximadamente 18.67px negrita; por debajo, 4.5:1. Su modal de ejemplo no implementa un focus trap completo.
- No apilar guias contradictorias: top-design exige dramatismo, taste impone bans esteticos y apple-design promueve translucencia. En CRM priman tarea, accesibilidad, consistencia y marca existente.
- Licencias incompletas: no redistribuir ni copiar skills/activos con procedencia o permisos sin aclarar. MIT declarada en A no sustituye texto/avisos; O no declara licencia; comprobar tambien licencias de las cuatro fuentes ligeras antes de cualquier redistribucion.
- frontend-design global tiene Apache-2.0 verificada; impeccable solo declaracion local. Las licencias de instrucciones no cubren automaticamente motores, fuentes, fotos o assets externos. Las tres skills propietarias synced no se portan.

## Seleccion aplicada

| Elemento | Estado auditado o comunicado | Reutilizacion / configuracion prevista | Limite |
| --- | --- | --- | --- |
| Cuatro ligeras constructora-erp | Reutilizadas; 17-19 lineas cada una. | skills.paths a originales: refactoring-ui, ux-heuristics, web-typography, microinteractions. | No copiar ni modificar; no aplicar navy/naranja ni vocabulario construccion. |
| frontend-design C | Auditada completa, Apache-2.0 verificada. | Una referencia global adicional, sola. | No cargar toda C ni otra frontend-design de proyectos. |
| Global O4 | Auditadas completas. | Reutilizar sin copiar: security-review, dataviz, simplify-changes, run-project. | Activar por tarea; run-project requiere autorizacion de ejecucion. |
| Launcher slim | Implementado: `sh .opencode/bin/opencode-local`. | Descubrimiento nativo: 13 IDs unicos, incluidas 9 skills reutilizadas, 2 ECC, graphify-local y customize-opencode incorporada. | Desactiva escaneo externo automatico y plugins; sin launcher no garantizar mismo catalogo reducido. |
| ECC | 8 familias evaluadas; 2 incorporadas y descubiertas por OpenCode. | verification-loop y e2e-testing, copias exactas MIT. | tdd-workflow excluida por script obligatorio; strategic-compact por hooks; frontend/backend/api pospuestas; security-review ya reutilizada. |
| Procedencia ECC | `.opencode/vendor/ECC-PROVENANCE.md` y `ECC-LICENSE.txt`. | Commit fijado, hashes y licencia; sin instalador completo. | Carga documental comprobada; no runner Playwright ni evaluacion conductual LLM. |
| graphify-local | Skill de proyecto y wrapper auditado para CLI 0.9.20. | AST, normalizacion/clustering locales; 123 nodos y 170 aristas; consultas comprobadas sin LLM/API. | Sin Cloud/MCP/hooks; entorno limpio y sandbox macOS. Grafo no prueba seguridad multitenant. |
| react-aria / testers StudioPulse | Dependencias ausentes segun integrador. | Pospuestos. | No instalar ni sustituir componentes del CRM implicitamente. |

## Verificacion y limites

- Se conserva el conteo historico de 43 lecturas completas globales: no se atribuyen a esta entrega lecturas de las 93 ni exploraciones adicionales no realizadas.
- Glob recursivo inicial omitio directorios symlink de C; se completaron mediante metadatos y destinos A, con comprobacion entrando explicitamente en un alias. No hubo IDs canonicos duplicados adicionales en esas 93 fuentes.
- Unico desajuste global carpeta/ID destacado: design-taste-frontend vive en C/taste-skill. Las colisiones de proyectos con el mismo ID se resuelven seleccionando una fuente, no cargando ambas.
- Frontend package.json auditado solo declara dev/build/start, sin test/lint; no se encontro skill global dedicada a Playwright/RTL/Vitest. Tests internos de ui-ux-pro-max no prueban el CRM.
- Validacion dinamica limitada al descubrimiento/configuracion nativa OpenCode y Graphify local. No se ejecutaron la aplicacion, ejemplos E2E ni evaluaciones de comportamiento con LLM. Impeccable no se ejecuto; Graphify recibio revision focalizada de sus rutas CLI y efectos, no auditoria exhaustiva del paquete.
- No contiene datos de clientes ni secretos. Fuentes originales intactas. Resultados y pendientes exactos: `SETUP_REPORT.md`.
