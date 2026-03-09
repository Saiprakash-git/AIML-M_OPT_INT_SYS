"""
LLM Helper Module for OptiMFG
Uses Groq API (llama-3.3-70b-versatile) for all LLM-powered features.
API key is loaded from .env file — never hardcoded.
"""

import os
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# System Prompt — gives the LLM full OptiMFG context
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert AI assistant embedded inside OptiMFG, an AI-driven manufacturing optimization platform built for pharmaceutical tablet production.

The system uses:
- NSGA-II genetic algorithm to find Pareto-optimal batch configurations
- A Digital Twin (XGBoost regressor) to predict manufacturing outcomes
- 8 machine input parameters:
    * Drying_Temp (°C), Compression_Force (kN), Machine_Speed (RPM),
      Moisture_Content (%), Granulation_Time (min), Binder_Amount (kg),
      Drying_Time (min), Lubricant_Conc (%)
- 5 predicted outcome targets:
    * Quality_Score (0–1, higher is better)
    * Energy_per_batch (kWh, lower is better)
    * Carbon_emission (kg CO2, lower is better)
    * Reliability_Index (0–1, higher is better)
    * Asset_Health_Score (0–1, higher is better)
- Optimization scenarios: "Energy Saving", "Quality Priority", "Balanced"
- Golden Signature: the single best parameter configuration selected from the Pareto front

Always be concise, precise, and practical. Use pharmaceutical manufacturing domain knowledge.
Never hallucinate parameter values or outcomes. Only reason from the data provided to you."""


def get_groq_client():
    """Load API key from .env and return a configured Groq client."""
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Make sure your .env file exists in the project root "
            "with the line: GROQ_API_KEY=your_key_here"
        )
    return Groq(api_key=api_key)


# ─────────────────────────────────────────────────────────────
# Feature 1: Pareto Analyst
# ─────────────────────────────────────────────────────────────
def analyze_pareto_results(pareto_df: pd.DataFrame, scenario: str) -> str:
    """Summarize all Pareto solutions in plain English for the operator."""
    try:
        client = get_groq_client()
        n = len(pareto_df)

        stats = {
            "total_solutions": n,
            "quality_range": [
                round(pareto_df["Predicted_Quality_Score"].min(), 3),
                round(pareto_df["Predicted_Quality_Score"].max(), 3),
            ],
            "energy_range_kwh": [
                round(pareto_df["Predicted_Energy"].min(), 2),
                round(pareto_df["Predicted_Energy"].max(), 2),
            ],
            "carbon_range_kg": [
                round(pareto_df["Predicted_Carbon"].min(), 2),
                round(pareto_df["Predicted_Carbon"].max(), 2),
            ],
            "reliability_range": [
                round(pareto_df["Predicted_Reliability"].min(), 4),
                round(pareto_df["Predicted_Reliability"].max(), 4),
            ],
            "optimization_scenario": scenario,
        }

        prompt = f"""Analyze these Pareto-optimal manufacturing configurations and write a concise 4-5 sentence plain-English summary for a plant operator.

Data from {n} Pareto solutions:
{json.dumps(stats, indent=2)}

Cover: what trade-offs exist, what the ranges mean practically, any concerns (e.g. low reliability), 
and which scenario ({scenario}) was used. Be direct and actionable. Avoid technical jargon."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=450,
            temperature=0.3,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ AI analysis unavailable: {str(e)}"


