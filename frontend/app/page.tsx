"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { API_URL, formatMoney, Inmueble, Tipo } from "./types";

type FormState = { titulo: string; tipo: Tipo; operacion: "venta" | "alquiler"; precio: string; moneda: "USD" | "VES"; zona: string; estado_ve: string; municipio: string; parroquia: string; urbanizacion: string; codigo_referencia: string; m2_construidos: string; m2_parcela: string; habitaciones: string; banos: string };
const initialForm: FormState = { titulo: "", tipo: "apartamento", operacion: "venta", precio: "", moneda: "USD", zona: "", estado_ve: "", municipio: "", parroquia: "", urbanizacion: "", codigo_referencia: "", m2_construidos: "", m2_parcela: "", habitaciones: "", banos: "" };

export default function Home() {
  const [items, setItems] = useState<Inmueble[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<FormState>(initialForm);
  const [filter, setFilter] = useState("todos");

  async function load() {
    setLoading(true); setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/inmuebles`, { cache: "no-store" });
      if (!response.ok) throw new Error(`La API devolvió ${response.status}`);
      setItems((await response.json()) as Inmueble[]);
    } catch (e) { setError(e instanceof Error ? e.message : "No se pudo cargar el listado"); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm(previous => ({ ...previous, [key]: value }));
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError("");
    const optionalNumber = (value: string) => value.trim() === "" ? null : Number(value);
    try {
      const payload = {
        titulo: form.titulo.trim(), tipo: form.tipo, operacion: form.operacion,
        precio: form.precio, moneda: form.moneda, zona: form.zona.trim(),
        estado_ve: form.estado_ve.trim() || null, municipio: form.municipio.trim() || null,
        parroquia: form.parroquia.trim() || null, urbanizacion: form.urbanizacion.trim() || null,
        codigo_referencia: form.codigo_referencia.trim() || null,
        m2_construidos: optionalNumber(form.m2_construidos), m2_parcela: optionalNumber(form.m2_parcela),
        habitaciones: form.tipo === "terreno" ? null : optionalNumber(form.habitaciones), banos: form.tipo === "terreno" ? null : optionalNumber(form.banos),
        estado: "borrador",
      };
      const response = await fetch(`${API_URL}/api/v1/inmuebles`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(`Error al guardar (${response.status}). Revisa los campos.`);
      setForm(initialForm); setShowForm(false); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "No se pudo guardar"); }
    finally { setSaving(false); }
  }

  const filtered = items.filter(item => filter === "todos" || item.tipo === filter);
  const demoCount = items.filter(item => item.titulo.startsWith("DEMO")).length;

  return (
    <>
      <div className="eyebrow">CENTRO DE OPERACIONES</div>
      <div className="heading-row">
        <div><h1>Tu cartera inmobiliaria</h1><p className="subtitle">Cartera inmobiliaria para Venezuela · USD / VES · fotografías originales.</p></div>
        <button className="button primary" type="button" onClick={() => setShowForm(v => !v)}>{showForm ? "Cerrar formulario" : "+ Nuevo inmueble"}</button>
      </div>
      <section className="stats">
        <div className="stat"><div className="stat-label">Inmuebles registrados</div><div className="stat-number">{loading ? "—" : items.length}</div></div>
        <div className="stat"><div className="stat-label">Borradores</div><div className="stat-number">{loading ? "—" : items.filter(i => i.estado === "borrador").length}</div></div>
        <div className="stat"><div className="stat-label">Registros DEMO</div><div className="stat-number">{loading ? "—" : demoCount}</div></div>
      </section>
      {error && <p className="error" role="alert">{error} — Comprueba que Docker y FastAPI estén funcionando.</p>}
      {showForm && <section className="panel form-panel">
        <h2>Nuevo inmueble</h2><p className="muted">Solo datos ficticios por ahora. Los campos no aplicables pueden quedar vacíos.</p>
        <form onSubmit={save} className="form-grid">
          <label className="field span-two">Título<input value={form.titulo} onChange={e => setField("titulo", e.target.value)} required minLength={3} maxLength={180} placeholder="Ejemplo: Apartamento con vista en Caracas" /></label>
          <label className="field">Tipo<select value={form.tipo} onChange={e => setField("tipo", e.target.value as Tipo)}><option value="apartamento">Apartamento</option><option value="casa">Casa</option><option value="quinta">Quinta</option><option value="townhouse">Townhouse</option><option value="local">Local</option><option value="oficina">Oficina</option><option value="galpon">Galpón</option><option value="terreno">Terreno</option></select></label>
          <label className="field">Operación<select value={form.operacion} onChange={e => setField("operacion", e.target.value as "venta" | "alquiler")}><option value="venta">Venta</option><option value="alquiler">Alquiler</option></select></label>
          <label className="field">Precio<input type="number" min="0" step="0.01" required value={form.precio} onChange={e => setField("precio", e.target.value)} /></label>
          <label className="field">Moneda<select value={form.moneda} onChange={e => setField("moneda", e.target.value as "USD" | "VES")}><option value="USD">USD — dólares</option><option value="VES">VES — bolívares</option></select></label>
          <label className="field">Estado venezolano<input value={form.estado_ve} maxLength={100} onChange={e => setField("estado_ve",e.target.value)} placeholder="Ej.: Miranda" /></label>
          <label className="field">Municipio<input value={form.municipio} maxLength={100} onChange={e => setField("municipio",e.target.value)} placeholder="Ej.: Baruta" /></label>
          <label className="field">Parroquia<input value={form.parroquia} maxLength={100} onChange={e => setField("parroquia",e.target.value)} /></label>
          <label className="field">Urbanización / sector<input value={form.urbanizacion} maxLength={120} onChange={e => setField("urbanizacion",e.target.value)} /></label>
          <label className="field">Referencia interna<input value={form.codigo_referencia} maxLength={80} onChange={e => setField("codigo_referencia",e.target.value)} placeholder="Código propio, no oficial" /></label>
          <label className="field">Zona<input value={form.zona} required minLength={2} onChange={e => setField("zona", e.target.value)} placeholder="Ciudad / zona ficticia" /></label>
          <label className="field">m² construidos<input type="number" min="0" value={form.m2_construidos} onChange={e => setField("m2_construidos", e.target.value)} /></label>
          <label className="field">m² parcela<input type="number" min="0" value={form.m2_parcela} onChange={e => setField("m2_parcela", e.target.value)} /></label>
          {form.tipo !== "terreno" && <><label className="field">Habitaciones<input type="number" min="0" value={form.habitaciones} onChange={e => setField("habitaciones", e.target.value)} /></label><label className="field">Baños<input type="number" min="0" value={form.banos} onChange={e => setField("banos", e.target.value)} /></label></>}
          <div className="span-two actions"><button className="button primary" type="submit" disabled={saving}>{saving ? "Guardando…" : "Guardar inmueble"}</button></div>
        </form>
      </section>}
      <section className="panel">
        <div className="panel-top"><h2>Inmuebles</h2><label className="filter">Filtrar <select value={filter} onChange={e => setFilter(e.target.value)}><option value="todos">Todos</option><option value="apartamento">Apartamentos</option><option value="casa">Casas</option><option value="quinta">Quintas</option><option value="townhouse">Townhouses</option><option value="local">Locales</option><option value="oficina">Oficinas</option><option value="galpon">Galpones</option><option value="terreno">Terrenos</option></select></label></div>
        {loading ? <p className="muted">Cargando…</p> : filtered.length === 0 ? <p className="muted">No hay inmuebles para este filtro.</p> : (
          <div className="property-list">{filtered.map(item => <Link className="property" href={`/inmuebles/${item.id}`} key={item.id}>
            <div className="property-picture">{item.tipo === "terreno" ? "◫" : "⌂"}</div>
            <div className="property-main"><div className="property-title">{item.titulo}</div><div className="muted small">{item.zona} · {item.tipo} · {item.operacion}</div></div>
            <div className="property-right"><strong>{formatMoney(item.precio, item.moneda)}</strong><span className="status">{item.estado}</span></div>
          </Link>)}</div>
        )}
      </section>
    </>
  );
}
