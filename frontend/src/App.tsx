import { Dashboard } from "./components/Dashboard";
import { LoginPage } from "./components/LoginPage";
import { useAuth } from "./auth/AuthContext";

export default function App() {
  const { profile, loading } = useAuth();
  if (loading) {
    return (
      <div className="shell">
        <div className="brand">
          Match<span>Arena</span>
        </div>
        <p>Loading session…</p>
      </div>
    );
  }
  return profile ? <Dashboard /> : <LoginPage />;
}
