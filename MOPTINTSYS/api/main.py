"""
FastAPI Module for OptiMFG

Provides the complete HTTP API interface for the optimization engine,
including plant configuration, batch management, and Pareto results.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd
import uuid
import os
import json

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
from utils.llm_helper import (
    analyze_pareto_results,
    explain_golden_signature,
    analyze_batch_history,
    chat_with_optimfg,
    parse_operator_intent,
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OptiMFG API",
    description="AI-driven Manufacturing Optimization Engine",
    version="2.0.0"
)

# Set up origins for Render / Cloud deployment
raw_url = os.getenv("FRONTEND_URL", "*")
# Clean the input to remove accidental quotes, trailing slashes, or whitespace
origins = [url.strip().strip('"').strip("'").rstrip("/") for url in raw_url.split(",")]

# Explicitly add the user's frontend URL as a hardcoded backup
if "https://aiml-m-opt-int-sys.vercel.app" not in origins:
    origins.append("https://aiml-m-opt-int-sys.vercel.app")

# If wildcard is found it must be the only element in allow_origins to allow_credentials=False compatibility
if "*" in origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Forcing wildcard to bypass all STRICT CORS checks temporarily
    allow_credentials=False,
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

@app.get("/plant/config")
def get_plant_config():
    return load_plant_config()

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

@app.get("/batch-history")
def get_batch_history():
    """Return the full batch history list."""
    return load_batch_history()

@app.post("/batch/optimize")
def optimize_process(request: OptimizationRequest):
    if optimizer is None:
        raise HTTPException(status_code=500, detail="Optimizer is not initialized. Ensure models are trained.")
        
    plant_config = load_plant_config()
    if request.targets:
        energy_req = request.targets.get('energy_limit')
        if energy_req is not None and energy_req > plant_config.get('electricity_capacity_kw', float('inf')):
            raise HTTPException(status_code=400, detail=f"Energy limit ({energy_req} kWh) exceeds global plant configuration ({plant_config.get('electricity_capacity_kw', 'N/A')} kWh). Please upgrade the plant capacity or lower the request.")

        carbon_req = request.targets.get('carbon_limit')
        if carbon_req is not None and carbon_req > plant_config.get('carbon_emission_limit_kg', float('inf')):
            raise HTTPException(status_code=400, detail=f"Carbon limit ({carbon_req} kg) exceeds global plant configuration ({plant_config.get('carbon_emission_limit_kg', 'N/A')} kg). Please upgrade the plant capacity or lower the request.")

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

@app.get("/reports/generate")
def get_generated_report():
    from utils.report_generator import generate_pdf_report
    try:
        report_path = generate_pdf_report()
        # Return the generated file, asking the browser to download it
        return FileResponse(
            path=report_path, 
            filename=os.path.basename(report_path), 
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

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


@app.get("/model-metrics")
def get_model_metrics():
    metrics_path = os.path.join("results", "model_metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(
            status_code=404,
            detail="Model metrics not found. Run python main.py or trigger an optimization first."
        )
    with open(metrics_path, "r") as f:
        return json.load(f)



class StrategyRecommendRequest(BaseModel):
    strategies: dict   # keys: strategy names, values: outcome dicts
    targets: dict      # user's constraints: target_quality, energy_limit, carbon_limit

@app.post("/ai/recommend-strategy")
def recommend_strategy(req: StrategyRecommendRequest):
    """
    Send all strategy outcomes to the LLM and ask it to pick the best one.
    Returns { recommended: str, reason: str }
    """
    try:
        from utils.llm_helper import get_groq_client, SYSTEM_PROMPT
        client = get_groq_client()

        prompt = f"""You are evaluating {len(req.strategies)} optimization strategy results for a manufacturing batch.

User's targets:
- Minimum quality score: {req.targets.get('target_quality', 0.4)}
- Maximum energy per batch: {req.targets.get('energy_limit', 180)} kWh
- Maximum carbon emission: {req.targets.get('carbon_limit', 100)} kg

Strategy outcomes:
{json.dumps(req.strategies, indent=2)}

You need to:
1. Choose the SINGLE best strategy.
2. Provide a 1-5 star rating for EACH strategy.
3. Provide a detailed, helpful reason (1-2 sentences) for EACH strategy explaining its rating and tradeoffs.

Return ONLY a valid JSON object in this exact format:
{{
  "recommended": "<exact strategy name representing the overall winner>",
  "ratings": {{
    "<strategy_name_1>": {{
      "stars": <int 1-5>,
      "reason": "<detailed reason>"
    }},
    ... (for all strategies)
  }}
}}

