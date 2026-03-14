import { useState, type ReactNode } from 'react';
import { api } from './api';
import { css } from './styles';
import { 
  Zap, 
  Factory, 
  History, 
  Sparkles, 
  TestTube2, 
  MessageSquare, 
  BarChart2,
  Activity,
  Box,
  Download
} from 'lucide-react';
import OptimizationDashboard from './views/OptimizationDashboard';
import PlantConfigView from './views/PlantConfigView';
import BatchHistoryView from './views/BatchHistoryView';
import GoldenSignaturesView from './views/GoldenSignaturesView';
import WhatIfSimulationView from './views/WhatIfSimulationView';
import AIChatbotView from './views/AIChatbotView';
import ModelStatsView from './views/ModelStatsView';
import DigitalTwinView from './views/DigitalTwinView';

type TabId = 'optimize' | 'plant' | 'history' | 'signatures' | 'whatif' | 'chat' | 'stats' | 'twin';

interface NavItem {
  id: TabId;
  icon: ReactNode;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'optimize',    icon: <Zap size={18} />, label: 'Optimization' },
  { id: 'plant',       icon: <Factory size={18} />, label: 'Plant Config' },
  { id: 'history',     icon: <History size={18} />, label: 'Batch History' },
  { id: 'signatures',  icon: <Sparkles size={18} />, label: 'Golden Signatures' },
  { id: 'whatif',      icon: <TestTube2 size={18} />, label: 'What-If Simulation' },
  { id: 'chat',        icon: <MessageSquare size={18} />, label: 'AI Chatbot' },
  { id: 'stats',       icon: <BarChart2 size={18} />, label: 'Model Stats' },
  { id: 'twin',        icon: <Box size={18} />, label: 'Digital Twin' },
];

const TAB_TITLES: Record<TabId, string> = {
  optimize:   'Optimization Dashboard',
  plant:      'Plant Configuration',
  history:    'Batch History',
  signatures: 'Golden Signatures Library',
  whatif:     'What-If Simulation',
  chat:       'AI Chatbot',
  stats:      'Model Statistics',
  twin:       'Live 3D Digital Twin',
};

export default function App() {
  const [active, setActive] = useState<TabId>('optimize');
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadReport = async () => {
    try {
      setIsDownloading(true);
      await api.exportReport();
    } catch (e) {
      console.error(e);
      alert('Failed to generate report. Make sure backend is running and generated models exist.');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <>
      <style>{css}</style>

      <div className="app">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="logo">
            <div className="logo-name">Opti<span>MFG</span></div>
            <div className="logo-sub">AI Manufacturing Platform</div>
          </div>
          <nav className="nav">
            {NAV_ITEMS.map(item => (
              <div
                key={item.id}
                className={`nav-item${active === item.id ? ' active' : ''}`}
                onClick={() => setActive(item.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24 }}>
                  {item.icon}
                </div>
                <span>{item.label}</span>
              </div>
            ))}
          </nav>
          <div className="sidebar-footer">
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <span className="status-dot" />
              <span style={{ fontWeight: 600, color: 'var(--text)' }}>System Online</span>
            </div>
            <span>Backend: localhost:8000</span>
            <br />
            <span style={{ fontSize: 11, marginTop: 4, display: 'block' }}>
              FastAPI + XGBoost + NSGA-II
            </span>
          </div>
        </aside>

        {/* Main content */}
        <div className="main">
          {/* Topbar */}
          <header className="topbar">
            <div className="topbar-title">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)' }}>
                {NAV_ITEMS.find(n => n.id === active)?.icon}
              </div>
              {TAB_TITLES[active]}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <span className="badge badge-live">
                <Activity size={14} className="pulse" />
                LIVE
              </span>
              <span className="topbar-meta">
                v2.0.0 · Digital Twin Active
              </span>
              <button 
                className="btn btn-primary btn-sm"
                onClick={handleDownloadReport}
                disabled={isDownloading}
                style={{ fontSize: 13, gap: 6, display: 'flex', alignItems: 'center' }}
              >
                {isDownloading ? <span className="spinner" /> : <Download size={14} />}
                {isDownloading ? 'Generating...' : 'Export PDF Report'}
              </button>
            </div>
          </header>

          {/* Tab content */}
          <main className="content">
            {active === 'optimize'   && <OptimizationDashboard />}
            {active === 'plant'      && <PlantConfigView />}
            {active === 'history'    && <BatchHistoryView />}
            {active === 'signatures' && <GoldenSignaturesView />}
            {active === 'whatif'     && <WhatIfSimulationView />}
            {active === 'chat'       && <AIChatbotView />}
            {active === 'stats'      && <ModelStatsView />}
            {active === 'twin'       && <DigitalTwinView />}
          </main>
        </div>
      </div>
    </>
  );
}