import { useCallback, useMemo, useState } from "react";
import { decodeJwtPayload } from "../lib/jwt";
import { clearStoredToken, getStoredToken } from "../lib/session";

export function useAuthSession() {
  const [token, setToken] = useState<string | null>(() => getStoredToken());

  const onLoginSuccess = useCallback(() => {
    setToken(getStoredToken());
  }, []);

  const onLogout = useCallback(() => {
    clearStoredToken();
    setToken(null);
  }, []);

  const displayName = useMemo(() => {
    if (!token) {
      return "User";
    }
    return decodeJwtPayload(token)?.name ?? "User";
  }, [token]);

  return {
    isAuthenticated: Boolean(token),
    displayName,
    onLoginSuccess,
    onLogout,
  };
}
