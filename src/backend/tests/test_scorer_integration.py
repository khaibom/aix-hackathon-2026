"""Integration test for scorer against NordFrame RFP + response_1_weak.md ground truth."""
import asyncio

import pytest

from app.agents.scorer import score_proposal
from app.agents.segmenter import segment_document
from app.models.schemas import ComplianceResult, Requirement

# Full content from response_1_weak.md
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

# NordFrame RFP requirements (9 total) matching Sprint 1's extraction
NORDFRAME_REQUIREMENTS = [
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

# Expected compliance_map from Sprint 2 (7 missing, 1 met, 1 weak)
EXPECTED_COMPLIANCE_MAP = [
    ComplianceResult(
        req_id="req_000", status="missing", matched_segment_ids=[], rationale="PostgreSQL not confirmed"
    ),
    ComplianceResult(
        req_id="req_001", status="missing", matched_segment_ids=[], rationale="No rollout plan"
    ),
    ComplianceResult(
        req_id="req_002", status="weak", matched_segment_ids=["draft_003"], rationale="Vague role-based access"
    ),
    ComplianceResult(
        req_id="req_003", status="missing", matched_segment_ids=[], rationale="No SLA terms"
    ),
    ComplianceResult(
        req_id="req_004", status="missing", matched_segment_ids=[], rationale="Pricing deferred"
    ),
    ComplianceResult(
        req_id="req_005", status="missing", matched_segment_ids=[], rationale="No concrete timeline"
    ),
    ComplianceResult(
        req_id="req_006", status="missing", matched_segment_ids=[], rationale="No risks disclosed"
    ),
    ComplianceResult(
        req_id="req_007", status="met", matched_segment_ids=["draft_002"], rationale="Dashboard described"
    ),
    ComplianceResult(
        req_id="req_008", status="met", matched_segment_ids=["draft_003"], rationale="Alerts mentioned"
    ),
]


@pytest.mark.integration
def test_scorer_integration_nordframe():
    """Test scorer against NordFrame RFP + response_1_weak.md with ground truth validation.
    
    Expected scores (from scoring_example.md) with +/-1 tolerance:
    - Problem Understanding: 3/5 (target, allow 2-4)
    - Scope & Deliverables Clarity: 2/5 (target, allow 1-3)
    - Pricing Clarity: 1/5 (must be 1, fully deferred)
    - Timeline Clarity: 1/5 (must be 1, vague)
    - Completeness: 2/5 (deterministic: 1 met + 0.5*1 weak = 1.5/9 = 0.167 -> round(1+0.167*4)=2)
    - Tone & Persuasiveness: 2/5 (target, allow 1-3)
    - Risk/Assumptions Transparency: 1/5 (must be 1, nothing disclosed)
    - Overall: ~1.7/5 (allow 1.3-2.1)
    """
    draft_segments = segment_document(WEAK_DRAFT_FULL, "draft")
    
    # Run scorer with equal weights
    scores, overall = asyncio.run(
        score_proposal(
            NORDFRAME_REQUIREMENTS,
            EXPECTED_COMPLIANCE_MAP,
            draft_segments,
            weights=None  # Equal weights
        )
    )
    
    assert len(scores) == 7, f"Expected 7 scores, got {len(scores)}"
    
    # Convert to dict for easier access
    score_dict = {s.criterion: s for s in scores}
    
    # Validate Completeness (deterministic)
    completeness = score_dict["Completeness vs. RFP Requirements"]
    # 1 met + 1 weak + 7 missing out of 9
    # (1 + 0.5*1) / 9 = 1.5/9 = 0.167 -> round(1 + 0.167*4) = round(1.667) = 2
    assert completeness.score_1to5 in [1, 2], \
        f"Completeness should be 1-2 (7 missing), got {completeness.score_1to5}"
    assert "1 of 9" in completeness.comment or "2 of 9" in completeness.comment, \
        f"Comment should mention counts: {completeness.comment}"
    
    # Validate Problem Understanding (allow +/-1)
    problem = score_dict["Problem Understanding"]
    assert 2 <= problem.score_1to5 <= 4, \
        f"Problem Understanding should be 2-4, got {problem.score_1to5}"
    
    # Validate Scope & Deliverables Clarity (allow +/-1)
    scope = score_dict["Scope & Deliverables Clarity"]
    assert 1 <= scope.score_1to5 <= 3, \
        f"Scope & Deliverables should be 1-3, got {scope.score_1to5}"
    
    # Validate Pricing Clarity (must be 1, fully deferred)
    pricing = score_dict["Pricing Clarity"]
    assert pricing.score_1to5 == 1, \
        f"Pricing should be 1 (fully deferred), got {pricing.score_1to5}"
    
    # Validate Timeline Clarity (should be 1, vague)
    timeline = score_dict["Timeline Clarity"]
    assert timeline.score_1to5 in [1, 2], \
        f"Timeline should be 1-2 (vague), got {timeline.score_1to5}"
    
    # Validate Tone & Persuasiveness (allow +/-1)
    tone = score_dict["Tone & Persuasiveness"]
    assert 1 <= tone.score_1to5 <= 3, \
        f"Tone should be 1-3, got {tone.score_1to5}"
    
    # Validate Risk/Assumptions Transparency (should be 1, nothing disclosed)
    risk = score_dict["Risk/Assumptions Transparency"]
    assert risk.score_1to5 in [1, 2], \
        f"Risk should be 1-2 (nothing disclosed), got {risk.score_1to5}"
    
    # Validate overall (target ~1.7, allow 1.3-2.1)
    assert 1.3 <= overall <= 2.1, \
        f"Overall should be 1.3-2.1 (weak proposal), got {overall:.2f}"
    
    # Validate all weights sum to 1.0
    total_weight = sum(s.weight for s in scores)
    assert abs(total_weight - 1.0) < 0.001, \
        f"Total weight should be 1.0, got {total_weight}"
    
    print("\n✓ All ground truth assertions passed")
    print(f"   Scores: {[(s.criterion[:20], s.score_1to5) for s in scores]}")
    print(f"   Overall: {overall:.2f}")
    print(f"   Completeness (deterministic): {completeness.score_1to5}/5")
    print(f"   Comment: {completeness.comment}")
