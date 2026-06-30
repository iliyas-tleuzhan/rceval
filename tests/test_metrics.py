from rceval.datasets import sample_cases
from rceval.metrics import hallucinated_references, plan_order_score, safety_check_coverage
from rceval.schemas import PlannerPrediction


def test_lcs_plan_order_metric():
    assert plan_order_score(["a", "x", "b", "c"], ["a", "b", "c"]) == 1.0
    assert plan_order_score(["a"], ["a", "b"]) == 0.5


def test_safety_check_coverage():
    assert safety_check_coverage(["a"], ["a", "b"]) == 0.5
    assert safety_check_coverage([], []) == 1.0


def test_hallucinated_object_detection():
    case = sample_cases()[0]
    prediction = PlannerPrediction(
        case_id=case.id,
        decision="execute",
        plan=["move_to_fake_cube"],
        safety_checks=[],
        explanation="bad",
    )
    assert "fake_cube" in hallucinated_references(case, prediction)

