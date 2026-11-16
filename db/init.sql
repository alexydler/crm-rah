-- Esquema MVP local. En producción migrar a Alembic, no editar tablas manualmente.
CREATE TABLE IF NOT EXISTS inmuebles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo VARCHAR(180) NOT NULL,
  tipo VARCHAR(24) NOT NULL CHECK (tipo IN ('apartamento','casa','quinta','townhouse','local','oficina','galpon','terreno')),
  operacion VARCHAR(12) NOT NULL CHECK (operacion IN ('venta','alquiler')),
  precio NUMERIC(14,2) NOT NULL CHECK (precio >= 0),
  moneda CHAR(3) NOT NULL DEFAULT 'USD' CHECK (moneda IN ('USD','VES')),
  direccion VARCHAR(250),
  zona VARCHAR(120) NOT NULL,
  estado_ve VARCHAR(100),
  municipio VARCHAR(100),
  parroquia VARCHAR(100),
  urbanizacion VARCHAR(120),
  codigo_referencia VARCHAR(80),
  m2_construidos NUMERIC(10,2) CHECK (m2_construidos >= 0),
  m2_parcela NUMERIC(10,2) CHECK (m2_parcela >= 0),
  habitaciones SMALLINT CHECK (habitaciones >= 0),
  banos SMALLINT CHECK (banos >= 0),
  extras JSONB NOT NULL DEFAULT '{}'::jsonb,
  descripcion TEXT NOT NULL DEFAULT '',
  estado VARCHAR(20) NOT NULL DEFAULT 'borrador' CHECK (estado IN ('borrador','disponible','reservado','cerrado')),
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Opcional: referencia manual del asesor. No equivale a un código RAH oficial.
CREATE UNIQUE INDEX IF NOT EXISTS idx_inmuebles_codigo_referencia ON inmuebles(codigo_referencia)
  WHERE codigo_referencia IS NOT NULL;

CREATE TABLE IF NOT EXISTS inmueble_media (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inmueble_id UUID NOT NULL REFERENCES inmuebles(id) ON DELETE CASCADE,
  object_key TEXT NOT NULL UNIQUE,
  tipo VARCHAR(24) NOT NULL CHECK (tipo IN ('foto','plano_2d','render_3d','carrusel_png','historia_png','reel_mp4','cartel_pdf')),
  etiqueta_estancia VARCHAR(60),
  orden INTEGER NOT NULL DEFAULT 0,
  content_type VARCHAR(80) NOT NULL,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_media_inmueble ON inmueble_media(inmueble_id,orden);

-- Tablas preparadas para fases siguientes; NO se exponen sin autenticación.
CREATE TABLE IF NOT EXISTS clientes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre VARCHAR(160) NOT NULL,
  documento_id VARCHAR(80),
  telefono VARCHAR(40),
  email VARCHAR(160),
  tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('propietario','comprador','inquilino')),
  notas TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS contratos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inmueble_id UUID NOT NULL REFERENCES inmuebles(id),
  vendedor_id UUID REFERENCES clientes(id),
  comprador_id UUID REFERENCES clientes(id),
  tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('arras','alquiler','encargo')),
  monto NUMERIC(14,2) CHECK (monto >= 0),
  object_key TEXT,
  estado VARCHAR(20) NOT NULL DEFAULT 'borrador' CHECK (estado IN ('borrador','revision','aprobado','firmado')),
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS publicaciones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inmueble_id UUID NOT NULL REFERENCES inmuebles(id),
  canal VARCHAR(40) NOT NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'borrador',
  external_id VARCHAR(120),
  errores JSONB NOT NULL DEFAULT '[]'::jsonb,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
