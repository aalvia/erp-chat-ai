import { useEffect, useState, type FormEvent } from "react";
import { api } from "../services/api";
import type { Page } from "../types";

type AuditRow = {
  id: number;
  user_name: string | null;
  action: string;
  tool_name: string | null;
  result_status: string;
  message: string;
  created_at: string;
};

type Settings = { company_name: string; currency: string; tax_rate: number; low_stock_threshold: number };

export function AuditPage() {
  const [data, setData] = useState<Page<AuditRow> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Page<AuditRow>>("/api/audit?page_size=30").then(setData).catch((caught) => setError(caught.message));
  }, []);
  return (
    <section className="card">
      <h1>Auditoría</h1>
      {error && <div className="notice error">{error}</div>}
      <table>
        <thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Estado</th><th>Detalle</th></tr></thead>
        <tbody>
          {data?.items.map((row) => (
            <tr key={row.id}>
              <td>{new Date(row.created_at).toLocaleString("es-ES")}</td>
              <td>{row.user_name}</td>
              <td>{row.tool_name || row.action}</td>
              <td>{row.result_status}</td>
              <td>{row.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export function SettingsPage() {
  const [form, setForm] = useState<Settings | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { api<Settings>("/api/settings").then(setForm).catch((caught) => setError(caught.message)); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!form) return;
    try {
      const updated = await api<Settings>("/api/settings", { method: "PUT", body: JSON.stringify(form) });
      setForm(updated);
      setNotice("Configuración guardada. El impuesto se aplicará a las ventas nuevas.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo guardar.");
    }
  }

  if (!form) return error ? <div className="notice error">{error}</div> : <p>Cargando...</p>;
  return (
    <form className="card stack" onSubmit={submit}>
      <h1>Configuración</h1>
      <p className="muted">Moneda de demostración: {form.currency}. El impuesto por defecto es 0 y se puede cambiar aquí.</p>
      {notice && <div className="notice">{notice}</div>}
      {error && <div className="notice error">{error}</div>}
      <label>Empresa<input value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} /></label>
      <label>Impuesto (%)<input type="number" min={0} max={100} step="0.01" value={form.tax_rate} onChange={(event) => setForm({ ...form, tax_rate: Number(event.target.value) })} /></label>
      <label>Umbral de stock bajo<input type="number" min={0} value={form.low_stock_threshold} onChange={(event) => setForm({ ...form, low_stock_threshold: Number(event.target.value) })} /></label>
      <button className="btn">Guardar</button>
    </form>
  );
}
