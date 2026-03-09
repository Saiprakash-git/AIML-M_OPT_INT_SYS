import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import uuid
import json

# Import components from the existing modules
from data.data_loader import load_manufacturing_data
from features.feature_engineering import preprocess_features
from models.digital_twin_model import DigitalTwinModel
from optimization.optimizer import ManufacturingOptimizer
from optimization.golden_signature import select_golden_signature, update_golden_signature
from utils.storage import load_plant_config, save_plant_config, load_batch_history, save_batch_result

st.set_page_config(page_title="OptiMFG | AI Decision Platform", layout="wide")

st.title("🏭 OptiMFG: Complete AI-Driven Manufacturing Decision Platform")

# Multi-tab layout for complete features
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Optimization Dashboard", "Plant Configuration", "Batch History", "Golden Signatures Library", "What-If Simulation"])

# -----------------------------------------------------------------------------
# TAB 1: OPTIMIZATION DASHBOARD (Batch Creation & Execution)
# -----------------------------------------------------------------------------
with tab1:
    st.markdown("""
    Create a batch run by setting operational limits. The Digital Twin will optimize parameters 
    using NSGA-II to safely meet targets.
    """)
    
    st.sidebar.header("Section 1: Batch Setup & Constraints")
    
    with st.sidebar.form("batch_form"):
        batch_id = st.text_input("Batch ID", value=f"BATCH-{str(uuid.uuid4())[:6].upper()}")
        material_type = st.selectbox("Material Type", ["Standard Powder", "High Density", "Granular"])
        batch_size = st.number_input("Batch Size (kg)", value=500.0)
        
        st.markdown("### Optimization Targets")
        scenario = st.selectbox("Optimization Priority", ["Energy Saving", "Quality Priority", "Balanced"], index=2)
        target_quality = st.slider("Target Quality Score (Min)", 0.0, 1.0, 0.40, 0.01)
        energy_limit = st.number_input("Energy Limit per Batch (kWh)", value=180.0)
        carbon_limit = st.number_input("Carbon Emission Limit (kg)", value=100.0)
        
        st.markdown("### Advanced Controls")
        pop_size = st.slider("Population Size (NSGA-II)", 10, 200, 50, 10)
        n_gen = st.slider("Generations (NSGA-II)", 5, 100, 20, 5)
        
        submitted = st.form_submit_button("Run Target-Driven Optimization")
        
    if submitted:
        st.info(f"Starting pipeline for exactly {batch_id}...")
        
        with st.spinner("Loading and preprocessing data..."):
            try:
                raw_data = load_manufacturing_data("data/_h_batch_production_data.xlsx", "data/_h_batch_process_data.xlsx")
                processed_data = preprocess_features(raw_data)
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.stop()
                
        with st.spinner("Training Digital Twin Model..."):
            dt_model = DigitalTwinModel()
            try:
                dt_model.train(processed_data, "models/digital_twin.pkl")
            except Exception as e:
                st.error(f"Error training model: {e}")
                st.stop()
                
        with st.spinner("Running Target-Driven Multi-Objective Optimization..."):
            optimizer = ManufacturingOptimizer(dt_model)
            
            # Setup targets dictionary for optimizer
            optimization_targets = {
                "energy_limit": energy_limit,
                "carbon_limit": carbon_limit,
                "target_quality": target_quality
            }
            
            # Load continuous learning preference weights
            try:
                from utils.storage import load_operator_preferences
                operator_prefs = load_operator_preferences()
            except ImportError:
                operator_prefs = None
            
            try:
                pareto_df = optimizer.optimize(pop_size=pop_size, n_gen=n_gen, targets=optimization_targets, preferences=operator_prefs)
                if pareto_df is None or pareto_df.empty:
                    st.warning("No solutions found that satisfy all the hard constraints. Try loosening the limits.")
                    st.stop()
                    
                st.success(f"Optimization complete! Found {len(pareto_df)} viable Pareto-optimal configurations.")
                
                # Identify the 3 strategic options
                energy_sig = select_golden_signature(pareto_df, "Energy Saving")
                quality_sig = select_golden_signature(pareto_df, "Quality Priority")
                balanced_sig = select_golden_signature(pareto_df, "Balanced")
                
                sig_map = {
                    "Energy Saving": energy_sig,
                    "Quality Priority": quality_sig,
                    "Balanced": balanced_sig
                }
                main_recommendation = sig_map[scenario]
                
                # Assign batch context to signature and update library
                main_recommendation["batch_context"] = batch_id
                main_recommendation["material_type"] = material_type
                update_golden_signature(main_recommendation)
                
                # Save batch results comprehensively
                batch_result_record = {
                    "batch_id": batch_id,
                    "material_type": material_type,
                    "optimization_mode": scenario,
                    "targets_used": optimization_targets,
                    "recommended_configuration": main_recommendation["parameters"],
                    "predicted_outcomes": main_recommendation["predictions"],
                    "pareto_solutions_count": len(pareto_df)
                }
                save_batch_result(batch_result_record)
                
                st.divider()
                
                # Section 2: Recommendation Engine & Golden Signature
                st.header("🏆 Recommended Golden Signature")
                st.markdown(f"### Priority Mode: **{scenario}**")
                
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown("#### Exact Machine Parameters")
                    params = main_recommendation["parameters"]
                    st.code(f"""
Drying Temperature: {params['Drying_Temp']:.1f}°C
Compression Force: {params['Compression_Force']:.1f} kN
Machine Speed: {params['Machine_Speed']:.1f} RPM
Moisture Content: {params['Moisture_Content']:.2f}%
Granulation Time: {params['Granulation_Time']:.1f} min
Binder Amount: {params['Binder_Amount']:.1f} kg
Drying Time: {params['Drying_Time']:.1f} min
Lubricant Conc: {params['Lubricant_Conc']:.2f}%
                    """)
                    
                with rc2:
                    st.markdown("#### Predicted Outcomes")
                    preds = main_recommendation["predictions"]
                    
                    # Highlight if constraints met
                    q_icon = "✅" if preds['Quality_Score'] >= target_quality else "⚠️"
                    e_icon = "✅" if preds['Energy_per_batch'] <= energy_limit else "⚠️"
                    c_icon = "✅" if preds['Carbon_emission'] <= carbon_limit else "⚠️"
                    
                    st.code(f"""
{q_icon} Quality Score: {preds['Quality_Score']:.3f} (Target: >{target_quality})
{e_icon} Energy Consump: {preds['Energy_per_batch']:.2f} kWh (Limit: <{energy_limit})
{c_icon} Carbon Emiss: {preds['Carbon_emission']:.2f} kg (Limit: <{carbon_limit})
Reliability Score: {preds['Reliability_Index']:.3f}
Asset Health: {preds.get('Asset_Health_Score', 1.0):.3f}
Balanced Score: {preds['Balanced_Score']:.3f}
                    """)

                st.divider()

                # Highlight coordinates for Golden point
                golden_q = preds['Quality_Score']
                golden_e = preds['Energy_per_batch']
                golden_c = preds['Carbon_emission']
                golden_r = preds['Reliability_Index']

                # Section 3: Pareto Visualizations
                st.header("📊 Tradeoff Visualizations")
                
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    fig1 = px.scatter(
                        pareto_df, x='Predicted_Quality_Score', y='Predicted_Energy',
                        hover_data=['Granulation_Time', 'Compression_Force'],
                        title="Energy vs Quality",
                        color_discrete_sequence=['#1f77b4']
                    )
                    fig1.add_trace(go.Scatter(x=[golden_q], y=[golden_e], mode='markers', marker=dict(size=14, color='red', symbol='star'), name='Golden Sig'))
                    st.plotly_chart(fig1, use_container_width=True)
                    
                with c2:
                    fig2 = px.scatter(
                        pareto_df, x='Predicted_Quality_Score', y='Predicted_Carbon',
                        hover_data=['Binder_Amount', 'Drying_Temp'],
                        title="Carbon vs Quality",
                        color_discrete_sequence=['#2ca02c']
                    )
                    fig2.add_trace(go.Scatter(x=[golden_q], y=[golden_c], mode='markers', marker=dict(size=14, color='red', symbol='star'), name='Golden Sig'))
                    st.plotly_chart(fig2, use_container_width=True)
                
                with c3:
                    fig3 = px.scatter(
                        pareto_df, x='Predicted_Energy', y='Predicted_Reliability',
                        hover_data=['Machine_Speed', 'Drying_Time'],
                        title="Reliability vs Energy",
                        color_discrete_sequence=['#ff7f0e']
                    )
                    fig3.add_trace(go.Scatter(x=[golden_e], y=[golden_r], mode='markers', marker=dict(size=14, color='red', symbol='star'), name='Golden Sig'))
                    st.plotly_chart(fig3, use_container_width=True)

                st.divider()

                # Section 4: Decision Comparison
                st.header("💡 Decision Comparison Panel")
                st.markdown("Alternate Top Strategy Recommendations:")
                
                dc1, dc2, dc3 = st.columns(3)
                with dc1:
                    st.info("🌱 **Energy Efficient Alternative**")
                    e_preds = energy_sig['predictions']
                    st.markdown(f"Quality: **{e_preds['Quality_Score']:.3f}**\n\nEnergy: **{e_preds['Energy_per_batch']:.1f}** kWh\n\nAsset Health: **{e_preds.get('Asset_Health_Score', 1.0):.3f}**")
                with dc2:
                    st.success("⚖️ **Balanced Alternative**")
                    b_preds = balanced_sig['predictions']
                    st.markdown(f"Quality: **{b_preds['Quality_Score']:.3f}**\n\nEnergy: **{b_preds['Energy_per_batch']:.1f}** kWh\n\nAsset Health: **{b_preds.get('Asset_Health_Score', 1.0):.3f}**")
                with dc3:
                    st.warning("🏅 **Quality Maximizing Alternative**")
                    q_preds = quality_sig['predictions']
                    st.markdown(f"Quality: **{q_preds['Quality_Score']:.3f}**\n\nEnergy: **{q_preds['Energy_per_batch']:.1f}** kWh\n\nAsset Health: **{q_preds.get('Asset_Health_Score', 1.0):.3f}**")

                st.divider()
                st.header("📋 Full Pareto Output Table")
                display_df = pareto_df.rename(columns={
                    'Predicted_Quality_Score': 'Quality Score',
                    'Predicted_Energy': 'Energy (kWh)',
                    'Predicted_Carbon': 'Carbon (CO2)',
                    'Predicted_Reliability': 'Reliability',
                    'Asset_Health_Score': 'Asset Health',
                    'Balanced_Score': 'Balanced Score'
                })
                st.dataframe(display_df)
                    
            except Exception as e:
                st.error(f"Error during optimization: {e}")

