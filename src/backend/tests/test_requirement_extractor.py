import asyncio

import pytest

from app.agents.requirement_extractor import extract_requirements
from app.agents.segmenter import segment_document

RFP_TEXT = """# 1. Scope
1. Web-based real-time dashboard across 6 warehouses
2. Automated low-stock alerts
3. Integration with existing PostgreSQL database (no migration)
4. Role-based access

# 2. Implementation
5. Data migration and onboarding rollout plan
6. Support & maintenance SLAs after go-live
7. Documented assumptions, limitations, and risks

Budget: €80,000–120,000
Timeline: Pilot in 3 months, full rollout in 6 months
"""


@pytest.mark.integration
def test_requirement_extractor():
    segments = segment_document(RFP_TEXT, "rfp")
    reqs = asyncio.run(extract_requirements(segments))

    # Expecting 7 numbered + 2 unnumbered (budget/timeline)
    assert len(reqs) >= 7

    hard_reqs = [r for r in reqs if r.criticality == "hard"]
    assert len(hard_reqs) >= 7

    has_budget = any(r.category == "Budget" for r in reqs)
    has_timeline = any(r.category == "Timeline" for r in reqs)
    assert has_budget and has_timeline

    pg_req = next(
        r for r in reqs if "PostgreSQL" in r.requirement_text or "database" in r.requirement_text
    )
    assert pg_req.criticality == "hard"

    # Verify source_segment_ids validity
    valid_ids = {s.id for s in segments}
    for r in reqs:
        assert len(r.source_segment_ids) > 0
        for sid in r.source_segment_ids:
            assert sid in valid_ids
