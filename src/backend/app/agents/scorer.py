"""Scorer agent - evaluates draft proposals against a fixed 7-criterion rubric.

Completeness vs. RFP Requirements is computed deterministically from compliance_map.
Other 6 criteria are LLM-judged in a single batch call.
"""
import asyncio
import logging

from pydantic import BaseModel

from app.models.schemas import ComplianceResult, CriterionScore, Requirement, Segment
from app.services.llm_client import call_gemini

logger = logging.getLogger(__name__)

# Fixed 7-criterion rubric (do not modify these names)
FIXED_CRITERIA = [
    "Problem Understanding",
    "Scope & Deliverables Clarity",
    "Pricing Clarity",
    "Timeline Clarity",
    "Completeness vs. RFP Requirements",
    "Tone & Persuasiveness",
    "Risk/Assumptions Transparency",
]


class ScoreList(BaseModel):
    scores: list[CriterionScore]


def _compute_completeness_score(compliance_map: list[ComplianceResult]) -> CriterionScore:
    """Compute Completeness score deterministically from compliance_map.
    
    Formula: (met_count + 0.5 * weak_count) / total
    Mapped to 1-5 scale: score = round(1 + ratio * 4)
    
    This ensures reproducibility - same compliance_map always yields same score.
    """
    if not compliance_map:
        return CriterionScore(
            criterion="Completeness vs. RFP Requirements",
            score_1to5=1,
            comment="No requirements to evaluate.",
            weight=0.0,
            weighted_score=0.0,
        )
    
    met_count = sum(1 for r in compliance_map if r.status == "met")
    weak_count = sum(1 for r in compliance_map if r.status == "weak")
    total = len(compliance_map)
    missing_count = total - met_count - weak_count
    
    completeness_ratio = (met_count + 0.5 * weak_count) / total
    score_1to5 = round(1 + completeness_ratio * 4)
    
    comment = (
        f"{met_count} of {total} requirements fully met, "
        f"{weak_count} weakly addressed, {missing_count} missing."
    )
    
    logger.info(
        f"Completeness score computed: {score_1to5}/5 "
        f"(ratio: {completeness_ratio:.2f}, {met_count}M+{weak_count}W+{missing_count}X)"
    )
    
    return CriterionScore(
        criterion="Completeness vs. RFP Requirements",
        score_1to5=score_1to5,
        comment=comment,
        weight=0.0,  # Will be set later
        weighted_score=0.0,  # Will be computed later
    )


