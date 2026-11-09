export type Player = {
  player_id: string;
  username: string;
  rating: number;
  status: string;
  created_at: string;
  updated_at: string;
  token?: string;
};

export type QueueEntry = {
  queue_id: string;
  player_id: string;
  rating: number;
  status: string;
  created_at: string;
  updated_at: string;
  match_id: string | null;
};

export type Match = {
  match_id: string;
  player_ids: string[];
  status: string;
  created_at: string;
  game_id: string;
  rating_spread: number;
};

export type Game = {
  game_id: string;
  match_id: string | null;
  player_ids: string[];
  capacity: number;
  status: string;
  created_at: string;
  host_id: string | null;
  name: string | null;
  slots_remaining: number;
};

export type QueueStatus = {
  state: string;
  wait_seconds: number | null;
  tolerance: number | null;
  window: { lower: number; upper: number } | null;
  entry: QueueEntry | null;
  match: Match | null;
};

export type PlayerProfile = {
  player: Player;
  recent_queue_entries: QueueEntry[];
  recent_matches: Match[];
};

export type CurrentMatch = {
  match: Match;
  game: Game | null;
  players: Player[];
};

export type ApiError = {
  error: string;
  message: string;
};
