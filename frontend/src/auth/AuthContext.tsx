import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { AUTH_EXPIRED_EVENT, authApi, authStorage } from "../lib/authClient";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  uid: string | null;
  email: string | null;
  name: string | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readState(): Omit<AuthState, "isLoading"> {
  return {
    isAuthenticated: Boolean(authStorage.idToken),
    uid: authStorage.uid,
    email: authStorage.email,
    name: authStorage.name,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ ...readState(), isLoading: true });

  useEffect(() => {
    const handleExpired = () => setState((s) => ({ ...s, ...readState(), name: null }));
    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired);
  }, []);

  // Xác thực token hiện có (nếu có) bằng cách gọi /auth/me khi app khởi động,
  // để phát hiện token đã hết hạn/không hợp lệ trước khi render dashboard.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!authStorage.idToken) {
        setState((s) => ({ ...s, isLoading: false }));
        return;
      }
      try {
        const me = await authApi.me();
        const resolvedName = me.name ?? me.profile?.name ?? authStorage.name ?? null;
        if (resolvedName) {
          authStorage.saveName(resolvedName);
        }
        if (!cancelled) {
          setState({ ...readState(), isLoading: false, name: resolvedName });
        }
      } catch {
        if (!cancelled) setState({ ...readState(), isLoading: false });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email, password);
    authStorage.save(tokens);
    authStorage.saveEmail(email);

    let resolvedName: string | null = null;
    try {
      const me = await authApi.me();
      resolvedName = me.name ?? me.profile?.name ?? null;
      if (resolvedName) {
        authStorage.saveName(resolvedName);
      }
    } catch {
      // ignore
    }

    setState({ ...readState(), isLoading: false, name: resolvedName });
  }, []);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    const tokens = await authApi.register(email, password, name);
    authStorage.save(tokens);
    authStorage.saveEmail(email);
    if (name) {
      authStorage.saveName(name);
    }
    setState({ ...readState(), isLoading: false, name: name ?? null });
  }, []);

  const logout = useCallback(() => {
    authStorage.clear();
    setState({ ...readState(), isLoading: false, name: null });
  }, []);

  return <AuthContext.Provider value={{ ...state, login, register, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải dùng bên trong AuthProvider");
  return ctx;
}
