import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, money } from "../services/api";
import type { Customer, Page, Product, Sale } from "../types";

export function SalesPage() {
  const [data, setData] = useState<Page<Sale> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Page<Sale>>("/api/sales?page_size=20").then(setData).catch((caught) => setError(caught.message));
  }, []);
  return (
    <>
      <div className="page-head"><h1>Ventas</h1><Link className="btn" to="/sales/new">Nueva venta</Link></div>
      {error && <div className="notice error">{error}</div>}
      <section className="card">
        <table>
          <thead><tr><th>Número</th><th>Fecha</th><th>Cliente</th><th>Responsable</th><th>Estado</th><th>Total</th></tr></thead>
          <tbody>
            {data?.items.map((sale) => (
              <tr key={sale.id}>
                <td><Link to={`/sales/${sale.id}`}>{sale.number}</Link></td>
                <td>{sale.sale_date}</td>
                <td>{sale.customer_name}</td>
                <td>{sale.user_name}</td>
                <td><span className={sale.status === "CONFIRMADA" ? "badge" : "badge warn"}>{sale.status}</span></td>
                <td>{money(sale.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

export function SaleFormPage() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [customerId, setCustomerId] = useState(0);
  const [saleDate, setSaleDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [lines, setLines] = useState<{ product_id: number; quantity: number }[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<Page<Customer>>("/api/customers?page_size=100"),
      api<Page<Product>>("/api/products?page_size=100"),
    ]).then(([customerPage, productPage]) => {
      setCustomers(customerPage.items);
      setProducts(productPage.items);
      if (customerPage.items[0]) setCustomerId(customerPage.items[0].id);
    }).catch((caught) => setError(caught.message));
  }, []);

  function addLine() {
    if (!products[0]) return;
    setLines((current) => [...current, { product_id: products[0].id, quantity: 1 }]);
  }

  const total = lines.reduce((sum, line) => {
    const product = products.find((item) => item.id === line.product_id);
    return sum + (product ? product.sale_price * line.quantity : 0);
  }, 0);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const sale = await api<Sale>("/api/sales", {
        method: "POST",
        body: JSON.stringify({ customer_id: customerId, sale_date: saleDate, notes, items: lines }),
      });
      navigate(`/sales/${sale.id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo registrar la venta.");
    }
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h1>Nueva venta</h1>
      <label>Cliente
        <select value={customerId} onChange={(event) => setCustomerId(Number(event.target.value))}>
          {customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}
        </select>
      </label>
      <label>Fecha<input type="date" value={saleDate} onChange={(event) => setSaleDate(event.target.value)} /></label>
      {lines.map((line, index) => (
        <div className="toolbar" key={index}>
          <select value={line.product_id} onChange={(event) => setLines(lines.map((item, itemIndex) => itemIndex === index ? { ...item, product_id: Number(event.target.value) } : item))}>
            {products.map((product) => <option key={product.id} value={product.id}>{product.name} · stock {product.quantity} · {money(product.sale_price)}</option>)}
          </select>
          <input type="number" min={1} value={line.quantity} onChange={(event) => setLines(lines.map((item, itemIndex) => itemIndex === index ? { ...item, quantity: Number(event.target.value) } : item))} />
        </div>
      ))}
      <button type="button" className="btn secondary" onClick={addLine}>Agregar producto</button>
      <strong>Total estimado {money(total)}</strong>
      <label>Notas<input value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
      {error && <div className="notice error">{error}</div>}
      <button className="btn" disabled={lines.length === 0}>Confirmar venta</button>
    </form>
  );
}

export function SaleDetailPage() {
  const { id } = useParams();
  const [sale, setSale] = useState<Sale | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function load() {
    api<Sale>(`/api/sales/${id}`).then(setSale).catch((caught) => setError(caught.message));
  }
  useEffect(() => { load(); }, [id]);

  async function cancel() {
    try {
      const updated = await api<Sale>(`/api/sales/${id}/cancel`, { method: "POST" });
      setSale(updated);
      setNotice("Venta anulada y existencias devueltas.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo anular.");
    }
  }

  if (!sale) return error ? <div className="notice error">{error}</div> : <p>Cargando...</p>;
  return (
    <section className="card">
      <div className="page-head">
        <h1>{sale.number}</h1>
        {sale.status === "CONFIRMADA" && <button className="btn secondary" onClick={cancel}>Anular</button>}
      </div>
      {notice && <div className="notice">{notice}</div>}
      {error && <div className="notice error">{error}</div>}
      <p>{sale.customer_name} · {sale.sale_date} · {sale.user_name} · {sale.status}</p>
      <table>
        <thead><tr><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Subtotal</th></tr></thead>
        <tbody>
          {sale.details.map((detail) => (
            <tr key={detail.id}><td>{detail.product_name}</td><td>{detail.quantity}</td><td>{money(detail.unit_price)}</td><td>{money(detail.line_total)}</td></tr>
          ))}
        </tbody>
      </table>
      <p>Subtotal {money(sale.subtotal)} · Impuesto {sale.tax_rate}% ({money(sale.tax_amount)}) · <strong>Total {money(sale.total)}</strong></p>
    </section>
  );
}
