# Private answer key

Internal only. Do not copy this into candidate tickets, README, or code comments.

## Bug A — Duplicate active queue entries

**Tickets:** 1

**Where:** `MatchmakingService.enqueue` in `backend/matcharena/services/matchmaking_service.py`; `QueueRepository.insert` / `find_active_for_player` in `backend/matcharena/db/repositories/queue.py`; indexes in `backend/matcharena/db/indexes.py`.

**Root cause:** Check-then-insert. The service reads for an active row, then later inserts. Concurrent requests all observe "not queued". There is no unique partial index on `player_id` for active statuses, and insert is not a conditional upsert.

**Reproduce:** Register a player. Set `before_insert` to a 10-party barrier (or click **Send 10 requests** while the API is slow). Count `queue_entries` with that `player_id` and status in `waiting`/`reserved`. Expect more than one.

**Correct fix (smallest):** Unique partial index, e.g. unique `(player_id)` with `partialFilterExpression` on `status ∈ {waiting, reserved}`. Catch `DuplicateKeyError` and return the existing row. Optionally replace insert with `findOneAndUpdate` upsert that only creates when no active row exists.

**Alternatives:** Redis lock per player (still need the index). Transaction with snapshot read. Idempotency key from the client (does not save two tabs).

**Concepts:** read-then-write races, unique partial indexes, upsert, idempotency.

**Tests:** `test_ten_simultaneous_enqueue_calls_leave_one_active_entry` starts red, should go green. Sequential enqueue baseline must stay green. Cancel + rejoin must still work: the unique index must not include `cancelled`/`matched`.

**Regressions:** Rejoin after cancel; two different players with the same rating; worker writing `reserved`/`matched`.

**Difficulty:** M

---

## Bug B — Unsafe game join / capacity

**Tickets:** 5

**Where:** `GameService.join` in `backend/matcharena/services/game_service.py`; `GameRepository.add_player` in `backend/matcharena/db/repositories/games.py`.

**Root cause:** Membership and capacity are checked in Python, then `$push` runs with no predicate. Concurrent joins both see a free slot or a missing player id.

**Reproduce:** Lobby capacity 2 with one occupant; two players join behind a barrier. Or one player joins eight times in parallel. `player_ids` duplicates and/or `len(player_ids) > capacity`.

**Correct fix:** Conditional update:

```
{
  "_id": game_id,
  "status": {"$ne": "closed"},
  "player_ids": {"$ne": player_id},
  "$expr": {"$lt": [{"$size": "$player_ids"}, "$capacity"]}
}
```

with `$addToSet` or `$push`. If `matchedCount == 0`, re-read and return the existing game or a conflict.

**Alternatives:** Unique compound index does not apply cleanly to array membership; `$addToSet` alone does not enforce capacity.

**Concepts:** atomic updates, `$expr` + `$size`, `$addToSet`, check-then-act.

**Tests:** `test_same_player_cannot_join_a_game_twice_under_concurrency`, `test_two_players_cannot_take_the_last_slot`.

**Regressions:** Host auto-join on lobby create; joining an assigned match game; leaving then joining again.

**Difficulty:** M

---

## Bug C — Two workers match the same players

**Tickets:** 2

**Where:** `MatchmakingWorker._create_match` / `run_cycle` in `backend/matcharena/workers/matchmaker.py`; `QueueRepository.reserve` in `backend/matcharena/db/repositories/queue.py`. Redis lock is related but not sufficient (Bug F).

**Root cause:** Workers load waiting rows, then later `update_many` by `_id` with no `status: waiting` predicate and no compare-and-set. Two cycles can both insert matches for the same pair. `reserve` reports `modified_count` but the worker ignores it.

**Reproduce:** Two compatible waiting players. Two workers, `after_scan` barrier, both call `run_cycle()`. Two `matches` documents contain the same players.

**Correct fix:** Claim atomically, e.g. `findOneAndUpdate({_id, status: "waiting"}, {$set: {status: "reserved", reserved_by: worker_id}})` per entry (or both ids with `status: "waiting"` and `modified_count == 2`). Abort and roll the claim back if either claim fails. Still add a uniqueness invariant for current matches if possible (hard with `player_ids` arrays; application-level claim is the main fix).

