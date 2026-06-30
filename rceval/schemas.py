from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Decision(StrEnum):
    EXECUTE = "execute"
    CLARIFY = "clarify"
    REJECT = "reject"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Workspace(BaseModel):
    x: tuple[float, float]
    y: tuple[float, float]
    z: tuple[float, float]


class Robot(BaseModel):
    type: str = "arm_6dof"
    workspace: Workspace
    gripper: bool = True
    max_speed: float = Field(default=0.35, gt=0)


class SceneObject(BaseModel):
    name: str
    type: str
    position: tuple[float, float, float]
    movable: bool = True
    color: str | None = None


class Bounds(BaseModel):
    x: tuple[float, float]
    y: tuple[float, float]
    z: tuple[float, float]


class Zone(BaseModel):
    name: str
    type: str
    bounds: Bounds


class Scene(BaseModel):
    robot: Robot
    objects: list[SceneObject] = Field(default_factory=list)
    zones: list[Zone] = Field(default_factory=list)


class CaseMetadata(BaseModel):
    ambiguity: str = "explicit"
    requires_clarification: bool = False
    clarification_question: str | None = None
    is_solvable: bool = True
    failure_mode: str | None = None
    tags: list[str] = Field(default_factory=list)


class BenchmarkCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    instruction: str
    task_type: str
    difficulty: Difficulty
    expected_decision: Decision
    scene: Scene
    constraints: list[str] = Field(default_factory=list)
    expected_plan: list[str] = Field(default_factory=list)
    required_safety_checks: list[str] = Field(default_factory=list)
    allowed_objects: list[str] = Field(default_factory=list)
    allowed_zones: list[str] = Field(default_factory=list)
    metadata: CaseMetadata = Field(default_factory=CaseMetadata)

    @field_validator("allowed_objects")
    @classmethod
    def no_empty_objects(cls, value: list[str]) -> list[str]:
        return [item for item in value if item]


class PlannerPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    decision: Decision
    plan: list[str] = Field(default_factory=list)
    safety_checks: list[str] = Field(default_factory=list)
    explanation: str = ""
    clarification_question: str | None = None
    rejection_reason: str | None = None


class CaseScore(BaseModel):
    case_id: str
    decision_score: float
    format_score: float
    plan_order_score: float
    safety_score: float
    object_reference_score: float
    hallucination_penalty: float
    constraint_score: float
    clarification_score: float
    rejection_score: float
    overall_score: float
    passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AggregateScore(BaseModel):
    total_cases: int
    passed_cases: int
    mean_overall_score: float
    mean_safety_score: float
    mean_plan_order_score: float
    mean_object_reference_score: float
    decision_accuracy: float
    clarification_accuracy: float
    rejection_accuracy: float
    hallucination_rate: float


class ScoreReport(BaseModel):
    aggregate: AggregateScore
    cases: list[CaseScore]


class SafetyJudgement(BaseModel):
    case_id: str
    allowed: bool
    risk_level: RiskLevel
    issues: list[str] = Field(default_factory=list)
    required_fix: str | None = None
    safe_rewrite: str | None = None


Serializable = dict[str, Any] | list[dict[str, Any]]
FileFormat = Literal["jsonl", "yaml", "json"]

