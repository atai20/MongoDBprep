import { FormEvent, useState } from "react";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("alice");
  const [password, setPassword] = useState("password123");
  const [rating, setRating] = useState("1200");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await login(username, password);
      else await register(username, password, Number(rating) || undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <div className="topbar">
        <div className="brand">
          Match<span>Arena</span>
        </div>
      </div>
      <div className="panel" style={{ maxWidth: 420 }}>
        <h1>{mode === "login" ? "Sign in" : "Create player"}</h1>
        <p>Use a seeded demo account or register a new one. Password for demo users is password123.</p>
        <form className="stack" onSubmit={onSubmit}>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
          />
          {mode === "register" ? (
            <input value={rating} onChange={(e) => setRating(e.target.value)} placeholder="rating" />
          ) : null}
          <div className="row">
            <button className="primary" disabled={busy} type="submit">
              {mode === "login" ? "Login" : "Register"}
            </button>
            <button
              type="button"
              className="ghost"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
            >
              {mode === "login" ? "Need an account?" : "Have an account?"}
            </button>
          </div>
          <div className="error">{error}</div>
        </form>
      </div>
    </div>
  );
}
