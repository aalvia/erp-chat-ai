import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export function LoginPage() {
  const { user, login } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo iniciar sesión.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card stack" onSubmit={submit}>
        <div>
          <h1>Intelligent ERP</h1>
          <p className="muted">Horizonte Distribución. Ingresa con tu usuario local.</p>
        </div>
        <label>Usuario<input value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
        <label>Contraseña<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        {error && <div className="notice error">{error}</div>}
        <button className="btn" disabled={busy}>{busy ? "Ingresando..." : "Ingresar"}</button>
      </form>
    </div>
  );
}
