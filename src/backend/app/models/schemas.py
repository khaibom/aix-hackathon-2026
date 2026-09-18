from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Segment(BaseModel):
    id: str
    section: str
    para_idx: int
    text: str
    char_span: tuple[int, int]


class Requirement(BaseModel):
    req_id: str
    category: str
    requirement_text: str
    source_segment_ids: list[str]
    criticality: Literal["hard", "soft"]


class ComplianceResult(BaseModel):
    req_id: str
    status: Literal["met", "weak", "missing"]
    matched_segment_ids: list[str]
    rationale: str


class CriterionScore(BaseModel):
    criterion: str
    score_1to5: int
    comment: str
    weight: float
    weighted_score: float


class RewriteSuggestion(BaseModel):
    req_id: str
    original_text: str | None
    suggested_text: str
    insertion_point: str


class AuditState(BaseModel):
    rfp_segments: list[Segment] = []
    draft_segments: list[Segment] = []
    requirements: list[Requirement] = []
    compliance_map: list[ComplianceResult] = []
    scores: list[CriterionScore] = []
    rewrites: list[RewriteSuggestion] = []
    inferred_priorities: list[str] = []
    weights: dict[str, float] = {}
