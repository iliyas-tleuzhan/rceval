from __future__ import annotations

import re

from rceval.schemas import BenchmarkCase, PlannerPrediction

SYMBOLIC_REFERENCES = {
    "home",
    "target",
    "selected_object",
    "selected_cube",
    "matching_bin",
    "workspace",
    "safe_zone",
    "object",
    "objects",
}

ACTION_PREFIXES = (
    "move_to_",
    "grasp_",
    "place_in_",
    "place_on_",
    "avoid_",
    "inspect_",
    "release_",
    "approach_",
    "pregrasp_",
)


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


def manipulation_order_score(plan: list[str]) -> float:
    """Score symbolic manipulation order without penalizing approach-before-grasp."""
    if not _has_manipulation(plan):
        return 1.0
    checks: list[bool] = []
    grasp_idx = _first_idx(plan, ("grasp_", "grasp_object", "close_gripper"))
    release_idx = _first_idx(plan, ("release_", "release_object", "open_gripper_at"))
    lift_idx = _first_idx(plan, ("lift_",))
    verify_idx = _first_idx(plan, ("verify_",))
    move_indices = [idx for idx, step in enumerate(plan) if step.startswith("move_to_")]

    if grasp_idx is None:
        return 0.0
    if release_idx is not None:
        checks.append(grasp_idx < release_idx)
    if lift_idx is not None:
        checks.append(grasp_idx < lift_idx)
    if len(move_indices) >= 2:
        checks.append(grasp_idx < move_indices[-1])
        checks.append(move_indices[0] < grasp_idx)
    if verify_idx is not None and release_idx is not None:
        checks.append(release_idx < verify_idx)
    return sum(checks) / len(checks) if checks else 1.0


def extract_references(text_items: list[str], candidates: set[str]) -> set[str]:
    refs: set[str] = set()
    blob = " ".join(text_items).lower()
    for candidate in candidates:
        pattern = rf"(?<![a-z0-9]){re.escape(candidate.lower())}(?![a-z0-9])"
        if re.search(pattern, blob):
            refs.add(candidate)
    return refs


def hallucinated_references(case: BenchmarkCase, prediction: PlannerPrediction) -> set[str]:
    known = scene_reference_names(case)
    candidates = extracted_plan_references(prediction.plan, known)
    return {token for token in candidates if token not in known and token not in SYMBOLIC_REFERENCES}


def object_reference_score(case: BenchmarkCase, prediction: PlannerPrediction) -> float:
    names = scene_reference_names(case)
    refs = extracted_plan_references(prediction.plan, names)
    if case.allowed_zones and any("forbidden_zone" in step or "forbidden_zones" in step for step in prediction.plan):
        refs.update(case.allowed_zones)
    hallucinations = hallucinated_references(case, prediction)
    if hallucinations:
        return 0.0
    if case.expected_decision != "execute" and prediction.decision == case.expected_decision:
        return 1.0
    expected_refs = {
        name
        for name in names
        if any(name in step for step in case.expected_plan) or name in case.instruction.lower()
    }
    if not expected_refs:
        return 1.0
    return len(refs & expected_refs) / len(expected_refs)


def scene_reference_names(case: BenchmarkCase) -> set[str]:
    names = set(case.allowed_objects) | set(case.allowed_zones)
    names |= {obj.name for obj in case.scene.objects}
    names |= {zone.name for zone in case.scene.zones}
    names |= SYMBOLIC_REFERENCES
    return names


def extracted_plan_references(plan: list[str], known_names: set[str] | None = None) -> set[str]:
    known_names = known_names or set()
    refs: set[str] = set()
    for step in plan:
        lowered = step.lower()
        for name in known_names:
            if name and _contains_name(lowered, name):
                refs.add(name)
        for prefix in ACTION_PREFIXES:
            if lowered.startswith(prefix):
                refs.add(lowered.removeprefix(prefix))
    return {_normalize_reference(ref) for ref in refs if ref and not _is_action_or_check(ref)}


def _is_action_or_check(token: str) -> bool:
    if token in SYMBOLIC_REFERENCES:
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


def _contains_name(text: str, name: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(name.lower())}(?![a-z0-9])"
    return bool(re.search(pattern, text))


def _normalize_reference(reference: str) -> str:
    for suffix in ("_safely", "_success"):
        reference = reference.removesuffix(suffix)
    return reference


def _has_manipulation(plan: list[str]) -> bool:
    return any("grasp" in step or "release" in step or "lift" in step for step in plan)


def _first_idx(plan: list[str], prefixes: tuple[str, ...]) -> int | None:
    return next(
        (idx for idx, step in enumerate(plan) if any(step.startswith(prefix) for prefix in prefixes)),
        None,
    )
