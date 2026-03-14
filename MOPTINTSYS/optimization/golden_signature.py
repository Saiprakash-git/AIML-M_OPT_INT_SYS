"""
Golden Signature Module for OptiMFG

Handles the evaluation, selection, and storage of the best-performing 
parameter sets ("Golden Signatures") from the optimizer's Pareto front.
It stores these benchmarks in a JSON file, updating them only if performance improves.
"""

import pandas as pd
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Define paths
SIGNATURE_FILE = "golden_signature.json"

def select_golden_signature(pareto_df: pd.DataFrame, scenario: str = "balanced") -> dict:
    """
    Selects the best configuration from the Pareto front based on a chosen scenario.
    
    Args:
        pareto_df (pd.DataFrame): The optimal configurations from the optimizer.
        scenario (str): Mode of selection ('Energy Saving', 'Quality Priority', 'Balanced').
        
    Returns:
        dict: The selected Golden Signature configuration including parameters, predictions, and score.
    """
    logging.info(f"Selecting best Golden Signature for scenario: '{scenario}'")
    
    df = pareto_df.copy()
    
    # 1. Determine best index based on scenario
    scenario_clean = scenario.lower().replace(" ", "-")
    if scenario_clean in ["energy-saving", "energy", "eco"]:
        # Energy Mode: select solution with lowest energy
        best_idx = df['Predicted_Energy'].idxmin()
        best_score = -df.loc[best_idx, 'Predicted_Energy']  # Negative so 'higher is better' logic in update matches conceptually
    elif scenario_clean in ["quality-priority", "quality"]:
        # Quality Mode: select solution with highest Quality_Score
        best_idx = df['Predicted_Quality_Score'].idxmax()
        best_score = df.loc[best_idx, 'Predicted_Quality_Score']
    else: 
        # Balanced Mode: select solution with highest Balanced_Score
        best_idx = df['Balanced_Score'].idxmax()
        best_score = df.loc[best_idx, 'Balanced_Score']
    
    # Extract the row as a dictionary
    best_row = df.loc[best_idx].to_dict()
    
    # Construct the final signature package matching user requested format
    signature = {
        "scenario": scenario,
        "overall_score": float(best_score),
        "parameters": {
            "Granulation_Time": float(best_row['Granulation_Time']),
            "Binder_Amount": float(best_row['Binder_Amount']),
            "Drying_Temp": float(best_row['Drying_Temp']),
            "Drying_Time": float(best_row['Drying_Time']),
            "Compression_Force": float(best_row['Compression_Force']),
            "Machine_Speed": float(best_row['Machine_Speed']),
            "Lubricant_Conc": float(best_row['Lubricant_Conc']),
            "Moisture_Content": float(best_row['Moisture_Content'])
        },
        "predictions": {
            "Quality_Score": float(best_row['Predicted_Quality_Score']),
            "Energy_per_batch": float(best_row['Predicted_Energy']),
            "Carbon_emission": float(best_row['Predicted_Carbon']),
            "Reliability_Index": float(best_row['Predicted_Reliability']),
            "Balanced_Score": float(best_row['Balanced_Score'])
        }
    }
    
    return signature

def update_golden_signature(new_signature: dict, filepath: str = SIGNATURE_FILE):
    """
    Compares the new signature with the existing one (if any) and updates the JSON
    database IF the new signature has a higher overall score.
    """
    logging.info("Evaluating new Golden Signature against historical benchmark...")
    
    # 1. Load existing signature
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                historical_data = json.load(f)
            except json.JSONDecodeError:
                historical_data = {}
    else:
        historical_data = {}
        
    scenario = new_signature["scenario"]
    
    # 2. Check if a benchmark already exists for this scenario
    if scenario in historical_data:
        old_score = historical_data[scenario].get("overall_score", 0.0)
        new_score = new_signature["overall_score"]
        
        if new_score > old_score:
            logging.info(f"New benchmark achieved! Score improved from {old_score} to {new_score}.")
            historical_data[scenario] = new_signature
        else:
            logging.info(f"Signature rejected. New score ({new_score}) did not beat historical benchmark ({old_score}).")
            return False # Indicate no update was made
    else:
        # First time running this scenario
        logging.info(f"Establishing first Golden Signature for '{scenario}'. Score: {new_signature['overall_score']}")
        historical_data[scenario] = new_signature

    # 3. Save the updated database back to JSON
    with open(filepath, 'w') as f:
        json.dump(historical_data, f, indent=4)
        
    logging.info(f"Golden Signatures successfully written to {filepath}")
    return True # Indicate an update was made
