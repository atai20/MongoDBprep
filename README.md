# MatchArena

MatchArena is a small multiplayer matchmaking service. Players register, join an ELO-based queue, get paired into a match, and enter a game lobby.

This repository is meant to be inherited like a production codebase: trace a request across the frontend, API, services, MongoDB/Redis, and the background worker, then change a narrow slice of behavior.

## Stack

- Python 3.11, FastAPI, PyMongo, redis-py
- MongoDB 7 (source of truth for players, queue entries, matches, games)
- Redis 7 (worker coordination and heartbeats)
- React + TypeScript + Vite
- pytest
- Docker Compose

## Quick start

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

Seed demo players and a large queue (once):

```bash
docker compose exec backend python -m matcharena.scripts.seed
```

Demo logins (password `password123`): `alice` 1200, `bob` 1220, `carol` 100, `dave` 3000, `erin` 2400, `frank` 2420, `gina` 1000, `hugo` 1080.

## Local development

```bash
docker compose up -d mongo redis
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m matcharena.scripts.init_db
uvicorn matcharena.main:create_app --factory --reload --port 8000
```

Worker (separate terminal):

```bash
cd backend
python -m matcharena.workers
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Tests

Run from `backend/`:

```bash
pytest -m baseline
pytest -m acceptance
pytest
```

Baseline tests describe behavior that already holds. Acceptance tests encode open ticket criteria.

MongoDB and Redis must be running. Tests use database `matcharena_test` and Redis DB 15.

## Repository map

See [REPOSITORY_MAP.md](REPOSITORY_MAP.md) and [API.md](API.md).

Interview tickets live in [ASSESSMENT.md](ASSESSMENT.md). Timeboxing and explanation format: [INTERVIEW_PROTOCOL.md](INTERVIEW_PROTOCOL.md). After a fix: [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md).

## Matchmaking rules

- Initial rating window: ±50
- Window grows by 50 every 10 seconds waited
- Maximum window: ±500
- Valid ratings: 100–3000
- A player should have at most one active queue entry (`waiting` or `reserved`)
- A player should appear in a given game at most once
- Game `player_ids` length must never exceed `capacity`
