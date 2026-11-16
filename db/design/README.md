# Diseño de datos multiagencia — no ejecutar

Esta carpeta contiene una especificación **de estructura objetivo**, NO una migración ni un script de inicialización operativo. El sistema v0.2 arranca sobre `db/init.sql` y sigue siendo monoempresa. Modificar `db/init.sql` NO migra volúmenes PostgreSQL ya creados.

El próximo sprint debe implementar Alembic, comprobar migración para bases nuevas y existentes, backfill DEMO controlado, activar auth y seguridad, RLS en todas las tablas tenant-owned y test de extremo a extremo. No ejecutar los ejemplos SQL de esta carpeta en la base actual ni en producción.
