import { HomeScreen } from "./components/HomeScreen";
import { LoginScreen } from "./components/LoginScreen";
import { useAuthSession } from "./hooks/useAuthSession";

function App() {
  const { isAuthenticated, displayName, onLoginSuccess, onLogout } =
    useAuthSession();

  if (!isAuthenticated) {
    return <LoginScreen onLoginSuccess={onLoginSuccess} />;
  }

  return <HomeScreen displayName={displayName} onLogout={onLogout} />;
}

export default App;
