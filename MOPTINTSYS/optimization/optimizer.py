"""
Optimizer Module for OptiMFG

Implements the multi-objective optimization engine using NSGA-II 
to identify the best parameter combinations balancing quality and resources.
"""

import pandas as pd
import numpy as np
import logging

from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class ManufacturingOptimizationProblem(Problem):
    def __init__(self, dt_model, bounds, targets=None, preferences=None):
        """
        Defines the multi-objective optimization problem for PyMoo.
        
        Args:
            dt_model: The trained Digital Twin model used to evaluate parameters.
            bounds: A tuple (xl, xu) specifying lower and upper bounds for the 8 variables.
            targets: Dictionary with optional keys 'energy_limit', 'carbon_limit', 'target_quality'
            preferences: Dictionary of weights from operator feedback.
        """
        self.dt_model = dt_model
        self.targets = targets or {}
        self.preferences = preferences or {}
        self.feature_names = [
            'Granulation_Time', 'Binder_Amount', 'Drying_Temp', 'Drying_Time',
            'Compression_Force', 'Machine_Speed', 'Lubricant_Conc', 'Moisture_Content'
        ]
        
        # Emission factor for calculating Carbon emissions from Energy
        self.emission_factor = 0.45 
        
        # Determine number of inequality constraints based on targets
        n_ieq_constr = 0
        if self.targets.get('energy_limit'): n_ieq_constr += 1
        if self.targets.get('carbon_limit'): n_ieq_constr += 1
        if self.targets.get('target_quality'): n_ieq_constr += 1
        
        # 8 decision variables, 4 objectives
        # Objectives are minimized by default in PyMoo.
        super().__init__(n_var=8, n_obj=4, n_ieq_constr=n_ieq_constr, xl=bounds[0], xu=bounds[1])
        
    def _evaluate(self, x, out, *args, **kwargs):
        """
        Evaluates a batch of solutions (population) and calculates objective values.
        
        Args:
            x (np.ndarray): 2D array of shape (n_samples, 8) containing process parameters.
            out (dict): The output dictionary where objective values 'F' will be stored.
        """
        # Convert population batch into a DataFrame for the Digital Twin model
        parameters_df = pd.DataFrame(x, columns=self.feature_names)
        
        # Predict outcomes using the Digital Twin model for the whole batch
        # Assuming the model returns at least Hardness, Friability, Dissolution_Rate, Energy_per_batch
        predictions = self.dt_model.predict(parameters_df)
        
        # We need to compute 4 objectives for each sample.
        # PyMoo minimizes by default.
        # 1. Maximize Quality_Score -> Minimize (-Quality_Score)
        # 2. Minimize Energy_per_batch -> Minimize (Energy_per_batch)
        # 3. Minimize Carbon_emission -> Minimize (Carbon_emission)
        # 4. Maximize Reliability_Index -> Minimize (-Reliability_Index)
        
        f1 = -np.array(predictions['Quality_Score']) * self.preferences.get('quality_weight', 1.0)
        f2 = np.array(predictions['Energy_per_batch']) * self.preferences.get('energy_weight', 1.0)
        f3 = np.array(predictions['Carbon_emission'])
        f4 = -np.array(predictions['Reliability_Index'])
        
        # Stack the objectives horizontally so the final shape is (n_samples, 4)
        out["F"] = np.column_stack([f1, f2, f3, f4])
        
        if self.targets:
            g_list = []
            if self.targets.get('energy_limit'):
                # energy_per_batch <= energy_limit => (energy - limit) <= 0
                g_list.append(np.array(predictions['Energy_per_batch']) - self.targets['energy_limit'])
            if self.targets.get('carbon_limit'):
                g_list.append(np.array(predictions['Carbon_emission']) - self.targets['carbon_limit'])
            if self.targets.get('target_quality'):
                # target_quality <= Quality => (target - Quality) <= 0
                g_list.append(self.targets['target_quality'] - np.array(predictions['Quality_Score']))
                
            if g_list:
                out["G"] = np.column_stack(g_list)


