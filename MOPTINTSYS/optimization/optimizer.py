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

class ManufacturingProblem(Problem):
    def __init__(self, dt_model, bounds):
        """
        Defines the multi-objective optimization problem for PyMoo.
        
        Args:
            dt_model: The trained Digital Twin model used to evaluate parameters.
            bounds: A tuple (xl, xu) specifying lower and upper bounds for the 8 variables.
        """
        self.dt_model = dt_model
        self.feature_names = [
            'Granulation_Time', 'Binder_Amount', 'Drying_Temp', 'Drying_Time',
            'Compression_Force', 'Machine_Speed', 'Lubricant_Conc', 'Moisture_Content'
        ]
        
        # 8 decision variables, 5 objectives (hardness, dissolution, friability, energy, carbon)
        # Objectives are minimized by default in PyMoo.
        super().__init__(n_var=8, n_obj=5, n_ieq_constr=0, xl=bounds[0], xu=bounds[1])

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
        predictions = self.dt_model.predict(parameters_df)
        
        # We need to compute 5 objectives for each sample.
        # PyMoo minimizes by default.
        # 1. Maximize Hardness -> Minimize (-Hardness)
        # 2. Maximize Dissolution_Rate -> Minimize (-Dissolution_Rate)
        # 3. Minimize Friability -> Minimize (Friability)
        # 4. Minimize Energy_per_batch -> Minimize (Energy_per_batch)
        # 5. Minimize Carbon_emission -> Minimize (Carbon_emission)
        
        f1 = -np.array(predictions['Hardness'])
        f2 = -np.array(predictions['Dissolution_Rate'])
        f3 = np.array(predictions['Friability'])
        f4 = np.array(predictions['Energy_per_batch'])
        f5 = np.array(predictions['Carbon_emission'])
        
        # Stack the objectives horizontally so the final shape is (n_samples, 5)
        out["F"] = np.column_stack([f1, f2, f3, f4, f5])


class ManufacturingOptimizer:
    def __init__(self, digital_twin_model):
        """
        Initializes the optimizer with the trained Digital Twin model.
        
        Args:
            digital_twin_model: The predictive model used to evaluate configurations.
        """
        self.dt_model = digital_twin_model
        
    def evaluate_solution(self, parameters_vector: np.ndarray) -> dict:
        """
        Evaluation function for testing a single configuration directly.
        (Used independently of the vectorized PyMoo problem).
        """
        feature_names = [
            'Granulation_Time', 'Binder_Amount', 'Drying_Temp', 'Drying_Time',
            'Compression_Force', 'Machine_Speed', 'Lubricant_Conc', 'Moisture_Content'
        ]
        
        if isinstance(parameters_vector, list):
            parameters_vector = np.array(parameters_vector)
            
        parameters_df = pd.DataFrame([parameters_vector], columns=feature_names)
        predictions = self.dt_model.predict(parameters_df)
        
        outcomes = {
            'hardness': predictions['Hardness'][0],
            'friability': predictions['Friability'][0],
            'dissolution_rate': predictions['Dissolution_Rate'][0],
            'energy': predictions['Energy_per_batch'][0],
            'carbon': predictions['Carbon_emission'][0]
        }
        
        return outcomes

    def optimize(self, bounds: tuple, pop_size: int = 100, n_gen: int = 50):
        """
        Runs the NSGA-II optimization algorithm.
        
        Args:
            bounds (tuple): Tuple of two lists/arrays (lower_bounds, upper_bounds) for the 8 parameters.
            pop_size (int): Number of individuals in the population.
            n_gen (int): Number of generations to run the evolution.
            
        Returns:
            pd.DataFrame: A dataframe containing all optimal parameter sets and their predicted outcomes.
        """
        logging.info("Step 1: Defining the PyMoo problem...")
        problem = ManufacturingProblem(self.dt_model, bounds)
        
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
        
        # Remember to revert the maximized targets back to positive values
        results_df['Predicted_Hardness'] = -pareto_objectives[:, 0]
        results_df['Predicted_Dissolution_Rate'] = -pareto_objectives[:, 1]
        results_df['Predicted_Friability'] = pareto_objectives[:, 2]
        results_df['Predicted_Energy'] = pareto_objectives[:, 3]
        results_df['Predicted_Carbon'] = pareto_objectives[:, 4]
        
        return results_df
