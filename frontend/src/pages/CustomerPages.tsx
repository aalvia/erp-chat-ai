import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, money } from "../services/api";
import type { Customer, Page, Sale } from "../types";

const empty = { identification: "", name: "", email: "", phone: "", address: "", is_active: true };

export function CustomersPage() {
  const [search, setSearch] = useState("");
  const [data, setData] = useState<Page<Customer> | null>(null);
  const [error, setError] = useState("");

  function load() {
    const params = new URLSearchParams({ page_size: "20", include_inactive: "true" });
    if (search) params.set("search", search);
    api<Page<Customer>>(`/api/customers?${params}`).then(setData).catch((caught) => setError(caught.message));
  }
  useEffect(() => { load(); }, []);

  return (
    <>
      <div className="page-head"><h1>Clientes</h1><Link className="btn" to="/customers/new">Nuevo cliente</Link></div>
      {error && <div className="notice error">{error}</div>}
      <section className="card">
        <form className="toolbar" onSubmit={(event) => { event.preventDefault(); load(); }}>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nombre o identificación" />
          <button className="btn secondary">Buscar</button>
        </form>
        <table>
          <thead><tr><th>Identificación</th><th>Nombre</th><th>Correo</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            {data?.items.map((customer) => (
              <tr key={customer.id}>
                <td>{customer.identification}</td>
                <td>{customer.name}</td>
                <td>{customer.email}</td>
                <td><span className={customer.is_active ? "badge" : "badge warn"}>{customer.is_active ? "Activo" : "Inactivo"}</span></td>
                <td><Link to={`/customers/${customer.id}`}>Ver</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

export function CustomerFormPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/api/customers", { method: "POST", body: JSON.stringify(form) });
      navigate("/customers");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo guardar.");
    }
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h1>Nuevo cliente</h1>
      <label>Identificación<input value={form.identification} onChange={(event) => setForm({ ...form, identification: event.target.value })} required /></label>
      <label>Nombre<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
      <label>Correo<input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
      <label>Teléfono<input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label>
      <label>Dirección<input value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} /></label>
      {error && <div className="notice error">{error}</div>}
      <button className="btn">Guardar</button>
    </form>
  );
}

export function CustomerDetailPage() {
  const { id } = useParams();
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [sales, setSales] = useState<Sale[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api<Customer>(`/api/customers/${id}`).then(setCustomer).catch((caught) => setError(caught.message));
    api<Page<Sale>>(`/api/customers/${id}/purchases`).then((page) => setSales(page.items)).catch(() => setSales([]));
  }, [id]);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!customer) return;
    try {
      const updated = await api<Customer>(`/api/customers/${id}`, { method: "PUT", body: JSON.stringify(customer) });
      setCustomer(updated);
      setNotice("Cliente actualizado.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo actualizar.");
    }
  }

  if (!customer) return error ? <div className="notice error">{error}</div> : <p>Cargando...</p>;
  return (
    <div className="grid-2">
      <form className="card stack" onSubmit={save}>
        <h1>{customer.name}</h1>
        {notice && <div className="notice">{notice}</div>}
        {error && <div className="notice error">{error}</div>}
        <label>Identificación<input value={customer.identification} onChange={(event) => setCustomer({ ...customer, identification: event.target.value })} /></label>
        <label>Nombre<input value={customer.name} onChange={(event) => setCustomer({ ...customer, name: event.target.value })} /></label>
        <label>Correo<input value={customer.email || ""} onChange={(event) => setCustomer({ ...customer, email: event.target.value })} /></label>
        <label>Teléfono<input value={customer.phone || ""} onChange={(event) => setCustomer({ ...customer, phone: event.target.value })} /></label>
        <label>Dirección<input value={customer.address || ""} onChange={(event) => setCustomer({ ...customer, address: event.target.value })} /></label>
        <label><span>Activo</span><input type="checkbox" checked={customer.is_active} onChange={(event) => setCustomer({ ...customer, is_active: event.target.checked })} /></label>
        <button className="btn">Guardar cambios</button>
      </form>
      <section className="card">
        <h2>Historial de compras</h2>
        <table>
          <thead><tr><th>Número</th><th>Fecha</th><th>Total</th></tr></thead>
          <tbody>
            {sales.map((sale) => (
              <tr key={sale.id}><td><Link to={`/sales/${sale.id}`}>{sale.number}</Link></td><td>{sale.sale_date}</td><td>{money(sale.total)}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
