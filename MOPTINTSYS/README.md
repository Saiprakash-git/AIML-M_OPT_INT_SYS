# 🏭 OptiMFG: Multi-Objective Manufacturing Optimization System

OptiMFG is an AI-driven optimization system designed to compute the "Golden Signature" (the absolute best combination of machine settings) for industrial batch manufacturing processes, specifically modeled around pharmaceutical/tablet production.

## 🎯 Project Goals

The system aims to balance two conflicting operational objectives using advanced AI techniques:
1. **Maximize Product Quality:** Optimize parameters like Hardness, Dissolution Rate, and minimize Friability.
2. **Minimize Environmental Impact:** Keep Energy Consumption and Carbon Emissions as low as possible without sacrificing quality.

---

## 🏗️ Architecture & Core Modules

The project is structured into modular components:

- **`data/` (Data Ingestion)**
  - Responsible for loading historical batch outcomes (`_h_batch_production_data.xlsx`) and continuous time-series process logs (`_h_batch_process_data.xlsx`).
  - Aggregates time-series sensor data and merges everything by `Batch_ID` into a unified dataset.
- **`features/` (Feature Engineering)**
  - Cleans and transforms raw data.
  - Dynamically calculates critical targets like **Energy Consumption** (from power and time) and **Carbon Emissions** (using standard grid emission factors).
- **`models/` (Digital Twin Model)**
  - Instead of running expensive real-world trials, a Machine Learning model (`MultiOutput XGBoost Regressor`) acts as a virtual simulator.
  - It maps 8 machine inputs (e.g., Compression Force, Drying Temp) to instantly predict the 5 resulting quality/energy outcomes.
- **`optimization/` (AI Optimization Engine)**
  - Implements **NSGA-II** (Non-dominated Sorting Genetic Algorithm) via the `pymoo` library.
  - Generates a "Pareto Front"—the perfect mathematical boundary where you cannot improve quality without using more energy, and vice versa.
  - Features a `Golden Signature` selector that parses the exact Pareto front to find the single best parameter configuration based on the user's priority constraints.
- **`visualization/` & `dashboard.py` (Interactive UI)**
  - A comprehensive minimal Streamlit dashboard that visualizes trade-offs.
  - Generates real-time 2D and 3D interactive Plotly charts showing the trade-offs between Hardness, Carbon Emissions, and Energy.

---

## 🚀 Getting Started

Ensure you have Python installed, then install the required dependencies:

```bash
pip install pandas numpy scikit-learn xgboost pymoo plotly streamlit openpyxl fastapi pydantic
```

### 1. Running the CLI Pipeline

To run the entire end-to-end process in the terminal (Data Load -> Train -> Optimize -> Export Results):

```bash
python main.py
```
*This will generate HTML dashboards inside a automatically created `results/` folder.*

### 2. Running the Interactive Dashboard (GUI)

To interactively explore the NSGA-II optimization process and visualize the Pareto Front:

```bash
streamlit run dashboard.py
```

### 3. API Deployment 

An asynchronous FastAPI environment has been established to serve the engine programmatically. You can hook it into custom frontends:

```bash
uvicorn api.main:app --reload
```
*Access the Swagger UI at `http://localhost:8000/docs` to test JSON payloads against the Optimizer.*
