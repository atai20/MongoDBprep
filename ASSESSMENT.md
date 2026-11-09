# MatchArena assessment tickets

Work one ticket at a time. Stay inside the 75-minute window in `INTERVIEW_PROTOCOL.md`.

Do not treat the frontend as optional: it is the easiest way to reproduce player behavior, including repeated clicks and parallel requests.

---

## Ticket 1 — Duplicate matchmaking entries

**Time limit:** 75 minutes

### Reported symptoms

During busy periods, the same player sometimes appears more than once in the matchmaking queue. Support has seen this after clients retry, after players mash "Find match", and when two tabs submit at the same time.

Cancellation still appears to work when the player only has one entry. Rejoining after a clean cancel is a required flow.

### Reproduction

1. Register or log in.
2. Click **Find match**.
3. Click **Send 10 requests** (or issue ten concurrent `POST /api/matchmaking/queue` calls).
4. Inspect queue documents for that `player_id` with status `waiting` or `reserved`.
5. Cancel and rejoin sequentially, then repeat the burst.

Relevant endpoints:

- `POST /api/matchmaking/queue`
- `DELETE /api/matchmaking/queue`
- `GET /api/matchmaking/status`

### Acceptance criteria

- A player cannot have multiple active queue entries.
- Repeated requests do not create duplicate entries.
- Simultaneous requests are handled safely.
- Cancellation and rejoining still work.

Suggested tests: `pytest -m "acceptance and concurrency"` focusing on queue entry counts in MongoDB, not only HTTP 200s.

---

## Ticket 2 — Duplicate matches under load

**Time limit:** 75 minutes

### Reported symptoms

Some players are assigned to more than one match. This shows up when more than one matchmaking worker is running, or when a worker is slow and another process picks up the same waiting players.

Players can end up with two `pending`/`active` match documents. Queue entries and player status may not agree.

### Reproduction

1. Queue two compatible mid-range players (for example ratings 1500 and 1520).
2. Run two worker cycles against the same waiting queue (`python -m matcharena.workers --threads 2 --once`, or two processes).
3. Inspect `matches` for those player IDs.
4. Retry with a worker that is interrupted or delayed while pairing.

Relevant endpoints / processes:

- `POST /api/matchmaking/queue`
- `GET /api/matchmaking/current`
- `python -m matcharena.workers`
- `GET /api/ops/workers`

### Acceptance criteria

- A player cannot be matched twice.
- Multiple workers can safely process the queue.
- Failed worker operations do not leave players in an invalid state.

---

## Ticket 3 — ELO matchmaking failures

**Time limit:** 75 minutes

### Reported symptoms

Players at the extreme ends of the rating range wait indefinitely even when a compatible opponent is already queued. Ordinary mid-ladder pairings still work.

Reports also mention exact rating-window edges and players who have been waiting for different amounts of time.

### Reproduction

1. Queue two players rated 100 and 120. Run a worker cycle.
2. Queue two players rated 3000 and 2980. Run a worker cycle.
3. Queue 1000 and 1050 (exact base-window edge) immediately.
4. Queue 1000, wait 60 seconds, then queue 1080. Run a worker cycle.
5. Compare with a known-good mid-range pair such as 1200 and 1230.

Relevant endpoints / modules:

- `POST /api/matchmaking/queue`
- `GET /api/matchmaking/status`
- worker pairing path
- rating window / tolerance rules in README

### Acceptance criteria

- The lowest and highest valid ratings are supported.
- Tolerance expands correctly over time.
- Boundary conditions work.
- Existing mid-range matchmaking behavior is preserved.

---

## Ticket 4 — Slow matchmaking under high traffic

**Time limit:** 75 minutes

### Reported symptoms

Queue processing gets slower as more players enter matchmaking. A seeded environment with thousands of queue documents makes this obvious. Pairing results for small queues still look normal; the complaint is cost, not the happy-path pairing of two nearby ratings.

### Reproduction

1. Run `python -m matcharena.scripts.seed` if the queue is small.
2. Inspect how waiting players are selected and how candidate opponents are queried.
3. Compare that with the indexes actually present on `queue_entries`.
4. Use `explain("executionStats")` (the ops route can help) and compare documents examined versus documents returned.

Relevant endpoints:

- `GET /api/ops/indexes`
- `GET /api/ops/queue/stats`
- `GET /api/ops/queue/explain`
- worker candidate selection

### Acceptance criteria

- Identify the expensive query.
- Evaluate the existing MongoDB indexes.
- Improve the relevant query performance.
- Preserve correct matchmaking results.

---

## Ticket 5 — Duplicate game joins and cancellation conflicts

**Time limit:** 75 minutes

### Reported symptoms

Players sometimes appear twice in `game.player_ids`. Open lobbies can exceed `capacity` when two clients join the last slot together.

Separately, a player who cancels matchmaking while a worker is pairing them may still be placed in a match, or a queue entry may be `cancelled` while a match document still lists them.

### Reproduction

1. Create a lobby with capacity 2 and one occupant. Join from two players at the same time (or use **Join 6x**).
2. Join the same game repeatedly from one player as fast as possible.
3. Queue two compatible players. Cancel one of them while a worker cycle is pairing. Inspect queue, match, and player status.

Relevant endpoints:

- `POST /api/games/`
- `POST /api/games/{game_id}/join`
- `POST /api/games/{game_id}/leave`
- `DELETE /api/matchmaking/queue`
- worker reserve / match creation

### Acceptance criteria

- No duplicate game membership.
- Game capacity is respected.
- Cancellation and matchmaking transitions remain consistent.
- Repeated requests are safe.
