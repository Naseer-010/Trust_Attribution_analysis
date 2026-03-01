"""
Modular AI Provider
====================
Three functions — researcher picks one by changing a single line:

  use_hardcoded()    - Static pre-defined JSON responses (no AI needed)
  use_proprietary()  - ChatOpenAI via API key from .env
  use_opensource()   - HuggingFace model via langchain-huggingface

All three use the SAME cues from cues_config.json.
Both AI functions use the SAME prompt template from prompt_templates.py.
Reproducibility: temperature=0 for deterministic outputs.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESEARCHER: To switch mode, change ONLY the function call
at the bottom of this file (or in main.py):

  result = use_hardcoded(condition_id, scenario_id)
  result = use_proprietary(condition_id, scenario_id)
  result = use_opensource(condition_id, scenario_id)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from prompt_templates import build_prompt

load_dotenv()

# ─── Load the cues config JSON ──────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "cues_config.json"

def load_cue_config() -> dict:
    """Load cue configuration from the JSON file."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _get_scenario(cue_config: dict, scenario_id: Optional[int] = None) -> dict:
    """Get a specific scenario or a random one from the config."""
    scenarios = cue_config["task_scenarios"]
    if scenario_id is not None:
        for s in scenarios:
            if s["id"] == scenario_id:
                return s
    return random.choice(scenarios)


def _is_error_scenario(cue_config: dict, scenario_id: int) -> bool:
    """Check if this scenario should get a deliberately wrong answer."""
    wrong_ids = cue_config["error_injection"]["deliberately_wrong_scenario_ids"]
    return scenario_id in wrong_ids


