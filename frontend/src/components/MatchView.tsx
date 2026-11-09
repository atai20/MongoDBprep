import { useState } from "react";
import { api } from "../api/client";
import type { CurrentMatch } from "../api/types";
import { StatusBadge } from "./StatusBadge";

type Props = {
  current: CurrentMatch | null;
  onChanged: () => Promise<void>;
};

export function MatchView({ current, onChanged }: Props) {
  const [error, setError] = useState<string | null>(null);

  if (!current) {
    return (
      <div className="panel">
        <h2>Current match</h2>
        <p>No active match.</p>
      </div>
    );
  }

  async function join() {
    if (!current?.game) return;
    try {
      await api.joinGame(current.game.game_id);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Join failed");
    }
  }

  async function leave() {
    if (!current?.game) return;
    try {
      await api.leaveGame(current.game.game_id);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Leave failed");
    }
  }

  return (
    <div className="panel">
      <h2>Current match</h2>
      <div className="stat">
        <span>Match</span>
        <StatusBadge value={current.match.status} />
      </div>
      <div className="stat">
        <span>Spread</span>
        <strong>{current.match.rating_spread}</strong>
      </div>
      <div className="stat">
        <span>Players</span>
        <strong>{current.players.map((p) => `${p.username} (${p.rating})`).join(" vs ")}</strong>
      </div>
      {current.game ? (
        <>
          <div className="stat">
            <span>Game</span>
            <StatusBadge value={current.game.status} />
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="primary" onClick={join}>
              Join assigned game
            </button>
            <button className="danger" onClick={leave}>
              Leave game
            </button>
            <button onClick={() => current.game && api.burstJoin(current.game.game_id, 8)}>
              Join 8x
            </button>
          </div>
        </>
      ) : null}
      <div className="error">{error}</div>
    </div>
  );
}
