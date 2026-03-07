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

def calculate_normalized_scores(pareto_df: pd.DataFrame, scenario: str) -> pd.Series:
    """
    Normalizes the objectives of the Pareto front and calculates a single 
    performance score based on the chosen scenario weights.
    Higher score is better.
    """
    df = pareto_df.copy()
    
    # 1. Normalize objectives between 0 and 1 for fair comparison
    # For targets we want to MAXIMIZE, 1 is best.
    # For targets we want to MINIMIZE, we invert them so 1 is still best.
    
    # Maximize objectives: (x - min) / (max - min) -> handle division by zero
    for col in ['Predicted_Hardness', 'Predicted_Dissolution_Rate']:
        min_val, max_val = df[col].min(), df[col].max()
        if max_val > min_val:
            df[col + '_norm'] = (df[col] - min_val) / (max_val - min_val)
        else:
            df[col + '_norm'] = 1.0
            
    # Minimize objectives: (max - x) / (max - min) -> inverted, so higher is better
    for col in ['Predicted_Friability', 'Predicted_Energy', 'Predicted_Carbon']:
        min_val, max_val = df[col].min(), df[col].max()
        if max_val > min_val:
            df[col + '_norm'] = (max_val - df[col]) / (max_val - min_val)
        else:
            df[col + '_norm'] = 1.0
            
    # 2. Assign scenario weights
    # Structure: [Hardness, Dissolution, Friability, Energy, Carbon]
    if scenario == "energy-saving":
        weights = {'hardness': 0.1, 'dissolution': 0.1, 'friability': 0.1, 'energy': 0.35, 'carbon': 0.35}
    elif scenario == "quality-priority":
        weights = {'hardness': 0.3, 'dissolution': 0.4, 'friability': 0.2, 'energy': 0.05, 'carbon': 0.05}
    else: # balanced
        weights = {'hardness': 0.2, 'dissolution': 0.2, 'friability': 0.2, 'energy': 0.2, 'carbon': 0.2}
        
    # 3. Calculate weighted sum score
    scores = (
        df['Predicted_Hardness_norm'] * weights['hardness'] +
        df['Predicted_Dissolution_Rate_norm'] * weights['dissolution'] +
        df['Predicted_Friability_norm'] * weights['friability'] +
        df['Predicted_Energy_norm'] * weights['energy'] +
        df['Predicted_Carbon_norm'] * weights['carbon']
    )
    
    return scores

def select_golden_signature(pareto_df: pd.DataFrame, scenario: str = "balanced") -> dict:
    """
    Selects the best configuration from the Pareto front based on a chosen scenario.
    
    Args:
        pareto_df (pd.DataFrame): The optimal configurations from the optimizer.
        scenario (str): Mode of selection ('energy-saving', 'quality-priority', 'balanced').
        
    Returns:
        dict: The selected Golden Signature configuration including parameters, predictions, and score.
    """
    logging.info(f"Selecting best Golden Signature for scenario: '{scenario}'")
    
    # Calculate performance scores
    scores = calculate_normalized_scores(pareto_df, scenario)
    
    # Find the index of the highest score
    best_idx = scores.idxmax()
    best_score = scores.loc[best_idx]
    
    # Extract the row as a dictionary
    best_row = pareto_df.loc[best_idx].to_dict()
    
    # Construct the final signature package
    signature = {
        "scenario": scenario,
        "overall_score": round(best_score, 4),
        "parameters": {
            "Granulation_Time": best_row['Granulation_Time'],
            "Binder_Amount": best_row['Binder_Amount'],
            "Drying_Temp": best_row['Drying_Temp'],
            "Drying_Time": best_row['Drying_Time'],
            "Compression_Force": best_row['Compression_Force'],
            "Machine_Speed": best_row['Machine_Speed'],
            "Lubricant_Conc": best_row['Lubricant_Conc'],
            "Moisture_Content": best_row['Moisture_Content']
        },
        "predictions": {
            "Hardness": best_row['Predicted_Hardness'],
            "Dissolution_Rate": best_row['Predicted_Dissolution_Rate'],
            "Friability": best_row['Predicted_Friability'],
            "Energy_per_batch": best_row['Predicted_Energy'],
            "Carbon_emission": best_row['Predicted_Carbon']
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
