import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { api, authToken } from "../api/client";
import type { User } from "../api/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authToken.get()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((currentUser) => {
        if (currentUser.role === "admin") setUser(currentUser);
        else authToken.clear();
      })
      .catch(() => authToken.clear())
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email: string, password: string) => {
        const response = await api.login(email, password);
        if (response.user.role !== "admin") {
          throw new Error("login.adminOnly");
        }
        authToken.set(response.access_token);
        setUser(response.user);
      },
      logout: () => {
        authToken.clear();
        setUser(null);
      }
    }),
    [loading, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
