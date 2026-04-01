import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { decodeJwtPayload } from "../lib/jwt";
import {
  clearStoredToken,
  getValidStoredToken,
  onAuthExpired,
} from "../lib/session";

export function useAuthSession() {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() =>
    getValidStoredToken(),
  );

  useEffect(() => {
    return onAuthExpired(() => {
      setToken(null);
      queryClient.clear();
    });
  }, [queryClient]);

  const onLoginSuccess = useCallback(() => {
    setToken(getValidStoredToken());
  }, []);

  const onLogout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    queryClient.clear();
  }, [queryClient]);

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
