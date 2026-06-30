from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

from rceval.schemas import BenchmarkCase, PlannerPrediction

T = TypeVar("T", bound=BaseModel)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_records(path: str | Path) -> list[dict]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".jsonl":
        records = []
        with file_path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                stripped = line.strip()
                if stripped:
                    try:
                        records.append(json.loads(stripped))
                    except json.JSONDecodeError as exc:
                        msg = f"{file_path}:{line_no}: invalid JSONL record: {exc}"
                        raise ValueError(msg) from exc
        return records
    if suffix in {".yaml", ".yml"}:
        with file_path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or []
        return loaded if isinstance(loaded, list) else [loaded]
    if suffix == ".json":
        with file_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        return loaded if isinstance(loaded, list) else [loaded]
    msg = f"Unsupported file format for {file_path}"
    raise ValueError(msg)


def write_records(path: str | Path, records: list[BaseModel | dict]) -> None:
    file_path = Path(path)
    ensure_parent(file_path)
    data = [r.model_dump(mode="json") if isinstance(r, BaseModel) else r for r in records]
    suffix = file_path.suffix.lower()
    if suffix == ".jsonl":
        with file_path.open("w", encoding="utf-8") as handle:
            for record in data:
                handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        return
    if suffix in {".yaml", ".yml"}:
        with file_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)
        return
    if suffix == ".json":
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
        return
    msg = f"Unsupported file format for {file_path}"
    raise ValueError(msg)


def read_cases(path: str | Path) -> list[BenchmarkCase]:
    return [BenchmarkCase.model_validate(record) for record in read_records(path)]


def read_predictions(path: str | Path) -> list[PlannerPrediction]:
    return [PlannerPrediction.model_validate(record) for record in read_records(path)]


def write_json(path: str | Path, payload: BaseModel | dict) -> None:
    file_path = Path(path)
    ensure_parent(file_path)
    data = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")

