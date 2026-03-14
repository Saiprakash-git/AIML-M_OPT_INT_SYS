import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../api';
import type { ModelMetrics } from '../types';
import { CheckCircle, BarChart2, ClipboardList } from 'lucide-react';
import FieldTooltip from '../components/InfoTooltip';

export default function ModelStatsView() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getModelMetrics()
      .then(setMetrics)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="card"><div className="empty-state"><span className="spinner" /> Loading model statistics...</div></div>
  );

  if (error) return (
    <div>
      <div className="alert alert-warn"><ClipboardList size={18} /> {error}</div>
      <div className="card">
        <div className="empty-state" style={{ padding: '64px 24px' }}>
          <div className="empty-icon"><BarChart2 size={48} color="var(--border2)" /></div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>Model Stats Unavailable</div>
          <div>To view model performance statistics:</div>
          <ol style={{ textAlign: 'left', display: 'inline-block', marginTop: 16, lineHeight: 2, color: 'var(--text2)' }}>
            <li>Go to the <strong>Optimization Dashboard</strong> tab</li>
            <li>Run an optimization (this trains the Digital Twin)</li>
            <li>Return here to view the statistics</li>
          </ol>
        </div>
      </div>
    </div>
  );

  if (!metrics) return null;

  const entries = Object.entries(metrics);
  const barData = entries.map(([target, m]) => ({
    name: target.replace(/_/g, ' '),
    MAE: parseFloat(m.MAE.toFixed(4)),
    RMSE: parseFloat(m.RMSE.toFixed(4)),
  }));

  const consistencyData = entries.map(([target, m]) => {
    const ratio = m.MAE > 0 ? m.RMSE / m.MAE : 0;
    const assessment = ratio <= 1.5 ? 'Good' : ratio <= 2.0 ? 'Acceptable' : 'Check for Outliers';
    const color = ratio <= 1.5 ? 'var(--success)' : ratio <= 2.0 ? 'var(--warn)' : 'var(--danger)';
    return { target: target.replace(/_/g, ' '), ratio: ratio.toFixed(4), assessment, color };
  });

  return (
    <div>
      <div className="alert alert-success mb"><CheckCircle size={18} /> Model metrics loaded successfully</div>

      {/* KPI cards */}
      <div className="mb">
        <div className="card-title" style={{ marginBottom: 16, display: 'flex', alignItems: 'center' }}>
          <BarChart2 size={16} color="var(--accent)" /> Performance Metrics by Target Variable
          <FieldTooltip text="Shows regression error metrics. Lower is better. MAE is average error, RMSE penalizes larger errors more heavily." />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(entries.length, 3)},1fr)`, gap: 16, marginBottom: 20 }}>
          {entries.map(([target, m]) => (
            <div className="card" key={target} style={{ padding: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', marginBottom: 16 }}>
                {target.replace(/_/g, ' ')}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <span style={{ color: 'var(--muted)', fontWeight: 500 }}>MAE</span>
                <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--text)', fontWeight: 600 }}>{m.MAE.toFixed(4)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', fontSize: 13 }}>
                <span style={{ color: 'var(--muted)', fontWeight: 500 }}>RMSE</span>
                <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--text)', fontWeight: 600 }}>{m.RMSE.toFixed(4)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bar chart */}
      <div className="card mb">
        <div className="card-title"><BarChart2 size={16} color="var(--muted)"/> Visual Comparison — MAE vs RMSE</div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={barData} margin={{ bottom: 20, top: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="name" tick={{ fill: 'var(--muted)', fontSize: 11 }} axisLine={{ stroke: 'var(--border)' }} tickLine={{ stroke: 'var(--border)' }} />
            <YAxis tick={{ fill: 'var(--muted)', fontSize: 11 }} axisLine={{ stroke: 'var(--border)' }} tickLine={{ stroke: 'var(--border)' }} />
            <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', fontSize: 12, borderRadius: 8, boxShadow: 'var(--shadow)' }} />
            <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text2)', fontWeight: 500 }} />
            <Bar dataKey="MAE" fill="var(--accent)" fillOpacity={0.9} name="MAE" radius={[4, 4, 0, 0]} />
            <Bar dataKey="RMSE" fill="var(--success)" fillOpacity={0.9} name="RMSE" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Summary table */}
      <div className="card mb">
        <div className="card-title"><ClipboardList size={16} color="var(--muted)"/> Summary Table</div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Target Variable</th><th>MAE</th><th>RMSE</th></tr>
            </thead>
            <tbody>
              {entries.map(([target, m]) => (
                <tr key={target}>
                  <td style={{ color: 'var(--text)', fontWeight: 500 }}>{target.replace(/_/g, ' ')}</td>
                  <td className="mono" style={{ color: 'var(--accent)', fontWeight: 600 }}>{m.MAE.toFixed(4)}</td>
                  <td className="mono" style={{ color: 'var(--success)', fontWeight: 600 }}>{m.RMSE.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Error consistency */}
      <div className="card mb">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center' }}>
          <CheckCircle size={16} color="var(--muted)"/> Error Consistency Analysis
          <FieldTooltip text="Evaluates the ratio of RMSE to MAE to detect significant outliers in model predictions." />
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Target</th><th>RMSE/MAE Ratio</th><th>Assessment</th></tr>
            </thead>
            <tbody>
              {consistencyData.map(row => (
                <tr key={row.target}>
                  <td style={{ color: 'var(--text)', fontWeight: 500 }}>{row.target}</td>
                  <td className="mono" style={{ fontWeight: 600 }}>{row.ratio}</td>
                  <td><span className="tag" style={{ background: `${row.color}18`, color: row.color, border: `1px solid ${row.color}44`, fontWeight: 600 }}>{row.assessment}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model info */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Model Type</div>
          <div style={{ fontSize: 14, color: 'var(--text)', lineHeight: 2.2 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)' }}><span style={{ color: 'var(--muted)' }}>Algorithm:</span> <span style={{ fontWeight: 500 }}>MultiOutput XGBoost</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)' }}><span style={{ color: 'var(--muted)' }}>Estimators:</span> <span className="mono">100</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)' }}><span style={{ color: 'var(--muted)' }}>Learning Rate:</span> <span className="mono">0.1</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--muted)' }}>Max Depth:</span> <span className="mono">5</span></div>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Features &amp; Targets</div>
          <div style={{ fontSize: 13, lineHeight: 2 }}>
            <div style={{ color: 'var(--accent)', marginBottom: 8, fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>8 Input Features</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
              {['Granulation Time', 'Binder Amount', 'Drying Temperature', 'Drying Time', 'Compression Force', 'Machine Speed', 'Lubricant Conc', 'Moisture Content'].map(f => (
                <div key={f} style={{ color: 'var(--text2)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--border2)' }} /> {f}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
