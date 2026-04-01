import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { HomeScreen } from "./components/HomeScreen";
import { LoginScreen } from "./components/LoginScreen";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuthSession } from "./hooks/useAuthSession";

function App() {
  const { isAuthenticated, displayName, onLoginSuccess, onLogout } =
    useAuthSession();
  const navigate = useNavigate();

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/" replace />
          ) : (
            <LoginScreen
              onLoginSuccess={() => {
                onLoginSuccess();
                navigate("/", { replace: true });
              }}
            />
          )
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <HomeScreen
              displayName={displayName}
              onLogout={() => {
                onLogout();
                navigate("/login", { replace: true });
              }}
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="*"
        element={
          <Navigate to={isAuthenticated ? "/" : "/login"} replace />
        }
      />
    </Routes>
  );
}

export default App;
