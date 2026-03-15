# OptiMFG AI Manufacturing Platform

![OptiMFG Dashboard](https://img.shields.io/badge/Status-Live-success?style=for-the-badge&logoColor=white) 
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)

Welcome to **OptiMFG**, an AI-driven, advanced manufacturing optimization platform. OptiMFG uses a powerful combination of Digital Twin technology, machine learning (MultiOutput XGBoost), and evolutionary algorithms (NSGA-II) to help factory operators balance energy consumption, carbon emissions, and product quality in real time.

## 🚀 Live Demo
**[OptiMFG is live! Click here to view the deployed Frontend Dashboard.](https://saiprakash-git.github.io/AIML-M_OPT_INT_SYS/)**

> Note: The link above assumes the project is deployed via GitHub Pages given the repository structure. If you have a different production URL (like Vercel or Netlify), replace this link!

---

## 📖 Key Features

### 1. Target-Driven Optimization Engine
State your goals (e.g., "Energy Saving", "Quality Priority", or "Balanced") and the system simulates thousands of combinations to recommend the **Golden Signature** — the absolute best possible machine parameters for your next batch.

### 2. Live 3D Digital Twin
A real-time 3D spatial visualization of your manufacturing equipment. It is fed by live IoT sensor data (simulated) and provides instant visual alerts if a critical parameter (like Core Temperature) exceeds safe limits.

### 3. AI Chatbot Assistant
A conversational interface connected directly to your plant's Digital Twin, Batch History, and Golden Signatures. Ask questions in plain English like *"What was my most energy efficient batch?"* and the AI will analyze your live database to answer.

### 4. Interactive What-If Simulation
A manual testing ground for the AI Digital Twin. Adjust the 8 machine parameters using sliders, and the system uses its XGBoost models to predict Quality, Energy, Carbon, and Machine Health without touching real equipment.

### 5. Continuous Learning & Batch History
Every optimized run is recorded in the Batch History. This data feeds back into the AI models, allowing the system to continuously learn and improve its predictions over time. You can view the mathematical health of these models (MAE/RMSE) on the Model Stats page.

---

## 🛠️ Technology Stack

**Frontend:**
*   **React** (v18)
*   **Vite** (Build Tool)
*   **TypeScript** (Type Safety)
*   **Recharts** (Data Visualization)
*   **Lucide React** (Iconography)
*   **Three.js / React Three Fiber** (3D Digital Twin)

**Backend / AI Engine:**
*   **FastAPI** (Python Web Framework)
*   **XGBoost** (Predictive Modeling)
*   **NSGA-II** (Multi-Objective Optimization via `pymoo`)
*   **Scikit-Learn** (Data Preprocessing)
*   **Pandas & NumPy** (Data Manipulation)

---

## 💻 Local Development Setup

To run the OptiMFG frontend locally:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Saiprakash-git/AIML-M_OPT_INT_SYS.git
    cd AIML-M_OPT_INT_SYS/optimfg-frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Start the development server:**
    ```bash
    npm run dev
    ```

4.  **Open in Browser:**
    Navigate to `http://localhost:5173` in your web browser.

---

## 📘 Documentation & Help

To help new operators learn the system, **every page in the OptiMFG dashboard includes a built-in Help button** in the top right corner. Clicking this button opens a page-specific dialog explaining what the page does and how to use its tools effectively.

---
*Built for the future of sustainable, AI-assisted manufacturing.*
