import asyncio

import pytest

from app.agents.gap_mapper import map_compliance
from app.agents.segmenter import segment_document
from app.models.schemas import Requirement

# Full content from response_1_weak.md - the deliberately weak, generic draft
WEAK_DRAFT_FULL = """# Proposal: Inventory Visibility Solution for NordFrame Logistics

**Submitted by:** BrightPath Software Solutions (fictional)
**Variant: WEAK — generic, deferred on key items**

## Introduction
Thank you for considering BrightPath for your inventory management needs.
We are a software company with experience delivering dashboards and data
solutions for logistics and retail clients across Europe.

## Our Understanding
NordFrame needs better visibility into warehouse inventory. We propose
building a modern dashboard solution to solve this.

## Our Approach
We will build a cloud-based dashboard that displays inventory data in real
time. Managers will be able to log in and view stock levels. The system
will be built using modern, scalable cloud architecture and industry best
practices to ensure reliability and performance.

## Features
- Real-time inventory dashboard
- Notifications for low stock
- Secure login for different users

## Timeline
We will begin work shortly after contract signing and aim to deliver the
solution in a timely manner, with regular updates along the way.

## Pricing
Pricing will be provided upon further discussion of detailed requirements,
and will depend on final scope.

## Why BrightPath
We have a talented team of engineers passionate about solving real business
problems with technology. We look forward to partnering with NordFrame
Logistics on this exciting project.
"""

# NordFrame RFP requirements (9 total) matching Sprint 1's extraction format
REQS = [
    Requirement(
        req_id="req_000",
        category="Technical",
        requirement_text="Integration with existing PostgreSQL database (no migration)",
        source_segment_ids=["rfp_001"],
        criticality="hard",
    ),
    Requirement(
        req_id="req_001",
        category="Functional",
        requirement_text="Data migration and onboarding rollout plan for 6 sites with minimal disruption",
        source_segment_ids=["rfp_002"],
        criticality="hard",
    ),
    Requirement(
        req_id="req_002",
        category="Technical",
        requirement_text="Role-based access: warehouse managers see only their site, HQ staff see all sites",
        source_segment_ids=["rfp_003"],
        criticality="hard",
    ),
    Requirement(
        req_id="req_003",
        category="Compliance/SLA",
        requirement_text="Support & maintenance terms after go-live (response times, SLAs)",
        source_segment_ids=["rfp_004"],
        criticality="hard",
    ),
    Requirement(
        req_id="req_004",
        category="Budget",
        requirement_text="Budget: €80,000–€120,000 total including first year of support",
        source_segment_ids=["rfp_005"],
        criticality="soft",
    ),
    Requirement(
        req_id="req_005",
        category="Timeline",
        requirement_text="Working pilot at one warehouse within 3 months; full rollout to all 6 sites within 6 months",
        source_segment_ids=["rfp_006"],
        criticality="hard",
    ),
    Requirement(
        req_id="req_006",
        category="Risk/Assumptions",
        requirement_text="Clear documentation of assumptions, limitations, or risks",
        source_segment_ids=["rfp_007"],
        criticality="soft",
    ),
    Requirement(
        req_id="req_007",
        category="Functional",
        requirement_text="Web-based dashboard showing real-time inventory levels across all 6 warehouses",
        source_segment_ids=["rfp_008"],
        criticality="hard",
    ),
    Requirement(
        req_id="req_008",
        category="Functional",
        requirement_text="Automated low-stock alerts sent to warehouse managers when items fall below configurable threshold",
        source_segment_ids=["rfp_009"],
        criticality="hard",
    ),
]


