import { LoginScreen } from "./components/LoginScreen";
import { useAuthSession } from "./hooks/useAuthSession";

function App() {
  const { isAuthenticated, displayName, onLoginSuccess, onLogout } =
    useAuthSession();

  if (!isAuthenticated) {
    return <LoginScreen onLoginSuccess={onLoginSuccess} />;
  }

  return (
    <main>
      <p>Signed in as {displayName}</p>
      <button type="button" onClick={onLogout}>
        Log out
      </button>
    </main>
  );
}

export default App;
