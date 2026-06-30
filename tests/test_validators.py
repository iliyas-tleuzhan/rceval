from rceval.datasets import sample_cases
from rceval.validators import validate_cases


def test_good_samples_semantically_validate():
    assert validate_cases(sample_cases()) == []


def test_bad_validation_cases_are_reported():
    case = sample_cases()[0].model_copy(deep=True)
    case.id = sample_cases()[1].id
    case.instruction = ""
    case.expected_plan = []
    case.allowed_objects = ["missing_cube"]
    errors = validate_cases([sample_cases()[1], case])
    assert any("duplicate case id" in error for error in errors)
    assert any("instruction is empty" in error for error in errors)
    assert any("empty expected_plan" in error for error in errors)
    assert any("missing_cube" in error for error in errors)
