import asyncio
import logging

from pydantic import BaseModel

from app.models.schemas import Requirement, Segment
from app.services.llm_client import call_gemini

logger = logging.getLogger(__name__)


class RequirementList(BaseModel):
    requirements: list[Requirement]


async def extract_requirements(rfp_segments: list[Segment]) -> list[Requirement]:
    """Extract requirements from RFP segments using Gemini."""
    segment_text = "\n".join(f"[{s.id}] {s.text}" for s in rfp_segments)
    prompt = f"""You are an expert Requirements Engineer. Your task is to extract EVERY SINGLE distinct requirement from the provided RFP segments.
Do not summarize. If there are 10 requirements, return 10 items.
Extract the budget and timeline as separate requirements if present.
All numbered bullet points are distinct requirements.

Valid categories: Technical, Functional, Budget, Timeline, Compliance/SLA, Risk/Assumptions.
Criticality: "hard" for all core deliverables and numbered bullet points, or if mandatory (must, required, shall, no migration). "soft" only for optional items or general context.
Use exact segment IDs for source_segment_ids.
req_id format: req_000, req_001, etc.

Segments:
{segment_text}
"""
    # ponytail: offload synchronous LLM call to thread to unblock FastAPI loop
    result = await asyncio.to_thread(call_gemini, prompt, RequirementList)

    reqs_data = result.get("requirements", [])
    valid_ids = {s.id for s in rfp_segments}

    validated_reqs = []
    for r in reqs_data:
        valid_sources = []
        for sid in r.get("source_segment_ids", []):
            if sid in valid_ids:
                valid_sources.append(sid)
            else:
                logger.warning(f"Hallucinated segment ID: {sid}")
        r["source_segment_ids"] = valid_sources
        validated_reqs.append(Requirement.model_validate(r))

    return validated_reqs
