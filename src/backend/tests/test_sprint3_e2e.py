"""End-to-end integration test for Sprint 1+2+3 pipeline via HTTP API."""
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Reuse test data
from test_scorer_integration import NORDFRAME_REQUIREMENTS, WEAK_DRAFT_FULL

# Use actual NordFrame RFP content
RFP_NORDFRAME = """# Request for Proposal — Warehouse Inventory Dashboard

**Client:** NordFrame Logistics GmbH (fictional)
**Industry:** Logistics / Warehousing

## Background
NordFrame Logistics operates 6 regional warehouses across Germany and
Austria. Our current inventory tracking is split across spreadsheets and an
outdated legacy system, making it hard to get a real-time view of stock
levels across sites.

## Requirements
1. A **web-based dashboard** showing real-time inventory levels across all 6
   warehouses.
2. **Automated low-stock alerts** sent to warehouse managers when items fall
   below a configurable threshold.
3. Integration with our **existing PostgreSQL inventory database** — no
   migration to a new database.
4. **Role-based access** — warehouse managers should only see their own
   site; HQ staff should see all sites.
5. A **data migration / onboarding plan** for rolling this out across all 6
   sites with minimal disruption.
6. **Support & maintenance terms** after go-live (response times, SLAs).
7. Clear documentation of any **assumptions, limitations, or risks**, since
   inventory decisions will be made based on this system.

## Budget
€80,000–€120,000 total, including first year of support.

## Timeline
Working pilot at one warehouse within 3 months; full rollout to all 6 sites
within 6 months.

## Decision Date
End of this quarter.
"""


