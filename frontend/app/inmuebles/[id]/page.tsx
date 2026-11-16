"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, useEffect, useState } from "react";
import { API_URL, formatMoney, Inmueble, MediaAsset } from "../../types";

export default function InmuebleDetail() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [item, setItem] = useState<Inmueble | null>(null);
  const [media, setMedia] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [propertyResponse, mediaResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/inmuebles/${id}`, { cache: "no-store" }),
        fetch(`${API_URL}/api/v1/inmuebles/${id}/media`, { cache: "no-store" }),
      ]);
      if (!propertyResponse.ok || !mediaResponse.ok) throw new Error("No se pudo leer la ficha del inmueble");
      setItem((await propertyResponse.json()) as Inmueble);
      setMedia((await mediaResponse.json()) as MediaAsset[]);
    } catch (e) { setError(e instanceof Error ? e.message : "Error de conexión"); }
    finally { setLoading(false); }
  }
  useEffect(() => { if (id) void load(); }, [id]);

  async function upload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 12 * 1024 * 1024) { setError("Máximo 12 MiB por foto"); return; }
    setUploading(true); setError("");
    try {
      const formData = new FormData(); formData.append("archivo", file);
      const response = await fetch(`${API_URL}/api/v1/inmuebles/${id}/media`, { method: "POST", body: formData });
      if (!response.ok) throw new Error(`No se pudo subir la foto (${response.status})`);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Error de subida"); }
    finally { setUploading(false); e.target.value = ""; }
  }

  if (loading) return <p className="muted">Cargando ficha…</p>;
  if (!item) return <div className="panel"><p className="error">{error || "Inmueble no encontrado"}</p><Link href="/">Volver al panel</Link></div>;
  return <>
    <Link href="/" className="back">← Volver a la cartera</Link>
    <div className="eyebrow">FICHA DEL INMUEBLE</div>
    <div className="heading-row"><div><h1>{item.titulo}</h1><p className="subtitle">{item.zona} · {item.tipo} · {item.operacion}</p></div><span className="status">{item.estado}</span></div>
    <section className="detail-grid">
      <div className="panel"><h2>Características</h2><div className="detail-price">{formatMoney(item.precio, item.moneda)}</div>
        <dl className="spec-list"><div><dt>Operación</dt><dd>{item.operacion}</dd></div>
          {item.codigo_referencia && <div><dt>Referencia interna</dt><dd>{item.codigo_referencia}</dd></div>}
          {item.estado_ve && <div><dt>Estado</dt><dd>{item.estado_ve}</dd></div>}
          {item.municipio && <div><dt>Municipio</dt><dd>{item.municipio}</dd></div>}
          {item.parroquia && <div><dt>Parroquia</dt><dd>{item.parroquia}</dd></div>}
          {item.urbanizacion && <div><dt>Urbanización / sector</dt><dd>{item.urbanizacion}</dd></div>}
          {item.m2_construidos !== null && <div><dt>Superficie construida</dt><dd>{item.m2_construidos} m²</dd></div>}
          {item.m2_parcela !== null && <div><dt>Parcela</dt><dd>{item.m2_parcela} m²</dd></div>}
          {item.habitaciones !== null && <div><dt>Habitaciones</dt><dd>{item.habitaciones}</dd></div>}
          {item.banos !== null && <div><dt>Baños</dt><dd>{item.banos}</dd></div>}
        </dl>
        <p className="muted">{item.descripcion || "Sin descripción adicional."}</p>
      </div>
      <div className="panel"><div className="panel-top"><h2>Galería de fotografías</h2><label className="button primary upload-button">{uploading ? "Subiendo…" : "+ Subir foto"}<input type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} disabled={uploading} hidden /></label></div>
        <p className="muted small">Originales intactos · JPG, PNG o WEBP · Máximo 12 MiB</p>
        {error && <p className="error" role="alert">{error}</p>}
        {media.length === 0 ? <div className="empty-gallery">Aún no hay fotos. Sube la primera imagen para probar el almacenamiento privado.</div> :
          <div className="gallery">{media.map(asset => <figure key={asset.id}><img src={asset.url_temporal} alt={asset.etiqueta_estancia || "Foto del inmueble"}/><figcaption>{asset.etiqueta_estancia || "Fotografía original"}</figcaption></figure>)}</div>}
      </div>
    </section>
    <p className="warning">La API de esta versión no tiene inicio de sesión: utiliza únicamente fotografías y datos de prueba.</p>
  </>;
}
