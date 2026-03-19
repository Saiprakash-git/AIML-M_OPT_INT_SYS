import { useState, useEffect } from 'react';
import { api } from '../api';
import type { GoldenSignatureMap, GoldenSignature } from '../types';
import { Sparkles, RefreshCw, Info, Trophy, Activity, LayoutGrid, Award, Settings2 } from 'lucide-react';
import FieldTooltip from '../components/InfoTooltip';
import HelpDialog from '../components/HelpDialog';

const SCENARIO_COLORS: Record<string, string> = {
  'Energy Saving': 'var(--accent)',
  'Quality Priority': 'var(--warn)',
  'Balanced': 'var(--success)',
};

const SCENARIO_BG: Record<string, string> = {
  'Energy Saving': '#EFF6FF',
  'Quality Priority': '#FFFBEB',
  'Balanced': '#ECFDF5',
};

function ParamGrid({ params }: { params: Record<string, number> }) {
  const labels: Record<string, string> = {
    Granulation_Time: 'Gran Time', Binder_Amount: 'Binder Amt',
    Drying_Temp: 'Dry Temp', Drying_Time: 'Dry Time',
    Compression_Force: 'Comp Force', Machine_Speed: 'Mach Speed',
    Lubricant_Conc: 'Lubricant', Moisture_Content: 'Moisture',
  };
  const units: Record<string, string> = {
    Granulation_Time: 'min', Binder_Amount: 'kg', Drying_Temp: '°C',
    Drying_Time: 'min', Compression_Force: 'kN', Machine_Speed: 'RPM',
    Lubricant_Conc: '%', Moisture_Content: '%',
  };
  return (
    <div className="params-grid">
      {Object.entries(params).map(([k, v]) => (
        <div className="param-item" key={k}>
          <div className="param-name">{labels[k] ?? k}</div>
          <div className="param-val">{Number(v).toFixed(2)}<span style={{ fontSize: 11, color: 'var(--muted)', marginLeft: 4 }}>{units[k]}</span></div>
        </div>
      ))}
    </div>
  );
}

function SigCard({ name, data }: { name: string; data: GoldenSignature }) {
  const color = SCENARIO_COLORS[name] ?? 'var(--accent)';
  const bg = SCENARIO_BG[name] ?? 'var(--surface2)';
  const preds = data.predictions ?? {};
  return (
    <div className="sig-card" style={{ borderColor: `${color}44`, background: 'var(--surface)', padding: 0, overflow: 'hidden' }}>
      <div className="sig-header" style={{ padding: '20px 24px', background: bg, borderBottom: `1px solid ${color}33`, margin: 0 }}>
        <div className="flex-center gap-sm">
          <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'Inter', fontSize: 16, fontWeight: 700, color }}>
            {name === 'Energy Saving' ? <Activity size={18} /> : name === 'Quality Priority' ? <Award size={18} /> : <Trophy size={18} />}
            {name}
          </span>
          {data.batch_context && (
            <span className="tag tag-info" style={{ fontSize: 11, background: 'rgba(255,255,255,0.8)' }}>Batch: {data.batch_context}</span>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text2)', fontWeight: 600 }}>
          Fitness Score: <span style={{ color, fontFamily: 'JetBrains Mono', fontSize: 14 }}>
            {Number(data.overall_score ?? 0).toFixed(4)}
          </span>
        </div>
      </div>

      <div className="grid-2" style={{ padding: 24, gap: 32 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Settings2 size={14} /> Machine Parameters
          </div>
          {data.parameters && <ParamGrid params={data.parameters as unknown as Record<string, number>} />}
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <LayoutGrid size={14} /> Predicted Outcomes
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { label: 'Quality Score', key: 'Quality_Score', color: 'var(--accent4)', fmt: (v: number) => v.toFixed(4) },
              { label: 'Energy / Batch', key: 'Energy_per_batch', color: 'var(--accent)', fmt: (v: number) => `${v.toFixed(2)} kWh` },
              { label: 'Carbon Emission', key: 'Carbon_emission', color: 'var(--success)', fmt: (v: number) => `${v.toFixed(2)} kg` },
              { label: 'Reliability Index', key: 'Reliability_Index', color: 'var(--warn)', fmt: (v: number) => v.toFixed(4) },
              { label: 'Asset Health', key: 'Asset_Health_Score', color: '#8B5CF6', fmt: (v: number) => v.toFixed(4) },
            ].map(row => (
              <div key={row.key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--muted)', fontWeight: 500 }}>{row.label}</span>
                <span style={{ fontFamily: 'JetBrains Mono', color: row.color, fontWeight: 600 }}>{row.fmt(preds[row.key as keyof typeof preds] ?? 0)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function GoldenSignaturesView() {
  const [sigs, setSigs] = useState<GoldenSignatureMap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    api.getGoldenSignatures()
      .then(data => setSigs(data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const entries = sigs ? Object.entries(sigs) : [];

  return (
    <div>
      <div className="flex-between mb">
        <div style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 500, display: 'flex', alignItems: 'center' }}>
          {entries.length} strategy signature{entries.length !== 1 ? 's' : ''} stored
          <FieldTooltip text="Saved best-in-class machine parameters for different optimization priorities. The system uses these as references for future batches." />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button className="btn btn-muted btn-sm" style={{ display: 'flex', alignItems: 'center', gap: 6 }} onClick={load}>
            <RefreshCw size={14} className={loading ? "spinner" : ""} /> Refresh
          </button>
          <HelpDialog title="Golden Signatures Guide" style={{ position: 'static' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <p><strong>What is this page?</strong></p>
              <p>A Golden Signature is the absolute best set of machine parameters ever discovered by the AI for a specific goal (Energy, Quality, or Balanced). This page acts as your "Hall of Fame" library.</p>
              <p><strong>How to use it:</strong></p>
              <ul style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <li><strong>Reference Best Practices:</strong> Use these values as a starting point for manual machine setup if the AI is offline.</li>
                <li><strong>Continuous Improvement:</strong> The system automatically overwrites a signature if a future batch achieves a higher "Fitness Score" for that category.</li>
                <li><strong>Compare Strategies:</strong> Quickly glance at the difference in predicted outcomes (like Carbon Emission vs. Quality) between an Energy Saving signature and a Quality Priority signature.</li>
              </ul>
            </div>
          </HelpDialog>
        </div>
      </div>

      {loading && (
        <div className="card"><div className="empty-state"><span className="spinner" /> Loading signatures...</div></div>
      )}
      {error && <div className="alert alert-danger"><Info size={18} /> {error}</div>}

      {!loading && entries.length === 0 && (
        <div className="card">
          <div className="empty-state" style={{ padding: '64px 24px' }}>
            <div className="empty-icon"><Sparkles size={48} color="var(--border2)" /></div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>No Signatures Found</div>
            <div style={{ color: 'var(--muted)' }}>
              No Golden Signatures stored yet. Run the Optimization Dashboard to establish strategy baselines.
            </div>
            <button className="btn btn-primary mt" style={{ marginTop: 24 }} onClick={load}><RefreshCw size={14} /> Refresh</button>
          </div>
        </div>
      )}

      {entries.map(([name, data]) => (
        <SigCard key={name} name={name} data={data} />
      ))}
    </div>
  );
}
