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
    # We estimate total process time using the available time parameters.
    # Assuming 'Granulation_Time' and 'Drying_Time' are in minutes.
    if 'Power_Consumption_kW' in processed_df.columns:
        total_time_mins = 0
        if 'Granulation_Time' in processed_df.columns:
            total_time_mins += processed_df['Granulation_Time']
        if 'Drying_Time' in processed_df.columns:
            total_time_mins += processed_df['Drying_Time']
            
        # Convert total time to hours
        total_time_hours = total_time_mins / 60.0
        
        # Calculate Energy Consumption in kWh per batch
        processed_df['Energy_Consumption_kWh'] = processed_df['Power_Consumption_kW'] * total_time_hours
    
    # -------------------------------------------------------------------------
    # 2. Feature Engineering: Carbon Emissions
    # -------------------------------------------------------------------------
    # Carbon_Emission = Total Energy * Emission Factor
    if 'Energy_Consumption_kWh' in processed_df.columns:
        processed_df['Carbon_Emissions_kg'] = processed_df['Energy_Consumption_kWh'] * CARBON_EMISSION_FACTOR
        
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
    # 4. Data Scaling
    # -------------------------------------------------------------------------
    # Note: Target columns (outcomes) usually aren't scaled prior to train-test splits 
    # unless necessary for specific algorithms. We keep this simple and return the complete dataframe.
    # We can separate X (features) and y (targets) later in the modeling phase.
    
    # Drop any new missing values generated during calculations
    processed_df = processed_df.fillna(0)
    
    return processed_df
