import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import type { Page, Role, User } from "../types";

export function UsersPage() {
  const [search, setSearch] = useState("");
  const [data, setData] = useState<Page<User> | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  function load(page = 1) {
    const params = new URLSearchParams({ page: String(page), page_size: "10" });
    if (search) params.set("search", search);
    api<Page<User>>(`/api/users?${params}`).then(setData).catch((caught) => setError(caught.message));
  }

  useEffect(() => { load(); }, []);

  async function toggle(user: User) {
    try {
      await api(`/api/users/${user.id}/status`, { method: "PATCH", body: JSON.stringify({ is_active: !user.is_active }) });
      setNotice(user.is_active ? "Usuario desactivado." : "Usuario activado.");
      load(data?.page || 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo cambiar el estado.");
    }
  }

  return (
    <>
      <div className="page-head"><h1>Usuarios</h1><Link className="btn" to="/admin/users/new">Nuevo usuario</Link></div>
      {notice && <div className="notice">{notice}</div>}
      {error && <div className="notice error">{error}</div>}
      <section className="card">
        <form className="toolbar" onSubmit={(event) => { event.preventDefault(); load(); }}>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por nombre o usuario" />
          <button className="btn secondary">Buscar</button>
        </form>
        <table>
          <thead><tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            {data?.items.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.full_name}</td>
                <td>{user.role_name}</td>
                <td><span className={user.is_active ? "badge" : "badge warn"}>{user.is_active ? "Activo" : "Inactivo"}</span></td>
                <td>
                  <Link to={`/admin/users/${user.id}`}>Editar</Link>{" "}
                  <button className="btn secondary" onClick={() => toggle(user)}>{user.is_active ? "Desactivar" : "Activar"}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

export function UserFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [roles, setRoles] = useState<Role[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ username: "", email: "", full_name: "", password: "", role_id: 0, is_active: true });

  useEffect(() => {
    api<Role[]>("/api/roles").then((rows) => {
      setRoles(rows);
      if (!id && rows[0]) setForm((current) => ({ ...current, role_id: rows[0].id }));
    });
    if (id) {
      api<Page<User>>("/api/users?page_size=100").then((page) => {
        const user = page.items.find((item) => item.id === Number(id));
        if (!user) return;
        setForm({ username: user.username, email: user.email, full_name: user.full_name, password: "", role_id: user.role_id, is_active: user.is_active });
      });
    }
  }, [id]);

  function update(field: string, value: string | number | boolean) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      if (id) {
        await api(`/api/users/${id}`, {
          method: "PUT",
          body: JSON.stringify({
            email: form.email,
            full_name: form.full_name,
            password: form.password || null,
            role_id: Number(form.role_id),
            is_active: form.is_active,
          }),
        });
      } else {
        await api("/api/users", { method: "POST", body: JSON.stringify({ ...form, role_id: Number(form.role_id) }) });
      }
      navigate("/admin/users");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo guardar.");
    }
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h1>{id ? "Editar usuario" : "Nuevo usuario"}</h1>
      {!id && <label>Usuario<input value={form.username} onChange={(event) => update("username", event.target.value)} required /></label>}
      <label>Nombre<input value={form.full_name} onChange={(event) => update("full_name", event.target.value)} required /></label>
      <label>Correo<input type="email" value={form.email} onChange={(event) => update("email", event.target.value)} required /></label>
      <label>Contraseña<input type="password" value={form.password} onChange={(event) => update("password", event.target.value)} required={!id} /></label>
      <label>Rol
        <select value={form.role_id} onChange={(event) => update("role_id", Number(event.target.value))}>
          {roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
        </select>
      </label>
      <label><span>Activo</span><input type="checkbox" checked={form.is_active} onChange={(event) => update("is_active", event.target.checked)} /></label>
      {error && <div className="notice error">{error}</div>}
      <button className="btn">Guardar</button>
    </form>
  );
}

export function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  useEffect(() => { api<Role[]>("/api/roles").then(setRoles).catch(() => setRoles([])); }, []);
  return (
    <>
      <h1>Roles y permisos</h1>
      {roles.map((role) => (
        <article className="card" key={role.id}>
          <h2>{role.name}</h2>
          <p className="muted">{role.description}</p>
          <p>{role.permissions.map((permission) => permission.name).join(" · ")}</p>
        </article>
      ))}
    </>
  );
}
