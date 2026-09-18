import asyncio

import pytest

from app.agents.gap_mapper import map_compliance
from app.models.schemas import Requirement, Segment


def test_gap_mapper_unit(monkeypatch):
    """Unit test for normal flow with met, weak, and missing statuses."""
    reqs = [
        Requirement(
            req_id="r1",
            category="Technical",
            requirement_text="Must have X",
            source_segment_ids=["rfp_1"],
            criticality="hard",
        ),
        Requirement(
            req_id="r2",
            category="Technical",
            requirement_text="Should have Y",
            source_segment_ids=["rfp_2"],
            criticality="soft",
        ),
        Requirement(
            req_id="r3",
            category="Functional",
            requirement_text="Must have Z",
            source_segment_ids=["rfp_3"],
            criticality="hard",
        ),
    ]
    draft = [
        Segment(
            id="draft_1",
            section="Intro",
            para_idx=1,
            text="We have X completely.",
            char_span=(0, 10),
        ),
        Segment(
            id="draft_2",
            section="Intro",
            para_idx=2,
            text="We kind of support Y.",
            char_span=(11, 20),
        ),
    ]

    def fake_call_gemini(prompt, schema, **kwargs):
        return {
            "results": [
                {
                    "req_id": "r1",
                    "status": "met",
                    "matched_segment_ids": ["draft_1"],
                    "rationale": "draft_1 has X",
                },
                {
                    "req_id": "r2",
                    "status": "weak",
                    "matched_segment_ids": ["draft_2"],
                    "rationale": "draft_2 is vague",
                },
                {
                    "req_id": "r3",
                    "status": "missing",
                    "matched_segment_ids": ["draft_99"],  # Hallucinated ID
                    "rationale": "Not there",
                },
            ]
        }

    import app.agents.gap_mapper

    monkeypatch.setattr(app.agents.gap_mapper, "call_gemini", fake_call_gemini)

    results = asyncio.run(map_compliance(reqs, draft))

    assert len(results) == 3
    
    r1 = next(r for r in results if r.req_id == "r1")
    assert r1.status == "met"
    assert "draft_1" in r1.matched_segment_ids

    r2 = next(r for r in results if r.req_id == "r2")
    assert r2.status == "weak"
    assert "draft_2" in r2.matched_segment_ids

    # Verify hallucination guard works: draft_99 should be filtered out
    r3 = next(r for r in results if r.req_id == "r3")
    assert r3.status == "missing"
    assert len(r3.matched_segment_ids) == 0, \
        "Hallucinated segment ID 'draft_99' should be filtered out for missing status"


def test_gap_mapper_incomplete_response(monkeypatch):
    """Test that retry logic works when LLM returns incomplete results."""
    reqs = [
        Requirement(
            req_id="r1",
            category="Technical",
            requirement_text="Requirement 1",
            source_segment_ids=["rfp_1"],
            criticality="hard",
        ),
        Requirement(
            req_id="r2",
            category="Technical",
            requirement_text="Requirement 2",
            source_segment_ids=["rfp_2"],
            criticality="hard",
        ),
        Requirement(
            req_id="r3",
            category="Functional",
            requirement_text="Requirement 3",
            source_segment_ids=["rfp_3"],
            criticality="hard",
        ),
    ]
    draft = [
        Segment(
            id="draft_1",
            section="Main",
            para_idx=1,
            text="Content here.",
            char_span=(0, 10),
        ),
    ]

    call_count = 0

    def fake_call_gemini_incomplete(prompt, schema, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # First call: missing r3
            return {
                "results": [
                    {
                        "req_id": "r1",
                        "status": "met",
                        "matched_segment_ids": ["draft_1"],
                        "rationale": "Has requirement 1",
                    },
                    {
                        "req_id": "r2",
                        "status": "missing",
                        "matched_segment_ids": [],
                        "rationale": "Missing requirement 2",
                    },
                ]
            }
        else:
            # Second call (retry): includes r3
            return {
                "results": [
                    {
                        "req_id": "r3",
                        "status": "weak",
                        "matched_segment_ids": ["draft_1"],
                        "rationale": "Partially covers requirement 3",
                    },
                ]
            }

    import app.agents.gap_mapper

    monkeypatch.setattr(app.agents.gap_mapper, "call_gemini", fake_call_gemini_incomplete)

    results = asyncio.run(map_compliance(reqs, draft))

    # Should have all 3 results after retry
    assert len(results) == 3, f"Expected 3 results after retry, got {len(results)}"
    assert call_count == 2, "Should have called LLM twice (initial + retry)"
    
    res_map = {r.req_id: r for r in results}
    assert "r1" in res_map
    assert "r2" in res_map
    assert "r3" in res_map
    assert res_map["r3"].status == "weak"


def test_gap_mapper_empty_requirements():
    """Test that empty requirements list raises ValueError."""
    draft = [
        Segment(
            id="draft_1",
            section="Main",
            para_idx=1,
            text="Content.",
            char_span=(0, 8),
        ),
    ]
    
    with pytest.raises(ValueError, match="requirements list cannot be empty"):
        asyncio.run(map_compliance([], draft))


def test_gap_mapper_empty_draft():
    """Test that empty draft segments list raises ValueError."""
    reqs = [
        Requirement(
            req_id="r1",
            category="Technical",
            requirement_text="Must have X",
            source_segment_ids=["rfp_1"],
            criticality="hard",
        ),
    ]
    
    with pytest.raises(ValueError, match="draft_segments list cannot be empty"):
        asyncio.run(map_compliance(reqs, []))


def test_gap_mapper_pads_missing_requirements(monkeypatch):
    """Test that requirements missing after retry are padded with default missing status."""
    reqs = [
        Requirement(
            req_id="r1",
            category="Technical",
            requirement_text="Requirement 1",
            source_segment_ids=["rfp_1"],
            criticality="hard",
        ),
        Requirement(
            req_id="r2",
            category="Technical",
            requirement_text="Requirement 2",
            source_segment_ids=["rfp_2"],
            criticality="hard",
        ),
    ]
    draft = [
        Segment(
            id="draft_1",
            section="Main",
            para_idx=1,
            text="Content.",
            char_span=(0, 8),
        ),
    ]

    def fake_call_gemini_always_incomplete(prompt, schema, **kwargs):
        # Always returns only r1, never r2 (even after retry)
        return {
            "results": [
                {
                    "req_id": "r1",
                    "status": "met",
                    "matched_segment_ids": ["draft_1"],
                    "rationale": "Has requirement 1",
                },
            ]
        }

    import app.agents.gap_mapper

    monkeypatch.setattr(app.agents.gap_mapper, "call_gemini", fake_call_gemini_always_incomplete)

    results = asyncio.run(map_compliance(reqs, draft))

    # Should still have 2 results (r2 padded with default)
    assert len(results) == 2
    
    res_map = {r.req_id: r for r in results}
    assert res_map["r1"].status == "met"
    assert res_map["r2"].status == "missing"
    assert res_map["r2"].rationale == "Not evaluated — extraction incomplete"
    assert len(res_map["r2"].matched_segment_ids) == 0
