# MatchArena API

All JSON. Authenticated routes expect `Authorization: Bearer <token>`.

## Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | no | `{username, password, rating?}` |
| POST | `/api/auth/login` | no | `{username, password}` |
| POST | `/api/auth/logout` | optional | revoke current token |

Register and login return the player fields plus `token`.

## Player

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/me` | yes | profile, recent queue entries, recent matches |
| PATCH | `/api/me/rating` | yes | `{rating}` |

## Matchmaking

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/matchmaking/queue` | yes | enter matchmaking |
| DELETE | `/api/matchmaking/queue` | yes | cancel matchmaking |
| GET | `/api/matchmaking/status` | yes | queue state, wait, tolerance, window |
| GET | `/api/matchmaking/current` | yes | current match, assigned game, opponents |

Queue statuses: `waiting`, `reserved`, `matched`, `cancelled`.

## Games

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/games/` | no | open lobbies |
| POST | `/api/games/` | yes | `{name, capacity}` create lobby and join it |
| GET | `/api/games/{game_id}` | no | game document |
| POST | `/api/games/{game_id}/join` | yes | join lobby or assigned match game |
| POST | `/api/games/{game_id}/leave` | yes | leave game |

Matched games can only be joined by the players listed on the match.

## Health and ops

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | process liveness |
| GET | `/api/health/ready` | MongoDB and Redis ping |
| GET | `/api/ops/indexes` | `list_indexes()` for core collections |
| GET | `/api/ops/queue/stats` | queue counts by status |
| GET | `/api/ops/queue/explain` | `explain("executionStats")` for waiting-player queries |
| GET | `/api/ops/workers` | Redis worker heartbeats |

`GET /api/ops/queue/explain` accepts `lower`, `upper`, `exclude_player_id`, `limit`.

## Errors

```json
{ "error": "conflict", "message": "..." }
```

Common codes: `unauthorized`, `validation_failed`, `not_found`, `conflict`, `already_matched`, `not_queued`, `game_full`.
