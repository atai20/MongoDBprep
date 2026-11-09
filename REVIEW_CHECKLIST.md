# Review checklist

Use this after a ticket, before you call the work done.

## Close-out steps

1. Lock in the fix with a focused commit if Git is available.
2. Add a small regression test.
3. Remove temporary logs, debug code, and unnecessary scaffolding.
4. Rerun the entire affected flow from a clean state.
5. Recheck every acceptance criterion.
6. Record observed symptoms and whether each is explained.
7. Test repeated actions and unusual action sequences.
8. Check failure and retry behavior.
9. Inspect the final Git diff.
10. Leave the last 10–15 minutes for cleanup and explanation.

## Evaluation rubric

| Area | What good looks like |
|---|---|
| Correctness | Invariants hold under sequential and concurrent use |
| Root-cause identification | The failing operation is named; symptoms are not treated as the cause |
| Scope of changes | The patch is as small as the diagnosis allows |
| Verification | Database state is checked, not only HTTP responses |
| Debugging process | Reproduction came before the edit |
| Code quality | No leftover instrumentation; names and error paths stay consistent |
| Communication | Observation → diagnosis → consequence → solution → verification |
| Effective use of time and AI | Assistant used for tracing and review, not unattended rewriting |

## Follow-up questions

- How did you find the issue?
- Why did you choose this fix?
- How do you know it works?
- What else could break?
- What would you do with more time?
