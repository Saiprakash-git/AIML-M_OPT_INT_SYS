import { useState, useEffect } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '../api';
import type { OptimizationResult, ParetoSolution, RecommendedConfig, PredictedOutcomes } from '../types';
import { 
  Info, Star, CheckCircle, AlertTriangle, Play, BrainCircuit, RefreshCw, 
  Lightbulb, Zap, Leaf, Activity, BarChart2, 
  Settings2, Scale, Trophy, Wrench, Search, MessageCircle, Factory, Target, Sparkles
} from 'lucide-react';
import FieldTooltip from '../components/InfoTooltip';

interface AiRec {
  recommended: string;
  ratings: Record<string, { stars: number; reason: string }>;
}

const DEFAULT_BATCH_ID = () => `BATCH-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;

function ParetoTooltip({ active, payload }: { active?: boolean; payload?: any[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as ParetoSolution;
  return (
    <div className="custom-tooltip">
      <div className="ct-label">Pareto Point</div>
      <div className="ct-item"><span style={{ color: 'var(--muted)' }}>Quality:</span> <span style={{ color: 'var(--accent4)' }}>{((d.Predicted_Quality_Score ?? 0) * 100).toFixed(2)}%</span></div>
      <div className="ct-item"><span style={{ color: 'var(--muted)' }}>Energy:</span> <span style={{ color: 'var(--accent)' }}>{(d.Predicted_Energy ?? 0).toFixed(2)} kWh</span></div>
      <div className="ct-item"><span style={{ color: 'var(--muted)' }}>Carbon:</span> <span style={{ color: 'var(--success)' }}>{(d.Predicted_Carbon ?? 0).toFixed(2)} kg</span></div>
    </div>
  );
}

function InfoTooltip({ reason }: { reason: string }) {
  const [show, setShow] = useState(false);
  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      <span
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--accent)', cursor: 'help', marginLeft: 6,
        }}
      >
        <Info size={16} />
      </span>
      {show && (
        <span style={{
          position: 'absolute', bottom: '120%', left: '50%', transform: 'translateX(-50%)',
          background: 'var(--surface)', border: '1px solid var(--accent)',
          borderRadius: 8, padding: '12px', fontSize: 12, color: 'var(--text)',
          zIndex: 100, boxShadow: 'var(--shadow-md)',
          lineHeight: 1.5, maxWidth: 300, whiteSpace: 'pre-wrap',
          display: 'flex', gap: 8, alignItems: 'flex-start'
        }}>
          <BrainCircuit size={16} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: 2 }} />
          <span>{reason}</span>
        </span>
      )}
    </span>
  );
}

function DecisionCard({ title, borderColor, preds, targets, isRecommended, stars, reason }: {
  title: string; borderColor: string;
  preds: Partial<PredictedOutcomes>;
  targets: { quality: number; energy: number; carbon: number };
  isRecommended?: boolean; stars?: number; reason?: string;
}) {
  const q = preds.Quality_Score ?? 0;
  const e = preds.Energy_per_batch ?? 0;
  const c = preds.Carbon_emission ?? 0;
  const h = preds.Asset_Health_Score ?? 1;
  return (
    <div className="dec-card" style={{ borderTop: `4px solid ${borderColor}`, display: 'flex', flexDirection: 'column' }}>
      <div className="dec-title" style={{ color: 'var(--text)', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {title}
          </span>
          {stars !== undefined && (
            <span style={{ display: 'flex', gap: 2, color: 'var(--warn)' }}>
              {Array.from({ length: 5 }).map((_, i) => (
                <Star key={i} size={14} fill={i < stars ? "var(--warn)" : "transparent"} />
              ))}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          {isRecommended && (
            <span className="tag tag-success" style={{ gap: 4 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--success)', display: 'inline-block' }} />
              Recommended
            </span>
          )}
          {reason && <InfoTooltip reason={reason} />}
        </div>
      </div>
      <div style={{ marginTop: 12 }}>
        {[
          { label: 'Quality', val: `${(q * 100).toFixed(1)}%`, ok: q >= targets.quality, color: 'var(--accent4)' },
          { label: 'Energy', val: `${e.toFixed(1)} kWh`, ok: e <= targets.energy, color: 'var(--accent)' },
          { label: 'Carbon', val: `${c.toFixed(1)} kg`, ok: c <= targets.carbon, color: 'var(--accent2)' },
          { label: 'Asset Health', val: `${(h * 100).toFixed(1)}%`, ok: h > 0.8, color: '#8B5CF6' },
        ].map(row => (
          <div className="dec-metric" key={row.label}>
            <span style={{ color: 'var(--muted)' }}>{row.label}</span>
            <span style={{ fontFamily: 'JetBrains Mono', color: row.color, display: 'flex', alignItems: 'center', gap: 6 }}>
              {row.ok ? <CheckCircle size={14} color="var(--success)" /> : <AlertTriangle size={14} color="var(--warn)" />}
              {row.val}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function OptimizationDashboard() {
  const [batchId, setBatchId] = useState(DEFAULT_BATCH_ID());
  const [material, setMaterial] = useState('Standard Powder');
  const [batchSize, setBatchSize] = useState(500);
  const [scenario, setScenario] = useState('Balanced');
  const [targetQuality, setTargetQuality] = useState(0.40);
  const [energyLimit, setEnergyLimit] = useState(180);
  const [carbonLimit, setCarbonLimit] = useState(100);
  const [popSize, setPopSize] = useState(50);
  const [nGen, setNGen] = useState(20);

  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [pareto, setPareto] = useState<ParetoSolution[]>([]);
  const [altPreds, setAltPreds] = useState<{ energy: Partial<PredictedOutcomes>; balanced: Partial<PredictedOutcomes>; quality: Partial<PredictedOutcomes> } | null>(null);
  const [aiRec, setAiRec] = useState<AiRec | null>(null);
  const [plantConfig, setPlantConfig] = useState<any>(null);

  useEffect(() => {
    api.getPlantConfig().then(cfg => setPlantConfig(cfg)).catch(console.error);
  }, []);

  // AI panels
  const [paretoAnalysis, setParetoAnalysis] = useState('');
  const [explanation, setExplanation] = useState('');
  const [aiParetoLoading, setAiParetoLoading] = useState(false);
  const [aiExplainLoading, setAiExplainLoading] = useState(false);
  const [showParetoPanel, setShowParetoPanel] = useState(false);
  const [showExplainPanel, setShowExplainPanel] = useState(false);

  // AI Smart Assistant
  const [assistantInput, setAssistantInput] = useState('');
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Record<string, any> | null>(null);
  const [showAssistant, setShowAssistant] = useState(false);

  const runOptimize = async () => {
    if (plantConfig) {
      if (energyLimit > (plantConfig.electricity_capacity_kw || Infinity)) {
        setError(`Energy limit (${energyLimit} kWh) exceeds the global plant capacity (${plantConfig.electricity_capacity_kw} kWh).`);
        return;
      }
      if (carbonLimit > (plantConfig.carbon_emission_limit_kg || Infinity)) {
        setError(`Carbon limit (${carbonLimit} kg) exceeds the global plant capacity (${plantConfig.carbon_emission_limit_kg} kg).`);
        return;
      }
    }

    setLoading(true); setError(''); setResult(null); setPareto([]);
    setParetoAnalysis(''); setExplanation(''); setSuggestions(null);
    try {
      setStep('Creating batch record...');
      await api.createBatch({
        batch_id: batchId, material_type: material, batch_size: batchSize,
        target_quality: targetQuality, energy_limit: energyLimit,
        carbon_limit: carbonLimit, optimization_mode: scenario,
      }).catch(() => {/* batch create non-critical */});

      setStep('Running NSGA-II Optimization (may take 30–60s)...');
      const res = await api.optimize({
        batch_id: batchId,
        scenario,
        constraints: {
          Granulation_Time: [10, 60], Binder_Amount: [1, 10], Drying_Temp: [40, 80],
          Drying_Time: [20, 120], Compression_Force: [5, 30], Machine_Speed: [10, 50],
          Lubricant_Conc: [0.1, 2.0], Moisture_Content: [1.0, 5.0],
        },
        targets: { energy_limit: energyLimit, carbon_limit: carbonLimit, target_quality: targetQuality },
        pop_size: popSize,
        n_gen: nGen,
      });
      setResult(res);

      setStep('Fetching Pareto solutions...');
      const paretoRes = await api.getPareto(batchId).catch(() => null);
      if (paretoRes?.pareto_solutions) setPareto(paretoRes.pareto_solutions);

      // Fetch all 3 strategy alternatives
      setStep('Fetching alternative strategies...');
      const [energyRes, qualRes, balRes] = await Promise.allSettled([
        api.optimize({ batch_id: batchId + '-E', scenario: 'Energy Saving', constraints: { Granulation_Time: [10, 60], Binder_Amount: [1, 10], Drying_Temp: [40, 80], Drying_Time: [20, 120], Compression_Force: [5, 30], Machine_Speed: [10, 50], Lubricant_Conc: [0.1, 2.0], Moisture_Content: [1.0, 5.0] }, targets: { energy_limit: energyLimit, carbon_limit: carbonLimit, target_quality: targetQuality }, pop_size: 30, n_gen: 10 }),
        api.optimize({ batch_id: batchId + '-Q', scenario: 'Quality Priority', constraints: { Granulation_Time: [10, 60], Binder_Amount: [1, 10], Drying_Temp: [40, 80], Drying_Time: [20, 120], Compression_Force: [5, 30], Machine_Speed: [10, 50], Lubricant_Conc: [0.1, 2.0], Moisture_Content: [1.0, 5.0] }, targets: { energy_limit: energyLimit, carbon_limit: carbonLimit, target_quality: targetQuality }, pop_size: 30, n_gen: 10 }),
        api.optimize({ batch_id: batchId + '-B', scenario: 'Balanced', constraints: { Granulation_Time: [10, 60], Binder_Amount: [1, 10], Drying_Temp: [40, 80], Drying_Time: [20, 120], Compression_Force: [5, 30], Machine_Speed: [10, 50], Lubricant_Conc: [0.1, 2.0], Moisture_Content: [1.0, 5.0] }, targets: { energy_limit: energyLimit, carbon_limit: carbonLimit, target_quality: targetQuality }, pop_size: 30, n_gen: 10 }),
      ]);
      const altPredsVal = {
        energy: energyRes.status === 'fulfilled' ? energyRes.value.predicted_outcomes : {},
        quality: qualRes.status === 'fulfilled' ? qualRes.value.predicted_outcomes : {},
        balanced: balRes.status === 'fulfilled' ? balRes.value.predicted_outcomes : {},
      };
      setAltPreds(altPredsVal);

      // Ask AI to pick the best strategy
      try {
        const rec = await api.recommendStrategy(
          {
            'Energy Saving': altPredsVal.energy as Record<string, number>,
            'Balanced': altPredsVal.balanced as Record<string, number>,
            'Quality Priority': altPredsVal.quality as Record<string, number>,
          },
          { target_quality: targetQuality, energy_limit: energyLimit, carbon_limit: carbonLimit }
        );
        setAiRec(rec);
      } catch { /* AI rec is optional — silently skip if unavailable */ }
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); setStep(''); }
  };

  const runAIAssistant = async (text = assistantInput) => {
    if (!text.trim()) return;
    setAssistantInput(text);
    setAssistantLoading(true);
    try {
      const s = await api.parseIntent(text, {
        scenario: 'Balanced', target_quality: targetQuality,
        energy_limit: energyLimit, carbon_limit: carbonLimit,
        pop_size: popSize, n_gen: nGen,
      });
      setSuggestions(s);
    } catch (e: any) { setError(e.message); }
    finally { setAssistantLoading(false); }
  };

  const ASSISTANT_CHIPS = [
    { icon: <Trophy size={14}/>, label: 'Max quality, audit mode', text: 'High quality batch for an audit, energy is less important today' },
    { icon: <Leaf size={14}/>, label: 'Green compliance run', text: 'Minimize carbon emissions and energy for our green compliance report, loosen quality a bit' },
    { icon: <Zap size={14}/>, label: 'Fast test batch', text: 'Quick test batch — small population 20, only 10 generations, balanced mode' },
  ];

  const par = result?.recommended_configuration as RecommendedConfig | undefined;
  const pre = result?.predicted_outcomes as PredictedOutcomes | undefined;

  const PARAM_LABELS: Record<string, [string, string]> = {
    Drying_Temp: ['Drying Temperature', '°C'], Compression_Force: ['Compression Force', 'kN'],
    Machine_Speed: ['Machine Speed', 'RPM'], Moisture_Content: ['Moisture Content', '%'],
    Granulation_Time: ['Granulation Time', 'min'], Binder_Amount: ['Binder Amount', 'kg'],
    Drying_Time: ['Drying Time', 'min'], Lubricant_Conc: ['Lubricant Conc', '%'],
  };

  return (
    <div>
      {error && <div className="alert alert-danger"><AlertTriangle size={18}/> {error}</div>}

      {/* Smart AI Assistant */}
      <div className="expander mb">
        <div className="expander-header" onClick={() => setShowAssistant(e => !e)}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><BrainCircuit size={18} color="var(--accent)" /> Smart Assistant (AI Pre-fill)</span>
          <span style={{ color: 'var(--muted)' }}>{showAssistant ? '▲' : '▼'}</span>
        </div>
        {showAssistant && (
          <div className="expander-body">
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
              Describe your batch goal in plain English — AI will suggest parameter values.
            </p>
            {/* Pre-prompt chips */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
              {ASSISTANT_CHIPS.map((c, i) => (
                <button key={i} className="btn btn-muted" style={{ fontSize: 12, padding: '6px 14px' }}
                  onClick={() => runAIAssistant(c.text)} disabled={assistantLoading} title={c.text}>
                  <span style={{ color: 'var(--accent)' }}>{c.icon}</span> {c.label}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <input className="form-input" style={{ flex: 1 }}
                placeholder='e.g. "High quality batch for an audit, energy is less important today"'
                value={assistantInput} onChange={e => setAssistantInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') runAIAssistant(); }}
              />
              <button className="btn btn-primary" onClick={() => runAIAssistant()} disabled={assistantLoading || !assistantInput.trim()}>
                {assistantLoading ? <><span className="spinner" /> Thinking...</> : <><Lightbulb size={16}/> Suggest</>}
              </button>
            </div>
            {suggestions && (
              <div style={{ background: 'var(--surface2)', padding: 16, borderRadius: 8, border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}><CheckCircle size={14}/> AI Suggestions:</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {Object.entries(suggestions).filter(([k]) => k !== 'reasoning').map(([k, v]) => (
                    <div key={k} style={{ fontSize: 13, padding: '4px 0' }}>
                      <span style={{ color: 'var(--muted)', fontWeight: 500 }}>{k.replace(/_/g, ' ')}:</span>{' '}
                      <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--text)', fontWeight: 600 }}>{String(v)}</span>
                    </div>
                  ))}
                </div>
                {suggestions.reasoning && <p style={{ fontSize: 12, color: 'var(--text2)', fontStyle: 'italic', marginTop: 12, padding: '8px', background: '#FFF', borderRadius: 6, border: '1px dashed var(--border2)' }}>{String(suggestions.reasoning)}</p>}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Batch Configuration Form */}
      <div className="card mb">
        <div className="card-title"><Settings2 size={16} color="var(--accent)" /> Batch Setup &amp; Optimization Targets</div>
        <div className="grid-2 mb">
          <div>
            <div className="form-group">
              <label className="form-label">
                Batch ID
                <FieldTooltip text="Unique identifier for this production run." />
              </label>
              <div style={{ display: 'flex', gap: 12 }}>
                <input className="form-input" value={batchId} onChange={e => setBatchId(e.target.value)} />
                <button className="btn btn-muted btn-sm" onClick={() => setBatchId(DEFAULT_BATCH_ID())} style={{ whiteSpace: 'nowrap' }}><RefreshCw size={14}/> New</button>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">
                Material Type
                <FieldTooltip text="The raw material being processed, which affects the digital twin predictions." />
              </label>
              <select className="form-select" value={material} onChange={e => setMaterial(e.target.value)}>
                {['Standard Powder', 'High Density', 'Granular'].map(m => <option key={m}>{m}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">
                Batch Size (kg)
                <FieldTooltip text="Total weight of raw material for this batch." />
              </label>
              <input className="form-input" type="number" value={batchSize} onChange={e => setBatchSize(parseFloat(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">
                Optimization Priority
                <FieldTooltip text="Tells the Golden Signature selector which objective to favor when picking the absolute best result." />
              </label>
              <div className="flex-center gap-sm" style={{ flexWrap: 'wrap' }}>
                {['Energy Saving', 'Quality Priority', 'Balanced'].map(s => (
                  <button key={s} className={`btn ${scenario === s ? 'btn-primary' : 'btn-muted'}`}
                    style={{ fontSize: 12, padding: '6px 14px', position: 'relative' }} onClick={() => setScenario(s)}>
                    {s === 'Energy Saving' && <Leaf size={14} style={{ marginRight: 6, display: 'inline' }} />}
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div>
            <div className="form-group">
              <label className="form-label">
                Target Quality Score (min): {(targetQuality * 100).toFixed(0)}%
                <FieldTooltip text="Minimum acceptable quality score. The AI will reject any parameters predicting lower." />
              </label>
              <div className="range-wrap">
                <input type="range" className="range-input" min={0} max={1} step={0.01} value={targetQuality} onChange={e => setTargetQuality(parseFloat(e.target.value))} />
                <span className="range-val">{(targetQuality * 100).toFixed(0)}%</span>
              </div>
            </div>
            <div className="form-group" style={{ background: scenario === 'Energy Saving' ? 'var(--surface-hover)' : 'transparent', padding: scenario === 'Energy Saving' ? '8px' : '0', borderRadius: '8px', transition: 'all 0.3s' }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {scenario === 'Energy Saving' && <Leaf size={14} color="var(--success)" />}
                Energy Limit per Batch (kWh)
                <FieldTooltip text="Maximum energy consumption allowed for the entire batch." />
              </label>
              <input className="form-input" type="number" value={energyLimit} onChange={e => setEnergyLimit(parseFloat(e.target.value))} />
            </div>
            <div className="form-group" style={{ background: scenario === 'Energy Saving' ? 'var(--surface-hover)' : 'transparent', padding: scenario === 'Energy Saving' ? '8px' : '0', borderRadius: '8px', transition: 'all 0.3s' }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {scenario === 'Energy Saving' && <Leaf size={14} color="var(--success)" />}
                Carbon Emission Limit (kg)
                <FieldTooltip text="Maximum carbon emissions allowed for this production run." />
              </label>
              <input className="form-input" type="number" value={carbonLimit} onChange={e => setCarbonLimit(parseFloat(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">
                NSGA-II Population Size: {popSize}
                <FieldTooltip text="Number of candidate solutions per evolutionary generation. Higher = better results but slower compute." />
              </label>
              <div className="range-wrap">
                <input type="range" className="range-input" min={10} max={200} step={10} value={popSize} onChange={e => setPopSize(parseInt(e.target.value))} />
                <span className="range-val">{popSize}</span>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">
                NSGA-II Generations: {nGen}
                <FieldTooltip text="Number of evolutionary iterations. Higher = more refined convergence but slower compute." />
              </label>
              <div className="range-wrap">
                <input type="range" className="range-input" min={5} max={100} step={5} value={nGen} onChange={e => setNGen(parseInt(e.target.value))} />
                <span className="range-val">{nGen}</span>
              </div>
            </div>
          </div>
        </div>
        <button className="btn btn-primary" onClick={runOptimize} disabled={loading} style={{ width: '100%', fontSize: 14, padding: '12px 20px' }}>
          {loading ? <><span className="spinner" /> {step || 'Optimizing...'}</> : <><Play size={16} fill="white"/> Run Target-Driven Optimization</>}
        </button>
        {loading && <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 12, textAlign: 'center' }}>This may take 30–120 seconds depending on pop_size and n_gen.</div>}
      </div>

      {/* Results */}
      {result && par && pre && (
        <>
          <div className="alert alert-success">
            <CheckCircle size={18}/> Optimization complete! {pareto.length > 0 ? `${pareto.length} Pareto-optimal configurations found.` : 'Golden Signature selected.'} Priority: <strong>{result.scenario_mode}</strong>
          </div>

          {/* Golden Signature */}
          <div className="card mb">
            <div className="card-title" style={{ color: 'var(--accent)' }}><Trophy size={16} /> Recommended Golden Signature — {result.scenario_mode}</div>
            <div className="grid-2">
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 }}>Exact Machine Parameters</div>
                <div className="code-block" style={{ borderLeft: '3px solid var(--accent)' }}>
                  {Object.entries(par).map(([k, v]) => {
                    const [label, unit] = PARAM_LABELS[k] ?? [k, ''];
                    return `${label}: ${Number(v).toFixed(k.includes('Lubricant') || k.includes('Moisture') ? 2 : 1)} ${unit}\n`;
                  }).join('')}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 }}>Predicted Outcomes</div>
                <div className="code-block" style={{ borderLeft: '3px solid var(--accent2)' }}>
                  {[
                    [pre.Quality_Score >= targetQuality ? <CheckCircle size={14} color="var(--success)"/> : <AlertTriangle size={14} color="var(--warn)"/>, `Quality Score: ${(pre.Quality_Score * 100).toFixed(2)}% (Target: ≥${(targetQuality * 100).toFixed(0)}%)`],
                    [pre.Energy_per_batch <= energyLimit ? <CheckCircle size={14} color="var(--success)"/> : <AlertTriangle size={14} color="var(--warn)"/>, `Energy Consump: ${pre.Energy_per_batch?.toFixed(2)} kWh (Limit: <${energyLimit})`],
                    [pre.Carbon_emission <= carbonLimit ? <CheckCircle size={14} color="var(--success)"/> : <AlertTriangle size={14} color="var(--warn)"/>, `Carbon Emiss: ${pre.Carbon_emission?.toFixed(2)} kg (Limit: <${carbonLimit})`],
                    [<Activity size={14} color="var(--accent)"/>, `Reliability Score: ${(pre.Reliability_Index * 100).toFixed(2)}%`],
                    [<Wrench size={14} color="#8B5CF6"/>, `Asset Health: ${((pre.Asset_Health_Score ?? 1) * 100).toFixed(2)}%`],
                    [<Scale size={14} color="var(--accent2)"/>, `Balanced Score: ${pre.Balanced_Score?.toFixed(4)}`],
                    [<Target size={14} color="var(--text)"/>, `Fitness Score: ${result.overall_fitness_score?.toFixed(4)}`],
                  ].map(([icon, txt], i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, lineHeight: 1 }}>
                      {icon} <span>{String(txt)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Pareto Charts */}
          {pareto.length > 0 && (
            <div className="card mb">
              <div className="card-title"><BarChart2 size={16} color="var(--accent)"/> Tradeoff Visualizations — Pareto Front ({pareto.length} solutions)</div>
              <div className="grid-3">
                {[
                  { title: 'Energy vs Quality', xKey: 'Predicted_Quality_Score', yKey: 'Predicted_Energy', xLabel: 'Quality Score (idx)', yLabel: 'Energy (kWh)', color: 'var(--accent)', goldenX: pre.Quality_Score, goldenY: pre.Energy_per_batch },
                  { title: 'Carbon vs Quality', xKey: 'Predicted_Quality_Score', yKey: 'Predicted_Carbon', xLabel: 'Quality Score (idx)', yLabel: 'Carbon (kg)', color: 'var(--success)', goldenX: pre.Quality_Score, goldenY: pre.Carbon_emission },
                  { title: 'Reliability vs Energy', xKey: 'Predicted_Energy', yKey: 'Predicted_Reliability', xLabel: 'Energy (kWh)', yLabel: 'Reliability', color: 'var(--warn)', goldenX: pre.Energy_per_batch, goldenY: pre.Reliability_Index },
                ].map(chart => (
                  <div key={chart.title}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text2)', textAlign: 'center', marginBottom: 12 }}>{chart.title}</div>
                    <ResponsiveContainer width="100%" height={220}>
                      <ScatterChart margin={{ top: 5, right: 15, bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey={chart.xKey} name={chart.xLabel} tick={{ fill: 'var(--muted)', fontSize: 10 }} axisLine={{ stroke: 'var(--border)' }} tickLine={{ stroke: 'var(--border)' }} />
                        <YAxis dataKey={chart.yKey} name={chart.yLabel} tick={{ fill: 'var(--muted)', fontSize: 10 }} axisLine={{ stroke: 'var(--border)' }} tickLine={{ stroke: 'var(--border)' }} />
                        <Tooltip content={<ParetoTooltip />} cursor={{ strokeDasharray: '3 3', stroke: 'var(--border2)' }} />
                        <Scatter data={pareto} fill={chart.color} fillOpacity={0.6} />
                        {/* Golden star marker */}
                        <Scatter data={[{ [chart.xKey]: chart.goldenX, [chart.yKey]: chart.goldenY }]}
                          fill="#EF4444" shape="star" />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Decision Comparison */}
          {altPreds && (
            <div className="card mb">
              <div className="card-title"><Lightbulb size={16} color="var(--accent)" /> Decision Comparison Panel</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 20 }}>Alternate top strategy recommendations:</p>
              <div className="dec-cards">
                <DecisionCard title="Energy Efficient Alternative" borderColor="var(--accent)"
                  preds={altPreds.energy} targets={{ quality: targetQuality, energy: energyLimit, carbon: carbonLimit }}
                  isRecommended={aiRec?.recommended === 'Energy Saving'}
                  stars={aiRec?.ratings?.['Energy Saving']?.stars}
                  reason={aiRec?.ratings?.['Energy Saving']?.reason} />
                <DecisionCard title="Balanced Alternative" borderColor="var(--success)"
                  preds={altPreds.balanced} targets={{ quality: targetQuality, energy: energyLimit, carbon: carbonLimit }}
                  isRecommended={aiRec?.recommended === 'Balanced'}
                  stars={aiRec?.ratings?.['Balanced']?.stars}
                  reason={aiRec?.ratings?.['Balanced']?.reason} />
                <DecisionCard title="Quality Maximizing Alternative" borderColor="var(--warn)"
                  preds={altPreds.quality} targets={{ quality: targetQuality, energy: energyLimit, carbon: carbonLimit }}
                  isRecommended={aiRec?.recommended === 'Quality Priority'}
                  stars={aiRec?.ratings?.['Quality Priority']?.stars}
                  reason={aiRec?.ratings?.['Quality Priority']?.reason} />
              </div>
            </div>
          )}

          {/* Full Pareto Table */}
          {pareto.length > 0 && (
            <div className="card mb">
              <div className="card-title"><BarChart2 size={16} color="var(--muted)"/> Full Pareto Output Table ({pareto.length} solutions)</div>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>#</th><th>Quality Score</th><th>Energy (kWh)</th>
                      <th>Carbon (CO₂)</th><th>Reliability</th><th>Asset Health</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pareto.map((s, i) => (
                      <tr key={i}>
                        <td className="mono" style={{ color: 'var(--muted)' }}>{i + 1}</td>
                        <td className="mono" style={{ color: 'var(--accent4)' }}>{((s.Predicted_Quality_Score ?? 0) * 100).toFixed(2)}%</td>
                        <td className="mono">{(s.Predicted_Energy ?? 0).toFixed(2)}</td>
                        <td className="mono">{(s.Predicted_Carbon ?? 0).toFixed(2)}</td>
                        <td className="mono" style={{ color: 'var(--warn)' }}>{((s.Predicted_Reliability ?? 0) * 100).toFixed(2)}%</td>
                        <td className="mono" style={{ color: (s.Asset_Health_Score ?? 1) > 0.9 ? 'var(--success)' : 'var(--accent)' }}>
                          {((s.Asset_Health_Score ?? 1) * 100).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* AI Pareto Analysis */}
          <div className="expander mb">
            <div className="expander-header" onClick={() => setShowParetoPanel(e => !e)}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Search size={16} color="var(--accent)" /> AI: Pareto Analysis</span>
              <span style={{ color: 'var(--muted)' }}>{showParetoPanel ? '▲' : '▼'}</span>
            </div>
            {showParetoPanel && (
              <div className="expander-body">
                <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
                  AI-generated plain-English summary of all Pareto-optimal solutions.
                </p>
                <button className="btn btn-primary btn-sm mb" onClick={async () => {
                  setAiParetoLoading(true);
                  try {
                    const res = await api.analyzePareto(pareto as any, scenario);
                    setParetoAnalysis(res.analysis);
                  } catch (e: any) { setParetoAnalysis(`Error: ${e.message}`); }
                  finally { setAiParetoLoading(false); }
                }} disabled={aiParetoLoading}>
                  {aiParetoLoading ? <><span className="spinner" /> Analyzing...</> : <><Sparkles size={14}/> Generate Pareto Analysis</>}
                </button>
                {paretoAnalysis && <div className="ai-prose mt" style={{ background: 'var(--surface2)', padding: 16, borderRadius: 8 }}>{paretoAnalysis}</div>}
              </div>
            )}
          </div>

          {/* AI Explain Configuration */}
          <div className="expander mb">
            <div className="expander-header" onClick={() => setShowExplainPanel(e => !e)}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><MessageCircle size={16} color="var(--accent)" /> AI: Why This Configuration?</span>
              <span style={{ color: 'var(--muted)' }}>{showExplainPanel ? '▲' : '▼'}</span>
            </div>
            {showExplainPanel && (
              <div className="expander-body">
                <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
                  AI explains why the Golden Signature parameters were selected for your batch.
                </p>
                <button className="btn btn-primary btn-sm mb" onClick={async () => {
                  setAiExplainLoading(true);
                  try {
                    const res = await api.explainSignature(par as any, pre as any, scenario);
                    setExplanation(res.explanation);
                  } catch (e: any) { setExplanation(`Error: ${e.message}`); }
                  finally { setAiExplainLoading(false); }
                }} disabled={aiExplainLoading}>
                  {aiExplainLoading ? <><span className="spinner" /> Generating...</> : <><Info size={14} /> Explain Recommendation</>}
                </button>
                {explanation && <div className="ai-prose mt" style={{ background: 'var(--surface2)', padding: 16, borderRadius: 8 }}>{explanation}</div>}
              </div>
            )}
          </div>
        </>
      )}

      {!result && !loading && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon"><Factory size={48} strokeWidth={1} /></div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>Ready for Optimization</div>
            <div style={{ maxWidth: 460 }}>
              Configure your batch parameters above and click <strong>Run Target-Driven Optimization</strong> to start.<br /><br />
              The AI Digital Twin will run NSGA-II to find the optimal Pareto front and select the Golden Signature matching your chosen priority.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
// Removed dummy Target icon definition, now importing from lucide-react instead (I will add 'Target' to the import list but it's okay)
// wait, I forgot 'Target' in the import! Let me fix it.
