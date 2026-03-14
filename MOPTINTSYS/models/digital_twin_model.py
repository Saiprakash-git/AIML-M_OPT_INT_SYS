"""
Digital Twin Model Module for OptiMFG

Contains the machine learning models (e.g., XGBoost with MultiOutputRegressor) 
that predict outcomes (quality, energy, emissions) based on process parameters.
"""

import pandas as pd
import numpy as np
import joblib
import logging

from xgboost import XGBRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class DigitalTwinModel:
    def __init__(self):
        """
        Initializes the MultiOutput XGBoost model used for predicting manufacturing outcomes.
        """
        # Define the exact input features (controllable process parameters)
        self.input_features = [
            'Granulation_Time',
            'Binder_Amount',
            'Drying_Temp',
            'Drying_Time',
            'Compression_Force',
            'Machine_Speed',
            'Lubricant_Conc',
            'Moisture_Content'
        ]
        
        # Define the exact target outputs to predict
        self.output_targets = [
            'Quality_Score',
            'Energy_per_batch',
            'Carbon_emission',
            'Reliability_Index',
            'Asset_Health_Score'
        ]
        
        # Initialize the base XGBoost regressor
        # random_state ensures reproducibility
        xgb = XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        # Wrap it in a MultiOutputRegressor to predict multiple targets simultaneously
        self.model = MultiOutputRegressor(xgb)
        
        # Store model performance metrics
        self.metrics = {}

    def train(self, df: pd.DataFrame, model_save_path: str = 'models/digital_twin.pkl'):
        """
        Trains the Digital Twin predictive model and saves it to disk.
        
        Args:
            df (pd.DataFrame): The preprocessed dataset containing features and targets.
            model_save_path (str): Filepath to save the trained model.
        """
        logging.info("Preparing data for Digital Twin model training...")
        
        # Ensure all required columns are present
        missing_cols = [col for col in self.input_features + self.output_targets if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing essential columns in the dataframe: {missing_cols}. Please check feature engineering.")

        # Extract features (X) and targets (y)
        X = df[self.input_features]
        y = df[self.output_targets]
        
        logging.info(f"Training MultiOutput XGBoost Regressor on {len(X)} samples...")
        self.model.fit(X, y)
        logging.info("Training complete.")
        
        # Evaluate model performance on the training set (for sanity check)
        # Note: In a real-world scenario, you'd evaluate on a separate test set.
        self.evaluate(X, y)
        
        # Save the model
        joblib.dump(self.model, model_save_path)
        logging.info(f"Model successfully saved to {model_save_path}")

    def evaluate(self, X, y_true):
        """
        Evaluates the model using Mean Absolute Error (MAE) and 
        Root Mean Squared Error (RMSE) for each target.
        """
        logging.info("Evaluating model performance...")
        y_pred = self.model.predict(X)
        
        metrics = {}
        # y_pred is an array of shape (n_samples, n_targets). We evaluate each target.
        for i, target in enumerate(self.output_targets):
            mae = mean_absolute_error(y_true[target], y_pred[:, i])
            rmse = np.sqrt(mean_squared_error(y_true[target], y_pred[:, i]))
            
            metrics[target] = {
                'MAE': float(mae),
                'RMSE': float(rmse)
            }
            
            logging.info(f"Target: {target} | MAE: {mae:.4f} | RMSE: {rmse:.4f}")
        
        # Store metrics for later access
        self.metrics = metrics
        return metrics

    def load_model(self, model_path: str = 'models/digital_twin.pkl'):
        """
        Loads a previously trained model from disk.
        """
        self.model = joblib.load(model_path)
        logging.info(f"Model loaded from {model_path}")

    def predict(self, process_parameters: pd.DataFrame) -> dict:
        """
        Simulates outcomes based on input process parameters.
        
        Args:
            process_parameters (pd.DataFrame): The input variables containing the 8 controllable features.
            
        Returns:
            dict: The predicted quality metrics, energy use, and emissions.
        """
        # Ensure the input DataFrame has the features in the correct order
        X_input = process_parameters[self.input_features]
        
        # Make predictions
        predictions = self.model.predict(X_input)
        
        # Format the output as a dictionary mappings list of predictions to their target names
        # Assuming predicting for a single configuration (batch size 1) or multiple
        results = {}
        for i, target in enumerate(self.output_targets):
            results[target] = predictions[:, i].tolist()
            
        return results
