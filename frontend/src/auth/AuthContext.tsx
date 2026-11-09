import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, storeToken } from "../api/client";
import type { Player, PlayerProfile } from "../api/types";

type AuthState = {
  profile: PlayerProfile | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, rating?: number) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setProfile(await api.me());
      setError(null);
    } catch {
      storeToken(null);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const acceptAuth = async (player: Player) => {
    if (!player.token) throw new Error("Missing session token");
    storeToken(player.token);
    await refresh();
  };

  const value = useMemo<AuthState>(
    () => ({
      profile,
      loading,
      error,
      async login(username, password) {
        setError(null);
        await acceptAuth(await api.login(username, password));
      },
      async register(username, password, rating) {
        setError(null);
        await acceptAuth(await api.register(username, password, rating));
      },
      async logout() {
        try {
          await api.logout();
        } finally {
          storeToken(null);
          setProfile(null);
        }
      },
      refresh,
    }),
    [profile, loading, error],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
