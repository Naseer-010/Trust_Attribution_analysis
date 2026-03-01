"""
Condition Management Framework
==============================
Loads condition configurations from cues_config.json.

2x2x2 factorial design across 3 cue dimensions:
  - Agent Identity:  "System-X" (neutral) vs "Sarah" (humanlike)
  - Tone:            "Technical" (formal)  vs "Empathetic" (conversational)
  - Confidence:      "Probabilistic" (calibrated) vs "Authoritative" (overstated)

Total conditions: 8
"""

import json
import random
import uuid
from pathlib import Path
from typing import Dict, Any

from prompt_templates import get_condition_display

# ─── Load Config ─────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "cues_config.json"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def assign_condition() -> Dict[str, Any]:
    """Randomly assign a participant to one of the 8 conditions."""
    cue_config = _load_config()
    participant_id = str(uuid.uuid4())[:8]
    condition_id = random.randint(1, len(cue_config["conditions"]))
    condition = get_condition_display(cue_config, condition_id)
    return {
        "participant_id": participant_id,
        "condition_id":   condition_id,
        "condition":      condition,
    }


def get_condition(condition_id: int) -> Dict[str, Any]:
    """Return the display config for a given condition ID."""
    cue_config = _load_config()
    num_conditions = len(cue_config["conditions"])
    if condition_id < 1 or condition_id > num_conditions:
        raise ValueError(f"Invalid condition_id: {condition_id}. Must be 1-{num_conditions}.")
    return get_condition_display(cue_config, condition_id)


def list_all_conditions() -> Dict[int, Dict[str, Any]]:
    """Return all conditions with their display configs."""
    cue_config = _load_config()
    result = {}
    for cid_str in cue_config["conditions"]:
        cid = int(cid_str)
        result[cid] = get_condition_display(cue_config, cid)
    return result
