import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, money } from "../../services/api";
import type { AssistantReply } from "../../types";

const ALLOWED = new Set([
  "/",
  "/admin/users",
  "/admin/users/new",
  "/admin/roles",
  "/customers",
  "/customers/new",
  "/products",
  "/products/new",
  "/inventory",
  "/inventory/movements",
  "/sales",
  "/sales/new",
  "/audit",
  "/settings",
]);

type ChatItem = { role: "user" | "assistant"; text: string; reply?: AssistantReply };

function sessionId() {
  const key = "erp_chat_session";
  const current = sessionStorage.getItem(key);
  if (current) return current;
  const created = crypto.randomUUID();
  sessionStorage.setItem(key, created);
  return created;
}

function safeRoute(route?: string | null) {
  if (!route) return null;
  if (ALLOWED.has(route)) return route;
  if (/^\/(customers|products|sales|admin\/users)\/\d+$/.test(route)) return route;
  return null;
}

function DataView({ data }: { data: Record<string, unknown> }) {
  const items = Array.isArray(data.items) ? (data.items as Record<string, unknown>[]) : null;
  const series = Array.isArray(data.ventas_por_mes) ? (data.ventas_por_mes as Record<string, unknown>[]) : null;
  return (
    <div>
      {typeof data.cantidad === "number" && typeof data.importe === "number" && (
        <p><strong>{String(data.cantidad)}</strong> · {money(Number(data.importe))}</p>
      )}
      {items && items.length > 0 && (
        <table className="mini-table">
          <tbody>
            {items.slice(0, 6).map((item, index) => (
              <tr key={index}>
                <td>{String(item.producto || item.nombre || item.cliente || item.usuario || item.numero || "")}</td>
                <td>{String(item.cantidad ?? item.unidades ?? item.importe ?? item.total ?? item.rol ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {series && series.length > 0 && (
        <div style={{ height: 160 }}>
          <ResponsiveContainer>
            <BarChart data={series}>
              <XAxis dataKey="mes" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="importe" fill="#1f6fbf" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export function AssistantPanel() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [items, setItems] = useState<ChatItem[]>([]);

  async function send(event?: FormEvent) {
    event?.preventDefault();
    const message = text.trim();
    if (!message || busy) return;
    setText("");
    setItems((current) => [...current, { role: "user", text: message }]);
    setBusy(true);
    try {
      const reply = await api<AssistantReply>("/api/assistant/chat", {
        method: "POST",
        body: JSON.stringify({ message, session_id: sessionId() }),
      });
      setItems((current) => [...current, { role: "assistant", text: reply.message, reply }]);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : "No se pudo consultar el asistente.";
      setItems((current) => [...current, { role: "assistant", text: messageText }]);
    } finally {
      setBusy(false);
    }
  }

  async function confirm(token: string) {
    setBusy(true);
    try {
      const reply = await api<AssistantReply>("/api/assistant/confirm", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setItems((current) => [...current, { role: "assistant", text: reply.message, reply }]);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : "No se pudo confirmar.";
      setItems((current) => [...current, { role: "assistant", text: messageText }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button className="chat-toggle" onClick={() => setOpen((value) => !value)} aria-label="Abrir asistente">IA</button>
      {open && (
        <section className="chat-panel" aria-label="ERP AI ASSISTANT">
          <div className="chat-head">
            <strong>ERP AI ASSISTANT</strong>
            <div className="muted" style={{ color: "#d5e2f2" }}>Consultas sobre este ERP</div>
          </div>
          <div className="chat-log">
            {items.length === 0 && <p className="muted">Pregunta dónde está una pantalla, cómo se usa o cuánto se vendió.</p>}
            {items.map((item, index) => (
              <article key={index} className={item.role === "user" ? "bubble user" : "bubble"}>
                <div>{item.text}</div>
                {item.reply?.data && <DataView data={item.reply.data} />}
                {item.reply?.actions?.map((action) => {
                  const route = safeRoute(action.route);
                  if (action.type === "NAVIGATE" && route) {
                    return (
                      <button key={action.label} className="btn" style={{ marginTop: 8 }} onClick={() => navigate(route)}>
                        {action.label}
                      </button>
                    );
                  }
                  if (action.type === "CONFIRM" && action.confirmation_token) {
                    return (
                      <button key={action.confirmation_token} className="btn green" style={{ marginTop: 8 }} onClick={() => confirm(action.confirmation_token!)}>
                        {action.label}
                      </button>
                    );
                  }
                  return null;
                })}
                {item.reply?.sources?.length ? (
                  <div className="sources">
                    {item.reply.sources.map((source) => (
                      <p key={source.title}><strong>{source.title}.</strong> {source.excerpt.slice(0, 180)}</p>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
            {busy && <p className="muted">Consultando...</p>}
          </div>
          <form className="chat-form" onSubmit={send}>
            <input value={text} onChange={(event) => setText(event.target.value)} placeholder="Escribe tu pregunta" aria-label="Mensaje para el asistente" />
            <button className="btn" disabled={busy}>Enviar</button>
          </form>
        </section>
      )}
    </>
  );
}