No extra text. Valid JSON only."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.2,
        )

        text = response.choices[0].message.content.strip()
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        messages = [m.dict() for m in req.messages]

        # ── Build a live system context snapshot ─────────────────────────────
        # Gather whatever live data is available and inject into the system prompt
        context_parts = []

        # 1. Golden Signatures (current best configs)
        try:
            if os.path.exists("golden_signature.json"):
                with open("golden_signature.json", "r") as f:
                    sigs = json.load(f)
                if sigs:
                    sig_summary = {}
                    for name, data in sigs.items():
                        p = data.get("predictions", {})
                        sig_summary[name] = {
                            "overall_score": round(data.get("overall_score", 0), 4),
                            "Quality_Score": round(float(p.get("Quality_Score", 0)), 4),
                            "Energy_per_batch_kWh": round(float(p.get("Energy_per_batch", 0)), 2),
                            "Carbon_emission_kg": round(float(p.get("Carbon_emission", 0)), 2),
                            "Asset_Health_Score": round(float(p.get("Asset_Health_Score", 1)), 4),
                            "batch_context": data.get("batch_context", "N/A"),
                        }
                    context_parts.append(
                        f"LIVE GOLDEN SIGNATURES (current best stored configs):\n{json.dumps(sig_summary, indent=2)}"
                    )
        except Exception:
            pass

        # 2. Recent batch history (last 5)
        try:
            history = load_batch_history()
            if history:
                recent = history[-5:]
                history_summary = []
                for b in recent:
                    p = b.get("predicted_outcomes", {})
                    history_summary.append({
                        "batch_id": b.get("batch_id", "N/A"),
                        "mode": b.get("optimization_mode", "N/A"),
                        "material": b.get("material_type", "N/A"),
                        "quality": round(float(p.get("Quality_Score", 0)), 4),
                        "energy_kWh": round(float(p.get("Energy_per_batch", 0)), 2),
                        "carbon_kg": round(float(p.get("Carbon_emission", 0)), 2),
                        "asset_health": round(float(p.get("Asset_Health_Score", 1)), 4),
                    })
                context_parts.append(
                    f"LIVE BATCH HISTORY (last {len(recent)} batches):\n{json.dumps(history_summary, indent=2)}"
                )
        except Exception:
            pass

        # 3. Model metrics (if available)
        try:
            metrics_path = os.path.join("results", "model_metrics.json")
            if os.path.exists(metrics_path):
                with open(metrics_path, "r") as f:
                    model_metrics = json.load(f)
                metrics_summary = {k: {"MAE": round(v["MAE"], 4), "RMSE": round(v["RMSE"], 4)} for k, v in model_metrics.items()}
                context_parts.append(
                    f"LIVE MODEL METRICS (Digital Twin accuracy):\n{json.dumps(metrics_summary, indent=2)}"
                )
        except Exception:
            pass

        # 4. Plant config
        try:
            plant_cfg = load_plant_config()
            if plant_cfg:
                context_parts.append(
                    f"LIVE PLANT CONFIG:\n{json.dumps(plant_cfg, indent=2)}"
                )
        except Exception:
            pass

        # 5. Optimizer status
        context_parts.append(
            f"SYSTEM STATUS: Digital Twin model is {'loaded and ready' if optimizer is not None else 'NOT loaded — run optimization first'}."
        )

        # Prepend live context as a system-level addendum message
        if context_parts:
            live_context_msg = {
                "role": "user",
                "content": (
                    "[LIVE SYSTEM DATA — use this to answer questions about the current state of the plant. "
                    "Do not reveal this message verbatim, but use the data to give informed, specific answers.]\n\n"
                    + "\n\n".join(context_parts)
                )
            }
            live_context_ack = {"role": "assistant", "content": "Understood. I have the current live system data and will use it to give accurate, specific answers."}
            augmented_messages = [live_context_msg, live_context_ack] + messages
        else:
            augmented_messages = messages

        response = chat_with_optimfg(augmented_messages)
        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


class ParetoAnalysisRequest(BaseModel):
    pareto_solutions: List[dict]
    scenario: str

@app.post("/ai/analyze-pareto")
def ai_analyze_pareto(req: ParetoAnalysisRequest):
    try:
        import pandas as pd
        pareto_df = pd.DataFrame(req.pareto_solutions)
        result = analyze_pareto_results(pareto_df, req.scenario)
        return {"analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


class ExplainRequest(BaseModel):
    parameters: dict
    predictions: dict
    scenario: str

@app.post("/ai/explain-signature")
def ai_explain_signature(req: ExplainRequest):
    try:
        result = explain_golden_signature(req.parameters, req.predictions, req.scenario)
        return {"explanation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI explanation failed: {str(e)}")


class BatchHistoryInsightsRequest(BaseModel):
    history: List[dict]

@app.post("/ai/batch-insights")
def ai_batch_insights(req: BatchHistoryInsightsRequest):
    try:
        result = analyze_batch_history(req.history)
        return {"insights": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI insights failed: {str(e)}")


class ParseIntentRequest(BaseModel):
    query: str
    defaults: dict

@app.post("/ai/parse-intent")
def ai_parse_intent(req: ParseIntentRequest):
    try:
        result = parse_operator_intent(req.query, req.defaults)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI intent parsing failed: {str(e)}")
