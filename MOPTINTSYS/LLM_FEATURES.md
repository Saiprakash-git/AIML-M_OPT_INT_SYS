# 🤖 LLM Features — OptiMFG AI Integration

This document explains the LLM-powered features added to OptiMFG using the **Groq API** (`llama-3.3-70b-versatile`).

---

## Setup

### 1. Install dependencies
```bash
pip install groq python-dotenv
```

### 2. Configure API Key
Create a `.env` file in the `MOPTINTSYS/` directory:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free key at [console.groq.com](https://console.groq.com)

> ⚠️ `.env` is in `.gitignore` — it will never be committed. Never hardcode the key in source files.

---

## File Structure

```
MOPTINTSYS/
├── utils/
│   └── llm_helper.py     ← All LLM logic lives here
├── dashboard.py           ← UI integration (additive only)
├── .env                   ← API key (never committed)
└── .gitignore             ← Excludes .env
```

---

## `utils/llm_helper.py` — Function Reference

All LLM calls are centralized in this module. Each function has its own `try/except` so one failure never crashes the dashboard.

### `get_groq_client()`
Loads the API key from `.env` and returns a configured `groq.Groq` client.

---

### `analyze_pareto_results(pareto_df, scenario)` → `str`
**Feature 1 — Pareto Analyst**

Summarizes all Pareto-optimal solutions in plain English for the plant operator.

| Arg | Type | Description |
|---|---|---|
| `pareto_df` | `pd.DataFrame` | Full Pareto output from the NSGA-II optimizer |
| `scenario` | `str` | Optimization mode: `"Energy Saving"`, `"Quality Priority"`, or `"Balanced"` |

**Where used:** Tab 1 → `🔍 AI: Pareto Analysis` expander after optimization results

---

### `explain_golden_signature(params, preds, scenario)` → `str`
**Feature 2 — Golden Signature Explainer**

Explains *why* the selected machine parameter configuration was chosen.

| Arg | Type | Description |
|---|---|---|
| `params` | `dict` | Machine parameter values (e.g. `Drying_Temp`, `Compression_Force`) |
| `preds` | `dict` | Predicted outcomes (e.g. `Quality_Score`, `Energy_per_batch`) |
| `scenario` | `str` | Optimization mode used |

**Where used:** Tab 1 → `💬 AI: Why This Configuration?` expander

---

### `parse_operator_intent(user_message, current_defaults)` → `dict`
**Feature 3 & 5 — Natural Language Parameter Parser**

Converts plain English into structured parameter key-value pairs. Works for both optimizer settings (Tab 1 sidebar) and machine parameters (Tab 5 What-If).

| Arg | Type | Description |
|---|---|---|
| `user_message` | `str` | Free-text operator input |
| `current_defaults` | `dict` | Current parameter defaults (used to tell the LLM what keys are valid) |

**Returns:** Dict with inferred key-value pairs + `"reasoning"` string explaining the inference.

**Example:**
```python
parse_operator_intent(
    "High quality for audit, energy doesn't matter",
    {"scenario": "Balanced", "target_quality": 0.4, "energy_limit": 180.0}
)
# → {"scenario": "Quality Priority", "target_quality": 0.55, "reasoning": "..."}
```

**Where used:**
- Tab 1 Sidebar → `🧠 Smart Assistant (AI Pre-fill)` expander
- Tab 5 → `💬 Describe Parameter Changes` expander

---

### `analyze_batch_history(history_list)` → `str`
**Feature 4 — Batch History Analyst**

Scans the last 10 batch records and surfaces patterns, trends, and actionable recommendations.

| Arg | Type | Description |
|---|---|---|
| `history_list` | `list` | List of batch result dicts from `batch_history.json` |

**Where used:** Tab 3 → `🤖 AI Insights on Batch History` expander

---

### `chat_with_optimfg(messages)` → `str`
**Feature 5 & 6 — General Chat**

Full conversational AI with OptiMFG-aware system prompt. Maintains multi-turn context.

| Arg | Type | Description |
|---|---|---|
| `messages` | `list` | List of `{"role": "user"/"assistant", "content": str}` dicts |

**Where used:**
- Tab 6 → `🤖 AI Chatbot` (persistent chat interface)

---

## How Session State Works (Tab 1)

Streamlit reruns the entire script on every user interaction (button click).  
To prevent ML results from vanishing when LLM buttons are clicked:

1. After optimization completes, **all results are stored in `st.session_state`**:
   - `opt_pareto_df`, `opt_params`, `opt_preds`, `opt_scenario`
   - `opt_target_quality`, `opt_energy_limit`, `opt_carbon_limit`
   - `opt_energy_preds`, `opt_quality_preds`, `opt_balanced_preds`

2. LLM analysis results are also stored in session state when generated:
   - `llm_pareto_summary` — Pareto Analyst output
   - `llm_explanation` — Golden Signature Explainer output

3. The **entire results panel** (Golden Signature, charts, LLM features) is rendered **outside** `if submitted:`, reading from session state — so it persists across all reruns.

---

## LLM Model

| Setting | Value |
|---|---|
| Provider | Groq |
| Model | `llama-3.3-70b-versatile` |
| Pareto Analyst | `max_tokens=450`, `temperature=0.3` |
| Explainer | `max_tokens=500`, `temperature=0.3` |
| Intent Parser | `max_tokens=350`, `temperature=0.1` (low temp for JSON accuracy) |
| History Analyst | `max_tokens=550`, `temperature=0.3` |
| Chatbot | `max_tokens=800`, `temperature=0.5` |

---

## Sample Prompts

| Feature | Sample Input |
|---|---|
| Smart Assistant | *"We have a regulatory audit, push quality above 0.5, energy doesn't matter"* |
| What-If Chat | *"What if I increase compression force to 25 kN and dry at 75°C?"* |
| Chatbot | *"Why is my reliability score always near 0.002?"* |
| Chatbot | *"What's the trade-off between compression force and quality score?"* |
| Chatbot | *"Explain the Pareto front in simple terms"* |
