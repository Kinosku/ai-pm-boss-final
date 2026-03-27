"use client";
import { createContext, useContext, useState, useEffect } from "react";
import { api } from "@/services/api";
import { useRouter } from "next/navigation";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Hydrate from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    const stored = localStorage.getItem("user");
    if (token && stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setUser(data.user);
    // Role-based redirect
    if (data.user.role === "boss") router.push("/dashboard/boss");
    else router.push("/dashboard/employee");
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    router.push("/");
  };

  const isBoss     = user?.role === "boss";
  const isEmployee = user?.role === "employee";

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, isBoss, isEmployee }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
};
