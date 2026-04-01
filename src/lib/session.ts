import { isJwtExpired } from "./jwt";

const TOKEN_KEY = "auth_token";

const authExpiredListeners = new Set<() => void>();

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Returns the stored token, or null if missing or JWT `exp` is in the past.
 * Clears storage when the token is expired.
 */
export function getValidStoredToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    return null;
  }
  if (isJwtExpired(token)) {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
  return token;
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function onAuthExpired(listener: () => void): () => void {
  authExpiredListeners.add(listener);
  return () => {
    authExpiredListeners.delete(listener);
  };
}

/** Clears the token and notifies subscribers (e.g. reset React auth state). */
export function invalidateSession(): void {
  clearStoredToken();
  for (const listener of authExpiredListeners) {
    listener();
  }
}
