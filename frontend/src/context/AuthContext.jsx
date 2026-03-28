"use client";
import { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

const AuthContext = createContext(null);
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const stored = localStorage.getItem("user");
    if (token && stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    const data = res.data;
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setUser(data.user);
    if (data.user.role === "boss") router.push("/dashboard/boss");
    else router.push("/dashboard/employee");
  };

  const signup = async (name, email, password, role) => {
  const res = await axios.post(`${API}/auth/register`, {
    full_name: name,
    email,
    password,
    role,
  });
  const loginRes = await axios.post(`${API}/auth/login`, { email, password });
  const loginData = loginRes.data;
  localStorage.setItem("token", loginData.access_token);
  localStorage.setItem("user", JSON.stringify(loginData.user));
  setUser(loginData.user);
  if (loginData.user.role === "boss") router.push("/dashboard/boss");
  else router.push("/dashboard/employee");
};

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    router.push("/");
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
};
