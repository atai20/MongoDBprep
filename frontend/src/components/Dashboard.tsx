import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CurrentMatch, Game, QueueStatus } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { GameView } from "./GameView";
import { MatchView } from "./MatchView";
import { QueueControls } from "./QueueControls";
import { StatusBadge } from "./StatusBadge";

export function Dashboard() {
  const { profile, logout, refresh } = useAuth();
  const [queue, setQueue] = useState<QueueStatus | null>(null);
  const [current, setCurrent] = useState<CurrentMatch | null>(null);
  const [games, setGames] = useState<Game[]>([]);
  const [rating, setRating] = useState(String(profile?.player.rating ?? 1200));
  const [notice, setNotice] = useState("");

  async function reload() {
    const [status, lobbyList] = await Promise.all([api.queueStatus(), api.listGames(), refresh()]);
    setQueue(status);
    setGames(lobbyList.games);
    try {
      setCurrent(await api.currentMatch());
    } catch {
      setCurrent(null);
    }
  }

  useEffect(() => {
    void reload();
    const timer = window.setInterval(() => void reload(), 1500);
    return () => window.clearInterval(timer);
  }, []);

  if (!profile) return null;
  const player = profile.player;

  async function saveRating() {
    try {
      await api.updateRating(Number(rating));
      setNotice("Rating updated");
      await reload();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Update failed");
    }
  }

  return (
    <div className="shell">
      <div className="topbar">
        <div>
          <div className="brand">
            Match<span>Arena</span>
          </div>
          <div className="muted">
            {player.username} · {player.player_id.slice(0, 8)}
          </div>
        </div>
        <div className="row">
          <StatusBadge value={player.status} />
          <button onClick={() => void reload()}>Refresh</button>
          <button className="ghost" onClick={() => void logout()}>
            Logout
          </button>
        </div>
      </div>

      <div className="grid">
        <div className="stack">
          <div className="panel">
            <h2>Player</h2>
            <div className="stat">
              <span>Rating</span>
              <strong>{player.rating}</strong>
            </div>
            <div className="stat">
              <span>Status</span>
              <StatusBadge value={player.status} />
            </div>
            <div className="row" style={{ marginTop: 12 }}>
              <input value={rating} onChange={(e) => setRating(e.target.value)} />
              <button onClick={() => void saveRating()}>Set rating</button>
            </div>
            <p className="muted">{notice}</p>
          </div>
          <QueueControls status={queue} onChanged={reload} />
          <MatchView current={current} onChanged={reload} />
        </div>
        <GameView games={games} onChanged={reload} />
      </div>
    </div>
  );
}
