import { createContext, useContext, useState, useEffect } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("let_token");
    if (token) {
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      api.get("/auth/me")
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem("let_token");
          delete api.defaults.headers.common["Authorization"];
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function login(email, password) {
    const res = await api.post("/auth/login", { email, password });
    const { user, token } = res.data;
    localStorage.setItem("let_token", token);
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    setUser(user);
    return user;
  }

  async function register(email, name, password) {
    const res = await api.post("/auth/register", { email, name, password });
    const { user, token } = res.data;
    localStorage.setItem("let_token", token);
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    setUser(user);
    return user;
  }

  function logout() {
    localStorage.removeItem("let_token");
    delete api.defaults.headers.common["Authorization"];
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
