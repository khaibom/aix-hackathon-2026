"""Integration test for rewriter against NordFrame RFP + response_1_weak.md."""
import asyncio

import pytest

from app.agents.rewriter import generate_rewrites
from app.agents.segmenter import segment_document
from app.models.schemas import ComplianceResult, Requirement

# Reuse fixtures from scorer integration test
from test_scorer_integration import (
    EXPECTED_COMPLIANCE_MAP,
    NORDFRAME_REQUIREMENTS,
    WEAK_DRAFT_FULL,
)


@pytest.mark.integration
def test_rewriter_integration_nordframe():
    """Test rewriter against NordFrame data with ground truth validation.
    
    Expected behavior:
    - Generate suggestions for weak + missing requirements only (8 total: 7 missing + 1 weak)
    - NO suggestions for met requirements (1 met: web dashboard)
    - All suggested_text > 10 chars
    - No placeholder patterns
    - Concrete RFP details used (e.g., actual budget €80k-120k)
    """
    draft_segments = segment_document(WEAK_DRAFT_FULL, "draft")
    
    # Run rewriter
    rewrites = asyncio.run(
        generate_rewrites(
            NORDFRAME_REQUIREMENTS,
            EXPECTED_COMPLIANCE_MAP,
            draft_segments,
        )
    )
    
    # Count weak and missing in compliance_map
    weak_count = sum(1 for c in EXPECTED_COMPLIANCE_MAP if c.status == "weak")
    missing_count = sum(1 for c in EXPECTED_COMPLIANCE_MAP if c.status == "missing")
    met_count = sum(1 for c in EXPECTED_COMPLIANCE_MAP if c.status == "met")
    expected_rewrite_count = weak_count + missing_count
    
    print(f"\nCompliance map: {met_count} met, {weak_count} weak, {missing_count} missing")
    print(f"Expected {expected_rewrite_count} suggestions (weak + missing)")
    print(f"Generated {len(rewrites)} suggestions")
    
    # Validate count matches weak + missing
    assert len(rewrites) == expected_rewrite_count, \
        f"Expected {expected_rewrite_count} suggestions, got {len(rewrites)}"
    
    # Validate no suggestions for met requirements
    met_req_ids = {c.req_id for c in EXPECTED_COMPLIANCE_MAP if c.status == "met"}
    rewrite_req_ids = {rw.req_id for rw in rewrites}
    overlap = met_req_ids & rewrite_req_ids
    assert not overlap, \
        f"Should not generate suggestions for met requirements, found: {overlap}"
    
    # Validate all suggested_text is substantial
    for rw in rewrites:
        assert len(rw.suggested_text) > 10, \
            f"{rw.req_id}: suggested_text too short ({len(rw.suggested_text)} chars)"
    
    # Validate no placeholder patterns
    placeholder_patterns = ["[insert", "[add", "[...]", "TBD", "to be determined"]
    for rw in rewrites:
        lower_text = rw.suggested_text.lower()
        for pattern in placeholder_patterns:
            assert pattern.lower() not in lower_text, \
                f"{rw.req_id}: suggested_text contains placeholder '{pattern}': {rw.suggested_text[:100]}"
    
    # Validate specific requirements use concrete RFP details
    
    # PostgreSQL requirement (req_000) - should mention "PostgreSQL"
    postgres_rw = next((rw for rw in rewrites if rw.req_id == "req_000"), None)
    if postgres_rw:
        assert "postgresql" in postgres_rw.suggested_text.lower(), \
            f"PostgreSQL suggestion should mention 'PostgreSQL': {postgres_rw.suggested_text}"
        print(f"✓ PostgreSQL suggestion uses concrete term")
    
    # Budget requirement (req_004) - should mention actual figures
    budget_rw = next((rw for rw in rewrites if rw.req_id == "req_004"), None)
    if budget_rw:
        has_concrete_budget = (
            "€80" in budget_rw.suggested_text or
            "80,000" in budget_rw.suggested_text or
            "120" in budget_rw.suggested_text or
            "120,000" in budget_rw.suggested_text
        )
        assert has_concrete_budget, \
            f"Budget suggestion should mention actual amounts (€80k-120k): {budget_rw.suggested_text}"
        print(f"✓ Budget suggestion uses concrete figures from RFP")
    
    # Timeline requirement (req_005) - should mention concrete months
    timeline_rw = next((rw for rw in rewrites if rw.req_id == "req_005"), None)
    if timeline_rw:
        has_concrete_timeline = (
            "3 month" in timeline_rw.suggested_text.lower() or
            "6 month" in timeline_rw.suggested_text.lower() or
            "pilot" in timeline_rw.suggested_text.lower()
        )
        assert has_concrete_timeline, \
            f"Timeline suggestion should mention concrete months: {timeline_rw.suggested_text}"
        print(f"✓ Timeline suggestion uses concrete milestones")
    
    # Role-based access (req_002) - weak status, should have original_text
    role_rw = next((rw for rw in rewrites if rw.req_id == "req_002"), None)
    if role_rw:
        # This requirement is "weak", so should have original_text
        compliance_result = next(c for c in EXPECTED_COMPLIANCE_MAP if c.req_id == "req_002")
        if compliance_result.status == "weak":
            assert role_rw.original_text is not None, \
                "Weak requirement should have original_text (not None)"
            assert len(role_rw.original_text) > 0, \
                "Weak requirement should have non-empty original_text"
            print(f"✓ Weak requirement has original_text")
    
    # Validate insertion_point is meaningful
    for rw in rewrites:
        assert rw.insertion_point and len(rw.insertion_point) > 5, \
            f"{rw.req_id}: insertion_point too short or empty: '{rw.insertion_point}'"
    
    print(f"\n✓ All rewriter validation checks passed")
    print(f"   Generated {len(rewrites)} concrete suggestions")
    print(f"   No placeholders found")
    print(f"   Concrete RFP details verified")
