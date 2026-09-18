"""End-to-end integration test for Sprint 1 + Sprint 2 pipeline.

Tests the complete workflow via FastAPI TestClient:
1. Create session
2. Segment RFP and draft documents
3. Extract requirements from RFP
4. Map compliance (gap analysis)
5. Validate session state and ground truth assertions
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

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

# Use actual response_1_weak.md content
DRAFT_WEAK = """# Proposal: Inventory Visibility Solution for NordFrame Logistics

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


@pytest.mark.integration
def test_sprint2_end_to_end():
    """Complete end-to-end test of Sprint 1 + Sprint 2 pipeline via HTTP API.
    
    This test validates:
    - Session creation and management
    - Document segmentation (Sprint 1)
    - Requirement extraction (Sprint 1)
    - Compliance mapping (Sprint 2)
    - Ground truth validation against NordFrame RFP vs response_1_weak.md
    - AuditState integrity throughout the workflow
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
        json={"rfp_text": RFP_NORDFRAME, "draft_text": DRAFT_WEAK}
    )
    assert response.status_code == 200
    segment_data = response.json()
    assert "rfp_segments" in segment_data
    assert "draft_segments" in segment_data
    assert len(segment_data["rfp_segments"]) > 0
    assert len(segment_data["draft_segments"]) > 0
    print(f"✓ Segmented: {len(segment_data['rfp_segments'])} RFP segments, "
          f"{len(segment_data['draft_segments'])} draft segments")
    
    # Step 3: Extract requirements from RFP
    response = client.post(f"/audit/session/{session_id}/extract-requirements")
    assert response.status_code == 200
    requirements = response.json()
    assert len(requirements) > 0
    print(f"✓ Extracted {len(requirements)} requirements")
    
    # Validate requirements structure
    for req in requirements:
        assert "req_id" in req
        assert "category" in req
        assert "requirement_text" in req
        assert "source_segment_ids" in req
        assert "criticality" in req
        assert req["criticality"] in ["hard", "soft"]
    
    # Expect at least 9 requirements (NordFrame RFP has 7 numbered + budget + timeline)
    assert len(requirements) >= 9, \
        f"Expected at least 9 requirements from NordFrame RFP, got {len(requirements)}"
    
    # Step 4: Map compliance (Gap Mapper - Sprint 2)
    response = client.post(f"/audit/session/{session_id}/map-compliance")
    assert response.status_code == 200
    compliance_results = response.json()
    assert len(compliance_results) == len(requirements), \
        f"Expected {len(requirements)} compliance results, got {len(compliance_results)}"
    print(f"✓ Mapped {len(compliance_results)} compliance results")
    
    # Validate compliance result structure
    for result in compliance_results:
        assert "req_id" in result
        assert "status" in result
        assert "matched_segment_ids" in result
        assert "rationale" in result
        assert result["status"] in ["met", "weak", "missing"]
        
        # Validate matched_segment_ids logic
        if result["status"] == "missing":
            assert len(result["matched_segment_ids"]) == 0, \
                f"Missing status should have empty matched_segment_ids for {result['req_id']}"
        
        # Validate rationale is meaningful
        assert len(result["rationale"]) > 20, \
            f"Rationale for {result['req_id']} should be substantial"
    
    # Step 5: Validate session state integrity
    response = client.get(f"/audit/session/{session_id}")
    assert response.status_code == 200
    session_state = response.json()
    
    # Verify all fields are populated correctly
    assert len(session_state["rfp_segments"]) > 0
    assert len(session_state["draft_segments"]) > 0
    assert len(session_state["requirements"]) == len(requirements)
    assert len(session_state["compliance_map"]) == len(compliance_results)
    print("✓ Session state validated - all fields populated correctly")
    
    # Step 6: Ground truth validation (NordFrame RFP vs response_1_weak.md)
    res_map = {r["req_id"]: r for r in compliance_results}
    
    # Count status distribution
    status_counts = {"met": 0, "weak": 0, "missing": 0}
    for r in compliance_results:
        status_counts[r["status"]] += 1
    
    print(f"\n✓ Status distribution: met={status_counts['met']}, "
          f"weak={status_counts['weak']}, missing={status_counts['missing']}")
    
    # Validate expected patterns based on ground truth
    # response_1_weak.md should have:
    # - Many "missing" (deferred pricing, no timeline, no PostgreSQL confirmation, etc.)
    # - Few "met" (web dashboard is clearly described)
    # - Some "weak" (role-based access mentioned vaguely)
    
    assert status_counts["missing"] >= 5, \
        "response_1_weak.md should have at least 5 missing requirements"
    assert status_counts["met"] >= 1, \
        "response_1_weak.md should have at least 1 met requirement (web dashboard)"
    
    # Validate specific key requirements if we can identify them
    # Note: req_ids are generated by LLM so we match by requirement_text patterns
    req_by_content = {
        req["requirement_text"].lower(): req["req_id"] 
        for req in requirements
    }
    
    # Check PostgreSQL requirement (should be missing - never confirmed)
    postgresql_req = next(
        (req for req in requirements if "postgresql" in req["requirement_text"].lower()),
        None
    )
    if postgresql_req:
        postgres_result = res_map[postgresql_req["req_id"]]
        assert postgres_result["status"] == "missing", \
            "PostgreSQL constraint should be missing (never confirmed in draft)"
        print(f"✓ PostgreSQL requirement correctly marked as missing")
    
    # Check web dashboard requirement (should be met - clearly described)
    dashboard_req = next(
        (req for req in requirements if "dashboard" in req["requirement_text"].lower() 
         and "web" in req["requirement_text"].lower()),
        None
    )
    if dashboard_req:
        dashboard_result = res_map[dashboard_req["req_id"]]
        assert dashboard_result["status"] == "met", \
            "Web dashboard should be met (clearly described in draft)"
        assert len(dashboard_result["matched_segment_ids"]) > 0
        print(f"✓ Web dashboard requirement correctly marked as met")
    
    # Check budget requirement (should be missing - deferred)
    budget_req = next(
        (req for req in requirements if "budget" in req["requirement_text"].lower() 
         or "€" in req["requirement_text"] or "80" in req["requirement_text"]),
        None
    )
    if budget_req:
        budget_result = res_map[budget_req["req_id"]]
        assert budget_result["status"] == "missing", \
            "Budget should be missing (deferred: 'provided upon further discussion')"
        print(f"✓ Budget requirement correctly marked as missing (deferred)")
    
    # Validate no requirement was silently dropped
    req_ids_in_requirements = {req["req_id"] for req in requirements}
    req_ids_in_compliance = {r["req_id"] for r in compliance_results}
    assert req_ids_in_requirements == req_ids_in_compliance, \
        "All requirements must have corresponding compliance results"
    print("✓ No requirements were silently dropped")
    
    print("\n✅ End-to-end Sprint 2 pipeline test passed!")
    print(f"   Processed {len(requirements)} requirements from NordFrame RFP")
    print(f"   Evaluated against response_1_weak.md draft proposal")
    print(f"   Ground truth validation: PASSED")


@pytest.mark.integration
def test_sprint2_e2e_error_handling():
    """Test error handling in the Sprint 2 pipeline."""
    client = TestClient(app)
    
    # Create session
    response = client.post("/audit/session")
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    
    # Try to map compliance without segmenting first (should get 400)
    response = client.post(f"/audit/session/{session_id}/map-compliance")
    assert response.status_code == 400
    assert "requirements is empty" in response.json()["detail"]
    print("✓ Correctly returns 400 when requirements missing")
    
    # Segment documents
    client.post(
        f"/audit/session/{session_id}/segment",
        json={"rfp_text": RFP_NORDFRAME, "draft_text": DRAFT_WEAK}
    )
    
    # Try to map compliance without extracting requirements (should get 400)
    response = client.post(f"/audit/session/{session_id}/map-compliance")
    assert response.status_code == 400
    assert "requirements is empty" in response.json()["detail"]
    print("✓ Correctly returns 400 when requirements not extracted")
    
    # Extract requirements
    client.post(f"/audit/session/{session_id}/extract-requirements")
    
    # Now it should work
    response = client.post(f"/audit/session/{session_id}/map-compliance")
    assert response.status_code == 200
    print("✓ Succeeds when all prerequisites are met")
    
    # Test invalid session ID
    response = client.post("/audit/session/invalid-id/map-compliance")
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]
    print("✓ Correctly returns 404 for invalid session")
    
    print("\n✅ Error handling test passed!")