@pytest.mark.integration
def test_gap_mapper_integration():
    """Integration test using full response_1_weak.md against NordFrame RFP requirements.
    
    This validates the ground truth expectations:
    - PostgreSQL constraint -> missing (never confirmed)
    - Migration/onboarding plan -> missing (no rollout section)
    - Role-based access -> weak (mentions "secure login" but not the two-tier split)
    - Support & maintenance SLAs -> missing (not mentioned)
    - Budget -> missing (deferred: "provided upon further discussion")
    - Timeline -> missing (no concrete dates)
    - Risks/assumptions -> missing (nothing disclosed)
    - Web dashboard -> met (clearly described)
    - Low-stock alerts -> met or weak (draft mentions "notifications for low stock")
    """
    draft_segments = segment_document(WEAK_DRAFT_FULL, "draft")
    results = asyncio.run(map_compliance(REQS, draft_segments))

    # Must return exactly 9 results (one per requirement)
    assert len(results) == 9, f"Expected 9 results, got {len(results)}"

    # Convert to dict for easier assertions
    res_map = {r.req_id: r for r in results}

    # Ground truth assertions based on response_1_weak.md content
    
    # req_000: PostgreSQL/no-migration -> MISSING (draft never confirms this constraint)
    assert res_map["req_000"].status == "missing", \
        f"PostgreSQL requirement should be missing, got {res_map['req_000'].status}"
    assert len(res_map["req_000"].matched_segment_ids) == 0, \
        "Missing status should have empty matched_segment_ids"
    
    # req_001: Migration/onboarding plan -> MISSING (no rollout section at all)
    assert res_map["req_001"].status == "missing", \
        f"Migration plan should be missing, got {res_map['req_001'].status}"
    assert len(res_map["req_001"].matched_segment_ids) == 0
    
    # req_002: Role-based access -> WEAK (says "secure login for different users" but no tier split)
    assert res_map["req_002"].status == "weak", \
        f"Role-based access should be weak, got {res_map['req_002'].status}"
    assert len(res_map["req_002"].matched_segment_ids) > 0, \
        "Weak status should have non-empty matched_segment_ids"
    
    # req_003: Support & maintenance SLAs -> MISSING (not mentioned anywhere)
    assert res_map["req_003"].status == "missing", \
        f"Support SLAs should be missing, got {res_map['req_003'].status}"
    assert len(res_map["req_003"].matched_segment_ids) == 0
    
    # req_004: Budget -> MISSING (deferred: "provided upon further discussion")
    assert res_map["req_004"].status == "missing", \
        f"Budget should be missing (deferred), got {res_map['req_004'].status}"
    assert len(res_map["req_004"].matched_segment_ids) == 0
    
    # req_005: Timeline -> MISSING (no concrete dates, just "in a timely manner")
    assert res_map["req_005"].status == "missing", \
        f"Timeline should be missing, got {res_map['req_005'].status}"
    assert len(res_map["req_005"].matched_segment_ids) == 0
    
    # req_006: Risks/assumptions -> MISSING (nothing disclosed)
    assert res_map["req_006"].status == "missing", \
        f"Risks should be missing, got {res_map['req_006'].status}"
    assert len(res_map["req_006"].matched_segment_ids) == 0
    
    # req_007: Web dashboard -> MET (draft clearly describes "cloud-based dashboard")
    assert res_map["req_007"].status == "met", \
        f"Web dashboard should be met, got {res_map['req_007'].status}"
    assert len(res_map["req_007"].matched_segment_ids) > 0, \
        "Met status should have non-empty matched_segment_ids"
    
    # req_008: Low-stock alerts -> MET or WEAK (draft says "notifications for low stock")
    # Could be "met" if LLM considers it sufficient, or "weak" if it expects more detail
    assert res_map["req_008"].status in ["met", "weak"], \
        f"Low-stock alerts should be met or weak, got {res_map['req_008'].status}"
    if res_map["req_008"].status != "missing":
        assert len(res_map["req_008"].matched_segment_ids) > 0

    # Validate all matched_segment_ids are valid draft segment IDs
    valid_draft_ids = {s.id for s in draft_segments}
    for r in results:
        for sid in r.matched_segment_ids:
            assert sid.startswith("draft_"), \
                f"Segment ID {sid} should start with 'draft_'"
            assert sid in valid_draft_ids, \
                f"Segment ID {sid} not found in draft segments"
    
    # Validate rationale is present and meaningful for all results
    for r in results:
        assert len(r.rationale) > 20, \
            f"Rationale for {r.req_id} should be substantial, got: {r.rationale}"
        # Rationale should reference what was asked for
        assert any(keyword in r.rationale.lower() for keyword in ["rfp", "require", "draft", "proposal"]), \
            f"Rationale for {r.req_id} should reference RFP/requirement and draft"

    print("\n✓ All ground truth assertions passed")
    print(f"✓ Status distribution: met={sum(1 for r in results if r.status == 'met')}, "
          f"weak={sum(1 for r in results if r.status == 'weak')}, "
          f"missing={sum(1 for r in results if r.status == 'missing')}")

