import { FormEvent, useState } from "react";
import { api } from "../api/client";
import type { Game } from "../api/types";
import { StatusBadge } from "./StatusBadge";

type Props = {
  games: Game[];
  onChanged: () => Promise<void>;
};

export function GameView({ games, onChanged }: Props) {
  const [name, setName] = useState("Custom Lobby");
  const [capacity, setCapacity] = useState("4");
  const [error, setError] = useState<string | null>(null);

  async function createLobby(event: FormEvent) {
    event.preventDefault();
    try {
      await api.createLobby(name, Number(capacity));
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function join(gameId: string) {
    try {
      await api.joinGame(gameId);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Join failed");
    }
  }

  return (
    <div className="panel">
      <h2>Open lobbies</h2>
      <form className="row" onSubmit={createLobby}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="lobby name" />
        <input
          value={capacity}
          onChange={(e) => setCapacity(e.target.value)}
          placeholder="capacity"
          style={{ flex: "0 0 90px" }}
        />
        <button className="primary" type="submit">
          Create
        </button>
      </form>
      <div style={{ marginTop: 12 }}>
        {games.length === 0 ? <p>No open lobbies.</p> : null}
        {games.map((game) => (
          <div className="game-card" key={game.game_id}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <strong>{game.name || "Unnamed"}</strong>
              <StatusBadge value={game.status} />
            </div>
            <p className="muted">
              {game.player_ids.length}/{game.capacity} players
            </p>
            <div className="row">
              <button onClick={() => join(game.game_id)}>Join</button>
              <button onClick={() => api.burstJoin(game.game_id, 6)}>Join 6x</button>
            </div>
          </div>
        ))}
      </div>
      <div className="error">{error}</div>
    </div>
  );
}
