import { useState, useEffect } from 'react';
import { api } from '../api';
import type { PlantConfig } from '../types';
import { Settings, Save, AlertCircle, CheckCircle } from 'lucide-react';
import InfoTooltip from '../components/InfoTooltip';

const DEFAULT_CONFIG: PlantConfig = {
  electricity_capacity_kw: 1000,
  machine_power_limit_kw: 500,
  emission_factor: 0.45,
  carbon_emission_limit_kg: 200,
  default_machine_configuration: 'Standard',
  plant_operating_constraints: 'None',
};

export default function PlantConfigView() {
  const [config, setConfig] = useState<PlantConfig>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [alert, setAlert] = useState<{ msg: string; type: string } | null>(null);

  useEffect(() => {
    api.getPlantConfig()
      .then(c => setConfig({ ...DEFAULT_CONFIG, ...c }))
      .catch(() => {/* use defaults */})
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api.savePlantConfig(config);
      setAlert({ msg: 'Plant configuration saved successfully and is active.', type: 'success' });
    } catch (e: any) {
      setAlert({ msg: `Save failed: ${e.message}`, type: 'danger' });
    } finally {
      setSaving(false);
      setTimeout(() => setAlert(null), 4000);
    }
  };

  if (loading) return (
    <div className="card"><div className="empty-state"><span className="spinner" /> Loading config...</div></div>
  );

  return (
    <div>
      {alert && (
        <div className={`alert alert-${alert.type}`}>
          {alert.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          {alert.msg}
        </div>
      )}
      <div className="card">
        <div className="card-title"><Settings size={16} color="var(--accent)" /> Global Plant Configuration</div>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 24 }}>
          Set default plant operational constraints used across the optimization system.
        </p>
        <div className="grid-2 mb">
          {/* Column 1 */}
          <div>
            <div className="form-group">
              <label className="form-label">
                Total Electricity Capacity (kW)
                <InfoTooltip text="Maximum electrical power available for the entire plant operations." />
              </label>
              <input
                className="form-input"
                type="number"
                value={config.electricity_capacity_kw}
                onChange={e => setConfig(c => ({ ...c, electricity_capacity_kw: parseFloat(e.target.value) }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label">
                Max Machine Power Limit (kW)
                <InfoTooltip text="Maximum power a single machine is allowed to draw at any given time." />
              </label>
              <input
                className="form-input"
                type="number"
                value={config.machine_power_limit_kw}
                onChange={e => setConfig(c => ({ ...c, machine_power_limit_kw: parseFloat(e.target.value) }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label">
                Global Carbon Limit (kg CO₂)
                <InfoTooltip text="Absolute maximum allowed carbon emissions across the current production cycle." />
              </label>
              <input
                className="form-input"
                type="number"
                value={config.carbon_emission_limit_kg}
                onChange={e => setConfig(c => ({ ...c, carbon_emission_limit_kg: parseFloat(e.target.value) }))}
              />
            </div>
          </div>
          {/* Column 2 */}
          <div>
            <div className="form-group">
              <label className="form-label">
                Emission Factor (kg CO₂/kWh)
                <InfoTooltip text="Grid emission factor used to convert electrical energy consumption into carbon emissions." />
              </label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                value={config.emission_factor}
                onChange={e => setConfig(c => ({ ...c, emission_factor: parseFloat(e.target.value) }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label">
                Default Machine Setting
                <InfoTooltip text="Base configuration preset applied when creating new batches." />
              </label>
              <input
                className="form-input"
                type="text"
                value={config.default_machine_configuration}
                onChange={e => setConfig(c => ({ ...c, default_machine_configuration: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label">
                Plant Operating Constraints
                <InfoTooltip text="Any additional operational rules or guidelines for the manufacturing floor." />
              </label>
              <textarea
                className="form-textarea"
                value={config.plant_operating_constraints}
                onChange={e => setConfig(c => ({ ...c, plant_operating_constraints: e.target.value }))}
              />
            </div>
          </div>
        </div>

        {/* Summary */}
        <div style={{
          background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8,
          padding: '16px 20px', marginBottom: 20, fontSize: 13, display: 'grid',
          gridTemplateColumns: 'repeat(3,1fr)', gap: 16
        }}>
          {[
            { label: 'Electricity Capacity', val: `${config.electricity_capacity_kw} kW` },
            { label: 'Power Limit', val: `${config.machine_power_limit_kw} kW` },
            { label: 'Carbon Limit', val: `${config.carbon_emission_limit_kg} kg` },
            { label: 'Emission Factor', val: `${config.emission_factor} kg/kWh` },
            { label: 'Machine Config', val: config.default_machine_configuration },
            { label: 'Constraints', val: config.plant_operating_constraints },
          ].map((item, i) => (
            <div key={i}>
              <div style={{ color: 'var(--text2)', fontSize: 11, fontWeight: 600, letterSpacing: 0.5, textTransform: 'uppercase', marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--text)', fontWeight: 600 }}>{item.val}</div>
            </div>
          ))}
        </div>

        <button className="btn btn-primary" onClick={save} disabled={saving} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {saving ? <><span className="spinner" /> Saving...</> : <><Save size={16} /> Save Plant Configuration</>}
        </button>
      </div>
    </div>
  );
}
