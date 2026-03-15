import { useState } from 'react';
import { api } from '../api';
import { 
  Flame, Thermometer, Droplets, Lightbulb, Zap, CheckCircle, 
  AlertTriangle, Brain, Settings2, Sparkles, Activity
} from 'lucide-react';
import FieldTooltip from '../components/InfoTooltip';
import HelpDialog from '../components/HelpDialog';

interface Params {
  Granulation_Time: number;
  Binder_Amount: number;
  Drying_Temp: number;
  Drying_Time: number;
  Compression_Force: number;
  Machine_Speed: number;
  Lubricant_Conc: number;
  Moisture_Content: number;
}

const DEFAULTS: Params = {
  Granulation_Time: 30, Binder_Amount: 5, Drying_Temp: 60, Drying_Time: 60,
  Compression_Force: 15, Machine_Speed: 30, Lubricant_Conc: 1.0, Moisture_Content: 2.5,
};

const RANGES: Record<keyof Params, [number, number, number, string]> = {
  Granulation_Time: [10, 60, 0.5, 'min'],
  Binder_Amount: [1, 10, 0.1, 'kg'],
  Drying_Temp: [40, 80, 0.5, '°C'],
  Drying_Time: [20, 120, 1, 'min'],
  Compression_Force: [5, 30, 0.1, 'kN'],
  Machine_Speed: [10, 50, 0.5, 'RPM'],
  Lubricant_Conc: [0.1, 2.0, 0.05, '%'],
  Moisture_Content: [1.0, 5.0, 0.1, '%'],
};

const LABELS: Record<keyof Params, string> = {
  Granulation_Time: 'Granulation Time', Binder_Amount: 'Binder Amount',
  Drying_Temp: 'Drying Temp', Drying_Time: 'Drying Time',
  Compression_Force: 'Compression Force', Machine_Speed: 'Machine Speed',
  Lubricant_Conc: 'Lubricant Conc', Moisture_Content: 'Moisture Content',
};

const TOOLTIPS: Record<keyof Params, string> = {
  Granulation_Time: 'Time spent in the high-shear granulator.',
  Binder_Amount: 'Amount of binding agent used to hold particles together.',
  Drying_Temp: 'Temperature set for the fluid bed dryer.',
  Drying_Time: 'Duration of the drying process to reach target moisture.',
  Compression_Force: 'Force applied during tableting.',
  Machine_Speed: 'Rotational speed of the tablet press.',
  Lubricant_Conc: 'Percentage of lubricant to prevent sticking.',
  Moisture_Content: 'Target residual moisture remaining in granules.',
};