async def score_proposal(
    requirements: list[Requirement],
    compliance_map: list[ComplianceResult],
    draft_segments: list[Segment],
    weights: dict[str, float] | None = None,
) -> tuple[list[CriterionScore], float]:
    """Score a draft proposal against the fixed 7-criterion rubric.
    
    Args:
        requirements: Extracted requirements from RFP
        compliance_map: Gap analysis results from Sprint 2
        draft_segments: Draft proposal segments
        weights: Optional custom weights per criterion (defaults to 1/7 each)
    
    Returns:
        Tuple of (list of CriterionScore objects, overall weighted score sum)
    """
    logger.info(
        f"Scoring proposal: {len(requirements)} requirements, "
        f"{len(compliance_map)} compliance results, {len(draft_segments)} draft segments"
    )
    
    # Step 1: Compute Completeness deterministically (no LLM)
    completeness_score = _compute_completeness_score(compliance_map)
    
    # Step 2: Build prompt for LLM to judge the other 6 criteria
    llm_criteria = [c for c in FIXED_CRITERIA if c != "Completeness vs. RFP Requirements"]
    
    draft_text = "\n\n".join(f"[{s.id}] {s.text}" for s in draft_segments)
    
    req_context = "\n".join(
        f"[{r.req_id}] ({r.criticality}) {r.requirement_text}"
        for r in requirements
    )
    
    prompt = f"""You are an expert Proposal Reviewer. Evaluate the draft proposal against the RFP requirements using the following criteria.

**RFP Requirements Context:**
{req_context}

**Draft Proposal Text:**
{draft_text}

**Criteria to evaluate (1-5 scale, where 1=poor, 5=excellent):**

1. **Problem Understanding**: Does the draft correctly reflect the client's actual stated problem/goals (from the RFP), not a generic pitch?

2. **Scope & Deliverables Clarity**: Are the deliverables specific and unambiguous? Is it clear what is/isn't included?

3. **Pricing Clarity**: Is pricing clearly stated, broken down, and easy to understand (vs. vague or "on request" or deferred)?

4. **Timeline Clarity**: Are milestones and dates concrete, not vague ("in due course," "as soon as possible", "timely manner")?

5. **Tone & Persuasiveness**: Does it read as confident, client-focused, and professional - not generic boilerplate? Does it show understanding of THIS client's context?

6. **Risk/Assumptions Transparency**: Are assumptions, dependencies, or risks clearly flagged rather than hidden or omitted?

For EACH criterion above, provide:
- A score from 1 to 5
- A one-sentence comment explaining the score, citing specific examples from the draft where possible

Be strict: if something is vague, deferred, or missing, score accordingly. Generic statements score lower than specific, client-tailored content.

Return exactly {len(llm_criteria)} scores, one for each criterion listed above.
"""
    
    def do_call(p: str) -> dict:
        return call_gemini(p, ScoreList)
    
    # Step 3: Call LLM for the 6 criteria
    result = await asyncio.to_thread(do_call, prompt)
    llm_scores_data = result.get("scores", [])
    
    # Validate we got the expected criteria back
    llm_scores = []
    for score_data in llm_scores_data:
        criterion = score_data.get("criterion", "")
        if criterion in llm_criteria:
            llm_scores.append(CriterionScore.model_validate(score_data))
        else:
            logger.warning(f"LLM returned unexpected criterion: {criterion}")
    
    if len(llm_scores) < len(llm_criteria):
        logger.warning(
            f"LLM returned {len(llm_scores)} scores, expected {len(llm_criteria)}. "
            f"Some criteria may be missing."
        )
    
    # Step 4: Combine Completeness + LLM scores in the fixed order
    all_scores = []
    for criterion in FIXED_CRITERIA:
        if criterion == "Completeness vs. RFP Requirements":
            all_scores.append(completeness_score)
        else:
            # Find the matching LLM score
            matching = next((s for s in llm_scores if s.criterion == criterion), None)
            if matching:
                all_scores.append(matching)
            else:
                # Fallback if LLM didn't return this criterion
                logger.error(f"Missing score for criterion: {criterion}")
                all_scores.append(
                    CriterionScore(
                        criterion=criterion,
                        score_1to5=3,
                        comment="Not evaluated - LLM response incomplete",
                        weight=0.0,
                        weighted_score=0.0,
                    )
                )
    
    # Step 5: Handle weights
    if weights is None:
        weights = {}
    
    # Fill missing weights with default 1/7
    default_weight = 1.0 / 7.0
    complete_weights = {}
    for criterion in FIXED_CRITERIA:
        if criterion in weights:
            complete_weights[criterion] = weights[criterion]
        else:
            complete_weights[criterion] = default_weight
    
    # Normalize weights to sum to 1.0
    total_weight = sum(complete_weights.values())
    if total_weight > 0:
        normalized_weights = {
            k: v / total_weight for k, v in complete_weights.items()
        }
    else:
        # Fallback to equal weights if all weights were 0
        normalized_weights = {k: default_weight for k in FIXED_CRITERIA}
    
    logger.info(f"Normalized weights: {normalized_weights}")
    
    # Step 6: Apply weights and compute overall
    for score in all_scores:
        score.weight = normalized_weights[score.criterion]
        score.weighted_score = score.score_1to5 * score.weight
    
    overall = sum(score.weighted_score for score in all_scores)
    
    logger.info(
        f"Scoring complete: overall={overall:.2f}, "
        f"scores: {[(s.criterion[:20], s.score_1to5) for s in all_scores]}"
    )
    
    return (all_scores, overall)
