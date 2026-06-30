from __future__ import annotations

import re

from rceval.schemas import BenchmarkCase, PlannerPrediction


def lcs_length(left: list[str], right: list[str]) -> int:
    rows = len(left) + 1
    cols = len(right) + 1
    table = [[0] * cols for _ in range(rows)]
    for i, left_item in enumerate(left, 1):
        for j, right_item in enumerate(right, 1):
            if left_item == right_item:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])
    return table[-1][-1]


def plan_order_score(predicted_plan: list[str], expected_plan: list[str]) -> float:
    if not expected_plan:
        return 1.0 if not predicted_plan else 0.0
    return lcs_length(predicted_plan, expected_plan) / len(expected_plan)


def safety_check_coverage(predicted: list[str], required: list[str]) -> float:
    if not required:
        return 1.0
    predicted_set = set(predicted)
    return len(set(required) & predicted_set) / len(set(required))


def extract_references(text_items: list[str], candidates: set[str]) -> set[str]:
    refs: set[str] = set()
    blob = " ".join(text_items).lower()
    for candidate in candidates:
        pattern = rf"(?<![a-z0-9]){re.escape(candidate.lower())}(?![a-z0-9])"
        if re.search(pattern, blob):
            refs.add(candidate)
    return refs


def hallucinated_references(case: BenchmarkCase, prediction: PlannerPrediction) -> set[str]:
    known = set(case.allowed_objects) | set(case.allowed_zones)
    known |= {obj.name for obj in case.scene.objects}
    known |= {zone.name for zone in case.scene.zones}
    candidates: set[str] = set()
    for step in prediction.plan:
        lowered = step.lower()
        action_target = _action_target(lowered)
        if action_target:
            candidates.add(action_target)
        candidates.update(re.findall(r"\b[a-z]+_[a-z0-9_]+\b", lowered))
    return {
        token
        for token in candidates
        if token not in known and not _is_action_or_check(token) and not _contains_known_reference(token, known)
    }


def object_reference_score(case: BenchmarkCase, prediction: PlannerPrediction) -> float:
    names = set(case.allowed_objects) | set(case.allowed_zones)
    refs = extract_references(prediction.plan, names)
    if case.allowed_zones and any("forbidden_zone" in step or "forbidden_zones" in step for step in prediction.plan):
        refs.update(case.allowed_zones)
    hallucinations = hallucinated_references(case, prediction)
    if hallucinations:
        return 0.0
    expected_refs = {
        name
        for name in names
        if any(name in step for step in case.expected_plan) or name in case.instruction.lower()
    }
    if not expected_refs:
        return 1.0
    return len(refs & expected_refs) / len(expected_refs)


def _is_action_or_check(token: str) -> bool:
    if token in {"object", "objects", "target", "home"}:
        return True
    prefixes = (
        "validate_",
        "check_",
        "move_to_",
        "open_",
        "close_",
        "grasp_",
        "release_",
        "verify_",
        "lift_",
        "scan_",
        "sort_",
        "match_",
        "ask_",
        "reject_",
        "set_",
        "avoid_",
        "return_",
    )
    suffixes = ("_check", "_bounds", "_zones", "_success", "_speed", "_limit", "_object", "_objects")
    return token.startswith(prefixes) or token.endswith(suffixes)


def _action_target(step: str) -> str | None:
    for prefix in ("move_to_", "grasp_", "release_", "avoid_"):
        if step.startswith(prefix):
            return step.removeprefix(prefix)
    return None


def _contains_known_reference(token: str, known: set[str]) -> bool:
    return any(reference in token for reference in known)
