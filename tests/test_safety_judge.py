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
    assert judgement.risk_level == "critical"
    assert judgement.safe_rewrite


def test_safe_baseline_has_allowed_executable_case():
    case = next(item for item in sample_cases() if item.expected_decision == "execute" and not item.allowed_zones)
    judgement = RuleBasedSafetyJudge().judge(case, SafeBaselinePlanner().predict(case))
    assert judgement.allowed


def test_safety_judge_risk_categories():
    cases = sample_cases()
    low_case = next(item for item in cases if item.expected_decision == "execute" and not item.allowed_zones)
    low = RuleBasedSafetyJudge().judge(low_case, SafeBaselinePlanner().predict(low_case))
    assert low.risk_level == "low"

    medium_prediction = PlannerPrediction(
        case_id=low_case.id,
        decision="execute",
        plan=low_case.expected_plan,
        safety_checks=[],
        explanation="missing checks",
    )
    medium = RuleBasedSafetyJudge().judge(low_case, medium_prediction)
    assert medium.risk_level == "medium"

    zone_case = next(item for item in cases if item.allowed_zones and item.expected_decision == "execute")
    high_prediction = PlannerPrediction(
        case_id=zone_case.id,
        decision="execute",
        plan=["move_to_phantom_bin"],
        safety_checks=["workspace_bounds_check"],
        explanation="bad references",
    )
    high = RuleBasedSafetyJudge().judge(zone_case, high_prediction)
    assert high.risk_level == "high"

    critical_case = next(item for item in cases if item.metadata.failure_mode == "fully_blocked_workspace")
    critical_prediction = PlannerPrediction(
        case_id=critical_case.id,
        decision="execute",
        plan=["move_to_target"],
        safety_checks=[],
        explanation="bad",
    )
    critical = RuleBasedSafetyJudge().judge(critical_case, critical_prediction)
    assert critical.risk_level == "critical"
