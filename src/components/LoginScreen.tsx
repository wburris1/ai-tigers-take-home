import { useLoginForm } from "../hooks/useLoginForm";

type LoginScreenProps = {
  onLoginSuccess?: () => void;
};

export function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const {
    email,
    password,
    isSubmitting,
    onEmailChange,
    onPasswordChange,
    onSubmit,
  } = useLoginForm({ onLoginSuccess });

  return (
    <main>
      <h1>Log in</h1>
      <form onSubmit={onSubmit} noValidate>
        <div>
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={onEmailChange}
            disabled={isSubmitting}
          />
        </div>
        <div>
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={onPasswordChange}
            disabled={isSubmitting}
          />
        </div>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
