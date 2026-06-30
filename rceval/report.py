from __future__ import annotations

from collections import Counter
from pathlib import Path

from rceval.safety_judge import RuleBasedSafetyJudge
from rceval.schemas import BenchmarkCase, PlannerPrediction, ScoreReport
from rceval.scoring import score_predictions


def render_report(cases: list[BenchmarkCase], predictions: list[PlannerPrediction]) -> str:
    report = score_predictions(cases, predictions)
    agg = report.aggregate
    by_case = {case.id: case for case in cases}
    by_prediction = {prediction.case_id: prediction for prediction in predictions}
    judge = RuleBasedSafetyJudge()
    judgements = [
        judge.judge(case, by_prediction[case.id])
        for case in cases
        if case.id in by_prediction
    ]
    issue_counter = Counter(issue for judgement in judgements for issue in judgement.issues)
    risk_counter = Counter(judgement.risk_level.value for judgement in judgements)
    errors = Counter(error for score in report.cases for error in score.errors)
    warnings = Counter(warning for score in report.cases for warning in score.warnings)
    confusion = _decision_confusion(cases, predictions)
    lines = [
        "# RCEval Evaluation Report",
        "",
        "## Summary",
        "",
        f"- Total cases: {agg.total_cases}",
        f"- Passed cases: {agg.passed_cases}",
        f"- Mean overall score: {agg.mean_overall_score:.3f}",
        f"- Mean safety score: {agg.mean_safety_score:.3f}",
        f"- Mean plan order score: {agg.mean_plan_order_score:.3f}",
        f"- Mean object reference score: {agg.mean_object_reference_score:.3f}",
        f"- Decision accuracy: {agg.decision_accuracy:.3f}",
        f"- Clarification accuracy: {agg.clarification_accuracy:.3f}",
        f"- Rejection accuracy: {agg.rejection_accuracy:.3f}",
        f"- Hallucination rate: {agg.hallucination_rate:.3f}",
        "",
        "## Per-Case Scores",
        "",
        "| Case | Overall | Safety | Plan Order | Decision | Passed |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for score in report.cases:
        case = by_case[score.case_id]
        lines.append(
            f"| {score.case_id} ({case.task_type}) | {score.overall_score:.3f} | "
            f"{score.safety_score:.3f} | {score.plan_order_score:.3f} | "
            f"{score.decision_score:.3f} | {score.passed} |"
        )
    lines.extend([
        "",
        "## Worst Cases",
        "",
        "| Case | Overall | Errors | Warnings |",
        "|---|---:|---|---|",
    ])
    for score in sorted(report.cases, key=lambda item: item.overall_score)[:5]:
        lines.append(
            f"| {score.case_id} | {score.overall_score:.3f} | "
            f"{'; '.join(score.errors) or '-'} | {('; '.join(score.warnings) or '-')} |"
        )
    lines.extend([
        "",
        "## Cases With Hallucinated References",
        "",
    ])
    hallucinated = [score for score in report.cases if score.hallucination_penalty > 0]
    if hallucinated:
        for score in hallucinated:
            lines.append(f"- {score.case_id}: {'; '.join(score.errors)}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Common Errors",
        "",
        *_counter_lines(errors),
        "",
        "## Common Warnings",
        "",
        *_counter_lines(warnings),
        "",
        "## Safety Issue Distribution",
        "",
        "| Risk/Issue | Count |",
        "|---|---:|",
    ])
    for risk, count in sorted(risk_counter.items()):
        lines.append(f"| risk:{risk} | {count} |")
    for issue, count in issue_counter.most_common(10):
        lines.append(f"| {issue} | {count} |")
    lines.extend([
        "",
        "## Decision Confusion Matrix",
        "",
        "| Expected \\ Predicted | execute | clarify | reject |",
        "|---|---:|---:|---:|",
    ])
    for expected in ("execute", "clarify", "reject"):
        row = confusion[expected]
        lines.append(f"| {expected} | {row['execute']} | {row['clarify']} | {row['reject']} |")
    lines.extend([
        "",
        "## Planner Recommendations",
        "",
    ])
    lines.extend(_recommendations(report, issue_counter))
    lines.extend([
        "",
        "## Example Failure Explanations",
        "",
    ])
    failures = [score for score in report.cases if score.errors or score.warnings]
    if failures:
        for score in failures[:5]:
            case = by_case[score.case_id]
            lines.append(f"- {score.case_id}: {case.instruction} {'; '.join(score.errors + score.warnings)}")
    else:
        lines.append("- No scored failures.")
    lines.append("")
    return "\n".join(lines)


def render_comparison(named_reports: dict[str, ScoreReport]) -> str:
    lines = [
        "# RCEval Planner Comparison",
        "",
        "| Prediction File | Total | Overall | Safety | Decision Accuracy | Hallucination Rate | Clarification Accuracy | Rejection Accuracy | Passed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, report in named_reports.items():
        agg = report.aggregate
        lines.append(
            f"| {Path(name).name} | {agg.total_cases} | {agg.mean_overall_score:.3f} | "
            f"{agg.mean_safety_score:.3f} | {agg.decision_accuracy:.3f} | "
            f"{agg.hallucination_rate:.3f} | {agg.clarification_accuracy:.3f} | "
            f"{agg.rejection_accuracy:.3f} | "
            f"{agg.passed_cases}/{agg.total_cases} |"
        )
    lines.append("")
    return "\n".join(lines)


def _decision_confusion(
    cases: list[BenchmarkCase], predictions: list[PlannerPrediction]
) -> dict[str, dict[str, int]]:
    matrix = {
        expected: {predicted: 0 for predicted in ("execute", "clarify", "reject")}
        for expected in ("execute", "clarify", "reject")
    }
    by_prediction = {prediction.case_id: prediction for prediction in predictions}
    for case in cases:
        prediction = by_prediction.get(case.id)
        if prediction:
            matrix[case.expected_decision.value][prediction.decision.value] += 1
    return matrix


def _counter_lines(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- None"]
    return [f"- {item}: {count}" for item, count in counter.most_common(10)]


def _recommendations(report: ScoreReport, issues: Counter[str]) -> list[str]:
    recommendations: list[str] = []
    agg = report.aggregate
    if agg.mean_safety_score < 0.95:
        recommendations.append("- Add missing required safety checks before emitting executable plans.")
    if agg.hallucination_rate > 0:
        recommendations.append("- Ground plan references against scene objects and zones before scoring.")
    if agg.decision_accuracy < 1.0:
        recommendations.append("- Improve decision routing for execute, clarify, and reject cases.")
    if any("manipulation order" in issue for issue in issues):
        recommendations.append("- Enforce grasp/lift/transport/release ordering for manipulation tasks.")
    if not recommendations:
        recommendations.append("- Planner behavior is strong on this benchmark; test on harder imported cases next.")
    return recommendations
