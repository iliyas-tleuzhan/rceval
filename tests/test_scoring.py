from rceval.datasets import sample_cases
from rceval.planners.oracle import OraclePlanner
from rceval.planners.safe_baseline import SafeBaselinePlanner
from rceval.planners.unsafe_baseline import UnsafeBaselinePlanner
from rceval.scoring import score_predictions


def test_oracle_planner_scores_high():
    cases = sample_cases()
    report = score_predictions(cases, [OraclePlanner().predict(case) for case in cases])
    assert report.aggregate.mean_overall_score > 0.95


def test_unsafe_planner_scores_lower_than_safe_planner():
    cases = sample_cases()
    safe = score_predictions(cases, [SafeBaselinePlanner().predict(case) for case in cases])
    unsafe = score_predictions(cases, [UnsafeBaselinePlanner().predict(case) for case in cases])
    assert unsafe.aggregate.mean_overall_score < safe.aggregate.mean_overall_score


def test_underspecified_task_should_clarify():
    case = next(item for item in sample_cases() if item.expected_decision == "clarify")
    prediction = SafeBaselinePlanner().predict(case)
    assert prediction.decision == "clarify"
    assert prediction.clarification_question


def test_impossible_task_should_reject():
    case = next(item for item in sample_cases() if item.task_type == "impossible_task")
    prediction = SafeBaselinePlanner().predict(case)
    assert prediction.decision == "reject"
    assert prediction.rejection_reason

