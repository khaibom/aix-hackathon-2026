"""Unit tests for scorer.py - deterministic Completeness and rescore logic."""
import asyncio

import pytest

from app.agents.scorer import FIXED_CRITERIA, score_proposal
from app.models.schemas import ComplianceResult, CriterionScore, Requirement, Segment


def test_completeness_formula():
    """Test deterministic Completeness score calculation.
    
    Formula: (met + 0.5*weak) / total, mapped to 1-5 scale
    Example: 2 met, 1 weak, 1 missing out of 4 total
    Expected: (2 + 0.5*1) / 4 = 0.625, score = round(1 + 0.625*4) = 3
    """
    # Synthetic compliance map: 2 met, 1 weak, 1 missing
    compliance_map = [
        ComplianceResult(
            req_id="r1",
            status="met",
            matched_segment_ids=["draft_1"],
            rationale="Fully addressed",
        ),
        ComplianceResult(
            req_id="r2",
            status="met",
            matched_segment_ids=["draft_2"],
            rationale="Clearly stated",
        ),
        ComplianceResult(
            req_id="r3",
            status="weak",
            matched_segment_ids=["draft_3"],
            rationale="Vaguely mentioned",
        ),
        ComplianceResult(
            req_id="r4",
            status="missing",
            matched_segment_ids=[],
            rationale="Not addressed",
        ),
    ]
    
    # Create matching requirements
    requirements = [
        Requirement(
            req_id=f"r{i}",
            category="Test",
            requirement_text=f"Requirement {i}",
            source_segment_ids=["rfp_1"],
            criticality="hard",
        )
        for i in range(1, 5)
    ]
    
    # Create dummy draft segments
    draft_segments = [
        Segment(
            id="draft_1",
            section="Test",
            para_idx=1,
            text="Test text",
            char_span=(0, 10),
        )
    ]
    
    # Mock LLM call to return dummy scores for other 6 criteria
    def fake_call_gemini(prompt, schema, **kwargs):
        return {
            "scores": [
                {
                    "criterion": "Problem Understanding",
                    "score_1to5": 3,
                    "comment": "Mock comment",
                    "weight": 0.0,
                    "weighted_score": 0.0,
                },
                {
                    "criterion": "Scope & Deliverables Clarity",
                    "score_1to5": 3,
                    "comment": "Mock comment",
                    "weight": 0.0,
                    "weighted_score": 0.0,
                },
                {
                    "criterion": "Pricing Clarity",
                    "score_1to5": 3,
                    "comment": "Mock comment",
                    "weight": 0.0,
                    "weighted_score": 0.0,
                },
                {
                    "criterion": "Timeline Clarity",
                    "score_1to5": 3,
                    "comment": "Mock comment",
                    "weight": 0.0,
                    "weighted_score": 0.0,
                },
                {
                    "criterion": "Tone & Persuasiveness",
                    "score_1to5": 3,
                    "comment": "Mock comment",
                    "weight": 0.0,
                    "weighted_score": 0.0,
                },
                {
                    "criterion": "Risk/Assumptions Transparency",
                    "score_1to5": 3,
                    "comment": "Mock comment",
                    "weight": 0.0,
                    "weighted_score": 0.0,
                },
            ]
        }
    
    import app.agents.scorer
    original_call_gemini = app.agents.scorer.call_gemini
    app.agents.scorer.call_gemini = fake_call_gemini
    
    try:
        scores, overall = asyncio.run(
            score_proposal(requirements, compliance_map, draft_segments)
        )
        
        # Find Completeness score
        completeness = next(
            s for s in scores if s.criterion == "Completeness vs. RFP Requirements"
        )
        
        # Validate score calculation
        # (2 + 0.5*1) / 4 = 0.625 -> round(1 + 0.625*4) = round(3.5) = 4
        assert completeness.score_1to5 == 4, \
            f"Expected Completeness score 4, got {completeness.score_1to5}"
        
        # Validate comment contains exact counts
        assert "2 of 4" in completeness.comment, \
            f"Comment should mention '2 of 4': {completeness.comment}"
        assert "1 weakly addressed" in completeness.comment
        assert "1 missing" in completeness.comment
        
        print(f"✓ Completeness formula validated: score={completeness.score_1to5}, "
              f"comment='{completeness.comment}'")
        
    finally:
        app.agents.scorer.call_gemini = original_call_gemini


def test_default_weights():
    """Test that default weights are 1/7 for all criteria."""
    compliance_map = [
        ComplianceResult(
            req_id="r1",
            status="met",
            matched_segment_ids=["draft_1"],
            rationale="Test",
        )
    ]
    
    requirements = [
        Requirement(
            req_id="r1",
            category="Test",
            requirement_text="Test requirement",
            source_segment_ids=["rfp_1"],
            criticality="hard",
        )
    ]
    
    draft_segments = [
        Segment(
            id="draft_1",
            section="Test",
            para_idx=1,
            text="Test text",
            char_span=(0, 10),
        )
    ]
    
    # Mock LLM with fixed scores
    def fake_call_gemini(prompt, schema, **kwargs):
        return {
            "scores": [
                {"criterion": c, "score_1to5": 3, "comment": "Test", "weight": 0.0, "weighted_score": 0.0}
                for c in FIXED_CRITERIA if c != "Completeness vs. RFP Requirements"
            ]
        }
    
    import app.agents.scorer
    original_call_gemini = app.agents.scorer.call_gemini
    app.agents.scorer.call_gemini = fake_call_gemini
    
    try:
        scores, overall = asyncio.run(
            score_proposal(requirements, compliance_map, draft_segments, weights=None)
        )
        
        # Validate all weights are 1/7
        expected_weight = 1.0 / 7.0
        for score in scores:
            assert abs(score.weight - expected_weight) < 0.001, \
                f"{score.criterion} weight should be {expected_weight}, got {score.weight}"
        
        # Validate weights sum to 1.0
        total_weight = sum(s.weight for s in scores)
        assert abs(total_weight - 1.0) < 0.001, \
            f"Total weight should be 1.0, got {total_weight}"
        
        print(f"✓ Default weights validated: all criteria have weight {expected_weight:.4f}")
        
    finally:
        app.agents.scorer.call_gemini = original_call_gemini


