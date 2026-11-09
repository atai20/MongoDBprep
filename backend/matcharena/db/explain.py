from __future__ import annotations

from typing import Any


def summarize_execution_stats(plan: dict[str, Any]) -> dict[str, Any]:
    stats = plan.get("executionStats", plan)
    stages: list[dict[str, Any]] = []
    _collect_stages(stats.get("executionStages") or plan.get("queryPlanner", {}).get("winningPlan"), stages)
    index_names = [s.get("indexName") for s in stages if s.get("indexName")]
    return {
        "n_returned": stats.get("nReturned"),
        "docs_examined": stats.get("totalDocsExamined"),
        "keys_examined": stats.get("totalKeysExamined"),
        "execution_time_ms": stats.get("executionTimeMillis"),
        "indexes": index_names,
        "stages": [s.get("stage") for s in stages if s.get("stage")],
        "winning_plan": plan.get("queryPlanner", {}).get("winningPlan"),
    }


def _collect_stages(node: Any, out: list[dict[str, Any]]) -> None:
    if not isinstance(node, dict):
        return
    out.append(
        {
            "stage": node.get("stage"),
            "indexName": node.get("indexName"),
            "docsExamined": node.get("docsExamined"),
            "nReturned": node.get("nReturned"),
        }
    )
    for key in ("inputStage", "winningPlan", "queryPlan"):
        if key in node:
            _collect_stages(node[key], out)
    for child in node.get("inputStages", []) or []:
        _collect_stages(child, out)
