"""
Bookstore Management System
Sprint 1 - T1-007
Developer: Alexis Silva
"""

import json
from pathlib import Path

RATES_PATH = Path(__file__).resolve().parent / "tax_rates.json"

STATES = []
STATES_BY_CODE = {}


def load_tax_rates():
    global STATES, STATES_BY_CODE
    data = json.loads(RATES_PATH.read_text())
    STATES = data["states"]
    STATES_BY_CODE = {s["code"]: s for s in STATES}
    return STATES


def state_rate(code):
    state = STATES_BY_CODE.get(code)
    return state["rate"] if state else None


load_tax_rates()
