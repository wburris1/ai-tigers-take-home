import { useMutation } from "@tanstack/react-query";
import { setStoredToken } from "../../lib/session";

export type LoginCredentials = {
  email: string;
  password: string;
};

export type LoginResponse = {
  token: string;
  user?: { name: string; email: string };
};

async function loginRequest(
  credentials: LoginCredentials,
): Promise<LoginResponse> {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  const data = (await res.json()) as LoginResponse & { error?: string };
  if (!res.ok) {
    throw new Error(data.error ?? "Login failed");
  }
  if (!data.token) {
    throw new Error("Login failed");
  }
  return { token: data.token, user: data.user };
}

export type UseLoginOptions = {
  onLoginSuccess?: () => void;
};

export function useLogin(options: UseLoginOptions = {}) {
  const { onLoginSuccess } = options;

  return useMutation({
    mutationFn: loginRequest,
    onSuccess: (data) => {
      setStoredToken(data.token);
      onLoginSuccess?.();
    },
  });
}
