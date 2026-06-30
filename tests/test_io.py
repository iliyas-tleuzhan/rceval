from pathlib import Path

from rceval.datasets import sample_cases
from rceval.io import read_cases, write_records


def test_jsonl_yaml_read_write(tmp_path: Path):
    cases = sample_cases()[:2]
    jsonl = tmp_path / "cases.jsonl"
    yaml = tmp_path / "cases.yaml"
    write_records(jsonl, cases)
    write_records(yaml, cases)
    assert len(read_cases(jsonl)) == 2
    assert len(read_cases(yaml)) == 2

