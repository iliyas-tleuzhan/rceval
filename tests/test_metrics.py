from rceval.datasets import sample_cases
from rceval.metrics import hallucinated_references, manipulation_order_score, plan_order_score, safety_check_coverage
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


def test_reference_extraction_handles_real_zone_and_symbolic_home():
    case = next(item for item in sample_cases() if "restricted_zone" in item.allowed_zones)
    prediction = PlannerPrediction(
        case_id=case.id,
        decision="execute",
        plan=["move_to_red_cube", "avoid_restricted_zone", "move_to_home", "move_to_phantom_bin"],
        safety_checks=[],
        explanation="mixed",
    )
    hallucinations = hallucinated_references(case, prediction)
    assert "red_cube" not in hallucinations
    assert "restricted_zone" not in hallucinations
    assert "home" not in hallucinations
    assert "phantom_bin" in hallucinations


def test_manipulation_order_score_allows_approach_before_grasp():
    assert manipulation_order_score(
        [
            "validate_scene",
            "check_workspace_bounds",
            "move_to_red_cube",
            "open_gripper",
            "grasp_red_cube",
            "lift_object",
            "move_to_blue_bin",
            "release_object",
            "verify_task_success",
        ]
    ) == 1.0
    assert manipulation_order_score(["move_to_blue_bin", "release_object", "grasp_red_cube"]) < 1.0
