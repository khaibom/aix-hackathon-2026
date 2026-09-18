"""Rewriter agent - generates specific, actionable suggestions for weak/missing requirements.

Only processes "weak" and "missing" requirements (skips "met").
Uses concrete RFP details, no generic placeholders.
"""
import asyncio
import logging
import re

from pydantic import BaseModel

from app.models.schemas import ComplianceResult, Requirement, RewriteSuggestion, Segment
from app.services.llm_client import call_gemini

logger = logging.getLogger(__name__)


class RewriteList(BaseModel):
    rewrites: list[RewriteSuggestion]


def _validate_suggested_text(suggested_text: str) -> tuple[bool, str]:
    """Validate that suggested_text is substantial and contains no placeholders.
    
    Returns: (is_valid, error_message)
    """
    if len(suggested_text) < 10:
        return False, f"Too short ({len(suggested_text)} chars)"
    
    # Check for placeholder patterns
    placeholder_patterns = [
        r"\[insert",
        r"\[add",
        r"\[\.\.\.+\]",
        r"\bTBD\b",
        r"\bto be determined\b",
        r"\bprovided later\b",
    ]
    
    for pattern in placeholder_patterns:
        if re.search(pattern, suggested_text, re.IGNORECASE):
            return False, f"Contains placeholder pattern: {pattern}"
    
    return True, ""


