# 75-minute interview protocol

Use this schedule for each ticket in `ASSESSMENT.md`.

| Time | Task |
|---|---|
| 0–5 min | Understand the ticket and acceptance criteria |
| 5–12 min | Read README, inspect project structure and Git status |
| 12–22 min | Trace relevant routes, services, database operations and workers |
| 22–30 min | Reproduce the issue and form a hypothesis |
| 30–35 min | Decide on the smallest correct fix |
| 35–50 min | Implement using AI carefully |
| 50–65 min | Run tests, add regression coverage, verify edge cases |
| 65–71 min | Inspect diff and remove debugging scaffolding |
| 71–75 min | Explain diagnosis, fix, testing and limitations |

## How to use the assistant

Ask it to map architecture, trace an endpoint, explain a query, or review a proposed patch. Do not paste the whole ticket and ask it to "fix the repo". Prefer narrow questions and keep the change set small.

## Explanation framework

When time is up, walk through the work in this order:

1. **Observation:** What exactly happens?
2. **Diagnosis:** Which operation causes it?
3. **Consequence:** Why does it produce the incorrect behavior?
4. **Solution:** What exactly changes?
5. **Verification:** How do we prove it works?

Keep each part concrete: name the invariant, the document you inspected, the test you ran, and the remaining risk.
