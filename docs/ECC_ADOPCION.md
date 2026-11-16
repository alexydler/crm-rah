# ECC para desarrollar CRM RAH VZLA — adopción controlada

Repositorio oficial: https://github.com/affaan-m/ECC

## Decisión

Usarlo como **herramienta de ingeniería**, no como dependencia del CRM en producción.
La primera prueba de adopción será SOLO en Claude Code con un repositorio de prueba/branch aislado. No instalarlo simultáneamente en los tres agentes.

## Prueba en Claude Code (tras leer la guía oficial y revisar permisos)

Dentro de Claude Code, como comandos separados:

```text
/plugin marketplace add https://github.com/affaan-m/ECC
/plugin install ecc@ecc
```

**No combinar** la instalación por plugin con un `install.sh --profile full` ni copiar a mano hooks. Después revisar los hooks, permisos y alcance efectivo del plugin en la máquina. No pegar nunca claves privadas en los prompts.

## Primeros flujos a evaluar

1. Plan de implementación por módulo, revisión de arquitectura y contratos.
2. Pruebas TDD para validación USD/VES, estados/municipios y subida de imágenes.
3. Seguridad y revisión de secretos de integración con MinIO/FastAPI.
4. Revisión de PR independiente antes de fusionar en `main`.

**Criterio de evaluación:** conservar solo las Skills/herramientas que mejoran las pruebas o reducen retrabajo. Sin métricas, no declarar que ECC acelera automáticamente el equipo.

## OpenCode y Antigravity

El soporte ECC no es idéntico en todas las herramientas; agregar adaptadores SOLO cuando el flujo estable con Claude Code funcione. Para OpenCode el repo ofrece soporte beta; Antigravity dispone de instalación minimal selectiva. No asumir igualdad de eventos/hooks.

## Seguridad

Los hooks pueden ejecutar comandos y los MCP podrían tener acceso a datos. Limitar permisos, revisar scripts, versionar cambios y no activar autopublicación/acciones destructivas. El módulo `AgentShield` puede ayudar a revisar la configuración, pero no sustituye una auditoría.