# -----------------------------------------------------------------------------
# TAB 2: PLANT CONFIGURATION
# -----------------------------------------------------------------------------
with tab2:
    st.header("🏭 Global Plant Configuration")
    config = load_plant_config()
    
    with st.form("plant_config_form"):
        st.markdown("Set default plant operational constraints used across the system.")
        col1, col2 = st.columns(2)
        with col1:
            elec_cap = st.number_input("Total Electricity Capacity (kW)", value=float(config.get("electricity_capacity_kw", 1000.0)))
            mac_pow = st.number_input("Max Machine Power Limit (kW)", value=float(config.get("machine_power_limit_kw", 500.0)))
            carbon_limit_gw = st.number_input("Global Carbon Limit (kg)", value=float(config.get("carbon_emission_limit_kg", 200.0)))
        with col2:
            emis_factor = st.number_input("Emission Factor (CO2/kWh)", value=float(config.get("emission_factor", 0.45)))
            def_config = st.text_input("Default Machine Setting", value=config.get("default_machine_configuration", "Standard"))
            constraints = st.text_area("Plant Operating Constraints", value=config.get("plant_operating_constraints", "None"))
            
        save_btn = st.form_submit_button("Save Plant Configuration")
        if save_btn:
            new_config = {
                "electricity_capacity_kw": elec_cap,
                "machine_power_limit_kw": mac_pow,
                "emission_factor": emis_factor,
                "carbon_emission_limit_kg": carbon_limit_gw,
                "default_machine_configuration": def_config,
                "plant_operating_constraints": constraints
            }
            save_plant_config(new_config)
            st.success("Plant configuration saved successfully and is active.")

