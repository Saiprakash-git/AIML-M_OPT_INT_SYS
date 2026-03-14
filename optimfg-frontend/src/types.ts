// ─── Shared TypeScript types for OptiMFG Dashboard ───────────────────────────

export interface PlantConfig {
  electricity_capacity_kw: number;
  machine_power_limit_kw: number;
  emission_factor: number;
  carbon_emission_limit_kg: number;
  default_machine_configuration: string;
  plant_operating_constraints: string;
}

export interface BatchCreateRequest {
  batch_id: string;
  material_type: string;
  batch_size: number;
  target_quality: number;
  energy_limit: number;
  carbon_limit: number;
  optimization_mode: string;
}

export interface ParameterConstraints {
  Granulation_Time: [number, number];
  Binder_Amount: [number, number];
  Drying_Temp: [number, number];
  Drying_Time: [number, number];
  Compression_Force: [number, number];
  Machine_Speed: [number, number];
  Lubricant_Conc: [number, number];
  Moisture_Content: [number, number];
}

export interface OptimizationRequest {
  batch_id: string;
  scenario: string;
  constraints: ParameterConstraints;
  targets: { energy_limit: number; carbon_limit: number; target_quality: number };
  pop_size: number;
  n_gen: number;
}

export interface RecommendedConfig {
  Granulation_Time: number;
  Binder_Amount: number;
  Drying_Temp: number;
  Drying_Time: number;
  Compression_Force: number;
  Machine_Speed: number;
  Lubricant_Conc: number;
  Moisture_Content: number;
}

export interface PredictedOutcomes {
  Quality_Score: number;
  Energy_per_batch: number;
  Carbon_emission: number;
  Reliability_Index: number;
  Asset_Health_Score: number;
  Balanced_Score: number;
}

export interface OptimizationResult {
  status: string;
  batch_id: string;
  scenario_mode: string;
  recommended_configuration: RecommendedConfig;
  predicted_outcomes: PredictedOutcomes;
  overall_fitness_score: number;
}

export interface ParetoSolution {
  Granulation_Time: number;
  Binder_Amount: number;
  Drying_Temp: number;
  Drying_Time: number;
  Compression_Force: number;
  Machine_Speed: number;
  Lubricant_Conc: number;
  Moisture_Content: number;
  Predicted_Quality_Score: number;
  Predicted_Energy: number;
  Predicted_Carbon: number;
  Predicted_Reliability: number;
  Asset_Health_Score: number;
  Balanced_Score: number;
}

export interface GoldenSignature {
  parameters: RecommendedConfig;
  predictions: PredictedOutcomes;
  overall_score: number;
  batch_context: string;
  material_type?: string;
}

export interface GoldenSignatureMap {
  [scenario: string]: GoldenSignature;
}

export interface BatchRecord {
  batch_id: string;
  material_type?: string;
  optimization_mode?: string;
  predicted_outcomes?: Partial<PredictedOutcomes>;
  status?: string;
  pareto_solutions_count?: number;
  targets_used?: {
    energy_limit: number;
    carbon_limit: number;
    target_quality: number;
  };
}

export interface SimulateRequest {
  parameters: {
    Granulation_Time: number;
    Binder_Amount: number;
    Drying_Temp: number;
    Drying_Time: number;
    Compression_Force: number;
    Machine_Speed: number;
    Lubricant_Conc: number;
    Moisture_Content: number;
  };
}

export interface ModelMetric {
  MAE: number;
  RMSE: number;
}

export interface ModelMetrics {
  [target: string]: ModelMetric;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface Toast {
  msg: string;
  type: 'success' | 'danger' | 'warn';
}
