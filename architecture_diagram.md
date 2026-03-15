# OptiMFG Architecture Diagram

This document contains the complete system architecture diagram for the **OptiMFG** platform based on the codebase analysis. The architecture leverages a React-based frontend and a Python (FastAPI) backend integrated with complex machine learning models (XGBoost, Isolation Forest) and an optimization engine (NSGA-II).

## System Architecture

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#61DAFB,stroke:#333,stroke-width:2px,color:#000;
    classDef react fill:#20232A,stroke:#61DAFB,stroke-width:2px,color:#61DAFB;
    classDef backend fill:#4B8BBE,stroke:#333,stroke-width:2px,color:#fff;
    classDef ml fill:#FFD43B,stroke:#333,stroke-width:2px,color:#000;
    classDef opt fill:#00A859,stroke:#333,stroke-width:2px,color:#fff;
    classDef data fill:#E8E8E8,stroke:#333,stroke-width:2px,color:#000;
    classDef external fill:#f9f9f9,stroke:#666,stroke-width:1px,stroke-dasharray: 5 5,color:#333;

    %% Frontend Components
    subgraph Frontend ["Frontend UI (React/Vite/TypeScript)"]
        Dashboard[OptiMFG Dashboard<br/>React UI Components]:::react
        ThreeJS[3D Digital Twin View<br/>Three.js/React Three Fiber]:::frontend
        Charts[Visualization Charts<br/>Recharts]:::frontend
        Chatbot[AI Chatbot Interface]:::frontend
        ApiClient[API Client / axios]:::frontend
    end

    %% Backend Server
    subgraph Backend ["Backend API Server (FastAPI / Python)"]
        API[FastAPI Endpoints]:::backend
        API -->|Handles Requests/Responses| LogicLayer(Business Logic Controller):::backend
    end

    %% Internal Data Storage
    subgraph DataStorage ["Data Storage & File System"]
        RawData[(Raw Batch Data<br/>Excel/CSV)]:::data
        ProcData[(Processed Datasets<br/>JSON/CSV)]:::data
        BatchHist[(Batch History<br/>batch_history.json)]:::data
        PlantConfig[(Plant Configuration<br/>plant_config.json)]:::data
    end

    %% Machine Learning Models
    subgraph ML ["Machine Learning Pipeline"]
        PreProc(Data Loader & Feature Engineering<br/>utils/data_loader):::ml
        DigitalTwin[Digital Twin Predictor<br/>MultiOutput XGBoost Regressor]:::ml
        AnomalyModel[Asset Health Monitor<br/>Isolation Forest Model]:::ml
    end

    %% Optimization Engine
    subgraph Optimization ["Optimization Engine"]
        NSGA[Multi-Objective Optimizer<br/>NSGA-II PyMoo]:::opt
        GoldenSig[Golden Signature Selection<br/>Min/Max Decision Matrices]:::opt
        Constraints[Physical Plant Constraints<br/>Penalty Functions]:::opt
    end

    %% Data Flow
    User((Plant Operator)) -->|Interacts with UI| Dashboard
    Dashboard --> ThreeJS
    Dashboard --> Charts
    Dashboard --> Chatbot
    Dashboard --> ApiClient

    ApiClient <-->|REST API Calls| API

    LogicLayer <-->|Read/Update| BatchHist
    LogicLayer <-->|Read/Update| PlantConfig

    %% ML Pipeline Flow
    RawData --> PreProc
    PreProc --> ProcData
    ProcData -->|Training Data| DigitalTwin
    ProcData -->|Time-series sensor data| AnomalyModel

    %% Optimization Flow
    DigitalTwin -->|Predicts multiple targets| NSGA
    Constraints -->|Restricts parameters| NSGA
    NSGA -->|Generates Pareto Front| GoldenSig
    GoldenSig -->|Returns Best Configuration| LogicLayer
    AnomalyModel -->|Calculates Asset Health Score| LogicLayer

    %% Feedback loop
    LogicLayer -->|Logs approved optimization| BatchHist
    BatchHist -->|Retraining Data| PreProc

```

### Component Details

**1. Frontend Application:**
*   Built with React, Vite, and TypeScript.
*   **3D Digital Twin View:** Uses Three.js and React Three Fiber to visually simulate the physical hardware and status flags (like overheating indicators).
*   **Charts:** Recharts to render parallel coordinates, objective distributions, and batch history metrics.
*   **AI Chatbot:** An interface connected to the LLM features of the platform, designed to answer plain English questions based on historical logs and optimization results.

**2. Backend Server (FastAPI):**
*   Exposes endpoints to retrieve configurations, run "What-If" simulations, trigger the NSGA-II optimizer, and record historical runs.
*   Serves as the broker between the interactive web dashboard and the heavier ML/Math logic.

**3. Machine Learning Pipeline:**
*   **Digital Twin Predictor:** Uses Extreme Gradient Boosting (`XGBRegressor`) wrapped in a `MultiOutputRegressor` to simultaneously predict multiple target metrics (Quality Score, Energy Consumption, Carbon Emissions) based on 8 key machine parameters.
*   **Asset Health Monitor:** Applies an **Isolation Forest** unsupervised algorithm on raw sensor time-series data to detect anomalous spikes, which linearly penalizes the equipment's health score.
*   **Feature Engineering:** Extracts meta-features like `Energy_per_batch` (time $\times$ power) and `Reliability Index` based on variance statistics.

**4. Optimization Engine:**
*   **NSGA-II (pymoo):** The core evolutionary algorithm exploring the 8-dimensional parameter space to generate a Pareto Front of optimal configurations (maximizing quality while minimizing carbon and footprint).
*   **Decision Matrix:** Sorts the Pareto solutions into actionable outcomes like "Energy Saving", "Quality Priority", or a "Balanced" mathematical hybrid.
*   **Feedback Loop:** By accepting or rejecting predictions, plant operators influence dynamic weights applied during consecutive optimization runs.
