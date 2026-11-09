import { useState } from "react";
import { api } from "../api/client";
import type { QueueStatus } from "../api/types";
import { StatusBadge } from "./StatusBadge";

type Props = {
  status: QueueStatus | null;
  onChanged: () => Promise<void>;
};

export function QueueControls({ status, onChanged }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [burstResult, setBurstResult] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function burst() {
    setBusy(true);
    setError(null);
    try {
      const results = await api.burstEnqueue(10);
      const fulfilled = results.filter((r) => r.status === "fulfilled").length;
      const rejected = results.length - fulfilled;
      setBurstResult(`10 parallel queue requests: ${fulfilled} ok, ${rejected} failed`);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Burst failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>Matchmaking</h2>
      <div className="stat">
        <span>Queue state</span>
        <StatusBadge value={status?.state ?? "unknown"} />
      </div>
      <div className="stat">
        <span>Wait</span>
        <strong>{status?.wait_seconds ?? 0}s</strong>
      </div>
      <div className="stat">
        <span>Tolerance</span>
        <strong>{status?.tolerance ?? "—"}</strong>
      </div>
      <div className="stat">
        <span>Window</span>
        <strong>
          {status?.window ? `${status.window.lower}–${status.window.upper}` : "—"}
        </strong>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <button className="primary" disabled={busy} onClick={() => run(() => api.enqueue())}>
          Find match
        </button>
        <button className="danger" disabled={busy} onClick={() => run(() => api.cancelQueue())}>
          Cancel
        </button>
        <button disabled={busy} onClick={burst}>
          Send 10 requests
        </button>
      </div>
      <p className="muted">{burstResult}</p>
      <div className="error">{error}</div>
    </div>
  );
}
