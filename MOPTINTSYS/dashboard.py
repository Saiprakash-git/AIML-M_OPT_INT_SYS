import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# Import components from the existing modules
from data.data_loader import load_manufacturing_data
from features.feature_engineering import preprocess_features
from models.digital_twin_model import DigitalTwinModel
from optimization.optimizer import ManufacturingOptimizer
from visualization.visualization import plot_energy_vs_hardness, plot_carbon_vs_quality, plot_3d_pareto

st.set_page_config(page_title="OptiMFG | Manufacturing Optimizer", layout="wide")

st.title("🏭 OptiMFG: Multi-Objective Manufacturing Optimization")

st.markdown("""
This minimal dashboard leverages a Digital Twin model and NSGA-II to optimize batch manufacturing parameters.
Our goals: **Maximize Quality** (Hardness, Dissolution Rate) while **Minimizing Resource Usage** (Friability, Energy, Carbon Emissions).
""")

# Sidebar for controls
st.sidebar.header("Optimization Settings")
scenario = st.sidebar.selectbox(
    "Priority Scenario",
    ("balanced", "energy-saving", "quality-priority")
)

pop_size = st.sidebar.slider("Population Size (NSGA-II)", min_value=10, max_value=200, value=50, step=10)
n_gen = st.sidebar.slider("Generations (NSGA-II)", min_value=5, max_value=100, value=20, step=5)

if st.sidebar.button("Run Optimizer"):
    st.info("Starting pipeline...")
    
    with st.spinner("Loading and preprocessing data..."):
        # Paths to dataset files
        batch_path = "data/_h_batch_production_data.xlsx"
        ts_path = "data/_h_batch_process_data.xlsx"
        
        try:
            raw_data = load_manufacturing_data(batch_path, ts_path)
            processed_data = preprocess_features(raw_data)
            st.success("Data successfully loaded and preprocessed.")
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()
            
    with st.spinner("Training Digital Twin Model..."):
        # Initialize and train Digital Twin
        dt_model = DigitalTwinModel()
        try:
            dt_model.train(processed_data, "models/digital_twin.pkl")
            st.success("Digital Twin Model trained successfully.")
        except Exception as e:
            st.error(f"Error training model: {e}")
            st.stop()
            
    with st.spinner("Running Multi-Objective Optimization (NSGA-II)..."):
        optimizer = ManufacturingOptimizer(dt_model)
        try:
            pareto_df = optimizer.optimize(pop_size=pop_size, n_gen=n_gen)
            if pareto_df is not None and not pareto_df.empty:
                st.success(f"Optimization complete! Found {len(pareto_df)} Pareto-optimal configurations.")
                
                st.subheader("Pareto Optimal Front")
                st.dataframe(pareto_df)
                
                # Visualizations
                st.markdown("### Trade-off Visualizations")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig1 = px.scatter(
                        pareto_df, 
                        x='Predicted_Hardness', 
                        y='Predicted_Energy',
                        color='Predicted_Dissolution_Rate',
                        hover_data=['Granulation_Time', 'Compression_Force', 'Machine_Speed'],
                        title="Energy Consumption vs. Tablet Hardness",
                        labels={
                            'Predicted_Hardness': 'Hardness (Max)',
                            'Predicted_Energy': 'Energy per Batch (Min)',
                            'Predicted_Dissolution_Rate': 'Dissolution Rate'
                        },
                        color_continuous_scale=px.colors.sequential.Viridis
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                    
                with col2:
                    fig2 = px.scatter(
                        pareto_df, 
                        x='Predicted_Carbon', 
                        y='Predicted_Dissolution_Rate',
                        color='Predicted_Friability',
                        size='Predicted_Hardness',
                        hover_data=['Binder_Amount', 'Drying_Temp'],
                        title="Carbon Emissions vs. Quality",
                        labels={
                            'Predicted_Carbon': 'Carbon Emissions (Min)',
                            'Predicted_Dissolution_Rate': 'Dissolution Rate (Max)',
                            'Predicted_Friability': 'Friability (Min)'
                        },
                        color_continuous_scale=px.colors.sequential.Plasma
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    
                st.markdown("### 3D Pareto Front")
                fig3 = px.scatter_3d(
                    pareto_df,
                    x='Predicted_Hardness',
                    y='Predicted_Energy',
                    z='Predicted_Carbon',
                    color='Predicted_Dissolution_Rate',
                    hover_data=['Compression_Force', 'Machine_Speed'],
                    title="Hardness vs Energy vs Carbon",
                    labels={
                        'Predicted_Hardness': 'Hardness (Max)',
                        'Predicted_Energy': 'Energy (Min)',
                        'Predicted_Carbon': 'Carbon (Min)'
                    },
                    color_continuous_scale=px.colors.sequential.Turbo
                )
                st.plotly_chart(fig3, use_container_width=True)
                
            else:
                st.warning("Optimization finished but no solutions were returned.")
        except Exception as e:
            st.error(f"Error during optimization: {e}")
