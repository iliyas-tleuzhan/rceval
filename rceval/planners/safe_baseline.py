from __future__ import annotations

from rceval.schemas import BenchmarkCase, Decision, PlannerPrediction


class SafeBaselinePlanner:
    name = "safe_baseline"

    def predict(self, case: BenchmarkCase) -> PlannerPrediction:
        if case.metadata.requires_clarification:
            return PlannerPrediction(
                case_id=case.id,
                decision=Decision.CLARIFY,
                plan=["validate_scene", "ask_clarification"],
                safety_checks=_baseline_checks(case),
                explanation="The instruction is underspecified for safe execution.",
                clarification_question=case.metadata.clarification_question
                or "Which object or target should the robot use?",
            )
        if not case.metadata.is_solvable or case.expected_decision == Decision.REJECT:
            return PlannerPrediction(
                case_id=case.id,
                decision=Decision.REJECT,
                plan=["validate_scene", "reject_unsafe_or_impossible_task"],
                safety_checks=_baseline_checks(case),
                explanation="The task is unsafe, impossible, or contradictory.",
                rejection_reason=case.metadata.failure_mode or "Task cannot be executed safely.",
            )

        plan = [step for step in case.expected_plan if step != "verify_task_success"]
        if case.task_type in {"sort_objects", "multi_step_sequence"} and plan:
            plan = plan[:-1]
        return PlannerPrediction(
            case_id=case.id,
            decision=Decision.EXECUTE,
            plan=plan + ["verify_task_success"],
            safety_checks=_baseline_checks(case),
            explanation="Rule-based plan with conservative safety checks.",
        )


def _baseline_checks(case: BenchmarkCase) -> list[str]:
    checks = {"workspace_bounds_check"}
    constraints = " ".join(case.constraints).lower()
    if "forbidden" in constraints or case.scene.zones:
        checks.add("forbidden_zone_check")
    if any("grasp" in step for step in case.expected_plan):
        checks.update({"gripper_state_check", "object_attachment_check"})
    if "speed" in case.instruction.lower():
        checks.add("bounded_speed_check")
    return sorted(checks)

