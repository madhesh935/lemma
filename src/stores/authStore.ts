/**
 * AEGIS-OS Auth Store — Zustand
 * Manages authentication state globally.
 */
import { create } from "zustand";
import type { AuthUser } from "@/types/lemma";
import { lemmaAuth, setAccessToken, clearTokens } from "@/lib/lemma/index";

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setTokens: (access: string, refresh: string, user: AuthUser) => void;
  clearError: () => void;
}

const STORAGE_KEY = "aegis_auth";

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const resp = await lemmaAuth.login(email, password);
      setAccessToken(resp.access_token);
      // Persist tokens
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        access: resp.access_token,
        refresh: resp.refresh_token,
        user: resp.user,
      }));
      set({
        user: resp.user,
        accessToken: resp.access_token,
        refreshToken: resp.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (e) {
      set({ isLoading: false, error: (e as Error).message });
      throw e;
    }
  },

  logout: () => {
    clearTokens();
    sessionStorage.removeItem(STORAGE_KEY);
    set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
  },

  setTokens: (access, refresh, user) => {
    setAccessToken(access);
    set({ accessToken: access, refreshToken: refresh, user, isAuthenticated: true });
  },

  clearError: () => set({ error: null }),
}));

// ─── Restore session on page load ─────────────────────────────────────────────
const stored = sessionStorage.getItem(STORAGE_KEY);
if (stored) {
  try {
    const { access, refresh, user } = JSON.parse(stored);
    setAccessToken(access);
    useAuthStore.setState({ accessToken: access, refreshToken: refresh, user, isAuthenticated: true });
  } catch {}
}
