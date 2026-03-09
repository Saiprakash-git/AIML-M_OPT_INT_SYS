"""
Feature Engineering Module for OptiMFG

Responsible for data preprocessing, scaling, handling missing values, 
and generating new features required for the Digital Twin model.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Constants
# Standard emission factor (e.g., kg CO2 per kWh of energy consumed)
# This value depends on the local energy grid. 
CARBON_EMISSION_FACTOR = 0.45 

def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and preprocesses the dataset before model training/inference,
    including deriving critical targets (Energy, Carbon).
    
    Args:
        df (pd.DataFrame): Raw dataframe from the data loader.
        
    Returns:
        pd.DataFrame: Preprocessed dataframe with feature-engineered columns.
    """
    
    # Work on a copy to avoid SettingWithCopyWarning
    processed_df = df.copy()
    
    # -------------------------------------------------------------------------
    # 1. Feature Engineering: Total Energy Consumption
    # -------------------------------------------------------------------------
    # Energy = Power * Time. 
    # If not already computed by the data loader, we estimate it.
    if 'Energy_per_batch' not in processed_df.columns and 'Power_Consumption_kW' in processed_df.columns:
        total_time_mins = 0
        if 'Granulation_Time' in processed_df.columns:
            total_time_mins += processed_df['Granulation_Time']
        if 'Drying_Time' in processed_df.columns:
            total_time_mins += processed_df['Drying_Time']
            
        # Convert total time to hours
        total_time_hours = total_time_mins / 60.0
        
        # Calculate Energy Consumption in kWh per batch
        processed_df['Energy_per_batch'] = processed_df['Power_Consumption_kW'] * total_time_hours
    
    # -------------------------------------------------------------------------
    # 2. Feature Engineering: Carbon Emissions
    # -------------------------------------------------------------------------
    # Carbon_Emission = Total Energy * Emission Factor
    if 'Energy_per_batch' in processed_df.columns:
        processed_df['Carbon_emission'] = processed_df['Energy_per_batch'] * CARBON_EMISSION_FACTOR
        
    # -------------------------------------------------------------------------
    # 3. Additional Derived Features (Examples)
    # -------------------------------------------------------------------------
    # Example A: "Temperature to Speed Ratio" - Can help explain stress on the machine
    if 'Temperature' in processed_df.columns and 'Machine_Speed' in processed_df.columns:
        # Adding a small epsilon to avoid division by zero
        processed_df['Temp_to_Speed_Ratio'] = processed_df['Temperature'] / (processed_df['Machine_Speed'] + 1e-6)
        
    # Example B: "Force Time Product" - proxy for total mechanical work done during compression
    if 'Compression_Force' in processed_df.columns and 'Machine_Speed' in processed_df.columns:
        # Assuming higher speed = less time spent compressing per tablet
        processed_df['Compression_Work_Proxy'] = processed_df['Compression_Force'] / (processed_df['Machine_Speed'] + 1e-6)

    # -------------------------------------------------------------------------
    # 4. Feature Engineering: Quality Score
    # -------------------------------------------------------------------------
    # Quality_Score = 0.4 * Hardness_norm + 0.4 * Dissolution_norm - 0.2 * Friability_norm
    if all(col in processed_df.columns for col in ['Hardness', 'Dissolution_Rate', 'Friability']):
        # Normalize between 0 and 1
        hardness_min, hardness_max = processed_df['Hardness'].min(), processed_df['Hardness'].max()
        diss_min, diss_max = processed_df['Dissolution_Rate'].min(), processed_df['Dissolution_Rate'].max()
        friab_min, friab_max = processed_df['Friability'].min(), processed_df['Friability'].max()
        
        # Avoid division by zero by using max checks
        if hardness_max > hardness_min:
            h_norm = (processed_df['Hardness'] - hardness_min) / (hardness_max - hardness_min)
        else:
            h_norm = 0.5
            
        if diss_max > diss_min:
            d_norm = (processed_df['Dissolution_Rate'] - diss_min) / (diss_max - diss_min)
        else:
            d_norm = 0.5
            
        if friab_max > friab_min:
            f_norm = (processed_df['Friability'] - friab_min) / (friab_max - friab_min)
        else:
            f_norm = 0.5
            
        processed_df['Quality_Score'] = 0.4 * h_norm + 0.4 * d_norm - 0.2 * f_norm
    
    # -------------------------------------------------------------------------
    # 5. Data Scaling
    # -------------------------------------------------------------------------
    # Note: Target columns (outcomes) usually aren't scaled prior to train-test splits 
    # unless necessary for specific algorithms. We keep this simple and return the complete dataframe.
    # We can separate X (features) and y (targets) later in the modeling phase.
    
    # Drop any new missing values generated during calculations
    processed_df = processed_df.fillna(0)
    
    return processed_df
