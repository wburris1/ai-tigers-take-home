import {
  FormEvent,
  useCallback,
  useState,
  type ChangeEvent,
} from "react";
import { setStoredToken } from "../lib/session";

const EMAIL = "example@helloconstellation.com";
const PASSWORD = "ConstellationInterview123!";

type UseLoginFormOptions = {
  onLoginSuccess?: () => void;
};

export function useLoginForm(options: UseLoginFormOptions = {}) {
  const { onLoginSuccess } = options;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onEmailChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setEmail(event.target.value);
    },
    [],
  );

  const onPasswordChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setPassword(event.target.value);
    },
    [],
  );

  const onSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (email !== EMAIL || password !== PASSWORD) {
        alert("Invalid email or password");
        return;
      }
      setIsSubmitting(true);
      try {
        const res = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = (await res.json()) as {
          token?: string;
          error?: string;
        };
        if (!res.ok) {
          alert(data.error ?? "Login failed");
          return;
        }
        if (!data.token) {
          alert("Login failed");
          return;
        }
        setStoredToken(data.token);
        onLoginSuccess?.();
      } catch {
        alert("Network error");
      } finally {
        setIsSubmitting(false);
      }
    },
    [email, password, onLoginSuccess],
  );

  return {
    email,
    password,
    isSubmitting,
    onEmailChange,
    onPasswordChange,
    onSubmit,
  };
}
