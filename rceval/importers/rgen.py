from __future__ import annotations

from rceval.schemas import BenchmarkCase


def convert_rgen_record(record: dict, index: int = 1) -> BenchmarkCase:
    metadata = record.get("metadata", {}) or {}
    if metadata.get("is_solvable") is False:
        decision = "reject"
    elif metadata.get("requires_clarification") is True:
        decision = "clarify"
    else:
        decision = "execute"

    scene = record.get("scene", {}) or {}
    robot = record.get("robot") or scene.get("robot") or _default_robot()
    objects = scene.get("objects", [])
    zones = scene.get("zones", [])
    allowed_objects = [obj["name"] for obj in objects if "name" in obj]
    allowed_zones = [zone["name"] for zone in zones if "name" in zone]
    return BenchmarkCase.model_validate(
        {
            "id": record.get("id", f"rceval_imported_{index:06d}"),
            "instruction": record.get("instruction", ""),
            "task_type": record.get("task_type", "imported_task"),
            "difficulty": record.get("difficulty", "medium"),
            "expected_decision": decision,
            "scene": {"robot": robot, "objects": objects, "zones": zones},
            "constraints": record.get("constraints", []),
            "expected_plan": record.get("expected_plan", []),
            "required_safety_checks": record.get("safety_checks", record.get("required_safety_checks", [])),
            "allowed_objects": record.get("allowed_objects", allowed_objects),
            "allowed_zones": record.get("allowed_zones", allowed_zones),
            "metadata": {
                "ambiguity": metadata.get("ambiguity", "explicit"),
                "requires_clarification": metadata.get("requires_clarification", False),
                "clarification_question": metadata.get("clarification_question"),
                "is_solvable": metadata.get("is_solvable", True),
                "failure_mode": metadata.get("failure_mode")
                or ("RGen record is marked unsolvable." if decision == "reject" else None),
                "tags": metadata.get("tags", ["rgen_import"]),
            },
        }
    )


def convert_rgen_records(records: list[dict]) -> list[BenchmarkCase]:
    return [convert_rgen_record(record, index + 1) for index, record in enumerate(records)]


def _default_robot() -> dict:
    return {
        "type": "arm_6dof",
        "workspace": {"x": [-0.5, 0.5], "y": [-0.5, 0.5], "z": [0.0, 0.8]},
        "gripper": True,
        "max_speed": 0.35,
    }
