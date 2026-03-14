import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import uuid
import json
from utils.llm_helper import (
    analyze_pareto_results, explain_golden_signature,
    parse_operator_intent, analyze_batch_history, chat_with_optimfg
)

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Optimization Dashboard", "Plant Configuration", "Batch History", "Golden Signatures Library", "What-If Simulation", "🤖 AI Chatbot", "📊 Model Stats"])

# -----------------------------------------------------------------------------
# TAB 1: OPTIMIZATION DASHBOARD (Batch Creation & Execution)
# -----------------------------------------------------------------------------
with tab1:
    st.markdown("""
    Create a batch run by setting operational limits. The Digital Twin will optimize parameters 
    using NSGA-II to safely meet targets.
    """)
    
    st.sidebar.header("Section 1: Batch Setup & Constraints")

    # ── LLM Feature 3: Smart Decision Assistant ──────────────────────────
    with st.sidebar.expander("🧠 Smart Assistant (AI Pre-fill)", expanded=False):
        st.caption("Describe your batch goal in plain English — AI will suggest parameter values to fill the form below.")
        assistant_input = st.text_area(
            "Your goal:",
            placeholder="e.g. High quality batch for an audit, energy is less important today",
            key="assistant_input",
            height=80,
        )
        if st.button("💡 Suggest Parameters", key="suggest_btn"):
            if assistant_input.strip():
                with st.spinner("Thinking..."):
                    current_defaults = {
                        "scenario": "Balanced",
                        "target_quality": 0.40,
                        "energy_limit": 180.0,
                        "carbon_limit": 100.0,
                        "pop_size": 50,
                        "n_gen": 20,
                    }
                    suggestions = parse_operator_intent(assistant_input, current_defaults)
                reasoning = suggestions.pop("reasoning", "")
                if suggestions:
                    st.success("AI Suggestions:")
                    for k, v in suggestions.items():
                        st.write(f"**{k.replace('_', ' ')}:** `{v}`")
                    if reasoning:
                        st.caption(f"*{reasoning}*")
                    st.info("Apply these values in the form below ↓")
                else:
                    st.warning("Could not extract parameters. Try being more specific.")
                    if reasoning:
                        st.caption(reasoning)
            else:
                st.warning("Please describe your goal first.")

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

                params = main_recommendation["parameters"]
                preds  = main_recommendation["predictions"]

                # ── Store ALL results in session_state ──
                # The display block outside `if submitted:` reads from here,
                # so clicking any button won’t wipe the results.
                st.session_state.update({
                    "opt_pareto_df":      pareto_df.copy(),
                    "opt_params":         params.copy(),
                    "opt_preds":          preds.copy(),
                    "opt_scenario":       scenario,
                    "opt_target_quality": target_quality,
                    "opt_energy_limit":   energy_limit,
                    "opt_carbon_limit":   carbon_limit,
                    "opt_energy_preds":   energy_sig["predictions"].copy(),
                    "opt_quality_preds":  quality_sig["predictions"].copy(),
                    "opt_balanced_preds": balanced_sig["predictions"].copy(),
                })
                for _k in ("llm_pareto_summary", "llm_explanation"):
                    st.session_state.pop(_k, None)

            except Exception as e:
                st.error(f"Error during optimization: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # PERSISTENT RESULTS PANEL
    # Rendered from session_state — survives ALL button clicks and reruns
    # ──────────────────────────────────────────────────────────────────────────
    if "opt_pareto_df" in st.session_state:
        _pf  = st.session_state["opt_pareto_df"]
        _sc  = st.session_state["opt_scenario"]
        _par = st.session_state["opt_params"]
        _pre = st.session_state["opt_preds"]
        _tq  = st.session_state["opt_target_quality"]
        _el  = st.session_state["opt_energy_limit"]
        _cl  = st.session_state["opt_carbon_limit"]
        _ep  = st.session_state["opt_energy_preds"]
        _qp  = st.session_state["opt_quality_preds"]
        _bp  = st.session_state["opt_balanced_preds"]

        st.success(f"✅ Optimization complete! {len(_pf)} Pareto-optimal configurations found.")
        st.divider()

        # ── Section 2: Recommended Golden Signature ──
        st.header("🏆 Recommended Golden Signature")
        st.markdown(f"### Priority Mode: **{_sc}**")
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("#### Exact Machine Parameters")
            st.code(f"""
Drying Temperature: {_par['Drying_Temp']:.1f}°C
Compression Force: {_par['Compression_Force']:.1f} kN
Machine Speed: {_par['Machine_Speed']:.1f} RPM
Moisture Content: {_par['Moisture_Content']:.2f}%
Granulation Time: {_par['Granulation_Time']:.1f} min
Binder Amount: {_par['Binder_Amount']:.1f} kg
Drying Time: {_par['Drying_Time']:.1f} min
Lubricant Conc: {_par['Lubricant_Conc']:.2f}%
            """)
        with rc2:
            st.markdown("#### Predicted Outcomes")
            q_icon = "✅" if _pre["Quality_Score"] >= _tq else "⚠️"
            e_icon = "✅" if _pre["Energy_per_batch"] <= _el else "⚠️"
            c_icon = "✅" if _pre["Carbon_emission"] <= _cl else "⚠️"
            st.code(f"""
{q_icon} Quality Score: {_pre['Quality_Score']:.3f} (Target: >{_tq})
{e_icon} Energy Consump: {_pre['Energy_per_batch']:.2f} kWh (Limit: <{_el})
{c_icon} Carbon Emiss: {_pre['Carbon_emission']:.2f} kg (Limit: <{_cl})
Reliability Score: {_pre['Reliability_Index']:.3f}
Asset Health: {_pre.get('Asset_Health_Score', 1.0):.3f}
Balanced Score: {_pre['Balanced_Score']:.3f}
            """)

        st.divider()

        # ── Section 3: Pareto Visualizations ──
        golden_q = _pre["Quality_Score"]
        golden_e = _pre["Energy_per_batch"]
        golden_c = _pre["Carbon_emission"]
        golden_r = _pre["Reliability_Index"]
        st.header("📊 Tradeoff Visualizations")
        c1, c2, c3 = st.columns(3)
        with c1:
            fig1 = px.scatter(_pf, x="Predicted_Quality_Score", y="Predicted_Energy",
                              hover_data=["Granulation_Time", "Compression_Force"],
                              title="Energy vs Quality", color_discrete_sequence=["#1f77b4"])
            fig1.add_trace(go.Scatter(x=[golden_q], y=[golden_e], mode="markers",
                                      marker=dict(size=14, color="red", symbol="star"), name="Golden Sig"))
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.scatter(_pf, x="Predicted_Quality_Score", y="Predicted_Carbon",
                              hover_data=["Binder_Amount", "Drying_Temp"],
                              title="Carbon vs Quality", color_discrete_sequence=["#2ca02c"])
            fig2.add_trace(go.Scatter(x=[golden_q], y=[golden_c], mode="markers",
                                      marker=dict(size=14, color="red", symbol="star"), name="Golden Sig"))
            st.plotly_chart(fig2, use_container_width=True)
        with c3:
            fig3 = px.scatter(_pf, x="Predicted_Energy", y="Predicted_Reliability",
                              hover_data=["Machine_Speed", "Drying_Time"],
                              title="Reliability vs Energy", color_discrete_sequence=["#ff7f0e"])
            fig3.add_trace(go.Scatter(x=[golden_e], y=[golden_r], mode="markers",
                                      marker=dict(size=14, color="red", symbol="star"), name="Golden Sig"))
            st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # ── Section 4: Decision Comparison ──
        st.header("💡 Decision Comparison Panel")
        st.markdown("Alternate Top Strategy Recommendations:")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.info("🌱 **Energy Efficient Alternative**")
            st.markdown(f"Quality: **{_ep['Quality_Score']:.3f}**\n\nEnergy: **{_ep['Energy_per_batch']:.1f}** kWh\n\nAsset Health: **{_ep.get('Asset_Health_Score', 1.0):.3f}**")
        with dc2:
            st.success("⚖️ **Balanced Alternative**")
            st.markdown(f"Quality: **{_bp['Quality_Score']:.3f}**\n\nEnergy: **{_bp['Energy_per_batch']:.1f}** kWh\n\nAsset Health: **{_bp.get('Asset_Health_Score', 1.0):.3f}**")
        with dc3:
            st.warning("� **Quality Maximizing Alternative**")
            st.markdown(f"Quality: **{_qp['Quality_Score']:.3f}**\n\nEnergy: **{_qp['Energy_per_batch']:.1f}** kWh\n\nAsset Health: **{_qp.get('Asset_Health_Score', 1.0):.3f}**")

        st.divider()

        # ── Section 5: Full Pareto Table ──
        st.header("📋 Full Pareto Output Table")
        st.dataframe(_pf.rename(columns={
            "Predicted_Quality_Score": "Quality Score",
            "Predicted_Energy": "Energy (kWh)",
            "Predicted_Carbon": "Carbon (CO2)",
            "Predicted_Reliability": "Reliability",
            "Asset_Health_Score": "Asset Health",
            "Balanced_Score": "Balanced Score",
        }))

        st.divider()

        # ── LLM Feature 1: Pareto Analyst ──
        with st.expander("🔍 AI: Pareto Analysis", expanded=False):
            st.caption(f"AI-generated plain-English summary of all {len(_pf)} Pareto-optimal solutions.")
            if st.button("Generate Pareto Analysis", key="pareto_analysis_btn"):
                with st.spinner("Analyzing solutions..."):
                    st.session_state["llm_pareto_summary"] = analyze_pareto_results(_pf, _sc)
            if "llm_pareto_summary" in st.session_state:
                st.markdown(st.session_state["llm_pareto_summary"])

        # ── LLM Feature 2: Golden Signature Explainer ──
        with st.expander("💬 AI: Why This Configuration?", expanded=False):
            st.caption("AI explains why the Golden Signature parameters were selected for your batch.")
            if st.button("Explain Recommendation", key="explain_btn"):
                with st.spinner("Generating explanation..."):
                    st.session_state["llm_explanation"] = explain_golden_signature(_par, _pre, _sc)
            if "llm_explanation" in st.session_state:
                st.markdown(st.session_state["llm_explanation"])

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

    # ── LLM Feature 4: Batch History Insights ───────────────────────────────
    if len(history) > 0:
        with st.expander(f"🤖 AI Insights on Batch History ({len(history)} records)", expanded=False):
            st.caption("AI-generated pattern analysis and recommendations across your historical batch data.")
            if st.button("Generate AI Insights", key="history_insights_btn"):
                with st.spinner("Analyzing batch history..."):
                    insights = analyze_batch_history(history)
                st.markdown(insights)

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

    # ── LLM Feature 5: What-If Chat Assistant ───────────────────────────────
    with st.expander("💬 Describe Parameter Changes (AI Assistant)", expanded=False):
        st.caption("Describe what you want to change in plain English — AI will suggest exact slider values.")
        whatif_query = st.text_input(
            "Your request:",
            placeholder="e.g. What if I increase compression force to 22 kN and dry at 70°C?",
            key="whatif_query",
        )
        if st.button("Get AI Suggestion", key="whatif_btn"):
            if whatif_query.strip():
                with st.spinner("Interpreting your request..."):
                    machine_defaults = {
                        "Granulation_Time": 30.0,
                        "Binder_Amount": 5.0,
                        "Drying_Temp": 60.0,
                        "Drying_Time": 60.0,
                        "Compression_Force": 15.0,
                        "Machine_Speed": 30.0,
                        "Lubricant_Conc": 1.0,
                        "Moisture_Content": 2.5,
                    }
                    result = parse_operator_intent(whatif_query, machine_defaults)
                reasoning = result.pop("reasoning", "")
                if result:
                    st.success("💡 Suggested slider values (set your sliders accordingly):")
                    cols = st.columns(2)
                    for i, (k, v) in enumerate(result.items()):
                        cols[i % 2].metric(k.replace("_", " "), v)
                    if reasoning:
                        st.caption(f"*{reasoning}*")
                else:
                    st.warning("Could not extract specific parameters. Try being more specific.")
                    if reasoning:
                        st.caption(reasoning)
            else:
                st.warning("Please describe your request first.")

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

# -----------------------------------------------------------------------------
# TAB 6: AI CHATBOT
# -----------------------------------------------------------------------------
with tab6:
    st.header("🤖 OptiMFG AI Assistant")
    st.markdown(
        "Ask anything about manufacturing optimization, machine parameters, Pareto fronts, "
        "Golden Signatures, or how to use this platform. The AI has full context of OptiMFG."
    )

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display existing conversation
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input at the bottom
    if user_input := st.chat_input("Ask anything about manufacturing optimization..."):
        # Append and display user message
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_with_optimfg(st.session_state.chat_messages)
            st.markdown(response)

        # Persist assistant response
        st.session_state.chat_messages.append({"role": "assistant", "content": response})

    # Clear button
    if st.session_state.get("chat_messages"):
        if st.button("🗑️ Clear Chat History", key="clear_chat_btn"):
            st.session_state.chat_messages = []
            st.rerun()

# -----------------------------------------------------------------------------
# TAB 7: MODEL STATISTICS
# -----------------------------------------------------------------------------
with tab7:
    st.header("📊 Digital Twin Model Performance")
    st.markdown("""
    This tab displays the accuracy and performance metrics of the Digital Twin model 
    used for predicting manufacturing outcomes. Lower MAE and RMSE values indicate better model performance.
    """)
    
    # Try to load model metrics from the results folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metrics_file = os.path.join(script_dir, "results", "model_metrics.json")
    
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, "r") as f:
                model_metrics = json.load(f)
            
            st.success("✅ Model metrics loaded successfully")
            st.markdown("---")
            
            # Display metrics by target
            st.subheader("Performance Metrics by Target Variable")
            
            # Create columns for each metric
            target_cols = st.columns(len(model_metrics))
            
            for idx, (target, metrics) in enumerate(model_metrics.items()):
                with target_cols[idx]:
                    st.markdown(f"### {target.replace('_', ' ')}")
                    st.metric("MAE (Mean Absolute Error)", f"{metrics['MAE']:.4f}")
                    st.metric("RMSE (Root Mean Squared Error)", f"{metrics['RMSE']:.4f}")
            
            st.markdown("---")
            
            # Create a summary table
            st.subheader("Summary Table")
            metrics_data = []
            for target, metrics in model_metrics.items():
                metrics_data.append({
                    "Target Variable": target.replace('_', ' '),
                    "MAE": f"{metrics['MAE']:.4f}",
                    "RMSE": f"{metrics['RMSE']:.4f}"
                })
            
            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(metrics_df, use_container_width=True)
            
            st.markdown("---")
            
            # Visualization of metrics
            st.subheader("Visual Comparison")
            
            mae_values = [metrics['MAE'] for metrics in model_metrics.values()]
            rmse_values = [metrics['RMSE'] for metrics in model_metrics.values()]
            target_names = [target.replace('_', ' ') for target in model_metrics.keys()]
            
            # Create a bar chart comparing MAE and RMSE
            fig = go.Figure(data=[
                go.Bar(name='MAE', x=target_names, y=mae_values, marker_color='lightblue'),
                go.Bar(name='RMSE', x=target_names, y=rmse_values, marker_color='lightcoral')
            ])
            
            fig.update_layout(
                title="Model Error Metrics by Target",
                xaxis_title="Target Variable",
                yaxis_title="Error Value",
                barmode='group',
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Model Info and Interpretation
            st.subheader("Model Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("""
                **Model Type:** MultiOutput XGBoost Regressor
                
                **Input Features (8):**
                - Granulation Time
                - Binder Amount
                - Drying Temperature
                - Drying Time
                - Compression Force
                - Machine Speed
                - Lubricant Concentration
                - Moisture Content
                """)
            
            with col2:
                st.info("""
                **Target Variables (5):**
                - Quality Score
                - Energy per Batch
                - Carbon Emission
                - Reliability Index
                - Asset Health Score
                
                **Hyperparameters:**
                - Estimators: 100
                - Learning Rate: 0.1
                - Max Depth: 5
                """)
            
            st.markdown("---")
            
            # Interpretation guide
            st.subheader("How to Interpret These Metrics")
            st.markdown("""
            - **MAE (Mean Absolute Error):** Average absolute difference between predicted and actual values.
              Lower values indicate more accurate predictions.
            
            - **RMSE (Root Mean Squared Error):** Square root of average squared differences. 
              Penalizes larger errors more heavily than MAE. Lower values are better.
            
            - **Ratio RMSE/MAE:** Values closer to 1.0 indicate consistent error distribution.
              Larger ratios suggest the model has some outlier prediction errors.
            """)
            
            # Calculate and display RMSE/MAE ratios
            st.subheader("Error Consistency Analysis")
            consistency_data = []
            for target, metrics in model_metrics.items():
                ratio = metrics['RMSE'] / metrics['MAE'] if metrics['MAE'] > 0 else 0
                consistency_data.append({
                    "Target": target.replace('_', ' '),
                    "RMSE/MAE Ratio": f"{ratio:.4f}",
                    "Assessment": "Good" if 1.0 <= ratio <= 1.5 else "Acceptable" if 1.5 < ratio <= 2.0 else "Check for Outliers"
                })
            
            consistency_df = pd.DataFrame(consistency_data)
            st.dataframe(consistency_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading model metrics: {e}")
            st.info("Run the optimization pipeline first to generate model metrics.")
    else:
        st.warning("📋 Model metrics not found")
        st.info("""
        To view model performance statistics:
        1. Go to the **Optimization Dashboard** tab
        2. Click **Run Target-Driven Optimization**
        3. This will generate the model metrics file
        4. Return to this tab to view the statistics
        """)
