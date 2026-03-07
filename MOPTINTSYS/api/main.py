"""
FastAPI Module for OptiMFG

Provides the HTTP API interface for the optimization engine.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

# Import the system modules
from models.digital_twin_model import DigitalTwinModel
from optimization.optimizer import ManufacturingOptimizer
from optimization.golden_signature import select_golden_signature, update_golden_signature

app = FastAPI(
    title="OptiMFG API",
    description="AI-driven Manufacturing Optimization Engine",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# Pydantic Schemas for Input Validation
# -----------------------------------------------------------------------------
class ParameterConstraints(BaseModel):
    """
    Defines the lower and upper bounds allowed for each manufacturing parameter.
    Default values are provided as a starting point.
    """
    Granulation_Time: List[float] = Field(default=[10.0, 60.0], description="[min, max] time in minutes")
    Binder_Amount: List[float] = Field(default=[1.0, 10.0], description="[min, max] amount in kg")
    Drying_Temp: List[float] = Field(default=[40.0, 80.0], description="[min, max] temp in Celsius")
    Drying_Time: List[float] = Field(default=[20.0, 120.0], description="[min, max] time in minutes")
    Compression_Force: List[float] = Field(default=[5.0, 30.0], description="[min, max] force in kN")
    Machine_Speed: List[float] = Field(default=[10.0, 50.0], description="[min, max] speed in RPM")
    Lubricant_Conc: List[float] = Field(default=[0.1, 2.0], description="[min, max] concentration %")
    Moisture_Content: List[float] = Field(default=[1.0, 5.0], description="[min, max] content %")

class OptimizationRequest(BaseModel):
    """
    The main request payload defining the optimization goals and problem scope.
    """
    scenario: str = Field(
        default="balanced", 
        description="Priority mode: 'energy-saving', 'quality-priority', or 'balanced'"
    )
    constraints: ParameterConstraints = ParameterConstraints()
    pop_size: int = Field(default=50, description="NSGA-II population size per generation")
    n_gen: int = Field(default=20, description="NSGA-II number of generations")

# -----------------------------------------------------------------------------
# Global State Initialization
# -----------------------------------------------------------------------------
dt_model = None
optimizer = None

@app.on_event("startup")
def load_models():
    """
    Lifecycle event that runs when the FastAPI server starts.
    Loads the Digital Twin model into memory.
    """
    global dt_model, optimizer
    try:
        dt_model = DigitalTwinModel()
        # In a real environment, you might want to load a pre-trained model here:
        # dt_model.load_model('models/digital_twin.pkl')
        optimizer = ManufacturingOptimizer(dt_model)
        print("Models successfully initialized in API.")
    except Exception as e:
        print(f"Warning: Model could not be fully initialized. Error: {e}")

# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.post("/optimize")
def optimize_process(request: OptimizationRequest):
    """
    Runs the multi-objective optimization engine to find the best manufacturing parameters.
    """
    if optimizer is None:
        raise HTTPException(status_code=500, detail="Optimizer is not initialized. Ensure models are trained.")

    # 1. Parse constraints into bounds arrays for PyMoo (lower_bounds, upper_bounds)
    lower_bounds = []
    upper_bounds = []
    
    # Feature ordering must match the Digital Twin training order
    order = [
        'Granulation_Time', 'Binder_Amount', 'Drying_Temp', 'Drying_Time', 
        'Compression_Force', 'Machine_Speed', 'Lubricant_Conc', 'Moisture_Content'
    ]
    
    for param in order:
        constraint = getattr(request.constraints, param)
        lower_bounds.append(constraint[0])
        upper_bounds.append(constraint[1])

    bounds = (np.array(lower_bounds), np.array(upper_bounds))

    # 2. Run the NSGA-II Optimizer
    try:
        pareto_df = optimizer.optimize(
            bounds=bounds, 
            pop_size=request.pop_size, 
            n_gen=request.n_gen
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization engine failed: {str(e)}")
        
    if pareto_df is None or pareto_df.empty:
        raise HTTPException(status_code=404, detail="No optimal solutions found within the given constraints.")

    # 3. Select the ultimate "Golden Signature" based on the scenario mode
    try:
        best_signature = select_golden_signature(pareto_df, scenario=request.scenario)
        # Attempt to save the signature back to the JSON database
        update_golden_signature(best_signature)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract Golden Signature: {str(e)}")

    # 4. Format the final output response
    # Converts pandas dataframe to standard list of Python dicts for JSON serialization
    pareto_list = pareto_df.to_dict(orient='records')

    # Round the predicted outcomes slightly for cleaner API response
    cleaned_predictions = {k: round(v, 4) if isinstance(v, float) else v for k, v in best_signature["predictions"].items()}
    cleaned_parameters = {k: round(v, 4) if isinstance(v, float) else v for k, v in best_signature["parameters"].items()}

    return {
        "status": "success",
        "scenario_mode": request.scenario,
        "recommended_configuration": cleaned_parameters,
        "predicted_outcomes": cleaned_predictions,
        "overall_fitness_score": best_signature["overall_score"],
        "metrics": {
            "pareto_solutions_found": len(pareto_list)
        },
        # We can return the full set so the frontend can build interactive plots:
        "pareto_optimal_front": pareto_list  
    }
