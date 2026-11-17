import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";
import type { Movement, Page, Product } from "../types";

export function InventoryPage() {
  const { can } = useAuth();
  const [data, setData] = useState<Page<Product> | null>(null);
  const [form, setForm] = useState({ product_id: 0, movement_type: "ENTRADA", quantity: 1, notes: "" });
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  function load() {
    api<Page<Product>>("/api/inventory?page_size=50").then((page) => {
      setData(page);
      if (page.items[0]) setForm((current) => ({ ...current, product_id: current.product_id || page.items[0].id }));
    }).catch((caught) => setError(caught.message));
  }
  useEffect(() => { load(); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/api/inventory/movements", { method: "POST", body: JSON.stringify(form) });
      setNotice("Movimiento registrado.");
      load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo registrar.");
    }
  }

  return (
    <>
      <div className="page-head"><h1>Inventario</h1><Link to="/inventory/movements">Ver historial</Link></div>
      {notice && <div className="notice">{notice}</div>}
      {error && <div className="notice error">{error}</div>}
      {can("inventory.write") && (
        <form className="card stack" onSubmit={submit}>
          <h2>Registrar movimiento</h2>
          <label>Producto
            <select value={form.product_id} onChange={(event) => setForm({ ...form, product_id: Number(event.target.value) })}>
              {data?.items.map((product) => <option key={product.id} value={product.id}>{product.sku} · {product.name}</option>)}
            </select>
          </label>
          <label>Tipo
            <select value={form.movement_type} onChange={(event) => setForm({ ...form, movement_type: event.target.value })}>
              <option value="ENTRADA">Entrada</option>
              <option value="SALIDA">Salida</option>
              <option value="AJUSTE">Ajuste al valor indicado</option>
            </select>
          </label>
          <label>Cantidad<input type="number" min={1} value={form.quantity} onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })} /></label>
          <label>Nota<input value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>
          <button className="btn">Registrar</button>
        </form>
      )}
      <section className="card">
        <table>
          <thead><tr><th>SKU</th><th>Producto</th><th>Existencia</th><th>Umbral</th></tr></thead>
          <tbody>
            {data?.items.map((product) => (
              <tr key={product.id}>
                <td>{product.sku}</td><td>{product.name}</td>
                <td><span className={product.quantity <= product.reorder_level ? "badge warn" : "badge"}>{product.quantity}</span></td>
                <td>{product.reorder_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

export function MovementsPage() {
  const [data, setData] = useState<Page<Movement> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Page<Movement>>("/api/inventory/movements?page_size=30").then(setData).catch((caught) => setError(caught.message));
  }, []);
  return (
    <section className="card">
      <h1>Historial de inventario</h1>
      {error && <div className="notice error">{error}</div>}
      <table>
        <thead><tr><th>Fecha</th><th>Producto</th><th>Tipo</th><th>Cantidad</th><th>Antes</th><th>Después</th><th>Origen</th></tr></thead>
        <tbody>
          {data?.items.map((row) => (
            <tr key={row.id}>
              <td>{new Date(row.created_at).toLocaleString("es-ES")}</td>
              <td>{row.sku}</td>
              <td>{row.movement_type}</td>
              <td>{row.quantity}</td>
              <td>{row.previous_quantity}</td>
              <td>{row.new_quantity}</td>
              <td>{row.reference_type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