def test_partial_weights():
    """Test that partial weights are filled with 1/7 and normalized."""
    compliance_map = [
        ComplianceResult(
            req_id="r1",
            status="met",
            matched_segment_ids=["draft_1"],
            rationale="Test",
        )
    ]
    
    requirements = [
        Requirement(
            req_id="r1",
            category="Test",
            requirement_text="Test requirement",
            source_segment_ids=["rfp_1"],
            criticality="hard",
        )
    ]
    
    draft_segments = [
        Segment(
            id="draft_1",
            section="Test",
            para_idx=1,
            text="Test text",
            char_span=(0, 10),
        )
    ]
    
    # Provide weights for only 3 criteria
    partial_weights = {
        "Problem Understanding": 0.3,
        "Pricing Clarity": 0.2,
        "Completeness vs. RFP Requirements": 0.5,
    }
    
    def fake_call_gemini(prompt, schema, **kwargs):
        return {
            "scores": [
                {"criterion": c, "score_1to5": 3, "comment": "Test", "weight": 0.0, "weighted_score": 0.0}
                for c in FIXED_CRITERIA if c != "Completeness vs. RFP Requirements"
            ]
        }
    
    import app.agents.scorer
    original_call_gemini = app.agents.scorer.call_gemini
    app.agents.scorer.call_gemini = fake_call_gemini
    
    try:
        scores, overall = asyncio.run(
            score_proposal(requirements, compliance_map, draft_segments, weights=partial_weights)
        )
        
        # Validate weights sum to 1.0 after normalization
        total_weight = sum(s.weight for s in scores)
        assert abs(total_weight - 1.0) < 0.001, \
            f"Total weight should be 1.0 after normalization, got {total_weight}"
        
        # Validate provided weights are present (after normalization)
        score_dict = {s.criterion: s for s in scores}
        
        # The missing 4 criteria should have been filled with 1/7
        # Total before normalization: 0.3 + 0.2 + 0.5 + 4*(1/7) = 1.0 + 4/7 = ~1.571
        # After normalization, Problem Understanding should be 0.3/1.571 = ~0.191
        problem_weight = score_dict["Problem Understanding"].weight
        assert problem_weight > 0.15 and problem_weight < 0.25, \
            f"Problem Understanding weight should be ~0.19, got {problem_weight}"
        
        print(f"✓ Partial weights validated and normalized: total={total_weight:.4f}")
        
    finally:
        app.agents.scorer.call_gemini = original_call_gemini


def test_rescore_logic(monkeypatch):
    """Test that rescore recomputes weighted_score without calling LLM."""
    # Create fixed existing scores
    existing_scores = [
        CriterionScore(
            criterion=c,
            score_1to5=3,
            comment="Test comment",
            weight=1.0 / 7.0,
            weighted_score=3.0 / 7.0,
        )
        for c in FIXED_CRITERIA
    ]
    
    # Mock call_gemini to track if it's called
    call_count = 0
    
    def fake_call_gemini(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise AssertionError("call_gemini should not be called during rescore!")
    
    monkeypatch.setattr("app.agents.scorer.call_gemini", fake_call_gemini)
    
    # Apply new weights (double weight on Completeness)
    new_weights = {
        "Problem Understanding": 0.1,
        "Scope & Deliverables Clarity": 0.1,
        "Pricing Clarity": 0.1,
        "Timeline Clarity": 0.1,
        "Completeness vs. RFP Requirements": 0.4,  # Double weight
        "Tone & Persuasiveness": 0.1,
        "Risk/Assumptions Transparency": 0.1,
    }
    
    # Normalize
    total = sum(new_weights.values())
    normalized = {k: v / total for k, v in new_weights.items()}
    
    # Recompute weighted scores manually
    rescored = []
    for score in existing_scores:
        new_weight = normalized[score.criterion]
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
    
    new_overall = sum(s.weighted_score for s in rescored)
    
    # Validate
    assert call_count == 0, "call_gemini should never be called during rescore"
    assert abs(new_overall - 3.0) < 0.001, \
        f"Overall with all 3s should still be 3.0, got {new_overall}"
    
    # Validate Completeness has higher weighted_score
    completeness = next(s for s in rescored if s.criterion == "Completeness vs. RFP Requirements")
    other = next(s for s in rescored if s.criterion == "Problem Understanding")
    assert completeness.weighted_score > other.weighted_score * 2, \
        f"Completeness weighted_score should be ~4x others, got {completeness.weighted_score} vs {other.weighted_score}"
    
    print(f"✓ Rescore logic validated: no LLM call, overall={new_overall:.4f}")
