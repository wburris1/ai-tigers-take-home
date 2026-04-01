import {
  useCallback,
  useState,
  type ChangeEvent,
  type SubmitEvent,
} from "react";
import { useLogin } from "./api/useLogin";

type UseLoginFormOptions = {
  onLoginSuccess?: () => void;
};

const VALID_EMAIL = "example@helloconstellation.com";
const VALID_PASSWORD = "ConstellationInterview123!";

export function useLoginForm(options: UseLoginFormOptions = {}) {
  const { onLoginSuccess } = options;
  const [email, setEmail] = useState(VALID_EMAIL);
  const [password, setPassword] = useState(VALID_PASSWORD);

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
    (event: SubmitEvent<HTMLFormElement>) => {
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
