import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, login as apiLogin } from "./api";
import type { User } from "./types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  // Only "loading" if there is a stored token we still need to validate.
  const [loading, setLoading] = useState(() => !!localStorage.getItem("pms_token"));

  useEffect(() => {
    if (!localStorage.getItem("pms_token")) return;

    api
      .get<User>("/users/me")
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("pms_token");
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const result = await apiLogin(email, password);
    localStorage.setItem("pms_token", result.access_token);
    const me = await api.get<User>("/users/me");
    setUser(me);
    return me;
  }

  function logout() {
    localStorage.removeItem("pms_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
