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
    Loads manufacturing batch data and process time-series data, 
    inspects their columns, and merges them on 'Batch_ID'.
    
    Args:
        batch_data_path (str): Path to the dataset containing process parameters and quality metrics.
        time_series_path (str): Path to the time-series dataset containing energy, temperature, pressure, etc.
        
    Returns:
        pd.DataFrame: A clean, merged dataframe containing all features at the batch level.
    """
    logging.info("Step 1: Loading datasets...")
    
    # 1. Load both datasets using pandas
    try:
        batch_df = pd.read_csv(batch_data_path)
        ts_df = pd.read_csv(time_series_path)
    except FileNotFoundError as e:
        logging.error(f"Data file not found: {e}")
        raise

    # 2. Inspect columns
    logging.info("Step 2: Inspecting columns...")
    logging.info(f"Batch Data Columns: {batch_df.columns.tolist()}")
    logging.info(f"Time-Series Data Columns: {ts_df.columns.tolist()}")
    
    # Check if 'Batch_ID' exists in both dataframes to perform the merge
    if 'Batch_ID' not in batch_df.columns:
        raise ValueError("Missing 'Batch_ID' in batch production data.")
    if 'Batch_ID' not in ts_df.columns:
        raise ValueError("Missing 'Batch_ID' in process time-series data.")

    # Time-series data inherently contains multiple readings over time per batch.
    # To merge it properly with fixed batch outcomes, we aggregate the sensors.
    # Here, we group by 'Batch_ID' and calculate the mean values for the sensors.
    logging.info("Aggregating time-series readings by Batch_ID (using average over time)...")
    ts_agg_df = ts_df.groupby('Batch_ID').mean().reset_index()

    # 3. Merge datasets using Batch_ID
    logging.info("Step 3: Merging datasets on 'Batch_ID'...")
    # 'inner' join ensures we only keep batches that appear in both files.
    merged_df = pd.merge(batch_df, ts_agg_df, on='Batch_ID', how='inner')
    
    # 4. Return a clean dataframe
    # A basic cleaning step: we drop purely duplicated rows and NaN values.
    initial_shape = merged_df.shape
    clean_df = merged_df.drop_duplicates()
    clean_df = clean_df.dropna()
    
    logging.info(f"Data load and merge complete.")
    logging.info(f"Initial merged shape: {initial_shape} | Cleaned shape: {clean_df.shape}")
    
    return clean_df
