import asyncio
import logging

from pydantic import BaseModel

from app.models.schemas import ComplianceResult, Requirement, Segment
from app.services.llm_client import call_gemini

logger = logging.getLogger(__name__)


class ComplianceList(BaseModel):
    results: list[ComplianceResult]


async def map_compliance(
    requirements: list[Requirement], draft_segments: list[Segment]
) -> list[ComplianceResult]:
    """Evaluate requirements against draft segments using Gemini."""
    # Input validation
    if not requirements:
        raise ValueError("requirements list cannot be empty")
    if not draft_segments:
        raise ValueError("draft_segments list cannot be empty")

    logger.info(
        f"Mapping {len(requirements)} requirements against {len(draft_segments)} draft segments"
    )

    draft_text = "\n".join(f"[{s.id}] {s.text}" for s in draft_segments)
    reqs_text = "\n".join(
        f"[{r.req_id}] ({r.criticality}) {r.requirement_text}" for r in requirements
    )

    prompt = f"""You are a Gap/Compliance Mapper. Evaluate the draft proposal against the RFP requirements.
Determine if each requirement is "met", "weak", or "missing" in the draft.

For each requirement, provide:
1. req_id: EXACTLY as given below.
2. status: "met" (clearly addressed), "weak" (vaguely/partially addressed), or "missing" (not addressed).
   - Be strict on "hard" requirements (a vague mention is "weak", not "met"). Hard requirements need specific, concrete evidence to be marked as "met".
   - If the draft defers the requirement with phrases like "will be provided later", "upon further discussion", "TBD", "to be determined", "pricing will be provided", "timeline to be discussed", mark it as "missing", NOT "weak".
   - A "weak" status requires at least a partial commitment or generic solution, not a deferral or absence.
   - Examples of deferrals that are "missing": "Pricing provided upon discussion", "Will be determined later", "Details TBD"
   - Examples of weak coverage: "We have a secure login" when RFP asks for specific role-based access details
3. matched_segment_ids: List of draft segment IDs that justify the status. For "missing", this MUST be an empty list [].
4. rationale: 1-2 sentences citing what the RFP asked for vs what the draft says/doesn't say, quoting or paraphrasing the draft segments.

Draft Segments:
{draft_text}

Requirements to evaluate:
{reqs_text}

You MUST return exactly {len(requirements)} results, one for each req_id.
"""

    # Token estimation
    estimated_tokens = (len(draft_text) + len(reqs_text) + len(prompt)) // 4
    logger.info(f"Estimated tokens: {estimated_tokens}")
    if estimated_tokens > 900_000:
        logger.warning(
            f"Estimated tokens ({estimated_tokens}) approaching context limit (1M)"
        )

    def do_call(p: str) -> dict:
        return call_gemini(p, ComplianceList)

    result = await asyncio.to_thread(do_call, prompt)
    results = result.get("results", [])

    # Retry once if incomplete
    returned_ids = {r.get("req_id") for r in results}
    expected_ids = {r.req_id for r in requirements}

    if expected_ids - returned_ids:
        missing_ids = expected_ids - returned_ids
        logger.warning(
            f"Incomplete LLM response, retrying. Missing req_ids: {', '.join(missing_ids)}"
        )
        retry_prompt = (
            prompt
            + f"\n\nWARNING: You missed some requirements in your previous output. You MUST evaluate these missing requirements: {', '.join(missing_ids)}"
        )
        retry_result = await asyncio.to_thread(do_call, retry_prompt)
        new_results = retry_result.get("results", [])
        for nr in new_results:
            if nr.get("req_id") not in returned_ids:
                results.append(nr)
                returned_ids.add(nr.get("req_id"))

    # Validate segment IDs and pad missing requirements
    valid_draft_ids = {s.id for s in draft_segments}
    final_results = []

    for r in results:
        rid = r.get("req_id")
        if rid not in expected_ids:
            continue  # Ignore extra hallucinated requirements

        matched = []
        if r.get("status") != "missing":
            for sid in r.get("matched_segment_ids", []):
                if sid in valid_draft_ids:
                    matched.append(sid)
                else:
                    logger.warning(
                        f"Hallucinated draft segment ID '{sid}' for req_id '{rid}' - filtering out"
                    )
        r["matched_segment_ids"] = matched
        final_results.append(ComplianceResult.model_validate(r))

    final_ids = {r.req_id for r in final_results}

    # Pad missing
    for req in requirements:
        if req.req_id not in final_ids:
            final_results.append(
                ComplianceResult(
                    req_id=req.req_id,
                    status="missing",
                    matched_segment_ids=[],
                    rationale="Not evaluated — extraction incomplete",
                )
            )

    # Sort to match original requirement order
    req_order = {req.req_id: i for i, req in enumerate(requirements)}
    final_results.sort(key=lambda x: req_order.get(x.req_id, 999))

    # Log status distribution
    status_counts = {"met": 0, "weak": 0, "missing": 0}
    for r in final_results:
        status_counts[r.status] += 1
    logger.info(f"Compliance mapping complete: {len(final_results)} results")
    logger.info(f"Status distribution: {status_counts}")

    return final_results
