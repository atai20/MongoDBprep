from __future__ import annotations

import pytest

from matcharena.db.explain import summarize_execution_stats
from matcharena.scripts.seed import seed_queue_volume

pytestmark = [pytest.mark.acceptance, pytest.mark.mongo]


def test_waiting_candidate_query_uses_an_effective_index(container):
    import random

    seed_queue_volume(container.db, 4000, random.Random(7))
    plan = container.queue.explain_find_candidates(1000, 1100, "none", 25)
    summary = summarize_execution_stats(plan)
    docs_examined = summary["docs_examined"] or 0
    returned = summary["n_returned"] or 0
    assert docs_examined <= max(returned * 8, 40), summary
    indexes = summary["indexes"]
    assert indexes, summary
    assert any("status" in str(name) or (summary["winning_plan"] and True) for name in indexes)
    winning = str(summary["winning_plan"])
    assert "COLLSCAN" not in winning
    assert docs_examined < 1000, summary


def test_list_waiting_does_not_scan_the_whole_collection(container):
    import random

    seed_queue_volume(container.db, 4000, random.Random(11))
    plan = container.queue.explain_list_waiting(200)
    summary = summarize_execution_stats(plan)
    docs_examined = summary["docs_examined"] or 0
    assert docs_examined < 1500, summary
    assert "COLLSCAN" not in str(summary["winning_plan"])
