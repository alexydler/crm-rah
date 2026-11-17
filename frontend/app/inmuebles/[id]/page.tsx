"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, useEffect, useRef, useState } from "react";
import { formatMoney, type Inmueble, type MediaAsset } from "../../types";
import { ApiError, canEditInmueble, validatePhoto } from "../../lib/api";
import { useCrm } from "../../components/crm-provider";
import { ErrorScreen } from "../../components/error-screen";

export default function InmuebleDetail() {
  const { id } = useParams<{ id: string }>();
  const { api, organizacion, reportError } = useCrm();
  const canUpload = canEditInmueble(organizacion.rol);
  const [item, setItem] = useState<Inmueble | null>(null);
  const [media, setMedia] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [uploadError, setUploadError] = useState<unknown>(null);
  const request = useRef<AbortController | null>(null);
  const readVersion = useRef(0);
  const mediaVersion = useRef(0);
  const loadingProperty = useRef(false);
  const renewingMedia = useRef(false);
  const mediaRetries = useRef(0);
  const retryTimer = useRef<number | undefined>(undefined);

  async function load(signal: AbortSignal) {
    const version = ++readVersion.current;
    const photosVersion = ++mediaVersion.current;
    loadingProperty.current = true;
    setLoading(true); setItem(null); setMedia([]); setError(null);
    try {
      const [property, photos] = await Promise.all([
        api.getInmueble(organizacion.id, id, signal), api.getMedia(organizacion.id, id, signal),
      ]);
      if (!signal.aborted && version === readVersion.current) {
        setItem(property);
        if (photosVersion === mediaVersion.current) setMedia(photos);
        mediaRetries.current = 0;
        window.clearTimeout(retryTimer.current);
      }
    } catch (cause) { if (!signal.aborted && version === readVersion.current) { setError(cause); reportError(cause); } }
    finally { if (!signal.aborted && version === readVersion.current) { loadingProperty.current = false; setLoading(false); } }
  }
  async function refreshMedia(signal: AbortSignal) {
    if (signal.aborted || loadingProperty.current || renewingMedia.current) return;
    renewingMedia.current = true;
    const version = ++mediaVersion.current;
    setUploadError(null);
    try {
      const photos = await api.getMedia(organizacion.id, id, signal);
      if (!signal.aborted && version === mediaVersion.current) {
        setMedia(photos);
        mediaRetries.current = 0;
        window.clearTimeout(retryTimer.current);
      }
    } catch (cause) {
      if (signal.aborted || version !== mediaVersion.current) return;
      if (cause instanceof ApiError && [401, 403, 404].includes(cause.status)) { setItem(null); setMedia([]); setError(cause); }
      else setUploadError(cause);
      reportError(cause);
      if (cause instanceof ApiError && [0, 500, 502, 503, 504].includes(cause.status) && mediaRetries.current < 3) {
        mediaRetries.current++;
        window.clearTimeout(retryTimer.current);
        retryTimer.current = window.setTimeout(() => { void refreshMedia(signal); }, 15000);
      }
    } finally { renewingMedia.current = false; }
  }
  useEffect(() => {
    const controller = new AbortController();
    request.current = controller;
    void load(controller.signal);
    // Renovar antes de los 900 s; también al volver de una pestaña suspendida.
    const refresh = () => { void refreshMedia(controller.signal); };
    const timer = window.setInterval(refresh, 14 * 60 * 1000);
    window.addEventListener("focus", refresh);
    return () => { controller.abort(); window.clearInterval(timer); window.clearTimeout(retryTimer.current); window.removeEventListener("focus", refresh); };
  }, [api, organizacion.id, id]);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    if (!canUpload) { setError(new ApiError(403)); return; }
    const input = event.currentTarget;
    const file = input.files?.[0];
    const signal = request.current?.signal;
    if (!file || !signal || signal.aborted || uploading) return;
    setUploading(true); setUploadError(null);
    try {
      validatePhoto(file);
      await api.uploadMedia(organizacion.id, id, file, undefined, signal);
      if (!signal.aborted) await load(signal);
    } catch (cause) {
      if (!signal.aborted) {
        if (cause instanceof ApiError && [401, 403, 404].includes(cause.status)) { setItem(null); setMedia([]); setError(cause); }
        else setUploadError(cause);
        reportError(cause);
      }
    } finally { input.value = ""; if (!signal.aborted) setUploading(false); }
  }

  if (loading) return <p role="status">Cargando ficha…</p>;
  if (error || !item) return <ErrorScreen error={error || new ApiError(404)} retry={() => request.current && void load(request.current.signal)} />;
  return <>
    <Link href="/" className="back">← Volver a la cartera</Link>
    <div className="eyebrow">FICHA DEMO · {organizacion.nombre_comercial}</div>
    <div className="heading-row"><div><h1>{item.titulo}</h1><p className="subtitle">{item.zona} · {item.tipo} · {item.operacion}</p></div><span className="status">{item.estado}</span></div>
    <section className="detail-grid">
      <div className="panel"><h2>Características</h2><div className="detail-price">{formatMoney(item.precio, item.moneda)}</div>
        <dl className="spec-list"><div><dt>Operación</dt><dd>{item.operacion}</dd></div>
          {item.codigo_referencia && <div><dt>Referencia interna</dt><dd>{item.codigo_referencia}</dd></div>}
          {item.estado_ve && <div><dt>Estado</dt><dd>{item.estado_ve}</dd></div>}
          {item.municipio && <div><dt>Municipio</dt><dd>{item.municipio}</dd></div>}
          {item.parroquia && <div><dt>Parroquia</dt><dd>{item.parroquia}</dd></div>}
          {item.urbanizacion && <div><dt>Urbanización / sector</dt><dd>{item.urbanizacion}</dd></div>}
          {item.m2_construidos != null && <div><dt>Superficie construida</dt><dd>{item.m2_construidos} m²</dd></div>}
          {item.m2_parcela != null && <div><dt>Parcela</dt><dd>{item.m2_parcela} m²</dd></div>}
          {item.habitaciones != null && <div><dt>Habitaciones</dt><dd>{item.habitaciones}</dd></div>}
          {item.banos != null && <div><dt>Baños</dt><dd>{item.banos}</dd></div>}
        </dl>
        <p className="muted">{item.descripcion || "Sin descripción adicional."}</p>
      </div>
      <div className="panel"><div className="panel-top"><h2>Galería de fotografías</h2>
        {canUpload && <label className="button primary upload-button">{uploading ? "Subiendo…" : "+ Subir foto DEMO"}<input className="file-input" type="file" accept="image/jpeg,image/png,image/webp" aria-label="Subir fotografía ficticia" onChange={upload} disabled={uploading} /></label>}
      </div>
        <p className="muted small">Solo fotos ficticias · Originales intactos · JPG, PNG o WEBP · Máximo 12 MiB</p>
        {!!uploadError && <p className="error" role="alert">{uploadError instanceof Error ? uploadError.message : "No se pudo subir la fotografía."}</p>}
        {media.length === 0 ? <div className="empty-gallery">{canUpload ? "Todavía no hay fotos. Sube una imagen ficticia para probar la galería de esta inmobiliaria." : "Todavía no hay fotos para este inmueble."}</div> :
          <div className="gallery">{media.map(asset => <figure key={asset.id}><img src={asset.url_temporal} referrerPolicy="no-referrer" alt={asset.etiqueta_estancia || "Fotografía DEMO del inmueble"} onError={() => setUploadError(new Error("La imagen no está disponible o su enlace temporal expiró. Vuelve a cargar la ficha."))} /><figcaption>{asset.etiqueta_estancia || "Fotografía original DEMO"}</figcaption></figure>)}</div>}
        <button className="button" type="button" disabled={uploading} onClick={() => request.current && void refreshMedia(request.current.signal)}>Actualizar enlaces de fotos</button>
      </div>
    </section>
  </>;
}