def _parse_ai_response(
    content: str,
    scenario: dict,
    cue_config: dict,
    condition_id: int,
) -> Dict[str, Any]:
    """Parse the AI response (JSON string) into a structured dict."""
    # Extract the condition display info
    condition_keys = cue_config["conditions"][str(condition_id)]
    dims = cue_config["cue_dimensions"]
    agent_name = dims["agent_identity"]["options"][condition_keys["agent_identity"]]["name"]

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # If the model didn't return clean JSON, wrap the raw text
        result = {
            "recommendation": "Accept",
            "confidence_score": 75,
            "explanation": content,
        }

    # Attach metadata
    result["scenario"] = scenario["context"]
    result["scenario_id"] = scenario["id"]
    result["correct_answer"] = scenario["correct_answer"]
    result["is_error_scenario"] = _is_error_scenario(cue_config, scenario["id"])
    result["agent_name"] = agent_name

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METHOD 1: HARDCODED — No AI, just pre-defined responses
# Use when: you only need user decision/latency data, not AI output
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def use_hardcoded(condition_id: int, scenario_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Return a static, pre-defined recommendation without calling any AI model.

    The cues from cues_config.json still determine the tone and framing of the
    hardcoded text. Error scenarios follow the same deliberately_wrong_scenario_ids.

    Args:
        condition_id: Which experimental condition (1-8)
        scenario_id:  Specific scenario number (1-10), or None for random
    """
    cue_config = load_cue_config()
    scenario = _get_scenario(cue_config, scenario_id)
    is_error = _is_error_scenario(cue_config, scenario["id"])

    # Get cue values for formatting
    condition_keys = cue_config["conditions"][str(condition_id)]
    dims = cue_config["cue_dimensions"]
    agent_name = dims["agent_identity"]["options"][condition_keys["agent_identity"]]["name"]
    tone_key = condition_keys["tone"]
    confidence_key = condition_keys["confidence"]

    # Determine recommendation (flip if error scenario)
    correct = scenario["correct_answer"]
    if is_error:
        recommendation = "Accept" if correct == "Reject" else "Reject"
    else:
        recommendation = correct

    # Confidence score based on framing style
    if confidence_key == "probabilistic":
        confidence_score = 73  # Fixed for reproducibility
    else:
        confidence_score = 94  # Fixed for reproducibility

    # Explanation based on tone
    if tone_key == "technical":
        if recommendation == "Accept":
            explanation = (
                f"Based on quantitative analysis of the key metrics, "
                f"the risk-adjusted return profile is favorable. "
                f"Statistical models indicate a {confidence_score}% probability of positive outcome."
            )
        else:
            explanation = (
                f"Quantitative assessment reveals insufficient risk-adjusted returns. "
                f"Key performance indicators fall below threshold values. "
                f"Models suggest a {100 - confidence_score}% probability of suboptimal outcome."
            )
    else:  # empathetic
        if recommendation == "Accept":
            explanation = (
                f"I understand this is a significant decision. Looking at the bigger picture, "
                f"I believe this opportunity aligns well with your goals. "
                f"I feel quite confident - about {confidence_score}% - that this will work out positively."
            )
        else:
            explanation = (
                f"I know this might be disappointing to hear, but I want to be honest with you. "
                f"After careful consideration, I think the risks outweigh the benefits here. "
                f"I'd estimate about a {100 - confidence_score}% chance things won't go as planned."
            )

    return {
        "recommendation": recommendation,
        "confidence_score": confidence_score,
        "explanation": explanation,
        "scenario": scenario["context"],
        "scenario_id": scenario["id"],
        "correct_answer": correct,
        "is_error_scenario": is_error,
        "agent_name": agent_name,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METHOD 2: PROPRIETARY — OpenAI via API key
# Use when: you want high-quality, reliable AI responses
# Requires: OPENAI_API_KEY in .env
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def use_proprietary(condition_id: int, scenario_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get AI recommendation using ChatOpenAI (proprietary model).

    Uses the SAME prompt template as use_opensource().
    Reproducible: temperature=0, seed=42.

    Args:
        condition_id: Which experimental condition (1-8)
        scenario_id:  Specific scenario number (1-10), or None for random
    """
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-key-here":
        raise ValueError(
            "OPENAI_API_KEY not configured.\n"
            "Set it in backend/.env or switch to use_hardcoded() / use_opensource()."
        )

    cue_config = load_cue_config()
    scenario = _get_scenario(cue_config, scenario_id)
    is_error = _is_error_scenario(cue_config, scenario["id"])

    # Build the shared prompt (same template as use_opensource)
    prompt = build_prompt(cue_config, condition_id, is_error_scenario=is_error)

    # Proprietary model — temperature=0 + seed for reproducibility
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        seed=42,
        openai_api_key=api_key,
    )

    chain = prompt | llm
    response = chain.invoke({"task_context": scenario["context"]})

    return _parse_ai_response(response.content, scenario, cue_config, condition_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METHOD 3: OPEN SOURCE — HuggingFace model via LangChain
# Use when: you want free, local/API-based open-source model
# Requires: HUGGINGFACE_API_KEY in .env (for Inference API)
#           OR a locally running model
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def use_opensource(
    condition_id: int, scenario_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get AI recommendation using HuggingFace model (open-source).

    Uses the SAME prompt template as use_proprietary().
    Reproducible: temperature=0.01 (HF doesn't accept exactly 0).

    Args:
        condition_id: Which experimental condition (1-8)
        scenario_id:  Specific scenario number (1-10), or None for random
    """
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

    hf_token = os.getenv("HUGGINGFACE_API_KEY", "")

    cue_config = load_cue_config()
    scenario = _get_scenario(cue_config, scenario_id)
    is_error = _is_error_scenario(cue_config, scenario["id"])

    # Build the shared prompt (same template as use_proprietary)
    prompt = build_prompt(cue_config, condition_id, is_error_scenario=is_error)

    # Open-source model via HuggingFace Inference API
    # temperature near 0 for reproducibility (HF requires > 0)
    llm_endpoint = HuggingFaceEndpoint(
        repo_id=os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"),
        task="text-generation",
        temperature=0.01,
        max_new_tokens=512,
        huggingfacehub_api_token=hf_token,
    )
    llm = ChatHuggingFace(llm=llm_endpoint)

    chain = prompt | llm
    response = chain.invoke({"task_context": scenario["context"]})

    return _parse_ai_response(response.content, scenario, cue_config, condition_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Change this ONE function to switch between methods
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_recommendation(condition_id: int, scenario_id: Optional[int] = None) -> Dict[str, Any]:
    """
    ┌─────────────────────────────────────────────────────────┐
    │  Change the line below to switch methods.               │
    │                                                         │
    │  Option 1:  return use_hardcoded(condition_id, ...)     │
    │  Option 2:  return use_proprietary(condition_id, ...)   │
    │  Option 3:  return use_opensource(condition_id, ...)    │
    └─────────────────────────────────────────────────────────┘
    """
    return use_hardcoded(condition_id, scenario_id)   # ← CHANGE THIS LINE


# ─── Quick test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test all 8 conditions with scenario 1
    print("Testing all conditions with scenario 1:\n")
    for cid in range(1, 9):
        result = get_recommendation(cid, scenario_id=1)
        print(f"  Condition {cid}: {result['agent_name']:>10} | "
              f"Rec: {result['recommendation']:>6} | "
              f"Conf: {result['confidence_score']}% | "
              f"Error: {result['is_error_scenario']}")

    # Test error scenario
    print(f"\nTesting error scenario (id=5):")
    result = get_recommendation(1, scenario_id=5)
    print(f"  Correct: {result['correct_answer']} | AI said: {result['recommendation']} | Error: {result['is_error_scenario']}")
