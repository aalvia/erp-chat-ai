import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { api, money } from "../services/api";
import type { Category, Page, Product } from "../types";

export function ProductsPage() {
  const [search, setSearch] = useState("");
  const [data, setData] = useState<Page<Product> | null>(null);
  const [error, setError] = useState("");
  function load() {
    const params = new URLSearchParams({ page_size: "20", include_inactive: "true" });
    if (search) params.set("search", search);
    api<Page<Product>>(`/api/products?${params}`).then(setData).catch((caught) => setError(caught.message));
  }
  useEffect(() => { load(); }, []);
  return (
    <>
      <div className="page-head"><h1>Productos</h1><Link className="btn" to="/products/new">Nuevo producto</Link></div>
      {error && <div className="notice error">{error}</div>}
      <section className="card">
        <form className="toolbar" onSubmit={(event) => { event.preventDefault(); load(); }}>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nombre o SKU" />
          <button className="btn secondary">Buscar</button>
        </form>
        <table>
          <thead><tr><th>SKU</th><th>Nombre</th><th>Categoría</th><th>Precio</th><th>Stock</th><th></th></tr></thead>
          <tbody>
            {data?.items.map((product) => (
              <tr key={product.id}>
                <td>{product.sku}</td>
                <td>{product.name}</td>
                <td>{product.category_name}</td>
                <td>{money(product.sale_price)}</td>
                <td><span className={product.quantity <= product.reorder_level ? "badge warn" : "badge"}>{product.quantity}</span></td>
                <td><Link to={`/products/${product.id}`}>Editar</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

export function ProductFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { can } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ sku: "", name: "", description: "", category_id: 0, sale_price: "1", cost: "0", initial_quantity: 0, is_active: true });

  useEffect(() => {
    api<Category[]>("/api/products/categories").then((rows) => {
      setCategories(rows);
      if (!id && rows[0]) setForm((current) => ({ ...current, category_id: rows[0].id }));
    });
    if (id) {
      api<Page<Product>>("/api/products?page_size=100&include_inactive=true").then((page) => {
        const product = page.items.find((item) => item.id === Number(id));
        if (!product) return;
        setForm({
          sku: product.sku,
          name: product.name,
          description: product.description,
          category_id: product.category_id,
          sale_price: String(product.sale_price),
          cost: String(product.cost),
          initial_quantity: product.quantity,
          is_active: product.is_active,
        });
      });
    }
  }, [id]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!can("products.write")) {
      setError("No tienes permiso para modificar productos.");
      return;
    }
    const payload = { ...form, category_id: Number(form.category_id), sale_price: form.sale_price, cost: form.cost };
    try {
      if (id) await api(`/api/products/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      else await api("/api/products", { method: "POST", body: JSON.stringify(payload) });
      navigate("/products");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo guardar.");
    }
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h1>{id ? "Editar producto" : "Nuevo producto"}</h1>
      <label>SKU<input value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} required /></label>
      <label>Nombre<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
      <label>Descripción<input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <label>Categoría
        <select value={form.category_id} onChange={(event) => setForm({ ...form, category_id: Number(event.target.value) })}>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
      </label>
      <label>Precio de venta<input value={form.sale_price} onChange={(event) => setForm({ ...form, sale_price: event.target.value })} required /></label>
      <label>Costo<input value={form.cost} onChange={(event) => setForm({ ...form, cost: event.target.value })} required /></label>
      {!id && <label>Existencia inicial<input type="number" min={0} value={form.initial_quantity} onChange={(event) => setForm({ ...form, initial_quantity: Number(event.target.value) })} /></label>}
      <label><span>Activo</span><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} /></label>
      {error && <div className="notice error">{error}</div>}
      <button className="btn">Guardar</button>
    </form>
  );
}
