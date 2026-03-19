import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import type { BatchRecord } from '../types';
import { History, RefreshCw, Bot, Brain, Database, AlertCircle } from 'lucide-react';
import FieldTooltip from '../components/InfoTooltip';
import HelpDialog from '../components/HelpDialog';

export default function BatchHistoryView() {
  const [history, setHistory] = useState<BatchRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState('');
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getBatchHistory();
      setHistory(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(`Could not load batch history: ${e.message}`);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const fetchInsights = async () => {
    if (history.length === 0) return;
    setInsightsLoading(true);
    try {
      const res = await api.batchInsights(history);
      setInsights(res.insights);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setInsightsLoading(false);
    }
  };

  const modeTag = (mode?: string) => {
    if (!mode) return null;
    const color = mode === 'Energy Saving' ? 'var(--accent)' : mode === 'Quality Priority' ? 'var(--warn)' : 'var(--success)';
    const bg = mode === 'Energy Saving' ? 'var(--info-bg, #EFF6FF)' : mode === 'Quality Priority' ? 'var(--warn-bg, #FFFBEB)' : 'var(--success-bg, #ECFDF5)';
    const borderColor = mode === 'Energy Saving' ? '#BFDBFE' : mode === 'Quality Priority' ? '#FDE68A' : '#A7F3D0';
    return <span className="tag" style={{ background: bg, color, border: `1px solid ${borderColor}` }}>{mode}</span>;
  };

  return (
    <div>
      <div className="flex-between mb">
        <span style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 500 }}>
          {loading ? 'Loading...' : `${history.length} record${history.length !== 1 ? 's' : ''} found`}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-muted btn-sm" style={{ display: 'flex', alignItems: 'center', gap: 6 }} onClick={load} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spinner" : ""} /> Refresh
          </button>
          <HelpDialog title="Batch History Guide" style={{ position: 'static' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <p><strong>What is this page?</strong></p>
              <p>This page acts as the system of record for all past optimization runs. Every time you optimize a batch on the Dashboard, the chosen configuration and its predicted results are logged here.</p>
              <p><strong>How to use it:</strong></p>
              <ul style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <li><strong>Review Past Runs:</strong> Scroll through the table to see the Quality, Energy, and Carbon metrics achieved by previous batches.</li>
                <li><strong>AI Insights:</strong> If you have multiple records, click the "AI Insights" panel at the top. The AI will analyze the entire history table to find trends (e.g., "Quality drops when moisture is too high").</li>
                <li><strong>Continuous Learning:</strong> This data feeds back into the AI models (viewable on the Model Stats page) to improve future predictions.</li>
              </ul>
            </div>
          </HelpDialog>
        </div>
      </div>

      {error && <div className="alert alert-danger"><AlertCircle size={18} /> {error}</div>}

      {/* AI Insights expander */}
      {history.length > 0 && (
        <div className="expander mb">
          <div className="expander-header" onClick={() => setShowInsights(e => !e)}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Bot size={18} color="var(--accent)" /> AI Insights on Batch History ({history.length} records)</span>
            <span style={{ color: 'var(--muted)' }}>{showInsights ? '▲' : '▼'}</span>
          </div>
          {showInsights && (
            <div className="expander-body">
              <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
                AI-generated pattern analysis and recommendations across your historical batch data.
              </p>
              <button className="btn btn-primary btn-sm mb" onClick={fetchInsights} disabled={insightsLoading}>
                {insightsLoading ? <><span className="spinner" /> Analyzing...</> : <><Brain size={14} /> Generate AI Insights</>}
              </button>
              {insights && <div className="ai-prose mt" style={{ background: 'var(--surface2)', padding: 16, borderRadius: 8 }}>{insights}</div>}
            </div>
          )}
        </div>
      )}

      <div className="card">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center' }}>
          <History size={16} color="var(--muted)" /> Historical Batch Results
          <FieldTooltip text="A growing log of executed production batches and their outcomes. Used for continuous model refinement." />
        </div>

        {loading && (
          <div className="empty-state"><span className="spinner" style={{ marginRight: 8 }} /> Loading batch history...</div>
        )}

        {!loading && history.length === 0 && (
          <div className="empty-state" style={{ padding: '64px 24px' }}>
            <div className="empty-icon"><Database size={48} color="var(--border2)" /></div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>No History Found</div>
            <div style={{ color: 'var(--muted)' }}>
              Run an optimization from the Dashboard tab to populate results.
            </div>
            <br />
            <button className="btn btn-muted btn-sm" onClick={load}><RefreshCw size={14} /> Try Again</button>
          </div>
        )}

        {!loading && history.length > 0 && (
          <>
            <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
              Found <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{history.length}</strong> continuous learning records
            </div>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Batch ID</th>
                    <th>Mode</th>
                    <th>Material</th>
                    <th>Quality Score</th>
                    <th>Energy (kWh)</th>
                    <th>Carbon (kg)</th>
                    <th>Asset Health</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((b, i) => {
                    const p = b.predicted_outcomes ?? {};
                    const hasOutcomes = Object.keys(p).length > 0;
                    return (
                      <tr key={i}>
                        <td className="mono" style={{ color: 'var(--accent)', fontWeight: 600 }}>{b.batch_id ?? 'N/A'}</td>
                        <td>{modeTag(b.optimization_mode)}</td>
                        <td style={{ color: 'var(--text2)', fontWeight: 500 }}>{b.material_type ?? 'N/A'}</td>
                        <td className="mono" style={{ color: hasOutcomes ? 'var(--warn)' : 'var(--muted)', fontWeight: 600 }}>
                          {hasOutcomes ? ((p.Quality_Score ?? 0) * 100).toFixed(2) + '%' : '—'}
                        </td>
                        <td className="mono" style={{ fontWeight: 500 }}>{hasOutcomes ? (p.Energy_per_batch ?? 0).toFixed(2) : '—'}</td>
                        <td className="mono" style={{ fontWeight: 500 }}>{hasOutcomes ? (p.Carbon_emission ?? 0).toFixed(2) : '—'}</td>
                        <td className="mono" style={{ color: (p.Asset_Health_Score ?? 1) > 0.9 ? 'var(--success)' : 'var(--warn)', fontWeight: 600 }}>
                          {hasOutcomes ? ((p.Asset_Health_Score ?? 1) * 100).toFixed(2) + '%' : '—'}
                        </td>
                        <td>
                          <span className="tag" style={{
                            background: b.status === 'Created' ? 'var(--surface2)' : '#ECFDF5',
                            color: b.status === 'Created' ? 'var(--muted)' : 'var(--success)',
                            border: `1px solid ${b.status === 'Created' ? 'var(--border)' : '#A7F3D0'}`,
                          }}>
                            {b.status ?? 'Complete'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
