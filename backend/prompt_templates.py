"""
LangChain Prompt Templates
===========================
Shared prompt template used by BOTH proprietary (OpenAI) and
open-source (HuggingFace) models.

Cues are dynamically loaded from cues_config.json and injected
into the system message. Error injection is also prompt-driven.
"""

from langchain_core.prompts import ChatPromptTemplate


# ─── System Prompt Template ──────────────────────────────────────────────────
# This is the SINGLE shared prompt used by both model functions.
# Variables injected at runtime:
#   {persona}              - from cues_config.json agent_identity
#   {tone_instruction}     - from cues_config.json tone
#   {confidence_instruction} - from cues_config.json confidence
#   {error_instruction}    - empty string OR error injection prompt
#   {task_context}         - the decision scenario text

SYSTEM_TEMPLATE = """{persona}

COMMUNICATION STYLE:
{tone_instruction}

CONFIDENCE FRAMING:
{confidence_instruction}

{error_instruction}

YOUR TASK:
A user will present a business decision scenario. You must analyze it and provide
your recommendation. Respond with a JSON object containing EXACTLY these fields:
- "recommendation": either "Accept" or "Reject"
- "confidence_score": a number between 0 and 100
- "explanation": a 2-3 sentence explanation of your reasoning

CRITICAL: Respond ONLY with the raw JSON object. No markdown, no code fences, no extra text."""


def build_prompt(
    cue_config: dict,
    condition_id: int,
    is_error_scenario: bool = False,
) -> ChatPromptTemplate:
    """
    Build a ChatPromptTemplate with cues injected from the JSON config.

    This is the SAME prompt used by both use_proprietary() and use_opensource().

    Args:
        cue_config: The loaded cues_config.json dict
        condition_id: Which condition (1-8) to use for cue selection
        is_error_scenario: Whether this scenario should get a wrong answer

    Returns:
        ChatPromptTemplate ready for invocation with {task_context}
    """
    # Look up which cue options this condition uses
    condition_keys = cue_config["conditions"][str(condition_id)]

    agent_key = condition_keys["agent_identity"]
    tone_key = condition_keys["tone"]
    confidence_key = condition_keys["confidence"]

    # Pull the actual cue values from the dimensions
    dims = cue_config["cue_dimensions"]
    agent_opts = dims["agent_identity"]["options"][agent_key]
    tone_opts = dims["tone"]["options"][tone_key]
    confidence_opts = dims["confidence"]["options"][confidence_key]

    # Error injection: if this scenario should be wrong, inject the instruction
    error_instruction = ""
    if is_error_scenario:
        error_instruction = (
            "IMPORTANT OVERRIDE INSTRUCTION:\n"
            + cue_config["error_injection"]["error_instruction"]
        )

    # Format the system message
    system_message = SYSTEM_TEMPLATE.format(
        persona=agent_opts["persona"],
        tone_instruction=tone_opts["instruction"],
        confidence_instruction=confidence_opts["instruction"],
        error_instruction=error_instruction,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{task_context}"),
    ])

    return prompt


def get_condition_display(cue_config: dict, condition_id: int) -> dict:
    """
    Get human-readable cue values for a condition (for the frontend).

    Returns:
        dict with agent_name, tone_style, confidence_framing, and label
    """
    condition_keys = cue_config["conditions"][str(condition_id)]
    dims = cue_config["cue_dimensions"]

    agent = dims["agent_identity"]["options"][condition_keys["agent_identity"]]
    tone = dims["tone"]["options"][condition_keys["tone"]]
    confidence = dims["confidence"]["options"][condition_keys["confidence"]]

    return {
        "condition_id": condition_id,
        "agent_identity": {"name": agent["name"], "label": agent["label"]},
        "tone": {"style": tone["style"]},
        "confidence": {"framing": confidence["framing"]},
        "label": f"{agent['name']} / {tone['style']} / {confidence['framing']}",
    }
