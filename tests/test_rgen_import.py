from pathlib import Path

from rceval.importers.rgen import convert_rgen_records
from rceval.io import read_cases, write_records


def test_rgen_import_works_on_fixture(tmp_path: Path):
    records = [
        {
            "id": "rgen_1",
            "instruction": "Move red cube to bin.",
            "task_type": "pick_and_place",
            "difficulty": "easy",
            "robot": {
                "type": "arm_6dof",
                "workspace": {"x": [-1, 1], "y": [-1, 1], "z": [0, 1]},
                "gripper": True,
                "max_speed": 0.3,
            },
            "scene": {
                "objects": [
                    {"name": "red_cube", "type": "cube", "position": [0, 0, 0.1], "movable": True},
                    {"name": "bin", "type": "container", "position": [0.2, 0, 0.1], "movable": False},
                ],
                "zones": [],
            },
            "constraints": ["respect workspace bounds"],
            "expected_plan": ["validate_scene"],
            "safety_checks": ["workspace_bounds_check"],
            "metadata": {"is_solvable": True},
        }
    ]
    cases = convert_rgen_records(records)
    assert cases[0].expected_decision == "execute"
    out = tmp_path / "cases.yaml"
    write_records(out, cases)
    assert read_cases(out)[0].id == "rgen_1"