async def generate_rewrites(
    requirements: list[Requirement],
    compliance_map: list[ComplianceResult],
    draft_segments: list[Segment],
) -> list[RewriteSuggestion]:
    """Generate specific rewrite suggestions for weak/missing requirements.
    
    Args:
        requirements: Extracted requirements from RFP
        compliance_map: Gap analysis results from Sprint 2
        draft_segments: Draft proposal segments
    
    Returns:
        List of RewriteSuggestion objects (only for weak/missing requirements)
    """
    logger.info(f"Generating rewrites for {len(compliance_map)} compliance results")
    
    # Step 1: Filter for weak and missing requirements only
    needs_rewrite = [
        cr for cr in compliance_map if cr.status in ["weak", "missing"]
    ]
    
    if not needs_rewrite:
        logger.info("No weak or missing requirements - nothing to rewrite")
        return []
    
    logger.info(
        f"Found {len(needs_rewrite)} requirements needing rewrites: "
        f"{sum(1 for r in needs_rewrite if r.status == 'weak')} weak, "
        f"{sum(1 for r in needs_rewrite if r.status == 'missing')} missing"
    )
    
    # Step 2: Build context for each requirement needing a rewrite
    req_map = {r.req_id: r for r in requirements}
    segment_map = {s.id: s for s in draft_segments}
    
    rewrite_contexts = []
    for cr in needs_rewrite:
        req = req_map.get(cr.req_id)
        if not req:
            logger.warning(f"Requirement {cr.req_id} not found, skipping")
            continue
        
        # For weak: combine matched draft segments as original_text
        original_text = None
        if cr.status == "weak" and cr.matched_segment_ids:
            matched_texts = []
            for seg_id in cr.matched_segment_ids:
                seg = segment_map.get(seg_id)
                if seg:
                    matched_texts.append(seg.text)
            if matched_texts:
                original_text = " ".join(matched_texts)
        
        rewrite_contexts.append({
            "req_id": cr.req_id,
            "requirement_text": req.requirement_text,
            "criticality": req.criticality,
            "status": cr.status,
            "original_text": original_text,
            "rationale": cr.rationale,
        })
    
    # Step 3: Build single batch LLM prompt for all rewrites
    contexts_text = []
    for i, ctx in enumerate(rewrite_contexts, 1):
        ctx_str = f"""**Requirement {i}: [{ctx['req_id']}]**
- Requirement text: {ctx['requirement_text']}
- Criticality: {ctx['criticality']}
- Status: {ctx['status']}
- Gap analysis: {ctx['rationale']}"""
        
        if ctx['original_text']:
            ctx_str += f"\n- Current draft text: \"{ctx['original_text']}\""
        else:
            ctx_str += "\n- Current draft text: (not mentioned anywhere)"
        
        contexts_text.append(ctx_str)
    
    prompt = f"""You are an expert Proposal Writer. Generate specific, actionable rewrite suggestions to address gaps in the draft proposal.

For EACH requirement below, provide:
1. **suggested_text**: Concrete, specific text that fully satisfies the requirement
   - For MISSING requirements: Write a complete sentence or paragraph that directly addresses what the RFP asked for
   - For WEAK requirements: Rewrite the existing text to be more specific and complete
   - Use ACTUAL details from the requirement (e.g., real budget figures like "€80,000-€120,000", actual constraint names like "PostgreSQL", concrete timelines like "3 months")
   - DO NOT use generic placeholders like "[insert pricing here]", "TBD", "[add details]", or "to be determined"
   - Write as if you are the proposal author - use professional, confident tone

2. **insertion_point**: Where to apply this change
   - For MISSING: Suggest a section (e.g., "Add a new 'Support & Maintenance' section after Pricing", "Append to the Timeline section")
   - For WEAK: Reference the segment to replace (e.g., "Replace existing text in the Features section")

3. **original_text**: 
   - For MISSING: null
   - For WEAK: the current draft text that needs improvement (already provided below)

**Requirements to address:**

{chr(10).join(contexts_text)}

Generate exactly {len(rewrite_contexts)} suggestions, one for each requirement above.
Each suggested_text must be substantive (at least one full sentence) and contain NO placeholders or "TBD" markers.
Use concrete details from the requirement text itself.
"""
    
    def do_call(p: str) -> dict:
        return call_gemini(p, RewriteList)
    
    # Step 4: Call LLM
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        result = await asyncio.to_thread(do_call, prompt)
        rewrites_data = result.get("rewrites", [])
        
        logger.info(f"LLM returned {len(rewrites_data)} rewrites (attempt {attempt})")
        
        # Step 5: Validate each suggestion
        all_valid = True
        validation_errors = []
        
        for i, rw_data in enumerate(rewrites_data):
            suggested_text = rw_data.get("suggested_text", "")
            is_valid, error_msg = _validate_suggested_text(suggested_text)
            
            if not is_valid:
                all_valid = False
                req_id = rw_data.get("req_id", f"unknown_{i}")
                validation_errors.append(f"{req_id}: {error_msg}")
                logger.warning(
                    f"Invalid suggested_text for {req_id}: {error_msg}. "
                    f"Text: {suggested_text[:100]}..."
                )
        
        if all_valid:
            # All valid - build final list
            final_rewrites = []
            for rw_data in rewrites_data:
                # Ensure original_text is None for missing (not empty string)
                if rw_data.get("original_text") == "":
                    rw_data["original_text"] = None
                
                try:
                    final_rewrites.append(RewriteSuggestion.model_validate(rw_data))
                except Exception as e:
                    logger.error(f"Validation error for rewrite: {e}")
                    # Skip invalid ones
            
            logger.info(
                f"Rewrite generation complete: {len(final_rewrites)} suggestions validated"
            )
            return final_rewrites
        
        # Not all valid - retry if we have attempts left
        if attempt < max_attempts:
            logger.warning(
                f"Validation failed for {len(validation_errors)} suggestions, retrying. "
                f"Errors: {validation_errors}"
            )
            prompt += f"""

**IMPORTANT REMINDER**: Your previous response had validation issues:
{chr(10).join(f"- {err}" for err in validation_errors)}

Please ensure:
- Every suggested_text is at least 10 characters long
- NO placeholders like "[insert...]", "TBD", "[add...]", or "to be determined"
- Use CONCRETE details from the requirements (actual numbers, names, constraints)
"""
        else:
            # Last attempt failed - raise exception
            raise ValueError(
                f"Rewrite validation failed after {max_attempts} attempts. "
                f"Errors: {validation_errors}"
            )
    
    # Should never reach here, but just in case
    raise ValueError("Rewrite generation failed unexpectedly")
