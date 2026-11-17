import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";
import type { User } from "../types";

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  can: (...codes: string[]) => boolean;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem("erp_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api<User>("/api/auth/me")
      .then(setUser)
      .catch(() => sessionStorage.removeItem("erp_token"))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      async login(username: string, password: string) {
        const result = await api<{ access_token: string; user: User }>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        sessionStorage.setItem("erp_token", result.access_token);
        setUser(result.user);
      },
      logout() {
        sessionStorage.removeItem("erp_token");
        setUser(null);
      },
      can(...codes: string[]) {
        if (!user) return false;
        return codes.some((code) => user.permissions.includes(code));
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("AuthProvider no está disponible.");
  return context;
}
