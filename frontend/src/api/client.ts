import type {
  CurrentMatch,
  Game,
  Player,
  PlayerProfile,
  QueueEntry,
  QueueStatus,
} from "./types";

const TOKEN_KEY = "matcharena.token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...init, headers });
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = body.message || body.error || response.statusText;
    throw new Error(message);
  }
  return body as T;
}

export const api = {
  register(username: string, password: string, rating?: number) {
    return request<Player>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, rating: rating || undefined }),
    });
  },
  login(username: string, password: string) {
    return request<Player>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },
  logout() {
    return request<void>("/api/auth/logout", { method: "POST" });
  },
  me() {
    return request<PlayerProfile>("/api/me");
  },
  updateRating(rating: number) {
    return request<Player>("/api/me/rating", {
      method: "PATCH",
      body: JSON.stringify({ rating }),
    });
  },
  enqueue() {
    return request<{ created: boolean; entry: QueueEntry }>("/api/matchmaking/queue", {
      method: "POST",
    });
  },
  cancelQueue() {
    return request<{ entry: QueueEntry }>("/api/matchmaking/queue", { method: "DELETE" });
  },
  queueStatus() {
    return request<QueueStatus>("/api/matchmaking/status");
  },
  currentMatch() {
    return request<CurrentMatch>("/api/matchmaking/current");
  },
  listGames() {
    return request<{ games: Game[] }>("/api/games/");
  },
  createLobby(name: string, capacity: number) {
    return request<Game>("/api/games/", {
      method: "POST",
      body: JSON.stringify({ name, capacity }),
    });
  },
  joinGame(gameId: string) {
    return request<Game>(`/api/games/${gameId}/join`, { method: "POST" });
  },
  leaveGame(gameId: string) {
    return request<Game>(`/api/games/${gameId}/leave`, { method: "POST" });
  },
  burstEnqueue(times: number) {
    return Promise.allSettled(Array.from({ length: times }, () => api.enqueue()));
  },
  burstJoin(gameId: string, times: number) {
    return Promise.allSettled(Array.from({ length: times }, () => api.joinGame(gameId)));
  },
};
