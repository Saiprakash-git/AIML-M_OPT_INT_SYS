import type {
  PlantConfig, BatchRecord, OptimizationRequest,
  OptimizationResult, ParetoSolution, GoldenSignatureMap,
  SimulateRequest, ModelMetrics, ChatMessage,
} from './types';

export const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json();
}

export const api = {
  // Plant
  getPlantConfig: () => request<PlantConfig>('/plant/config'),
  savePlantConfig: (cfg: PlantConfig) =>
    request('/plant/configure', { method: 'POST', body: JSON.stringify(cfg) }),

  // Batch
  createBatch: (payload: {
    batch_id: string; material_type: string; batch_size: number;
    target_quality: number; energy_limit: number; carbon_limit: number;
    optimization_mode: string;
  }) => request('/batch/create', { method: 'POST', body: JSON.stringify(payload) }),

  optimize: (payload: OptimizationRequest): Promise<OptimizationResult> =>
    request('/batch/optimize', { method: 'POST', body: JSON.stringify(payload) }),

  getBatch: (batchId: string): Promise<BatchRecord> => request(`/batch/${batchId}`),

  getBatchHistory: (): Promise<BatchRecord[]> => request('/batch-history'),

  getPareto: (batchId: string): Promise<{ batch_id: string; pareto_solutions: ParetoSolution[] }> =>
    request(`/pareto/${batchId}`),

  // Simulate
  simulate: (payload: SimulateRequest) =>
    request<{ status: string; predicted_outcomes: Record<string, number> }>(
      '/simulate', { method: 'POST', body: JSON.stringify(payload) }
    ),

  // Golden Signatures
  getGoldenSignatures: () => request<GoldenSignatureMap>('/golden-signatures'),

  // Model metrics
  getModelMetrics: () => request<ModelMetrics>('/model-metrics'),

  // Chat
  chat: (messages: ChatMessage[]): Promise<{ response: string }> =>
    request('/chat', { method: 'POST', body: JSON.stringify({ messages }) }),

  // AI helpers
  analyzePareto: (pareto_solutions: Record<string, number>[], scenario: string) =>
    request<{ analysis: string }>('/ai/analyze-pareto', {
      method: 'POST', body: JSON.stringify({ pareto_solutions, scenario }),
    }),

  explainSignature: (parameters: Record<string, number>, predictions: Record<string, number>, scenario: string) =>
    request<{ explanation: string }>('/ai/explain-signature', {
      method: 'POST', body: JSON.stringify({ parameters, predictions, scenario }),
    }),

  batchInsights: (history: BatchRecord[]) =>
    request<{ insights: string }>('/ai/batch-insights', {
      method: 'POST', body: JSON.stringify({ history }),
    }),

  parseIntent: (query: string, defaults: Record<string, number | string>) =>
    request<Record<string, number | string>>('/ai/parse-intent', {
      method: 'POST', body: JSON.stringify({ query, defaults }),
    }),

  recommendStrategy: (
    strategies: Record<string, Record<string, number>>,
    targets: { target_quality: number; energy_limit: number; carbon_limit: number }
  ) =>
    request<{
      recommended: string;
      ratings: Record<string, { stars: number; reason: string }>;
    }>('/ai/recommend-strategy', {
      method: 'POST', body: JSON.stringify({ strategies, targets }),
    }),

  // Reports
  exportReport: async () => {
    const res = await fetch(`${BASE}/reports/generate`);
    if (!res.ok) throw new Error('Failed to generate report');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    const disposition = res.headers.get('content-disposition');
    let filename = 'OptiMFG_Report.pdf';
    if (disposition && disposition.indexOf('filename=') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      const matches = filenameRegex.exec(disposition);
      if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