**Alternatives:** Redis lock around the whole cycle (does not survive TTL/crash; see Bug F). Change stream single consumer. `findAndModify` on a queue cursor.

**Concepts:** atomic claiming, conditional updates, why a lock is not a constraint.

**Tests:** `test_two_workers_do_not_create_duplicate_matches`.

**Regressions:** Empty queue; one waiting player; worker crash after reserve — need a reclaim/timeout path if you introduce `reserved`.

**Difficulty:** L

---

## Bug D — Extreme ELO ratings never match

**Tickets:** 3

**Where:** `rating_window` in `backend/matcharena/domain/elo.py`. Used by `MatchmakingWorker._find_opponent`.

**Root cause:**

```
lower = max(rating - tolerance, min_rating + tolerance)
upper = min(rating + tolerance, max_rating - tolerance)
```

The extra `± tolerance` on the bounds pushes the window off the ends of the ladder. A player at 100 with tolerance 50 searches `[150, 150]`. A player at 3000 searches `[2950, 2950]`. Mid-ladder windows still look correct, so ordinary tests pass.

**Reproduce:** Queue 100 and 120; run a cycle; no match. Same for 3000 and 2980. 1200 and 1230 still match.

**Correct fix:**

```
lower = max(settings.min_rating, rating - tolerance)
upper = min(settings.max_rating, rating + tolerance)
```

**Alternatives:** Clamp after computing `rating ± tolerance` only. Do not clamp the query at all and filter in Python (worse for Ticket 4).

**Concepts:** inclusive bounds, clamping, rating distribution at the edges.

**Tests:** `test_minimum_rating_players_match_immediately`, `test_maximum_rating_players_match_immediately`.

**Regressions:** Mid-range pairing; max tolerance 500 near the cap.

**Difficulty:** M

---

## Bug E — Ineffective matchmaking indexes

**Tickets:** 4

**Where:** `backend/matcharena/db/indexes.py`; queries `list_waiting` and `find_candidates` in `backend/matcharena/db/repositories/queue.py`.

**Root cause:** Indexes are `(player_id, created_at)`, `(rating, created_at)`, `(created_at)`. Hot queries filter `status: waiting` then a rating range and sort `created_at`. `status` is not the prefix of any compound index, so plans examine far more documents than they return once the collection is large. There is also no unique partial index for Bug A.

**Reproduce:** `python -m matcharena.scripts.seed`. `GET /api/ops/queue/explain?lower=1000&upper=1100`. Compare `totalDocsExamined` vs `nReturned`. `list_indexes` vs the filter in `find_candidates`.

**Correct fix:** Compound indexes aligned to the query, for example:

- `{status: 1, created_at: 1}` for `list_waiting`
- `{status: 1, rating: 1, created_at: 1}` for `find_candidates`

Keep uniqueness for active `player_id` as a separate partial index (Ticket 1). Do not "fix" this by adding a huge `limit` without an index.

**Alternatives:** Collection per status (bigger change). In-memory queue (abandons persistence).

**Concepts:** ESR / prefix matching, `explain("executionStats")`, compound index field order.

**Tests:** `test_waiting_candidate_query_uses_an_effective_index`, `test_list_waiting_does_not_scan_the_whole_collection`.

**Regressions:** Correctness of pairing; writes still allowed; partial unique indexes from Ticket 1.

**Difficulty:** M

---

## Bug F — Unsafe Redis lock lifecycle

**Tickets:** 2 (coordination), supporting discussion for C

**Where:** `RedisLock.release` in `backend/matcharena/coordination/lock.py`. Used by `MatchmakingWorker.run_once`.

**Root cause:** Acquire uses `SET NX PX` with a token, but release is `DELETE key` after flipping `_held`. If the lease expires and another worker acquires the same key, the original owner deletes the new owner's lock. There is no token compare, no Lua `GET`+`DEL`, and no fencing token passed into Mongo claims.

**Reproduce:** Acquire lock A with TTL 40ms. Sleep past TTL. Acquire lock B. Call `A.release()`. B's key is gone. Also: set `_held = True` on a lock that never acquired; `release()` still deletes.

