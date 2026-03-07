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

def plot_energy_vs_hardness(pareto_df: pd.DataFrame, save_path: str = None):
    """
    Plots a 2D Pareto front showing the trade-off between Energy Consumption and Hardness.
    
    Args:
        pareto_df (pd.DataFrame): DataFrame containing Pareto-optimal configurations.
        save_path (str, optional): If provided, saves the plot as an HTML file.
    """
    logging.info("Generating Energy vs Hardness Pareto plot...")
    
    fig = px.scatter(
        pareto_df, 
        x='Predicted_Hardness', 
        y='Predicted_Energy',
        color='Predicted_Dissolution_Rate',
        hover_data=['Granulation_Time', 'Compression_Force', 'Machine_Speed'],
        title="Pareto Front: Energy Consumption vs. Tablet Hardness",
        labels={
            'Predicted_Hardness': 'Hardness (Maximize)',
            'Predicted_Energy': 'Energy per Batch (Minimize)',
            'Predicted_Dissolution_Rate': 'Dissolution Rate'
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
    Plots a 2D Pareto front showing Carbon Emissions vs Quality (Dissolution Rate).
    Size represents Hardness and color represents Friability.
    
    Args:
        pareto_df (pd.DataFrame): DataFrame containing Pareto-optimal configurations.
        save_path (str, optional): If provided, saves the plot as an HTML file.
    """
    logging.info("Generating Carbon vs Quality Pareto plot...")
    
    # In this plot:
    # X-axis: Carbon Emissions (Minimize)
    # Y-axis: Dissolution Rate (Maximize)
    # Color: Friability (Minimize)
    # Size: Hardness (Maximize)
    
    fig = px.scatter(
        pareto_df, 
        x='Predicted_Carbon', 
        y='Predicted_Dissolution_Rate',
        color='Predicted_Friability',
        size='Predicted_Hardness',
        hover_data=['Binder_Amount', 'Drying_Temp'],
        title="Pareto Front: Carbon Emissions vs. Quality (Dissolution, Friability, Hardness)",
        labels={
            'Predicted_Carbon': 'Carbon Emissions (Minimize)',
            'Predicted_Dissolution_Rate': 'Dissolution Rate (Maximize)',
            'Predicted_Friability': 'Friability (Minimize)'
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
    Creates a 3D interactive plot of the three most conflicting objectives:
    Hardness, Energy, and Carbon.
    
    Args:
        pareto_df (pd.DataFrame): DataFrame containing Pareto-optimal configurations.
        save_path (str, optional): If provided, saves the plot as an HTML file.
    """
    logging.info("Generating 3D Pareto Front plot...")
    
    fig = px.scatter_3d(
        pareto_df,
        x='Predicted_Hardness',
        y='Predicted_Energy',
        z='Predicted_Carbon',
        color='Predicted_Dissolution_Rate',
        hover_data=['Compression_Force', 'Machine_Speed', 'Drying_Time'],
        title="3D Pareto Front: Hardness vs Energy vs Carbon",
        labels={
            'Predicted_Hardness': 'Hardness (Max)',
            'Predicted_Energy': 'Energy (Min)',
            'Predicted_Carbon': 'Carbon (Min)'
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
        
    plot_energy_vs_hardness(pareto_df, save_path=f"{output_dir}/energy_vs_hardness.html")
    plot_carbon_vs_quality(pareto_df, save_path=f"{output_dir}/carbon_vs_quality.html")
    plot_3d_pareto(pareto_df, save_path=f"{output_dir}/pareto_3d.html")