# ─────────────────────────────────────────────────────────────
# Feature 2: Golden Signature Explainer
# ─────────────────────────────────────────────────────────────
def explain_golden_signature(params: dict, preds: dict, scenario: str) -> str:
    """Explain why the Golden Signature parameters were selected."""
    try:
        client = get_groq_client()

        prompt = f"""Explain in 4-5 sentences why these specific machine parameters were selected as the optimal '{scenario}' configuration for this pharmaceutical manufacturing batch.

Machine Parameters:
{json.dumps(params, indent=2)}

Predicted Outcomes:
{json.dumps(preds, indent=2)}

Explain the reasoning behind the key parameter values, how they relate to the outcomes, and why this configuration beats the alternatives. Be specific and practical — the reader is a plant operator."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ AI explanation unavailable: {str(e)}"


# ─────────────────────────────────────────────────────────────
# Feature 3 & 5: Intent Parser (works for both optimizer params and machine params)
# ─────────────────────────────────────────────────────────────
def parse_operator_intent(user_message: str, current_defaults: dict) -> dict:
    """
    Parse natural language operator intent into parameter values.
    Works for both optimizer settings (Tab 1 sidebar) and
    machine parameters (Tab 5 what-if).
    Returns a dict of inferred key-value pairs + 'reasoning' string.
    """
    try:
        client = get_groq_client()

        keys_desc = "\n".join(
            [f'  - "{k}": {type(v).__name__} (current: {v})' for k, v in current_defaults.items()]
        )

        prompt = f"""Extract parameter preferences from this operator message and return a JSON object.

Operator message: "{user_message}"

Available parameters (with current defaults):
{keys_desc}

Return ONLY a valid JSON object. Include:
- Any of the above keys that the operator mentioned or clearly implied, with their suggested values
- "reasoning": a 1-sentence string explaining what you inferred

Rules:
- Only include keys you can confidently infer from the message
- Use the correct data types (float for decimals, int for integers, string for text)
- Return valid JSON only — no markdown, no extra text, no explanation outside the JSON"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=350,
            temperature=0.1,
        )

        text = response.choices[0].message.content.strip()

        # Strip markdown code blocks if present
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]

        return json.loads(text.strip())

    except json.JSONDecodeError:
        return {"reasoning": "AI returned an unparseable response. Please rephrase your request."}
    except Exception as e:
        return {"reasoning": f"Could not parse intent: {str(e)}"}


# ─────────────────────────────────────────────────────────────
# Feature 4: Batch History Analyst
# ─────────────────────────────────────────────────────────────
def analyze_batch_history(history_list: list) -> str:
    """Analyze historical batch records and surface patterns and insights."""
    try:
        if not history_list:
            return "No batch history available yet. Run some optimizations first."

        client = get_groq_client()

        # Summarize last 10 batches for the prompt
        recent = history_list[-10:]
        summary = []
        for b in recent:
            preds = b.get("predicted_outcomes", {})
            summary.append({
                "batch_id": b.get("batch_id", "N/A"),
                "mode": b.get("optimization_mode", "N/A"),
                "material": b.get("material_type", "N/A"),
                "quality": round(float(preds.get("Quality_Score", 0)), 3),
                "energy_kwh": round(float(preds.get("Energy_per_batch", 0)), 2),
                "carbon_kg": round(float(preds.get("Carbon_emission", 0)), 2),
                "asset_health": round(float(preds.get("Asset_Health_Score", 1.0)), 3),
            })

        prompt = f"""Analyze these {len(recent)} recent manufacturing batch records and provide 3-4 specific, actionable insights for the plant operator.

Batch records:
{json.dumps(summary, indent=2)}

Look for:
- Patterns in quality/energy/carbon across different optimization modes
- Which mode (Energy Saving / Quality Priority / Balanced) performs best and why
- Any anomalies or outliers worth flagging
- Concrete recommendations for future batches

Be concise and specific. Format as a numbered list of insights."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=550,
            temperature=0.3,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ AI insights unavailable: {str(e)}"


# ─────────────────────────────────────────────────────────────
# Feature 5 & 6: General Chat (What-If + AI Chatbot tab)
# ─────────────────────────────────────────────────────────────
def chat_with_optimfg(messages: list) -> str:
    """
    General-purpose chat with full OptiMFG context.
    Used by both What-If tab chat and the dedicated AI Chatbot tab.
    messages: list of {"role": "user"/"assistant", "content": str}
    """
    try:
        client = get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            max_tokens=800,
            temperature=0.5,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ AI response unavailable: {str(e)}"
