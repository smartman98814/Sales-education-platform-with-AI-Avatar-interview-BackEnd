"""
Interview scoring endpoint using sales performance evaluation rubric
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from openai import OpenAI
from app.config import settings
from app.utils.logger import get_logger
import json

router = APIRouter()
logger = get_logger(__name__)


class Message(BaseModel):
    text: str
    sender: str  # 'user' (Salesperson) or 'agent' (Prospect)
    timestamp: Optional[str] = None
    timestamp_ms: Optional[int] = None


class ScoreInterviewRequest(BaseModel):
    agent_id: int
    agent_name: str
    agent_role: str
    messages: List[Message]


class RawScores(BaseModel):
    opening_rapport: int  # 1-5
    discovery_qualification: int  # 1-5
    value_messaging: int  # 1-5
    objection_handling: int  # 1-5
    trial_advancement: int  # 1-5
    listening_adaptability: int  # 1-5
    professionalism: int  # 1-5


class WeightedPoints(BaseModel):
    opening_rapport: int  # 0-10
    discovery_qualification: int  # 0-20
    value_messaging: int  # 0-20
    objection_handling: int  # 0-20
    trial_advancement: int  # 0-15
    listening_adaptability: int  # 0-10
    professionalism: int  # 0-5


class Deduction(BaseModel):
    reason: str
    points: int  # Negative integer


class ScoreInterviewResponse(BaseModel):
    raw_scores: RawScores
    weighted_points: WeightedPoints
    pre_deduction_total: float
    deductions: List[Deduction]
    final_score: float
    tier: str
    strengths: List[str]
    coaching_items: List[str]
    detailed_feedback: str


@router.post(
    "/interviews/score",
    response_model=ScoreInterviewResponse,
    summary="Score interview performance using sales evaluation rubric"
)
async def score_interview(request: ScoreInterviewRequest):
    """
    Analyze sales interview conversation and provide detailed scoring
    based on the sales performance evaluation rubric.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured"
        )
    
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Build conversation transcript
        conversation_lines = []
        for msg in request.messages:
            speaker = "S" if msg.sender == "user" else "P"
            conversation_lines.append(f"{speaker}: {msg.text}")
        
        conversation_text = "\n".join(conversation_lines)
        
        # Get agent context
        from app.config.agent_configs import AGENT_CONFIGURATIONS
        agent_config = AGENT_CONFIGURATIONS.get(request.agent_id, {})
        agent_description = agent_config.get("description", request.agent_role)
        
        # Use the exact prompt provided by user
        scoring_prompt = f"""You are a sales performance evaluator. Score a full conversation between a Salesperson (S) and a Prospect (P) using the rubric below. Follow these rules strictly:

Scoring scale (per category)

Raw category score is 1–5:

5 Excellent — best-practice, highly effective

4 Strong — above average, minor improvements

3 Adequate — meets minimum expectation

2 Weak — inconsistent, needs coaching

1 Poor — unacceptable, ineffective

Categories & weights (convert each 1–5 to points out of 100)

Opening & Rapport — 10%

Discovery & Qualification — 20%

Value Messaging & Positioning — 20%

Objection Handling — 20%

Trial Advancement & Closing — 15% (free trial ask must be evaluated)

Listening, Adaptability & Conversation Flow — 10%

Professionalism & Brand Representation — 5%

Convert rule: (category_raw / 5) * category_weight.

Sum all category contributions → pre-deduction total (0–100).

Behavioral indicators (use these to choose 1–5 per category)

Opening & Rapport (10%)

5: Warm, confident intro; uses name; builds rapport fast; positive energy

3: Polite but transactional; no real rapport attempts

1: Rude/monotone/dismissive/confusing

Discovery & Qualification (20%)

5: Multiple open-ended, industry-relevant questions; uncovers space, goals, décor preferences, decision authority, timeline, pain

3: Basic/shallow questions; not consultative

1: No discovery; jumps to assumptions

Value Messaging & Positioning (20%)

5: Tailors Floral Image benefits to prospect needs (recurring rotations, zero maintenance, premium aesthetics, cost-effective vs fresh flowers, improves brand experience)

3: Lists features without benefits

1: Misrepresents or confuses the offering

Objection Handling (20%) (price/budget, using fresh flowers, not a priority, gatekeeper, "email only")

5: Welcomes objections, listens fully, acknowledges, clarifies, reframes to value, confidently advances

3: Basic/partial responses; light empathy

1: Avoids, concedes, or is defensive/dismissive

Trial Advancement & Closing (15%) (Free trial is the strongest CTA)

5: Naturally moves to next step; asks for free trial placement; confirms space/location; suggests install time

3: Mentions next step but vague or not scheduled

1: Never attempts trial/next step/close

Listening, Adaptability & Flow (10%)

5: Active listening, accurate recaps, adapts to persona, never interrupts, matches tone/pace

3: Linear Q→A; little adaptation

1: Talks over prospect; ignores input

Professionalism & Brand (5%)

5: Polished, confident, warm, positive energy; proud of brand

3: Acceptable but inconsistent branding

1: Unprofessional/negative; harms brand

Automatic global deductions (apply after summing categories)

Interrupting prospect repeatedly: −5

Misrepresenting pricing or product: −10

Never asking for a next step (incl. trial): −8

Talking >85% of the time: −5 (approximate via character/word counts per speaker)

Ignoring a stated objection: −6

Using aggressive or dismissive language: −10

If evidence is unclear, do not apply that deduction.

Final score & tiers

After deductions, clamp to 0–100, then assign:

90–100: Excellent — ready for live selling

75–89: Strong — continue refinement

60–74: Developing — coaching recommended

<60: Not ready — repeat simulator sessions

CONVERSATION TRANSCRIPT:
{conversation_text}

PROSPECT CONTEXT:
Prospect: {request.agent_name} - {request.agent_role}
Description: {agent_description}

Rules:

raw_scores.* are integers 1–5.

weighted_points.* are integers 0–100 (each category's contribution, already weighted).

deductions[].points are negative integers from the list above.

final_score is the weighted sum minus deductions, clamped 0–100.

Provide 2–4 strengths and 2–4 coaching items, concise and specific, referencing conversation evidence.

Do not fabricate details not present in the transcript; if a behavior didn't occur, score appropriately and explain briefly in coaching.

Respond with ONLY valid JSON in this exact structure:
{{
    "raw_scores": {{
        "opening_rapport": <1-5>,
        "discovery_qualification": <1-5>,
        "value_messaging": <1-5>,
        "objection_handling": <1-5>,
        "trial_advancement": <1-5>,
        "listening_adaptability": <1-5>,
        "professionalism": <1-5>
    }},
    "weighted_points": {{
        "opening_rapport": <0-10>,
        "discovery_qualification": <0-20>,
        "value_messaging": <0-20>,
        "objection_handling": <0-20>,
        "trial_advancement": <0-15>,
        "listening_adaptability": <0-10>,
        "professionalism": <0-5>
    }},
    "pre_deduction_total": <0-100>,
    "deductions": [
        {{"reason": "<deduction reason>", "points": <negative integer>}},
        ...
    ],
    "final_score": <0-100>,
    "tier": "<Excellent|Strong|Developing|Not ready>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "coaching_items": ["<coaching item 1>", "<coaching item 2>", ...],
    "detailed_feedback": "<Detailed explanation paragraph>"
}}

Only return the JSON, no additional text."""

        # Call OpenAI with JSON mode
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sales performance evaluator. Always respond with valid JSON only, following the exact structure provided."
                },
                {
                    "role": "user",
                    "content": scoring_prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        score_data = json.loads(response.choices[0].message.content)
        
        # Build response models
        raw_scores = RawScores(**score_data["raw_scores"])
        weighted_points = WeightedPoints(**score_data["weighted_points"])
        deductions = [Deduction(**d) for d in score_data.get("deductions", [])]
        
        return ScoreInterviewResponse(
            raw_scores=raw_scores,
            weighted_points=weighted_points,
            pre_deduction_total=float(score_data.get("pre_deduction_total", 0)),
            deductions=deductions,
            final_score=float(score_data.get("final_score", 0)),
            tier=score_data.get("tier", "Developing"),
            strengths=score_data.get("strengths", []),
            coaching_items=score_data.get("coaching_items", []),
            detailed_feedback=score_data.get("detailed_feedback", "No detailed feedback available")
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid response format from scoring service: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error scoring interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to score interview: {str(e)}"
        )