# -----------------------------------------------------------------------------
# TAB 3: BATCH HISTORY
# -----------------------------------------------------------------------------
with tab3:
    st.header("📚 Historical Batch Results")
    history = load_batch_history()
    
    if len(history) == 0:
        st.info("No historical batches found. Run an optimization to populate results.")
    else:
        st.markdown(f"Found **{len(history)}** continuous learning records.")
        # Flatten for pandas display
        flat_history = []
        for b in history:
            rec = {
                "Batch ID": b.get("batch_id", "N/A"),
                "Mode": b.get("optimization_mode", "N/A"),
                "Material": b.get("material_type", "N/A"),
                "Qual Score": b.get("predicted_outcomes", {}).get("Quality_Score", 0),
                "Energy Cons": b.get("predicted_outcomes", {}).get("Energy_per_batch", 0),
                "Carbon Em": b.get("predicted_outcomes", {}).get("Carbon_emission", 0),
                "Asset Health": b.get("predicted_outcomes", {}).get("Asset_Health_Score", 1.0)
            }
            flat_history.append(rec)
            
        history_df = pd.DataFrame(flat_history)
        st.dataframe(history_df, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: GOLDEN SIGNATURES
# -----------------------------------------------------------------------------
with tab4:
    st.header("✨ Master Golden Signature Library")
    st.markdown("Provides the most performant historical parameter configurations grouped by operational mode.")
    
    signatures = {}
    if os.path.exists("golden_signature.json"):
        with open("golden_signature.json", 'r') as f:
            try:
                signatures = json.load(f)
            except:
                pass
                
    if not signatures:
        st.info("No Golden Signatures stored. Run the optimizer to establish baselines.")
    else:
        for scenario_name, data in signatures.items():
            st.subheader(f"Strategy: {scenario_name}")
            colA, colB = st.columns(2)
            with colA:
                st.markdown("**Parameters:**")
                st.json(data.get("parameters", {}))
            with colB:
                st.markdown("**Metrics & Context:**")
                st.write(f"Overall Fitness Score: **{data.get('overall_score', 0):.4f}**")
                st.write(f"Asset Health Score: **{data.get('predictions', {}).get('Asset_Health_Score', 1.0):.4f}**")
                st.write(f"Associated Batch Context: **{data.get('batch_context', 'N/A')}**")
                st.json(data.get("predictions", {}))
            st.divider()

# -----------------------------------------------------------------------------
# TAB 5: WHAT-IF SIMULATION MODE
# -----------------------------------------------------------------------------
with tab5:
    st.header("🧪 What-If Simulation Mode")
    st.markdown("Manually explore the state space. Interactively adjust machine parameters to instantly view Digital Twin predicted outcomes without triggering an autonomous optimization process.")
    
    with st.form("what_if_form"):
        w1, w2 = st.columns(2)
        with w1:
            sim_gran_time = st.slider("Granulation Time (min)", 10.0, 60.0, 30.0, 0.5)
            sim_bind_amt = st.slider("Binder Amount (kg)", 1.0, 10.0, 5.0, 0.1)
            sim_dry_temp = st.slider("Drying Temp (°C)", 40.0, 80.0, 60.0, 0.5)
            sim_dry_time = st.slider("Drying Time (min)", 20.0, 120.0, 60.0, 1.0)
        with w2:
            sim_comp_force = st.slider("Compression Force (kN)", 5.0, 30.0, 15.0, 0.1)
            sim_speed = st.slider("Machine Speed (RPM)", 10.0, 50.0, 30.0, 0.5)
            sim_lube_conc = st.slider("Lubricant Conc (%)", 0.1, 2.0, 1.0, 0.05)
            sim_moist = st.slider("Moisture Content (%)", 1.0, 5.0, 2.5, 0.1)
            
        simulate_btn = st.form_submit_button("Run Digital Twin Simulation")
        
    if simulate_btn:
        with st.spinner("Connecting to Digital Twin..."):
            try:
                # Local instantiation
                raw_data = load_manufacturing_data("data/_h_batch_production_data.xlsx", "data/_h_batch_process_data.xlsx")
                processed_data = preprocess_features(raw_data)
                dt_model = DigitalTwinModel()
                dt_model.train(processed_data, "models/digital_twin.pkl")
                optimizer = ManufacturingOptimizer(dt_model)
                
                params = {
                    'Granulation_Time': sim_gran_time,
                    'Binder_Amount': sim_bind_amt,
                    'Drying_Temp': sim_dry_temp,
                    'Drying_Time': sim_dry_time,
                    'Compression_Force': sim_comp_force,
                    'Machine_Speed': sim_speed,
                    'Lubricant_Conc': sim_lube_conc,
                    'Moisture_Content': sim_moist
                }
                
                preds = optimizer.simulate_batch(params)
                
                st.success("Simulation Complete")
                st.markdown("### Predicted Outcomes")
                colA, colB, colC, colD = st.columns(4)
                colA.metric("Quality Score", f"{preds['Quality_Score']:.4f}")
                colB.metric("Energy (kWh)", f"{preds['Energy_per_batch']:.2f}")
                colC.metric("Carbon (kg)", f"{preds['Carbon_emission']:.2f}")
                
                h_score = preds.get('Asset_Health_Score', 1.0)
                h_icon = "🟢" if h_score > 0.9 else ("🟡" if h_score > 0.7 else "🔴")
                colD.metric(f"{h_icon} Asset Health", f"{h_score:.3f}")
                
            except Exception as e:
                st.error(f"Simulation failed: {e}")