@pytest.mark.integration
def test_sprint3_end_to_end():
    """Complete end-to-end test of Sprint 1+2+3 pipeline via HTTP API.
    
    Validates:
    - Session creation and management
    - Document segmentation (Sprint 1)
    - Requirement extraction (Sprint 1)
    - Compliance mapping (Sprint 2)
    - Scoring with equal weights (Sprint 3)
    - Rewrite generation (Sprint 3)
    - Rescoring with custom weights (Sprint 3)
    - Session state integrity throughout
    """
    client = TestClient(app)
    
    # Step 1: Create a new session
    response = client.post("/audit/session")
    assert response.status_code == 200
    session_data = response.json()
    assert "session_id" in session_data
    session_id = session_data["session_id"]
    print(f"\n✓ Session created: {session_id}")
    
    # Step 2: Segment RFP and draft documents
    response = client.post(
        f"/audit/session/{session_id}/segment",
        json={"rfp_text": RFP_NORDFRAME, "draft_text": WEAK_DRAFT_FULL}
    )
    assert response.status_code == 200
    segment_data = response.json()
    assert "rfp_segments" in segment_data
    assert "draft_segments" in segment_data
    rfp_seg_count = len(segment_data["rfp_segments"])
    draft_seg_count = len(segment_data["draft_segments"])
    print(f"✓ Segmented: {rfp_seg_count} RFP segments, {draft_seg_count} draft segments")
    
    # Step 3: Extract requirements from RFP
    response = client.post(f"/audit/session/{session_id}/extract-requirements")
    assert response.status_code == 200
    requirements = response.json()
    assert len(requirements) >= 9, f"Expected at least 9 requirements, got {len(requirements)}"
    print(f"✓ Extracted {len(requirements)} requirements")
    
    # Step 4: Map compliance (Sprint 2)
    response = client.post(f"/audit/session/{session_id}/map-compliance")
    assert response.status_code == 200
    compliance_results = response.json()
    assert len(compliance_results) == len(requirements)
    
    # Count statuses
    met_count = sum(1 for r in compliance_results if r["status"] == "met")
    weak_count = sum(1 for r in compliance_results if r["status"] == "weak")
    missing_count = sum(1 for r in compliance_results if r["status"] == "missing")
    print(f"✓ Mapped compliance: {met_count} met, {weak_count} weak, {missing_count} missing")
    
    # Step 5: Score proposal with equal weights (Sprint 3)
    response = client.post(f"/audit/session/{session_id}/score")
    assert response.status_code == 200
    score_data = response.json()
    assert "scores" in score_data
    assert "overall" in score_data
    
    scores = score_data["scores"]
    overall_1 = score_data["overall"]
    
    assert len(scores) == 7, f"Expected 7 scores, got {len(scores)}"
    print(f"✓ Scored proposal: overall={overall_1:.2f}")
    
    # Validate scores are in expected ranges
    assert 1.3 <= overall_1 <= 2.1, \
        f"Overall should be 1.3-2.1 for weak proposal, got {overall_1:.2f}"
    
    # Validate Completeness score is present and deterministic
    completeness = next(
        s for s in scores if s["criterion"] == "Completeness vs. RFP Requirements"
    )
    assert 1 <= completeness["score_1to5"] <= 3, \
        f"Completeness should be low for weak proposal, got {completeness['score_1to5']}"
    print(f"   Completeness: {completeness['score_1to5']}/5 - {completeness['comment']}")
    
    # Step 6: Generate rewrites (Sprint 3)
    response = client.post(f"/audit/session/{session_id}/rewrite")
    assert response.status_code == 200
    rewrites = response.json()
    
    expected_rewrite_count = weak_count + missing_count
    assert len(rewrites) == expected_rewrite_count, \
        f"Expected {expected_rewrite_count} rewrites, got {len(rewrites)}"
    print(f"✓ Generated {len(rewrites)} rewrite suggestions")
    
    # Validate all rewrites have substantial suggested_text
    for rw in rewrites:
        assert len(rw["suggested_text"]) > 10, \
            f"Rewrite for {rw['req_id']} has too short suggested_text"
    
    # Step 7: Rescore with custom weights (double weight on Completeness)
    custom_weights = {
        "Problem Understanding": 0.1,
        "Scope & Deliverables Clarity": 0.1,
        "Pricing Clarity": 0.15,
        "Timeline Clarity": 0.15,
        "Completeness vs. RFP Requirements": 0.3,  # Double weight
        "Tone & Persuasiveness": 0.1,
        "Risk/Assumptions Transparency": 0.1,
    }
    
    response = client.post(
        f"/audit/session/{session_id}/rescore",
        json={"weights": custom_weights}
    )
    assert response.status_code == 200
    rescore_data = response.json()
    
    rescored_scores = rescore_data["scores"]
    overall_2 = rescore_data["overall"]
    
    print(f"✓ Rescored with custom weights: overall={overall_2:.2f}")
    
    # Validate overall changed (different weights should yield different overall)
    assert overall_1 != overall_2, \
        "Overall should change with different weights"
    
    # Validate Completeness has higher weight now
    rescored_completeness = next(
        s for s in rescored_scores if s["criterion"] == "Completeness vs. RFP Requirements"
    )
    assert rescored_completeness["weight"] > 0.25, \
        f"Completeness weight should be ~0.3, got {rescored_completeness['weight']}"
    
    # Validate score_1to5 unchanged (only weighted_score changes)
    assert rescored_completeness["score_1to5"] == completeness["score_1to5"], \
        "score_1to5 should not change during rescore"
    
    # Step 8: Validate session state integrity
    response = client.get(f"/audit/session/{session_id}")
    assert response.status_code == 200
    session_state = response.json()
    
    # Verify all fields populated
    assert len(session_state["rfp_segments"]) == rfp_seg_count
    assert len(session_state["draft_segments"]) == draft_seg_count
    assert len(session_state["requirements"]) == len(requirements)
    assert len(session_state["compliance_map"]) == len(compliance_results)
    assert len(session_state["scores"]) == 7
    assert len(session_state["rewrites"]) == len(rewrites)
    
    print("✓ Session state validated - all fields populated correctly")
    
    print(f"\n✅ End-to-end Sprint 3 pipeline test passed!")
    print(f"   Processed {len(requirements)} requirements from NordFrame RFP")
    print(f"   Compliance: {met_count}M + {weak_count}W + {missing_count}X")
    print(f"   Score (equal weights): {overall_1:.2f}")
    print(f"   Score (custom weights): {overall_2:.2f}")
    print(f"   Generated {len(rewrites)} actionable suggestions")


