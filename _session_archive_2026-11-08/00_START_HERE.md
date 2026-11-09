# Session archive — Sunday Nov 8, 2026

Personal notes from tonight. **Not candidate-facing.** Do not treat this folder as part of the interview repo.

All times are **Eastern (UTC-5)** unless labeled UTC.

## Where we stopped

- Ticket 1 is **still open**. UI count `1` did not fix it.
- Acceptance tests still fail: 10 overlapping enqueues → 10 rows; cancel + 6 overlapping → 6 rows.
- Worker container `matcharena-worker-1` is **stopped**.
- Mongosh session is still open in terminal 4, database `matcharena`.
- Alice is stuck (`in_game` in Open Arena + a pending assigned match she never joined).
- Bob is the player who actually queued. Last inspect: **1** `waiting`/`reserved` row.

## Pick up tomorrow

1. Do not keep fighting Alice.
2. Leave Bob as-is, or Cancel him, or register a new user.
3. Keep the worker stopped if reproducing Ticket 1 in the UI.
4. The inspect query is still the right *check*. The command that actually produces 10 rows is:

```bash
cd backend
.venv\Scripts\python.exe -m pytest tests/test_acceptance_duplicate_queue.py -q
```

That uses database `matcharena_test`, not live `matcharena`.

## Files in this folder

| File | What it is |
|---|---|
| `01_ACTION_TIMELINE.md` | Timestamped log of **your** actions and outcomes |
| `chat_01_builder_and_ticket1_debug.md` | This Cursor thread: build the repo, move it, then Ticket 1 debug |
| `chat_02_interviewer.md` | Separate interviewer/proctor chat (this is where mongosh steps were first given) |
| `chat_03_start_project.md` | Separate “start out the project” chat |
| `chat_builder_compaction_segment_000.md` | Compacted earlier build/verify work from Chat 1 (233 turns) |
| `terminal_4.txt` | Full surviving mongosh / PowerShell log |
| `terminal_5.txt` | Idle PowerShell terminal (empty) |
| `raw_transcripts/` | Original Cursor `.jsonl` transcripts |

Cursor does not timestamp every mongosh line. Terminal times below are reconstructed from chat timestamps, Docker/Mongo boot times, and command order in `terminal_4.txt`.
