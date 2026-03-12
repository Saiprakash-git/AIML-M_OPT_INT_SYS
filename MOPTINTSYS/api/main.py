"""
FastAPI Module for OptiMFG

Provides the complete HTTP API interface for the optimization engine,
including plant configuration, batch management, and Pareto results.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd
import uuid
import os

# Import the system modules
from models.digital_twin_model import DigitalTwinModel
from optimization.optimizer import ManufacturingOptimizer
from optimization.golden_signature import select_golden_signature, update_golden_signature
from utils.storage import (
    save_plant_config, 
    load_plant_config, 
    save_batch_result, 
    load_batch_history,
    load_operator_preferences,
    save_operator_preferences
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OptiMFG API",
    description="AI-driven Manufacturing Optimization Engine",
    version="2.0.0"
)

# Add CORS so your external frontend web app can access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific URLs in production (e.g. ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Pydantic Schemas for Input Validation
# -----------------------------------------------------------------------------
class PlantConfig(BaseModel):
    electricity_capacity_kw: float
    machine_power_limit_kw: float
    emission_factor: float
    carbon_emission_limit_kg: float
    default_machine_configuration: str
    plant_operating_constraints: str

class BatchCreateRequest(BaseModel):
    batch_id: str
    material_type: str
    batch_size: float
    target_quality: float
    energy_limit: float
    carbon_limit: float
    optimization_mode: str

class OperatorFeedback(BaseModel):
    batch_id: str
    selected_configuration: dict
    feedback_notes: str
    approval_status: bool

class ParameterConstraints(BaseModel):
    Granulation_Time: List[float] = Field(default=[10.0, 60.0])
    Binder_Amount: List[float] = Field(default=[1.0, 10.0])
    Drying_Temp: List[float] = Field(default=[40.0, 80.0])
    Drying_Time: List[float] = Field(default=[20.0, 120.0])
    Compression_Force: List[float] = Field(default=[5.0, 30.0])
    Machine_Speed: List[float] = Field(default=[10.0, 50.0])
    Lubricant_Conc: List[float] = Field(default=[0.1, 2.0])
    Moisture_Content: List[float] = Field(default=[1.0, 5.0])

class OptimizationRequest(BaseModel):
    batch_id: str
    scenario: str = Field(default="Balanced")
    constraints: ParameterConstraints = ParameterConstraints()
    targets: Optional[Dict[str, float]] = None
    pop_size: int = Field(default=50)
    n_gen: int = Field(default=20)

class SimulateRequest(BaseModel):
    parameters: dict

# -----------------------------------------------------------------------------
# Global State Initialization
# -----------------------------------------------------------------------------
dt_model = None
optimizer = None

@app.on_event("startup")
def load_models():
    global dt_model, optimizer
    try:
        dt_model = DigitalTwinModel()
        # In a real setup, load the model natively:
        try:
            dt_model.load_model('models/digital_twin.pkl')
            optimizer = ManufacturingOptimizer(dt_model)
            print("Models successfully initialized in API.")
        except Exception as e:
            print("Could not load trained model. Train it first via CLI/dashboard. Error:", e)
    except Exception as e:
        print(f"Warning: Model could not be fully initialized. Error: {e}")

# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.post("/plant/configure")
def configure_plant(config: PlantConfig):
    save_plant_config(config.dict())
    return {"status": "success", "message": "Plant configuration updated successfully."}

@app.post("/batch/create")
def create_batch(req: BatchCreateRequest):
    # Store pending batch request to history or separate DB
    # We can just record it in batch history as 'Created'
    record = req.dict()
    record['status'] = 'Created'
    save_batch_result(record)
    return {"status": "success", "batch_id": req.batch_id}

@app.post("/batch/optimize")
def optimize_process(request: OptimizationRequest):
    if optimizer is None:
        raise HTTPException(status_code=500, detail="Optimizer is not initialized. Ensure models are trained.")

    lower_bounds, upper_bounds = [], []
    order = [
        'Granulation_Time', 'Binder_Amount', 'Drying_Temp', 'Drying_Time', 
        'Compression_Force', 'Machine_Speed', 'Lubricant_Conc', 'Moisture_Content'
    ]
    for param in order:
        constraint = getattr(request.constraints, param)
        lower_bounds.append(constraint[0])
        upper_bounds.append(constraint[1])
    bounds = (np.array(lower_bounds), np.array(upper_bounds))

    # Load operator preferences for adaptive weights
    preferences = load_operator_preferences()

    try:
        pareto_df = optimizer.optimize(
            bounds=bounds, 
            pop_size=request.pop_size, 
            n_gen=request.n_gen,
            targets=request.targets,
            preferences=preferences
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization engine failed: {str(e)}")
        
    if pareto_df is None or pareto_df.empty:
        raise HTTPException(status_code=404, detail="No optimal solutions found within the given constraints.")

    try:
        best_signature = select_golden_signature(pareto_df, scenario=request.scenario)
        # Add context to signature
        best_signature['batch_context'] = request.batch_id
        update_golden_signature(best_signature)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract Golden Signature: {str(e)}")

    pareto_list = pareto_df.to_dict(orient='records')
    
    cleaned_predictions = {k: float(round(v, 4)) if isinstance(v, float) else v for k, v in best_signature["predictions"].items()}
    cleaned_parameters = {k: float(round(v, 4)) if isinstance(v, float) else v for k, v in best_signature["parameters"].items()}

    result_payload = {
        "status": "success",
        "batch_id": request.batch_id,
        "scenario_mode": request.scenario,
        "recommended_configuration": cleaned_parameters,
        "predicted_outcomes": cleaned_predictions,
        "overall_fitness_score": best_signature["overall_score"]
    }
    
    # Store complete batch result
    complete_record = result_payload.copy()
    complete_record['pareto_solutions'] = pareto_list
    save_batch_result(complete_record)

    return result_payload

@app.get("/batch/{batch_id}")
def get_batch(batch_id: str):
    history = load_batch_history()
    for batch in history:
        if batch.get('batch_id') == batch_id:
            return batch
    raise HTTPException(status_code=404, detail="Batch not found.")

@app.post("/simulate")
def simulate_process(request: SimulateRequest):
    if optimizer is None:
        raise HTTPException(status_code=500, detail="Optimizer is not initialized.")
    try:
        predicted = optimizer.simulate_batch(request.parameters)
        return {"status": "success", "predicted_outcomes": predicted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

@app.get("/asset-health/{batch_id}")
def get_asset_health(batch_id: str):
    history = load_batch_history()
    for batch in history:
        if batch.get('batch_id') == batch_id:
            outcomes = batch.get('predicted_outcomes', {})
            health = outcomes.get('Asset_Health_Score', 1.0)
            return {"batch_id": batch_id, "Asset_Health_Score": health}
    raise HTTPException(status_code=404, detail="Batch not found.")

@app.get("/pareto/{batch_id}")
def get_pareto(batch_id: str):
    history = load_batch_history()
    for batch in history:
        if batch.get('batch_id') == batch_id and 'pareto_solutions' in batch:
            return {"batch_id": batch_id, "pareto_solutions": batch['pareto_solutions']}
    raise HTTPException(status_code=404, detail="Pareto solutions for batch not found.")

@app.get("/golden-signatures")
def get_golden_signatures():
    import json
    import os
    if os.path.exists("golden_signature.json"):
        with open("golden_signature.json", "r") as f:
            return json.load(f)
    return {}

@app.post("/operator-feedback")
def operator_feedback(feedback: OperatorFeedback):
    # Adjust operator preferences based on feedback
    preferences = load_operator_preferences()
    
    if not feedback.approval_status: # If operator rejects a recommendation
        notes = feedback.feedback_notes.lower()
        if "energy" in notes or "inefficient" in notes:
            # Rejects energy-saving explicitly -> boost quality focus
            preferences['quality_weight'] = float(round(preferences.get('quality_weight', 1.0) * 1.1, 2))
        elif "quality" in notes or "poor" in notes:
            # Rejects poor quality -> boost quality weight
            preferences['quality_weight'] = float(round(preferences.get('quality_weight', 1.0) * 1.1, 2))

    save_operator_preferences(preferences)

    # Store feedback log
    feedback_file = "operator_feedback.json"
    data = []
    if os.path.exists(feedback_file):
        import json
        with open(feedback_file, 'r') as f:
            try:
                data = json.load(f)
            except:
                pass
    data.append(feedback.dict())
    import json
    with open(feedback_file, 'w') as f:
        json.dump(data, f, indent=4)
        
    return {"status": "success", "message": "Feedback recorded. Preferences dynamically adjusted."}

@app.post("/system/retrain")
def retrain_digital_twin():
    from data.data_loader import load_manufacturing_data
    from features.feature_engineering import preprocess_features
    global dt_model, optimizer
    try:
        raw_data = load_manufacturing_data("data/_h_batch_production_data.xlsx", "data/_h_batch_process_data.xlsx")
        processed_data = preprocess_features(raw_data)
        
        if dt_model is None:
            dt_model = DigitalTwinModel()
            
        dt_model.train(processed_data, "models/digital_twin.pkl")
        optimizer = ManufacturingOptimizer(dt_model)
        
        return {"status": "success", "message": "Continuous Learning Triggered: Digital Twin retrained successfully with latest batch data."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {e}")