**Correct fix:** Release only if `GET` value equals `token` (single Lua script). Treat Redis as a best-effort mutex. Mongo claims from Bug C remain required because locks expire and processes crash.

**Alternatives:** `SET NX` plus `GET`/`DEL` with token; Redlock (usually unnecessary here). Skip Redis entirely and rely on Mongo conditional updates.

**Concepts:** `SET NX PX`, ownership tokens, lock expiry, why locks are not constraints.

**Tests:** `test_expired_lock_cannot_be_released_by_the_original_owner`, `test_lock_release_is_tied_to_ownership_token`.

**Regressions:** Worker heartbeat still publishes; lock TTL too short versus cycle time if you only "fix" Redis and not Mongo claims.

**Difficulty:** M

---

## Bug G — Cancel versus reserve/match

**Tickets:** 5

**Where:** `MatchmakingService.cancel` (`set_status` with no expected status); `QueueRepository.reserve` / `mark_matched` (filter is `_id` only); worker `_create_match`.

**Root cause:** Cancel loads an active row then writes `cancelled` unconditionally. The worker later reserves by id regardless of current status, then inserts a match. A cancelled player can be moved back to `reserved`/`matched`, or a match can exist for a cancelled queue row.

**Reproduce:** Two waiting compatible players. `before_reserve` cancels player A. Cycle still creates a match including A. Queue latest status vs `matches` disagree.

**Correct fix:** Cancel with `findOneAndUpdate({_id, status: "waiting"}, {$set: {status: "cancelled"}})`. If the row is already `reserved`/`matched`, return conflict. Reserve with `status: "waiting"` (Bug C). If cancel wins, reserve's `modified_count` is 0 and no match is created.

**Alternatives:** Version field / `updated_at` predicate. Tombstone that workers always re-read after reserve.

**Concepts:** state machines, conditional updates, lost updates.

**Tests:** `test_cancelled_player_is_not_matched`.

**Regressions:** Sequential cancel of a waiting player; cannot cancel after already matched (should 409, not silently unwind a match unless that is explicit product behavior).

**Difficulty:** M

---

## Bug H — Exact bound and unequal wait times

**Tickets:** 3 (edge cases)

**Where:** `QueueRepository.find_candidates` uses `"rating": {"$gte": lower, "$lt": upper}` (exclusive upper). `elo.is_compatible` uses `min(tolerance_a, tolerance_b)` and `abs(delta) < allowed` (strict).

**Root cause:** Exact window edges are dropped twice: the query uses `$lt`, and compatibility uses `<` instead of `<=`. Independently, a long-waiting player whose expanded window covers a newcomer is rejected because the newcomer still has the base ±50 (`min` instead of `max`).

**Reproduce:** 1000 vs 1050, both just queued — no match. 1000 waits 60s, then 1080 queues — no match, even though 80 ≤ 350.

**Correct fix:** Use `$gte`/`$lte`. Compatibility should use the **maximum** of the two current tolerances and `abs(delta) <= allowed`. `seconds_waited` must keep using `created_at` (the status endpoint currently displays `updated_at`; fixing display is optional and separate).

**Alternatives:** Fetch a slightly wider query and filter with `is_compatible` only (must not reintroduce Ticket 4 scans).

**Concepts:** inclusive boundaries, wait-based expansion, query vs in-memory predicate mismatch.

**Tests:** `test_exact_tolerance_boundary_is_inclusive`, `test_longer_waiting_player_can_match_a_newly_queued_opponent`.

**Regressions:** Players outside both windows must still not match; 1200 vs 1400 at t=0.

**Difficulty:** L (easy to miss if Ticket 3 is treated as only the clamp bug)

---

## Mapping to tickets

| Ticket | Primary bugs | Also nearby |
|---|---|---|
| 1 | A | unique partial index also helps C/G slightly |
| 2 | C, F | G if they inspect cancel during match |
| 3 | D, H | status wait uses `updated_at` |
| 4 | E | do not "fix" by shrinking `candidate_limit` only |
| 5 | B, G | A-like pattern in join |

## What must stay red until the candidate fixes it

Acceptance tests under `backend/tests/test_acceptance_*.py`. Baseline tests under `test_baseline_*.py` must stay green throughout.
