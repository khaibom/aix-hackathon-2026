import asyncio
from app.agents.segmenter import segment_document
from app.agents.requirement_extractor import extract_requirements

RFP_TEXT = "Request for Proposal — Warehouse Inventory Dashboard\n\nClient: NordFrame Logistics GmbH (fictional)\nIndustry: Logistics / Warehousing\n\n## Background\nNordFrame Logistics operates 6 regional warehouses across Germany and\nAustria. Our current inventory tracking is split across spreadsheets and an\noutdated legacy system, making it hard to get a real-time view of stock\nlevels across sites.\n\n## Requirements\n1. A web-based dashboard showing real-time inventory levels across all 6\n warehouses.\n2. Automated low-stock alerts sent to warehouse managers when items fall\n below a configurable threshold.\n3. Integration with our existing PostgreSQL inventory database — no\n migration to a new database.\n4. Role-based access — warehouse managers should only see their own\n site; HQ staff should see all sites.\n5. A data migration / onboarding plan for rolling this out across all 6\n sites with minimal disruption.\n6. Support & maintenance terms after go-live (response times, SLAs).\n7. Clear documentation of any assumptions, limitations, or risks, since\n inventory decisions will be made based on this system.\n\n## Budget\n€80,000–€120,000 total, including first year of support.\n\n## Timeline\nWorking pilot at one warehouse within 3 months; full rollout to all 6 sites\nwithin 6 months.\n\n## Decision Date\nEnd of this quarter."

segments = segment_document(RFP_TEXT, "rfp")
print("--- SEGMENTS ---")
for s in segments:
    print(f"[{s.id}] {s.text}")

print("\n--- REQUIREMENTS ---")
reqs = asyncio.run(extract_requirements(segments))
for r in reqs:
    print(f"[{r.req_id}] ({r.criticality}) {r.requirement_text} (from {r.source_segment_ids})")
