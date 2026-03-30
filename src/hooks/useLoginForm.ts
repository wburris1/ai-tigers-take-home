import {
  FormEvent,
  useCallback,
  useState,
  type ChangeEvent,
} from "react";
import { useLogin } from "./api/useLogin";

type UseLoginFormOptions = {
  onLoginSuccess?: () => void;
};

export function useLoginForm(options: UseLoginFormOptions = {}) {
  const { onLoginSuccess } = options;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const { mutate, isPending } = useLogin({ onLoginSuccess });

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
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      mutate(
        { email, password },
        {
          onError: (error) => {
            alert(
              error instanceof Error ? error.message : "Network error",
            );
          },
        },
      );
    },
    [email, password, mutate],
  );

  return {
    email,
    password,
    isSubmitting: isPending,
    onEmailChange,
    onPasswordChange,
    onSubmit,
  };
}
