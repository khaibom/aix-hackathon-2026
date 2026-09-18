import asyncio
from app.agents.segmenter import segment_document
from app.agents.requirement_extractor import extract_requirements

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

segments = segment_document(RFP_TEXT, "rfp")
reqs = asyncio.run(extract_requirements(segments))
for r in reqs:
    print(r.model_dump())
