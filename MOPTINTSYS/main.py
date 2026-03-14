"""
OptiMFG - Main Application Entry Point

Orchestrates the entire pipeline: Data Loading -> Feature Engineering -> 
Digital Twin Modeling -> Optimization -> Visualization/Storage.
"""

import sys
import os
from data.data_loader import load_manufacturing_data
from features.feature_engineering import preprocess_features
from models.digital_twin_model import DigitalTwinModel
from optimization.optimizer import ManufacturingOptimizer
from optimization.golden_signature import select_golden_signature
from visualization.visualization import generate_all_dashboards

def main():
    print("Starting OptiMFG Optimization Pipeline...")
    
    # Step 1: Data Loading & Preprocessing
    print("1. Loading and preprocessing data...")
    batch_path = "data/_h_batch_production_data.xlsx"
    ts_path = "data/_h_batch_process_data.xlsx"
    
    if not os.path.exists(batch_path) or not os.path.exists(ts_path):
        print(f"Error: Datasets not found at {batch_path} or {ts_path}")
        sys.exit(1)
        
    raw_data = load_manufacturing_data(batch_path, ts_path)
    processed_data = preprocess_features(raw_data)
    
    # Step 2: Digital Twin Modeling
    print("2. Initializing and training Digital Twin Model...")
    dt_model = DigitalTwinModel()
    dt_model.train(processed_data, model_save_path="models/digital_twin.pkl")
    
    # Save model metrics to JSON for dashboard access
    import json
    os.makedirs("results", exist_ok=True)
    with open("results/model_metrics.json", "w") as f:
        json.dump(dt_model.metrics, f, indent=2)
    
    # Step 3: Multi-Objective Optimization
    print("3. Running NSGA-II Optimizer...")
    optimizer = ManufacturingOptimizer(dt_model)
    # Using a small population for quicker execution in main block
    pareto_df = optimizer.optimize(pop_size=50, n_gen=20) 
    
    if pareto_df is None or pareto_df.empty:
        print("Optimization failed to find Pareto-optimal solutions.")
        sys.exit(1)
    
    # Step 4: Golden Signature Selection
    print("4. Identifying Golden Signatures...")
    best_signature = select_golden_signature(pareto_df, scenario="balanced")
    print(f"Selected Signature Score: {best_signature['overall_score']}")
    
    # Step 5: Output & Visualization
    print("5. Generating reports and visual dashboards...")
    os.makedirs("results", exist_ok=True)
    generate_all_dashboards(pareto_df, output_dir="results")
    
    print("Pipeline finished successfully. Dashboards generated in 'results' folder.")

if __name__ == "__main__":
    main()
