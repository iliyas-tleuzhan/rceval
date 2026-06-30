from __future__ import annotations

from rceval.schemas import BenchmarkCase, Decision, PlannerPrediction


class OraclePlanner:
    name = "oracle"

    def predict(self, case: BenchmarkCase) -> PlannerPrediction:
        return PlannerPrediction(
            case_id=case.id,
            decision=case.expected_decision,
            plan=list(case.expected_plan),
            safety_checks=list(case.required_safety_checks),
            explanation="Oracle prediction generated from the benchmark reference.",
            clarification_question=case.metadata.clarification_question
            if case.expected_decision == Decision.CLARIFY
            else None,
            rejection_reason=case.metadata.failure_mode
            if case.expected_decision == Decision.REJECT
            else None,
        )

