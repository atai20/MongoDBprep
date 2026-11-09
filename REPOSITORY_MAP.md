# Repository map

Requests are not handled in a single file. Start from the route and walk inward.

## Frontend

```
frontend/src/components/QueueControls.tsx
        → frontend/src/api/client.ts
        → POST /api/matchmaking/queue
```

Other UI surfaces:

- `LoginPage.tsx` — register / login
- `Dashboard.tsx` — player snapshot, polling
- `QueueControls.tsx` — enqueue, cancel, burst requests
- `MatchView.tsx` — current match, join/leave assigned game
- `GameView.tsx` — open lobbies
- `auth/AuthContext.tsx` — session token

## HTTP API

```
backend/matcharena/api/app.py
backend/matcharena/api/routes/*.py
backend/matcharena/api/deps.py
backend/matcharena/validation/schemas.py
backend/matcharena/api/serializers.py
```

## Services

```
AuthService            backend/matcharena/services/auth_service.py
PlayerService          backend/matcharena/services/player_service.py
MatchmakingService     backend/matcharena/services/matchmaking_service.py
GameService            backend/matcharena/services/game_service.py
```

## Persistence and coordination

```
Mongo client           backend/matcharena/db/mongo.py
Index setup            backend/matcharena/db/indexes.py
PlayerRepository       backend/matcharena/db/repositories/players.py
QueueRepository        backend/matcharena/db/repositories/queue.py
MatchRepository        backend/matcharena/db/repositories/matches.py
GameRepository         backend/matcharena/db/repositories/games.py
Redis client           backend/matcharena/coordination/redis_client.py
Locks                  backend/matcharena/coordination/lock.py
```

## Background matchmaking

```
python -m matcharena.workers
        → MatchmakingWorker.run_forever
        → run_once / run_cycle
        → ELO window + candidate query
        → reserve queue entries
        → insert match + game
```

Worker entry: `backend/matcharena/workers/__main__.py`
Pairing math: `backend/matcharena/domain/elo.py`

## Typical traces

Enqueue:

`QueueControls` → `api.enqueue` → `POST /api/matchmaking/queue` → `MatchmakingService.enqueue` → `QueueRepository` / `PlayerRepository`

Worker pairing:

`MatchmakingWorker.run_cycle` → `QueueRepository.list_waiting` → `elo.rating_window` → `QueueRepository.find_candidates` → `elo.choose_opponent` → `reserve` → match/game inserts

Join game:

`GameView` / `MatchView` → `POST /api/games/{id}/join` → `GameService.join` → `GameRepository.add_player`

## Ops endpoints

Useful while investigating, not part of the player UI:

- `GET /api/ops/indexes`
- `GET /api/ops/queue/stats`
- `GET /api/ops/queue/explain`
- `GET /api/ops/workers`
- `GET /api/health/ready`
