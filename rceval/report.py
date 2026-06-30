from __future__ import annotations

from pathlib import Path

from rceval.schemas import BenchmarkCase, PlannerPrediction, ScoreReport
from rceval.scoring import score_predictions


def render_report(cases: list[BenchmarkCase], predictions: list[PlannerPrediction]) -> str:
    report = score_predictions(cases, predictions)
    agg = report.aggregate
    lines = [
        "# RCEval Evaluation Report",
        "",
        "## Summary",
        "",
        f"- Total cases: {agg.total_cases}",
        f"- Passed cases: {agg.passed_cases}",
        f"- Mean overall score: {agg.mean_overall_score:.3f}",
        f"- Mean safety score: {agg.mean_safety_score:.3f}",
        f"- Decision accuracy: {agg.decision_accuracy:.3f}",
        f"- Hallucination rate: {agg.hallucination_rate:.3f}",
        "",
        "## Per-Case Scores",
        "",
        "| Case | Overall | Safety | Plan Order | Decision | Passed |",
        "|---|---:|---:|---:|---:|---|",
    ]
    by_case = {case.id: case for case in cases}
    for score in report.cases:
        case = by_case[score.case_id]
        lines.append(
            f"| {score.case_id} ({case.task_type}) | {score.overall_score:.3f} | "
            f"{score.safety_score:.3f} | {score.plan_order_score:.3f} | "
            f"{score.decision_score:.3f} | {score.passed} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_comparison(named_reports: dict[str, ScoreReport]) -> str:
    lines = [
        "# RCEval Planner Comparison",
        "",
        "| Prediction File | Overall | Safety | Plan Order | Decision Accuracy | Passed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, report in named_reports.items():
        agg = report.aggregate
        lines.append(
            f"| {Path(name).name} | {agg.mean_overall_score:.3f} | {agg.mean_safety_score:.3f} | "
            f"{agg.mean_plan_order_score:.3f} | {agg.decision_accuracy:.3f} | "
            f"{agg.passed_cases}/{agg.total_cases} |"
        )
    lines.append("")
    return "\n".join(lines)

