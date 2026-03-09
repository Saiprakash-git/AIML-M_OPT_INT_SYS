"""
Data Loader Module for OptiMFG

Handles data ingestion from various sources (CSV, databases, APIs) 
for both batch production data and time-series process data.
"""

import pandas as pd
import logging

# Basic logging configuration to track the data loading process
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_manufacturing_data(batch_data_path: str, time_series_path: str) -> pd.DataFrame:
    """
    Loads manufacturing batch data and process time-series data.
    - Production data is a single sheet.
    - Process data consists of multiple sheets (each sheet is a distinct Batch_ID).
    
    Args:
        batch_data_path (str): Path to the dataset containing batch parameters and quality metrics.
        time_series_path (str): Path to the time-series dataset containing energy, temperature, etc.
        
    Returns:
        pd.DataFrame: A clean, merged dataframe containing all features.
    """
    logging.info("Step 1: Loading datasets...")
    
    try:
        # 1. Load Batch Production Data
        if batch_data_path.endswith('.csv'):
            batch_df = pd.read_csv(batch_data_path)
        else:
            batch_df = pd.read_excel(batch_data_path)
            
        logging.info("Step 2: Processing multi-sheet Time-Series Data...")
        
        # 2. Load Process Time-Series Data (All sheets)
        if time_series_path.endswith('.csv'):
            # Fallback if someone uses a CSV (which doesn't support sheets)
            ts_data_dict = {"Batch_Undefined": pd.read_csv(time_series_path)}
        else:
            # Read all sheets from the Excel file into a dictionary of DataFrames
            ts_data_dict = pd.read_excel(time_series_path, sheet_name=None)
            
    except FileNotFoundError as e:
        logging.error(f"Data file not found: {e}")
        raise

    # 3. Process each sheet (each batch's time-series data)
    aggregated_ts_records = []
    
    for sheet_name, ts_df in ts_data_dict.items():
        # Clean potential whitespace from sheet name to ensure clean Batch_IDs
        batch_id = str(sheet_name).strip()
        
        # Standardize Batch_ID names (remove 'Batch_' prefix if it exists)
        if batch_id.startswith("Batch_"):
            batch_id = batch_id.replace("Batch_", "", 1)
            
        # Skip if dataframe is entirely empty
        if ts_df.empty:
            continue
            
        # We need specific columns to compute the energy proxy 
        # (Assuming Time_Minutes and Power_Consumption_kW exist)
        if 'Time_Minutes' not in ts_df.columns or 'Power_Consumption_kW' not in ts_df.columns:
            logging.warning(f"Skipping batch sheet {batch_id}: Missing Time or Power columns.")
            continue
            
        # Calculate total process time in hours for this specific batch
        total_time_minutes = ts_df['Time_Minutes'].max() # or sum depending on how time is logged
        # Assuming the maximum time logged represents the total duration of the phase
        total_time_hours = total_time_minutes / 60.0
        
        # Compute the average power consumption handling missing/strings dynamically
        avg_power_kw = ts_df['Power_Consumption_kW'].mean()
        
        # Compute Energy per batch
        energy_per_batch = avg_power_kw * total_time_hours
        
        # Compute variance for reliability calculation
        # If there's only one row, variance will be NaN, so fill with 0
        power_variance = ts_df['Power_Consumption_kW'].var() if len(ts_df) > 1 else 0
        
        temp_variance = 0
        if 'Temperature_C' in ts_df.columns:
            temp_variance = ts_df['Temperature_C'].var() if len(ts_df) > 1 else 0
            
        power_variance = 0 if pd.isna(power_variance) else power_variance
        temp_variance = 0 if pd.isna(temp_variance) else temp_variance
        
        reliability_index = 1.0 / (1.0 + power_variance + temp_variance)

        # Asset Health Monitoring via Isolation Forest (detects abnormal power patterns)
        from sklearn.ensemble import IsolationForest
        asset_health_score = 1.0
        if len(ts_df) > 10:
            # Need enough points to detect anomalies
            power_data = ts_df[['Power_Consumption_kW']].fillna(0)
            iso_forest = IsolationForest(contamination=0.05, random_state=42)
            anomalies = iso_forest.fit_predict(power_data)
            # -1 for anomalies, 1 for normal
            anomaly_ratio = sum(1 for a in anomalies if a == -1) / len(anomalies)
            asset_health_score = max(0.0, 1.0 - (anomaly_ratio * 5.0)) # Scale penalty 
        
        # Create an aggregated record for this specific batch
        record = {
            'Batch_ID': batch_id,
            'Power_Consumption_kW': avg_power_kw,
            'Energy_per_batch': energy_per_batch,
            'Power_variance': power_variance,
            'Temperature_variance': temp_variance,
            'Reliability_Index': reliability_index,
            'Asset_Health_Score': asset_health_score
        }
        
        # Add other sensor numeric averages (Temperature_C, Pressure_Bar, etc.)
        numeric_means = ts_df.mean(numeric_only=True)
        for col, mean_val in numeric_means.items():
            if col not in ['Time_Minutes', 'Power_Consumption_kW']:
                record[col] = mean_val
                
        aggregated_ts_records.append(record)
        
    # Convert all gathered time-series summaries into a solid DataFrame
    ts_agg_df = pd.DataFrame(aggregated_ts_records)
    
    if ts_agg_df.empty:
        raise ValueError("Failed to aggregate time-series data. Ensure the sheets are structured correctly.")
        
    # Ensure Batch_ID is uniformly formatted as a string for merging
    batch_df['Batch_ID'] = batch_df['Batch_ID'].astype(str).str.strip()
    
    # 4. Merge datasets using Batch_ID
    logging.info("Step 3: Merging datasets on 'Batch_ID'...")
    # 'inner' join ensures we only keep batches that appear in both files perfectly.
    merged_df = pd.merge(batch_df, ts_agg_df, on='Batch_ID', how='inner')
    
    # 5. Return a clean dataframe
    # Drop purely duplicated rows and NaN values
    initial_shape = merged_df.shape
    clean_df = merged_df.drop_duplicates()
    clean_df = clean_df.dropna()
    
    logging.info(f"Data load and merge complete.")
    logging.info(f"Initial merged shape: {initial_shape} | Cleaned shape: {clean_df.shape}")
    
    return clean_df
