import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { AssistantPanel } from "../chat/AssistantPanel";

const LINKS = [
  { to: "/", label: "Tablero", any: ["dashboard.read"] },
  { to: "/admin/users", label: "Usuarios", any: ["users.read"] },
  { to: "/admin/roles", label: "Roles", any: ["roles.read"] },
  { to: "/customers", label: "Clientes", any: ["customers.read"] },
  { to: "/products", label: "Productos", any: ["products.read"] },
  { to: "/inventory", label: "Inventario", any: ["inventory.read"] },
  { to: "/sales", label: "Ventas", any: ["sales.read_own", "sales.read_all", "sales.create"] },
  { to: "/audit", label: "Auditoría", any: ["audit.read"] },
  { to: "/settings", label: "Configuración", any: ["settings.write"] },
];

export function AppLayout() {
  const { user, logout, can } = useAuth();
  const [open, setOpen] = useState(false);
  return (
    <div className="shell">
      <aside className={open ? "sidebar open" : "sidebar"}>
        <div className="brand">INTELLIGENT ERP</div>
        <nav className="nav">
          {LINKS.filter((link) => can(...link.any)).map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === "/"} onClick={() => setOpen(false)}>
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setOpen((value) => !value)}>Menú</button>
          <strong>Horizonte Distribución</strong>
          <div>
            {user?.full_name} · {user?.role_name}{" "}
            <button className="btn secondary" onClick={logout}>Salir</button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
      <AssistantPanel />
    </div>
  );
}