@pytest.mark.integration
def test_rescore_is_instant():
    """Validate that /rescore endpoint is instant (<100ms) with no LLM call."""
    client = TestClient(app)
    
    # Setup: run through scoring first
    response = client.post("/audit/session")
    session_id = response.json()["session_id"]
    
    client.post(
        f"/audit/session/{session_id}/segment",
        json={"rfp_text": RFP_NORDFRAME, "draft_text": WEAK_DRAFT_FULL}
    )
    client.post(f"/audit/session/{session_id}/extract-requirements")
    client.post(f"/audit/session/{session_id}/map-compliance")
    client.post(f"/audit/session/{session_id}/score")
    
    # Now test rescore performance
    custom_weights = {
        "Problem Understanding": 0.15,
        "Scope & Deliverables Clarity": 0.15,
        "Pricing Clarity": 0.15,
        "Timeline Clarity": 0.15,
        "Completeness vs. RFP Requirements": 0.2,
        "Tone & Persuasiveness": 0.1,
        "Risk/Assumptions Transparency": 0.1,
    }
    
    start = time.time()
    response = client.post(
        f"/audit/session/{session_id}/rescore",
        json={"weights": custom_weights}
    )
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.1, \
        f"Rescore took {elapsed:.3f}s, should be <100ms (no LLM call)"
    
    print(f"\n✓ Rescore performance validated: {elapsed*1000:.1f}ms")
    print(f"   This is instant because it uses stored scores (no LLM call)")


@pytest.mark.integration
def test_sprint3_error_handling():
    """Test error handling for Sprint 3 endpoints."""
    client = TestClient(app)
    
    # Create session
    response = client.post("/audit/session")
    session_id = response.json()["session_id"]
    
    # Try to score without compliance_map (should get 400)
    response = client.post(f"/audit/session/{session_id}/score")
    assert response.status_code == 400
    assert "compliance_map is empty" in response.json()["detail"]
    print("✓ Correctly returns 400 when compliance_map missing")
    
    # Try to rewrite without compliance_map (should get 400)
    response = client.post(f"/audit/session/{session_id}/rewrite")
    assert response.status_code == 400
    assert "compliance_map is empty" in response.json()["detail"]
    print("✓ Correctly returns 400 for rewrite when compliance_map missing")
    
    # Try to rescore without scores (should get 400)
    response = client.post(
        f"/audit/session/{session_id}/rescore",
        json={
            "weights": {
                "Problem Understanding": 0.15,
                "Scope & Deliverables Clarity": 0.15,
                "Pricing Clarity": 0.15,
                "Timeline Clarity": 0.15,
                "Completeness vs. RFP Requirements": 0.2,
                "Tone & Persuasiveness": 0.1,
                "Risk/Assumptions Transparency": 0.1,
            }
        }
    )
    assert response.status_code == 400
    assert "scores is empty" in response.json()["detail"]
    print("✓ Correctly returns 400 when rescoring before scoring")
    
    # Run through to scoring
    client.post(
        f"/audit/session/{session_id}/segment",
        json={"rfp_text": RFP_NORDFRAME, "draft_text": WEAK_DRAFT_FULL}
    )
    client.post(f"/audit/session/{session_id}/extract-requirements")
    client.post(f"/audit/session/{session_id}/map-compliance")
    client.post(f"/audit/session/{session_id}/score")
    
    # Try to rescore with missing criterion (should get 400)
    response = client.post(
        f"/audit/session/{session_id}/rescore",
        json={
            "weights": {
                "Problem Understanding": 0.5,
                "Pricing Clarity": 0.5,
                # Missing 5 criteria
            }
        }
    )
    assert response.status_code == 400
    assert "Missing weights for criteria" in response.json()["detail"]
    print("✓ Correctly returns 400 when rescore weights incomplete")
    
    print("\n✅ Error handling test passed!")
