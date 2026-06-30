from __future__ import annotations

from rceval.schemas import BenchmarkCase, Decision, PlannerPrediction


class UnsafeBaselinePlanner:
    name = "unsafe_baseline"

    def predict(self, case: BenchmarkCase) -> PlannerPrediction:
        target = case.allowed_objects[0] if case.allowed_objects else "object"
        plan = [
            f"move_to_{target}",
            "move_to_phantom_bin",
            "release_object",
            "verify_task_success",
        ]
        return PlannerPrediction(
            case_id=case.id,
            decision=Decision.EXECUTE,
            plan=plan,
            safety_checks=[],
            explanation="Unsafe baseline intentionally skips checks and executes directly.",
        )

