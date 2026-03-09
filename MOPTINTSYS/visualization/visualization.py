"""
Visualization Module for OptiMFG

Provides functions to generate interactive charts and dashboards (using Plotly) 
for data analysis, model performance, and optimization results.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def plot_energy_vs_quality(pareto_df: pd.DataFrame, save_path: str = None):
    """
    Plots a 2D Pareto front showing the trade-off between Energy Consumption and Quality Score.
    
    Args:
        pareto_df (pd.DataFrame): DataFrame containing Pareto-optimal configurations.
        save_path (str, optional): If provided, saves the plot as an HTML file.
    """
    logging.info("Generating Energy vs Quality Pareto plot...")
    
    fig = px.scatter(
        pareto_df, 
        x='Predicted_Quality_Score', 
        y='Predicted_Energy',
        color='Predicted_Reliability',
        hover_data=['Granulation_Time', 'Compression_Force', 'Machine_Speed'],
        title="Pareto Front: Energy Consumption vs. Quality Score",
        labels={
            'Predicted_Quality_Score': 'Quality Score (Maximize)',
            'Predicted_Energy': 'Energy per Batch (Minimize)',
            'Predicted_Reliability': 'Reliability Score (Maximize)'
        },
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    fig.update_layout(template="plotly_dark", title_x=0.5)
    
    if save_path:
        fig.write_html(save_path)
        logging.info(f"Plot saved to {save_path}")
    else:
        fig.show()

def plot_carbon_vs_quality(pareto_df: pd.DataFrame, save_path: str = None):
    """
    Plots a 2D Pareto front showing Carbon Emissions vs Quality Score.
    
    Args:
        pareto_df (pd.DataFrame): DataFrame containing Pareto-optimal configurations.
        save_path (str, optional): If provided, saves the plot as an HTML file.
    """
    logging.info("Generating Carbon vs Quality Pareto plot...")
    
    fig = px.scatter(
        pareto_df, 
        x='Predicted_Quality_Score', 
        y='Predicted_Carbon',
        color='Predicted_Reliability',
        hover_data=['Binder_Amount', 'Drying_Temp'],
        title="Pareto Front: Carbon Emissions vs. Quality Score",
        labels={
            'Predicted_Carbon': 'Carbon Emissions (Minimize)',
            'Predicted_Quality_Score': 'Quality Score (Maximize)',
            'Predicted_Reliability': 'Reliability Score (Maximize)'
        },
        color_continuous_scale=px.colors.sequential.Plasma
    )
    
    fig.update_layout(template="plotly_dark", title_x=0.5)
    
    if save_path:
        fig.write_html(save_path)
        logging.info(f"Plot saved to {save_path}")
    else:
        fig.show()

def plot_3d_pareto(pareto_df: pd.DataFrame, save_path: str = None):
    """
    Creates a 3D interactive plot of Quality, Energy, and Reliability.
    
    Args:
        pareto_df (pd.DataFrame): DataFrame containing Pareto-optimal configurations.
        save_path (str, optional): If provided, saves the plot as an HTML file.
    """
    logging.info("Generating 3D Pareto Front plot...")
    
    fig = px.scatter_3d(
        pareto_df,
        x='Predicted_Quality_Score',
        y='Predicted_Energy',
        z='Predicted_Reliability',
        color='Predicted_Carbon',
        hover_data=['Compression_Force', 'Machine_Speed', 'Drying_Time'],
        title="3D Pareto Front: Quality vs Energy vs Reliability",
        labels={
            'Predicted_Quality_Score': 'Quality Score (Max)',
            'Predicted_Energy': 'Energy (Min)',
            'Predicted_Reliability': 'Reliability (Max)',
            'Predicted_Carbon': 'Carbon Emission'
        },
        color_continuous_scale=px.colors.sequential.Turbo
    )
    
    fig.update_layout(template="plotly_dark", title_x=0.5)
    
    if save_path:
        fig.write_html(save_path)
        logging.info(f"3D Plot saved to {save_path}")
    else:
        fig.show()

def generate_all_dashboards(pareto_df: pd.DataFrame, output_dir: str = "."):
    """
    Helper function to generate and save all plots.
    """
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    plot_energy_vs_quality(pareto_df, save_path=f"{output_dir}/energy_vs_quality.html")
    plot_carbon_vs_quality(pareto_df, save_path=f"{output_dir}/carbon_vs_quality.html")
    plot_3d_pareto(pareto_df, save_path=f"{output_dir}/pareto_3d.html")
