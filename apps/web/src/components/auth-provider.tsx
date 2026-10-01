"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, type Me } from "@/lib/api";

type AuthState = { me: Me | null; loading: boolean; refresh: () => Promise<Me | null>; logout: () => Promise<void> };
const Ctx = createContext<AuthState>({ me: null, loading: true, refresh: async () => null, logout: async () => {} });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    try {
      const m = await api<Me>("/me");
      setMe(m);
      return m;
    } catch {
      try {
        await api("/auth/refresh", { method: "POST" });
        const m = await api<Me>("/me");
        setMe(m);
        return m;
      } catch {
        setMe(null);
        return null;
      }
    } finally {
      setLoading(false);
    }
  }, []);
  const logout = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } finally {
      setMe(null);
    }
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);
  const value = useMemo(() => ({ me, loading, refresh, logout }), [me, loading, refresh, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);
