from rceval.datasets import sample_cases
from rceval.schemas import PlannerPrediction


def test_sample_cases_validate():
    cases = sample_cases()
    assert len(cases) >= 20
    assert cases[0].id.startswith("rceval_")


def test_prediction_schema_validates():
    prediction = PlannerPrediction.model_validate(
        {
            "case_id": "rceval_000001",
            "decision": "execute",
            "plan": ["validate_scene"],
            "safety_checks": ["workspace_bounds_check"],
            "explanation": "ok",
        }
    )
    assert prediction.decision == "execute"