export default function WhatIfSimulationView() {
  const [params, setParams] = useState<Params>(DEFAULTS);
  const [results, setResults] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [aiQuery, setAiQuery] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<Record<string, number | string> | null>(null);
  const [expanded, setExpanded] = useState(false);

  const simulate = async () => {
    setLoading(true); setError('');
    try {
      const res = await api.simulate({ parameters: params });
      setResults(res.predicted_outcomes);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const askAI = async (text = aiQuery) => {
    if (!text.trim()) return;
    setAiQuery(text);
    setAiLoading(true);
    try {
      const suggestions = await api.parseIntent(text, { ...DEFAULTS });
      setAiSuggestions(suggestions);
    } catch (e: any) { setError(e.message); }
    finally { setAiLoading(false); }
  };

  const WHATIF_CHIPS = [
    { icon: <Flame size={14} />, label: 'High compression + low moisture', text: 'What if I increase compression force to 25 kN and reduce moisture to 1.5%?' },
    { icon: <Thermometer size={14} />, label: 'Max drying temp slow speed', text: 'Set drying temperature to 78°C and reduce machine speed to 15 RPM' },
    { icon: <Droplets size={14} />, label: 'High binder long granulation', text: 'What happens if I use maximum binder amount of 9 kg with 50 min granulation time?' },
  ];

  const healthScore = results?.Asset_Health_Score ?? results?.Reliability_Index ?? 0;
  const healthColor = healthScore > 0.9 ? 'var(--success)' : healthScore > 0.7 ? 'var(--warn)' : 'var(--danger)';
  const healthIcon = healthScore > 0.9 ? <CheckCircle size={24} color="var(--success)" /> : healthScore > 0.7 ? <AlertTriangle size={24} color="var(--warn)" /> : <AlertTriangle size={24} color="var(--danger)" />;

  return (
    <div style={{ position: 'relative' }}>
      <HelpDialog title="What-If Simulation Guide">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <p><strong>What is this page?</strong></p>
          <p>This is a manual testing ground for the AI Digital Twin. Instead of the AI finding the best parameters for you, you provide the parameters, and the AI predicts the exact outcome.</p>
          <p><strong>How to use it:</strong></p>
          <ul style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <li><strong>Manual Sliders:</strong> Adjust the 8 machine parameters using the sliders below.</li>
            <li><strong>AI Suggestions:</strong> Not sure what to test? Ask the AI Assistant at the top (e.g., "What happens if I increase the drying temperature?"). It will give you recommended slider values to try.</li>
            <li><strong>Simulate:</strong> Click "Run Digital Twin Simulation". The system will use its XGBoost models to predict the Quality, Energy, Carbon, and Machine Health for those specific settings without touching the real equipment.</li>
          </ul>
        </div>
      </HelpDialog>

      {/* AI Assistant expander */}
      <div className="expander mb">
        <div className="expander-header" onClick={() => setExpanded(e => !e)}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Brain size={18} color="var(--accent)" /> Describe Parameter Changes (AI Assistant)</span>
          <span style={{ color: 'var(--muted)' }}>{expanded ? '▲' : '▼'}</span>
        </div>
        {expanded && (
          <div className="expander-body">
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
              Describe what you want to change in plain English — AI will suggest exact slider values.
            </p>
            {/* Pre-prompt chips */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
              {WHATIF_CHIPS.map((c, i) => (
                <button key={i} className="btn btn-muted" style={{ fontSize: 12, padding: '6px 14px' }}
                  onClick={() => askAI(c.text)} disabled={aiLoading} title={c.text}>
                  <span style={{ color: 'var(--accent)' }}>{c.icon}</span> {c.label}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <input
                className="form-input"
                style={{ flex: 1 }}
                placeholder='e.g. "What if I increase compression force to 22 kN and dry at 70°C?"'
                value={aiQuery}
                onChange={e => setAiQuery(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') askAI(); }}
              />
              <button className="btn btn-primary" onClick={() => askAI()} disabled={aiLoading || !aiQuery.trim()}>
                {aiLoading ? <><span className="spinner" /> Thinking...</> : <><Lightbulb size={16} /> Suggest</>}
              </button>
            </div>
            {aiSuggestions && (
              <div style={{ background: 'var(--surface2)', padding: 16, borderRadius: 8, border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 12, color: 'var(--accent)', marginBottom: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Sparkles size={14} /> AI Suggested Values — click Apply to update sliders:
                </div>
                <div className="params-grid" style={{ marginBottom: 16 }}>
                  {Object.entries(aiSuggestions)
                    .filter(([k]) => k !== 'reasoning' && k in DEFAULTS)
                    .map(([k, v]) => (
                      <div className="param-item" key={k} style={{ borderColor: 'var(--accent2)' }}>
                        <div className="param-name">{LABELS[k as keyof Params]}</div>
                        <div className="param-val" style={{ color: 'var(--text)' }}>{String(v)}</div>
                      </div>
                    ))}
                </div>
                {aiSuggestions.reasoning && (
                  <p style={{ fontSize: 12, color: 'var(--text2)', fontStyle: 'italic', marginBottom: 16, padding: '8px 12px', background: '#FFF', borderRadius: 6, border: '1px dashed var(--border2)' }}>
                    {String(aiSuggestions.reasoning)}
                  </p>
                )}
                <button className="btn btn-success" style={{ fontSize: 12, padding: '8px 16px' }} onClick={() => {
                  const updates: Partial<Params> = {};
                  for (const [k, v] of Object.entries(aiSuggestions)) {
                    if (k in DEFAULTS) updates[k as keyof Params] = Number(v);
                  }
                  setParams(p => ({ ...p, ...updates }));
                  setAiSuggestions(null);
                }}>
                  <CheckCircle size={14} /> Apply to Sliders
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sliders */}
      <div className="card mb">
        <div className="card-title"><Settings2 size={16} color="var(--accent)" /> Machine Parameter Sliders</div>
        <div className="grid-2">
          {(Object.keys(DEFAULTS) as (keyof Params)[]).map(key => {
            const [min, max, step, unit] = RANGES[key];
            return (
              <div className="form-group" key={key} style={{ marginBottom: 24 }}>
                <label className="form-label">
                  {LABELS[key]} ({unit})
                  <FieldTooltip text={TOOLTIPS[key]} />
                </label>
                <div className="range-wrap">
                  <input
                    type="range" className="range-input"
                    min={min} max={max} step={step}
                    value={params[key]}
                    onChange={e => setParams(p => ({ ...p, [key]: parseFloat(e.target.value) }))}
                  />
                  <span className="range-val">{params[key].toFixed(step < 1 ? 2 : 1)}</span>
                </div>
              </div>
            );
          })}
        </div>
        {error && <div className="alert alert-danger mt"><AlertTriangle size={18} /> {error}</div>}
        <button className="btn btn-primary mt" onClick={simulate} disabled={loading} style={{ width: '100%', padding: '14px', fontSize: 14 }}>
          {loading ? <><span className="spinner" /> Simulating Digital Twin...</> : <><Zap size={16} fill="white" /> Run Digital Twin Simulation</>}
        </button>
      </div>

      {/* Results */}
      {results && (
        <div className="card" style={{ animation: 'pulse 0.5s ease' }}>
          <div className="card-title"><Activity size={16} color="var(--success)" /> Predicted Outcomes</div>
          <div className="kpi-grid" style={{ marginBottom: 24 }}>
            <div className="kpi-card quality">
              <div className="kpi-label">Quality Score</div>
              <div className="kpi-value quality" style={{ color: 'var(--accent4)' }}>{((results.Quality_Score ?? 0) * 100).toFixed(2)}%</div>
            </div>
            <div className="kpi-card energy">
              <div className="kpi-label">Energy / Batch</div>
              <div className="kpi-value energy" style={{ color: 'var(--accent)' }}>{(results.Energy_per_batch ?? 0).toFixed(2)}<span className="kpi-unit">kWh</span></div>
            </div>
            <div className="kpi-card carbon">
              <div className="kpi-label">Carbon Emission</div>
              <div className="kpi-value carbon" style={{ color: 'var(--success)' }}>{(results.Carbon_emission ?? 0).toFixed(2)}<span className="kpi-unit">kg</span></div>
            </div>
            <div className="kpi-card health">
              <div className="kpi-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>{healthIcon} Asset Health</div>
              <div className="kpi-value health" style={{ color: healthColor }}>{(healthScore * 100).toFixed(2)}%</div>
            </div>
          </div>
          {results.Reliability_Index !== undefined && (
            <div style={{ fontSize: 13, color: 'var(--muted)', borderTop: '1px solid var(--border)', paddingTop: 16, display: 'flex', gap: 32 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                Reliability Index: <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--warn)', fontWeight: 600 }}>{(results.Reliability_Index * 100).toFixed(2)}%</span>
              </span>
              {results.Balanced_Score !== undefined && (
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  Balanced Score: <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--accent2)', fontWeight: 600 }}>{results.Balanced_Score.toFixed(4)}</span>
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
