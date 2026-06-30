from rceval.datasets import sample_cases
from rceval.planners.safe_baseline import SafeBaselinePlanner
from rceval.safety_judge import RuleBasedSafetyJudge
from rceval.schemas import PlannerPrediction


def test_missing_forbidden_zone_check_is_caught():
    case = next(item for item in sample_cases() if item.allowed_zones)
    prediction = PlannerPrediction(
        case_id=case.id,
        decision="execute",
        plan=case.expected_plan,
        safety_checks=["workspace_bounds_check"],
        explanation="missing zone check",
    )
    judgement = RuleBasedSafetyJudge().judge(case, prediction)
    assert not judgement.allowed
    assert any("forbidden" in issue for issue in judgement.issues)


def test_safety_judge_flags_unsafe_high_speed_command():
    case = next(item for item in sample_cases() if "fast as possible" in item.instruction)
    prediction = PlannerPrediction(
        case_id=case.id,
        decision="execute",
        plan=["move_to_red_cube"],
        safety_checks=[],
        explanation="bad",
    )
    judgement = RuleBasedSafetyJudge().judge(case, prediction)
    assert not judgement.allowed
    assert judgement.risk_level == "high"
    assert judgement.safe_rewrite


def test_safe_baseline_has_allowed_executable_case():
    case = next(item for item in sample_cases() if item.expected_decision == "execute" and not item.allowed_zones)
    judgement = RuleBasedSafetyJudge().judge(case, SafeBaselinePlanner().predict(case))
    assert judgement.allowed

