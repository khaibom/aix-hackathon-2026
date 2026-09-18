"""Audit router — Sprint 0 stubs only. No agent logic."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import (
    AuditState,
    Requirement,
    ComplianceResult,
    CriterionScore,
    RewriteSuggestion,
)
from app.services.llm_client import call_gemini

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit")

# ponytail: plain dict for session store; add Redis/DB when persistence matters
_sessions: dict[str, AuditState] = {}


@router.post("/session")
def create_session() -> dict[str, str]:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = AuditState()
    return {"session_id": session_id}


@router.get("/session/{session_id}")
def get_session(session_id: str) -> AuditState:
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@router.post("/session/{session_id}/llm-ping")
def llm_ping(session_id: str) -> dict:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    result = call_gemini("Reply with the single word: pong")
    return result


class SegmentRequest(BaseModel):
    rfp_text: str
    draft_text: str


@router.post("/session/{session_id}/segment")
def segment_docs(session_id: str, payload: SegmentRequest) -> dict:
    state = get_session(session_id)
    from app.agents.segmenter import segment_document
    state.rfp_segments = segment_document(payload.rfp_text, "rfp")
    state.draft_segments = segment_document(payload.draft_text, "draft")
    return {"rfp_segments": state.rfp_segments, "draft_segments": state.draft_segments}


@router.post("/session/{session_id}/extract-requirements")
async def extract_reqs(session_id: str) -> list[Requirement]:
    from app.models.schemas import Requirement
    state = get_session(session_id)
    if not state.rfp_segments:
        raise HTTPException(
            status_code=400,
            detail="rfp_segments is empty - call /segment with rfp_text first"
        )
    from app.agents.requirement_extractor import extract_requirements
    try:
        reqs = await extract_requirements(state.rfp_segments)
    except Exception as e:
        logger.error(f"Requirement extraction failed for session {session_id}: {e}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
    state.requirements = reqs
    logger.info(f"Extracted {len(reqs)} requirements for session {session_id}")
    return reqs


@router.post("/session/{session_id}/map-compliance")
async def map_compliance_endpoint(session_id: str) -> list[ComplianceResult]:
    from app.models.schemas import ComplianceResult
    state = get_session(session_id)
    
    # Validate prerequisites with clear, actionable error messages
    if not state.requirements:
        raise HTTPException(
            status_code=400,
            detail="requirements is empty - call /extract-requirements first"
        )
    if not state.draft_segments:
        raise HTTPException(
            status_code=400,
            detail="draft_segments is empty - call /segment with draft_text first"
        )

    from app.agents.gap_mapper import map_compliance
    try:
        results = await map_compliance(state.requirements, state.draft_segments)
    except ValueError as e:
        # ValueError from input validation should be 400 (client error)
        logger.error(f"Validation error in map_compliance for session {session_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Other exceptions are 502 (LLM service errors)
        logger.error(f"Compliance mapping failed for session {session_id}: {e}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
    
    state.compliance_map = results
    logger.info(f"Mapped {len(results)} compliance results for session {session_id}")
    return results


class ScoreRequest(BaseModel):
    weights: dict[str, float] | None = None


@router.post("/session/{session_id}/score")
async def score_endpoint(
    session_id: str, payload: ScoreRequest = ScoreRequest()
) -> dict:
    """Score the draft proposal against the 7-criterion rubric.
    
    Optional weights can be provided. Completeness is computed deterministically.
    """
    state = get_session(session_id)
    
    # Validate prerequisites
    if not state.compliance_map:
        raise HTTPException(
            status_code=400,
            detail="compliance_map is empty - call /map-compliance first"
        )
    if not state.requirements:
        raise HTTPException(
            status_code=400,
            detail="requirements is empty - call /extract-requirements first"
        )
    if not state.draft_segments:
        raise HTTPException(
            status_code=400,
            detail="draft_segments is empty - call /segment with draft_text first"
        )
    
    from app.agents.scorer import score_proposal
    
    try:
        scores, overall = await score_proposal(
            state.requirements,
            state.compliance_map,
            state.draft_segments,
            payload.weights,
        )
    except ValueError as e:
        # Validation errors are client errors
        logger.error(f"Validation error in score_proposal for session {session_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Other exceptions are LLM service errors
        logger.error(f"Scoring failed for session {session_id}: {e}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
    
    # Store scores in session
    state.scores = scores
    logger.info(
        f"Scored proposal for session {session_id}: overall={overall:.2f}, "
        f"{len(scores)} criteria"
    )
    
    return {"scores": scores, "overall": overall}


@router.post("/session/{session_id}/rewrite")
async def rewrite_endpoint(session_id: str) -> list[RewriteSuggestion]:
    """Generate specific rewrite suggestions for weak/missing requirements."""
    state = get_session(session_id)
    
    # Validate prerequisites
    if not state.compliance_map:
        raise HTTPException(
            status_code=400,
            detail="compliance_map is empty - call /map-compliance first"
        )
    if not state.requirements:
        raise HTTPException(
            status_code=400,
            detail="requirements is empty - call /extract-requirements first"
        )
    if not state.draft_segments:
        raise HTTPException(
            status_code=400,
            detail="draft_segments is empty - call /segment with draft_text first"
        )
    
    from app.agents.rewriter import generate_rewrites
    
    try:
        rewrites = await generate_rewrites(
            state.requirements,
            state.compliance_map,
            state.draft_segments,
        )
    except ValueError as e:
        # Validation errors (placeholder text, etc.) are LLM issues
        logger.error(f"Rewrite validation failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Rewrite generation failed validation: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Rewrite generation failed for session {session_id}: {e}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
    
    # Store rewrites in session
    state.rewrites = rewrites
    logger.info(
        f"Generated {len(rewrites)} rewrite suggestions for session {session_id}"
    )
    
    return rewrites


class RescoreRequest(BaseModel):
    weights: dict[str, float]  # REQUIRED - all 7 criteria


@router.post("/session/{session_id}/rescore")
def rescore_endpoint(session_id: str, payload: RescoreRequest) -> dict:
    """Recompute weighted scores with new weights (instant, no LLM call).
    
    This endpoint is designed for frontend weight sliders - it's free and instant.
    Reads existing scores from state, applies new weights, returns result without storing.
    """
    state = get_session(session_id)
    
    # Validate that scoring has been done
    if not state.scores:
        raise HTTPException(
            status_code=400,
            detail="scores is empty - call /score first before rescoring"
        )
    
    from app.agents.scorer import FIXED_CRITERIA
    
    # Validate all 7 criterion names are present in weights
    provided_criteria = set(payload.weights.keys())
    required_criteria = set(FIXED_CRITERIA)
    missing_criteria = required_criteria - provided_criteria
    
    if missing_criteria:
        raise HTTPException(
            status_code=400,
            detail=f"Missing weights for criteria: {sorted(missing_criteria)}. "
                   f"All 7 criteria required for /rescore: {FIXED_CRITERIA}"
        )
    
    # Normalize weights to sum to 1.0
    total_weight = sum(payload.weights.values())
    if total_weight <= 0:
        raise HTTPException(
            status_code=400,
            detail="Total weight must be greater than 0"
        )
    
    normalized_weights = {k: v / total_weight for k, v in payload.weights.items()}
    
    # Recompute weighted_score for each criterion (keep original score_1to5 and comment)
    rescored = []
    for score in state.scores:
        new_weight = normalized_weights[score.criterion]
        new_weighted = score.score_1to5 * new_weight
        
        rescored.append(
            CriterionScore(
                criterion=score.criterion,
                score_1to5=score.score_1to5,
                comment=score.comment,
                weight=new_weight,
                weighted_score=new_weighted,
            )
        )
    
    # Compute new overall
    new_overall = sum(s.weighted_score for s in rescored)
    
    logger.info(
        f"Rescored session {session_id} with new weights (no LLM call): "
        f"overall={new_overall:.2f}"
    )
    
    return {"scores": rescored, "overall": new_overall}
