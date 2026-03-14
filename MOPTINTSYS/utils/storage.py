import json
import os

# Always resolve files relative to this file's directory (MOPTINTSYS root)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLANT_CONFIG_FILE = os.path.join(_BASE_DIR, "plant_config.json")
BATCH_HISTORY_FILE = os.path.join(_BASE_DIR, "batch_history.json")


def save_plant_config(config: dict):
    with open(PLANT_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_plant_config() -> dict:
    if os.path.exists(PLANT_CONFIG_FILE):
        with open(PLANT_CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {
        "electricity_capacity_kw": 1000.0,
        "machine_power_limit_kw": 500.0,
        "emission_factor": 0.45,
        "carbon_emission_limit_kg": 200.0,
        "default_machine_configuration": "Standard",
        "plant_operating_constraints": "None"
    }

def save_batch_result(result: dict):
    history = load_batch_history()
    history.append(result)
    with open(BATCH_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def load_batch_history() -> list:
    if os.path.exists(BATCH_HISTORY_FILE):
        with open(BATCH_HISTORY_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return []

PREFERENCES_FILE = os.path.join(_BASE_DIR, "operator_preferences.json")

def save_operator_preferences(prefs: dict):
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump(prefs, f, indent=4)

def load_operator_preferences() -> dict:
    if os.path.exists(PREFERENCES_FILE):
        with open(PREFERENCES_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {
        "quality_weight": 1.0,
        "energy_weight": 1.0
    }
