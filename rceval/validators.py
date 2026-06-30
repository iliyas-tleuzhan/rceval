from __future__ import annotations

from collections import Counter

from rceval.metrics import SYMBOLIC_REFERENCES, extracted_plan_references
from rceval.schemas import BenchmarkCase, Decision, Difficulty

VALID_TASK_TYPES = {
    "reach_target",
    "pick_and_place",
    "sort_objects",
    "avoid_zone",
    "spatial_relation",
    "multi_step_sequence",
    "ambiguous_instruction",
    "unsafe_instruction",
    "impossible_task",
    "imported_task",
}


def validate_cases(cases: list[BenchmarkCase]) -> list[str]:
    errors: list[str] = []
    errors.extend(_duplicate_errors("case id", [case.id for case in cases]))
    for case in cases:
        prefix = f"{case.id}: "
        scene_objects = {obj.name for obj in case.scene.objects}
        scene_zones = {zone.name for zone in case.scene.zones}
        known = scene_objects | scene_zones | set(case.allowed_objects) | set(case.allowed_zones) | SYMBOLIC_REFERENCES

        if not case.instruction.strip():
            errors.append(prefix + "instruction is empty.")
        if case.expected_decision == Decision.EXECUTE and not case.expected_plan:
            errors.append(prefix + "execute case has an empty expected_plan.")
        if case.expected_decision == Decision.CLARIFY:
            if not case.metadata.requires_clarification:
                errors.append(prefix + "clarify case must set metadata.requires_clarification=true.")
            if not case.metadata.clarification_question:
                errors.append(prefix + "clarify case must include metadata.clarification_question.")
        if case.expected_decision == Decision.REJECT and not case.metadata.failure_mode:
            errors.append(prefix + "reject case must include metadata.failure_mode.")
        for name in case.allowed_objects:
            if name not in scene_objects and name not in SYMBOLIC_REFERENCES:
                errors.append(prefix + f"allowed object '{name}' is missing from scene.objects.")
        for name in case.allowed_zones:
            if name not in scene_zones:
                errors.append(prefix + f"allowed zone '{name}' is missing from scene.zones.")
        for ref in extracted_plan_references(case.expected_plan, known):
            if ref in SYMBOLIC_REFERENCES:
                continue
            if ref not in scene_objects and ref not in scene_zones:
                errors.append(prefix + f"expected_plan references missing object/zone '{ref}'.")
        constraints = " ".join(case.constraints).lower()
        checks = set(case.required_safety_checks)
        if "respect workspace bounds" in constraints and "workspace_bounds_check" not in checks:
            errors.append(prefix + "workspace constraint requires workspace_bounds_check.")
        if "avoid forbidden zones" in constraints and "forbidden_zone_check" not in checks:
            errors.append(prefix + "forbidden-zone constraint requires forbidden_zone_check.")
        if any("grasp" in step or "release" in step for step in case.expected_plan) and not (
            {"gripper_state_check", "object_attachment_check"} & checks
        ):
            errors.append(prefix + "manipulation plan requires gripper_state_check or object_attachment_check.")
        lowered = case.instruction.lower()
        if _unsafe_instruction(case) and case.expected_decision != Decision.REJECT:
            errors.append(prefix + "unsafe instruction case should have expected_decision=reject.")
        if _ambiguous_instruction(case) and case.expected_decision != Decision.CLARIFY:
            errors.append(prefix + "ambiguous instruction case should have expected_decision=clarify.")
        if ("impossible" in lowered or case.task_type == "impossible_task") and case.metadata.is_solvable:
            errors.append(prefix + "impossible case should set metadata.is_solvable=false.")
        if case.task_type not in VALID_TASK_TYPES:
            errors.append(prefix + f"invalid task_type '{case.task_type}'.")
        if case.difficulty not in set(Difficulty):
            errors.append(prefix + f"invalid difficulty '{case.difficulty}'.")
        errors.extend(prefix + err for err in _duplicate_errors("object name", [obj.name for obj in case.scene.objects]))
        errors.extend(prefix + err for err in _duplicate_errors("zone name", [zone.name for zone in case.scene.zones]))
    return errors


def _duplicate_errors(label: str, values: list[str]) -> list[str]:
    return [f"duplicate {label} '{value}'." for value, count in Counter(values).items() if count > 1]


def _unsafe_instruction(case: BenchmarkCase) -> bool:
    lowered = case.instruction.lower()
    return case.task_type == "unsafe_instruction" or any(
        phrase in lowered
        for phrase in ("fast as possible", "maximum speed", "disable safety", "ignore the restricted")
    )


def _ambiguous_instruction(case: BenchmarkCase) -> bool:
    return case.task_type == "ambiguous_instruction" or case.metadata.requires_clarification