class ManufacturingOptimizer:
    def __init__(self, digital_twin_model):
        """
        Initializes the optimizer with the trained Digital Twin model.
        
        Args:
            digital_twin_model: The predictive model used to evaluate configurations.
        """
        self.dt_model = digital_twin_model
        
    def simulate_batch(self, parameters: dict) -> dict:
        """
        Dedicated simulation interface that connects the optimizer and ML model.
        
        Args:
            parameters (dict): 8 process parameters (Granulation_Time, etc.)
            
        Returns:
            dict: Predicted Quality_Score, Energy_per_batch, Carbon_emission, Reliability_Index
        """
        # Convert dict to DataFrame 
        parameters_df = pd.DataFrame([parameters])
        # Model predictions
        predictions = self.dt_model.predict(parameters_df)
        
        return {
            'Quality_Score': predictions['Quality_Score'][0],
            'Energy_per_batch': predictions['Energy_per_batch'][0],
            'Carbon_emission': predictions['Carbon_emission'][0],
            'Reliability_Index': predictions['Reliability_Index'][0],
            'Asset_Health_Score': predictions.get('Asset_Health_Score', [1.0])[0]
        }

    def optimize(self, bounds=None, pop_size: int = 100, n_gen: int = 50, targets=None, preferences=None):
        """
        Runs the NSGA-II optimization algorithm.
        
        Args:
            bounds (tuple, optional): Tuple of two arrays (lower_bounds, upper_bounds). If None, realistic defaults are used.
            pop_size (int): Number of individuals in the population.
            n_gen (int): Number of generations to run the evolution.
            targets (dict, optional): Custom constraint targets (energy_limit, carbon_limit, target_quality).
            preferences (dict, optional): Learned operator priorities to adjust objective weights.
            
        Returns:
            pd.DataFrame: A dataframe containing all optimal parameter sets and their predicted outcomes.
        """
        # If bounds are not provided, we define realistic parameter bounds
        if bounds is None:
            # Order: Granulation_Time, Binder_Amount, Drying_Temp, Drying_Time, Compression_Force, Machine_Speed, Lubricant_Conc, Moisture_Content
            xl = np.array([10.0, 1.0, 40.0, 20.0, 5.0, 10.0, 0.1, 1.0])
            xu = np.array([60.0, 10.0, 80.0, 120.0, 30.0, 50.0, 2.0, 5.0])
            bounds = (xl, xu)
            
        logging.info("Step 1: Defining the PyMoo problem...")
        problem = ManufacturingOptimizationProblem(self.dt_model, bounds, targets=targets, preferences=preferences)
        
        logging.info("Step 2: Initializing NSGA-II algorithm...")
        algorithm = NSGA2(pop_size=pop_size)
        
        # Define termination criterion (number of generations)
        termination = get_termination("n_gen", n_gen)
        
        logging.info(f"Step 3: Running Optimization (pop_size={pop_size}, generations={n_gen})...")
        res = minimize(problem,
                       algorithm,
                       termination,
                       seed=42,
                       verbose=True)
                       
        logging.info("Optimization complete.")
        
        # Extract Pareto-optimal parameters (res.X) and their objectives (res.F)
        pareto_params = res.X
        pareto_objectives = res.F
        
        if pareto_params is None:
            logging.error("No Pareto-optimal solutions found.")
            return None
            
        # Format the results into a readable Pandas DataFrame
        logging.info(f"Found {len(pareto_params)} Pareto-optimal configurations.")
        
        # Decision variables
        feature_names = [
            'Granulation_Time', 'Binder_Amount', 'Drying_Temp', 'Drying_Time',
            'Compression_Force', 'Machine_Speed', 'Lubricant_Conc', 'Moisture_Content'
        ]
        results_df = pd.DataFrame(pareto_params, columns=feature_names)
        
        # Ask Digital Twin for full predictions to properly associate outcomes without tracking scaled variables
        full_preds = self.dt_model.predict(results_df)
        
        results_df['Predicted_Quality_Score'] = full_preds['Quality_Score']
        results_df['Predicted_Energy'] = full_preds['Energy_per_batch']
        results_df['Predicted_Carbon'] = full_preds['Carbon_emission']
        results_df['Predicted_Reliability'] = full_preds['Reliability_Index']
        results_df['Asset_Health_Score'] = full_preds.get('Asset_Health_Score', np.ones(len(results_df)))
        
        # Balanced_Score = Quality_Score - 0.2 * Energy_per_batch - 0.2 * Carbon_emission
        results_df['Balanced_Score'] = (
            results_df['Predicted_Quality_Score'] 
            - 0.2 * results_df['Predicted_Energy'] 
            - 0.2 * results_df['Predicted_Carbon']
        )
        
        return results_df

