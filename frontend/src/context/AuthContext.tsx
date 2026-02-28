"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authApi } from "@/lib/api";
import { saveAuth, clearAuth, getStoredUser, isAuthenticated } from "@/lib/auth";
import type { User, LoginRequest } from "@/lib/types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      clearAuth();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated()) {
      fetchMe();
    } else {
      setLoading(false);
    }
  }, [fetchMe]);

  const login = async (data: LoginRequest) => {
    const token = await authApi.login(data);
    saveAuth(token);
    const me = await authApi.me();
    setUser(me);
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAdmin: user?.rol === "admin",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
