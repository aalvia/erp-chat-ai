import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, money } from "../services/api";
import type { Dashboard } from "../types";

export function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Dashboard>("/api/dashboard").then(setData).catch((caught) => setError(caught.message));
  }, []);

  if (error) return <div className="notice error">{error}</div>;
  if (!data) return <p>Cargando indicadores...</p>;

  return (
    <>
      <div className="page-head">
        <h1>Tablero</h1>
        <span className="muted">{data.alcance === "propias" ? "Tus ventas" : "Toda la empresa"}</span>
      </div>
      <section className="kpis">
        <article className="card kpi"><span>Ventas</span><strong>{money(data.total_ventas)}</strong></article>
        <article className="card kpi"><span>Cantidad</span><strong>{data.cantidad_ventas}</strong></article>
        <article className="card kpi"><span>Productos</span><strong>{data.productos}</strong></article>
        <article className="card kpi"><span>Clientes</span><strong>{data.clientes}</strong></article>
        <article className="card kpi"><span>Stock bajo</span><strong>{data.bajo_inventario}</strong></article>
      </section>
      <section className="grid-2">
        <article className="card">
          <h2>Evolución de ventas</h2>
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={data.ventas_por_mes}>
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="importe" fill="#1f6fbf" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
        <article className="card">
          <h2>Productos más vendidos</h2>
          <table>
            <thead><tr><th>Producto</th><th>Unidades</th><th>Importe</th></tr></thead>
            <tbody>
              {data.productos_mas_vendidos.map((item) => (
                <tr key={item.sku}><td>{item.producto}</td><td>{item.unidades}</td><td>{money(item.importe)}</td></tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>
    </>
  );
}
