export const css = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  :root {
    /* Premium Light Theme Colors */
    --bg: #F4F7F9; /* Off-white sophisticated background */
    --surface: #FFFFFF; /* Pure white cards */
    --surface2: #F8FAFC; /* Slate 50 for slight contrast */
    --surface3: #F1F5F9; /* Slate 100 for secondary elements */
    
    --border: #E2E8F0; /* Slate 200 */
    --border2: #CBD5E1; /* Slate 300 */
    
    --accent: #4F46E5; /* Indigo 600 - Primary brand color */
    --accent2: #0D9488; /* Teal 600 - Secondary accent */
    --accent3: #EA580C; /* Orange 600 - Tertiary */
    --accent4: #CA8A04; /* Yellow 600 - Quaternary */
    
    --text: #0F172A; /* Slate 900 - High contrast text */
    --text2: #334155; /* Slate 700 - Subtext */
    --muted: #64748B; /* Slate 500 - De-emphasized text */
    
    --danger: #EF4444; /* Red 500 */
    --success: #10B981; /* Emerald 500 */
    --warn: #F59E0B; /* Amber 500 */
    
    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
    --shadow-md: 0 10px 15px -3px rgb(0 0 0 / 0.05), 0 4px 6px -4px rgb(0 0 0 / 0.05);
  }

  html, body, #root {
    height: 100%;
    width: 100%;
    overflow: hidden;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  .mono {
    font-family: 'JetBrains Mono', monospace;
  }

  /* Layout */
  .app {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }

  .sidebar {
    width: 260px;
    min-width: 260px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-sm);
    z-index: 10;
  }

  .logo {
    padding: 24px 24px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .logo-name {
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: var(--text);
    font-family: 'Inter', sans-serif;
  }

  .logo-name span {
    color: var(--accent);
  }

  .logo-sub {
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-weight: 500;
  }

  .nav {
    flex: 1;
    padding: 24px 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: var(--text2);
    border-radius: 8px;
    transition: all 0.2s ease;
    user-select: none;
  }

  .nav-item:hover {
    color: var(--text);
    background: var(--surface2);
  }

  .nav-item.active {
    color: var(--accent);
    background: #EEF2FF; /* Indigo 50 */
    font-weight: 600;
  }

  .nav-item.active .lucide {
    stroke-width: 2.5;
  }

  .sidebar-footer {
    padding: 20px 24px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--muted);
    background: var(--surface2);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    display: inline-block;
    margin-right: 8px;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  }

  .main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg);
  }

  .topbar {
    height: 64px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 32px;
    flex-shrink: 0;
    box-shadow: var(--shadow-sm);
    z-index: 5;
  }

  .topbar-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 12px;
    letter-spacing: -0.3px;
  }

  .topbar-meta {
    font-size: 12px;
    color: var(--muted);
    font-family: 'JetBrains Mono', monospace;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    font-family: 'Inter', sans-serif;
  }

  .badge-live {
    background: #ECFDF5; /* Emerald 50 */
    color: var(--success);
    border: 1px solid #D1FAE5; /* Emerald 100 */
  }

  .content {
    flex: 1;
    overflow-y: auto;
    padding: 32px;
  }

  .content::-webkit-scrollbar {
    width: 8px;
  }

  .content::-webkit-scrollbar-thumb {
    background: var(--border2);
    border-radius: 4px;
  }

  .content::-webkit-scrollbar-track {
    background: transparent;
  }

  /* Cards */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  
  .card:hover {
    box-shadow: var(--shadow-md);
  }

  .card-title {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .card-title::before {
    content: '';
    display: block;
    width: 4px;
    height: 14px;
    background: var(--accent);
    border-radius: 2px;
  }

  /* KPI */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;
  }

  .kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  
  .kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }

  .kpi-card::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
  }

  .kpi-card.energy::after { background: var(--accent); }
  .kpi-card.carbon::after { background: var(--accent2); }
  .kpi-card.quality::after { background: var(--accent4); }
  .kpi-card.reliability::after { background: var(--accent3); }
  .kpi-card.health::after { background: #8B5CF6; /* Violet 500 */ }

  .kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 12px;
  }

  .kpi-value {
    font-size: 32px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -1px;
  }

  .kpi-value.energy { color: var(--text); }
  .kpi-value.carbon { color: var(--text); }
  .kpi-value.quality { color: var(--text); }
  .kpi-value.reliability { color: var(--text); }
  .kpi-value.health { color: var(--text); }

  .kpi-unit {
    font-size: 14px;
    font-weight: 500;
    color: var(--muted);
    margin-left: 6px;
    font-family: 'Inter', sans-serif;
  }

  /* Grids */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
  .grid-2-1 { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
  .mb { margin-bottom: 20px; }
  .mt { margin-top: 20px; }

  /* Table */
  .table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;
  }

  .table th {
    text-align: left;
    padding: 12px 16px;
    font-size: 11px;
    letter-spacing: 1px;
    color: var(--muted);
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    font-weight: 600;
    background: var(--surface2);
  }

  .table th:first-child { border-top-left-radius: 8px; }
  .table th:last-child { border-top-right-radius: 8px; }

  .table td {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    color: var(--text2);
    font-weight: 500;
  }

  .table tr:last-child td { border-bottom: none; }
  .table tr:hover td { background: var(--surface2); color: var(--text); }
  .table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }

  /* Tags */
  .tag {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    font-family: 'Inter', sans-serif;
  }

  .tag-success { background: #ECFDF5; color: var(--success); border: 1px solid #D1FAE5; }
  .tag-warn { background: #FFFBEB; color: var(--warn); border: 1px solid #FEF3C7; }
  .tag-danger { background: #FEF2F2; color: var(--danger); border: 1px solid #FEE2E2; }
  .tag-info { background: #EFF6FF; color: var(--accent); border: 1px solid #DBEAFE; }

  /* Buttons */
  .btn {
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    letter-spacing: 0.5px;
    transition: all 0.2s ease;
    font-family: 'Inter', sans-serif;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .btn:disabled { opacity: 0.6; cursor: not-allowed; }

  .btn-primary { background: var(--accent); color: #FFF; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2); }
  .btn-primary:hover:not(:disabled) { background: #4338CA; transform: translateY(-1px); box-shadow: 0 6px 8px -1px rgba(79, 70, 229, 0.3); }

  .btn-success { background: #ECFDF5; color: var(--success); border: 1px solid #D1FAE5; }
  .btn-success:hover:not(:disabled) { background: #D1FAE5; }

  .btn-danger { background: #FEF2F2; color: var(--danger); border: 1px solid #FEE2E2; }
  .btn-danger:hover:not(:disabled) { background: #FEE2E2; }

  .btn-muted { background: var(--surface); color: var(--text2); border: 1px solid var(--border); box-shadow: var(--shadow-sm); }
  .btn-muted:hover:not(:disabled) { color: var(--text); border-color: var(--border2); background: var(--surface2); }

  .btn-sm { padding: 6px 12px; font-size: 12px; border-radius: 6px; }

  /* Alerts */
  .alert {
    padding: 14px 18px;
    border-radius: 8px;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    font-weight: 500;
  }

  .alert-success { background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; }
  .alert-danger { background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }
  .alert-warn { background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; }
  .alert-info { background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; }

  /* Forms */
  .form-group { margin-bottom: 20px; }
  .form-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text2);
    margin-bottom: 8px;
  }

  .form-input, .form-select, .form-textarea {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 14px;
    font-family: 'Inter', sans-serif;
    outline: none;
    transition: all 0.2s ease;
    box-shadow: var(--shadow-sm);
  }

  .form-input:focus, .form-select:focus, .form-textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  }

  .form-textarea { resize: vertical; min-height: 100px; }

  .range-wrap { display: flex; align-items: center; gap: 16px; }
  .range-input { flex: 1; accent-color: var(--accent); height: 6px; border-radius: 3px; background: var(--border); outline: none; }
  .range-val { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 600; color: var(--accent); min-width: 60px; text-align: right; }

  /* Flex utils */
  .flex { display: flex; }
  .flex-between { display: flex; justify-content: space-between; align-items: center; }
  .flex-center { display: flex; align-items: center; }
  .flex-wrap { flex-wrap: wrap; }
  .gap-sm { gap: 8px; }
  .gap { gap: 16px; }
  .gap-lg { gap: 24px; }
  .w100 { width: 100%; }

  /* Spinner */
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 3px solid var(--border2);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.5 } }
  .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }

  /* Params block */
  .params-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .param-item {
    background: var(--surface3);
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid var(--border);
  }
  .param-name { font-size: 10px; font-weight: 600; letter-spacing: 0.5px; color: var(--muted); text-transform: uppercase; margin-bottom: 6px; }
  .param-val { font-size: 15px; font-weight: 600; font-family: 'JetBrains Mono', monospace; color: var(--text); }

  /* Sig cards */
  .sig-card {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    background: var(--surface);
    margin-bottom: 16px;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s;
  }
  .sig-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow);
  }
  
  .sig-card.golden {
    border-color: #FDE047; /* Yellow 300 */
    background: #FEFCE8; /* Yellow 50 */
  }
  
  .sig-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }

  /* Decision comparison cards */
  .dec-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }
  .dec-card { border: 1px solid var(--border); border-radius: 12px; padding: 20px; background: var(--surface); box-shadow: var(--shadow-sm); }
  .dec-card.energy-card { border-top: 4px solid var(--accent); }
  .dec-card.balanced-card { border-top: 4px solid var(--success); }
  .dec-card.quality-card { border-top: 4px solid var(--warn); }
  
  .dec-title { font-size: 14px; font-weight: 700; margin-bottom: 16px; color: var(--text); display: flex; align-items: center; gap: 8px;}
  .dec-metric { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; font-weight: 500; color: var(--text2); border-bottom: 1px dashed var(--border);}
  .dec-metric:last-child { border-bottom: none; }

  /* Expandable section */
  .expander { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin-bottom: 16px; box-shadow: var(--shadow-sm); }
  .expander-header {
    padding: 14px 20px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    font-weight: 600;
    background: var(--surface);
    user-select: none;
    color: var(--text);
  }
  .expander-header:hover { background: var(--surface2); }
  .expander-body { padding: 20px; background: var(--surface); border-top: 1px solid var(--border); }

  /* Chat */
  .chat-wrap { display: flex; flex-direction: column; height: 500px; }
  .chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
  .chat-messages::-webkit-scrollbar { width: 6px; }
  .chat-messages::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
  
  .chat-bubble {
    padding: 14px 18px;
    border-radius: 12px;
    font-size: 14px;
    max-width: 80%;
    line-height: 1.6;
    box-shadow: var(--shadow-sm);
  }
  .chat-bubble.user { background: var(--accent); color: #FFF; align-self: flex-end; border-bottom-right-radius: 4px; }
  .chat-bubble.assistant { background: var(--surface); border: 1px solid var(--border); align-self: flex-start; color: var(--text); border-bottom-left-radius: 4px; }
  
  .chat-input-row { display: flex; gap: 12px; padding: 16px 20px; border-top: 1px solid var(--border); background: var(--surface); }
  .chat-input { flex: 1; background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 12px 16px; border-radius: 8px; font-size: 14px; font-family: 'Inter', sans-serif; outline: none; transition: all 0.2s;}
  .chat-input:focus { border-color: var(--accent); background: var(--surface); box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }

  /* Tooltip */
  .custom-tooltip { background: var(--surface); border: 1px solid var(--border); box-shadow: var(--shadow); padding: 12px 16px; border-radius: 8px; font-size: 12px; font-family: 'Inter', sans-serif; color: var(--text); }
  .ct-label { color: var(--text); font-weight: 600; margin-bottom: 8px; font-size: 13px; border-bottom: 1px solid var(--border); padding-bottom: 4px;}
  .ct-item { display: flex; justify-content: space-between; gap: 16px; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace;}

  /* Info Tooltip */
  .info-icon-wrap { position: relative; display: inline-flex; align-items: center; justify-content: center; margin-left: 6px; margin-top: -2px; cursor: help; color: var(--muted); vertical-align: middle; }
  .info-icon-wrap:hover { color: var(--accent); }
  .info-tooltip { visibility: hidden; opacity: 0; position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%) translateY(4px); background: var(--text); color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 11px; font-weight: 400; text-align: left; white-space: normal; width: max-content; max-width: 250px; pointer-events: none; z-index: 100; transition: all 0.2s; box-shadow: var(--shadow); line-height: 1.5; font-family: 'Inter', sans-serif;}
  .info-icon-wrap:hover .info-tooltip { visibility: visible; opacity: 1; transform: translateX(-50%) translateY(-6px); }
  .info-tooltip::after { content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); border-width: 5px; border-style: solid; border-color: var(--text) transparent transparent transparent; }

  /* Empty state */
  .empty-state { text-align: center; padding: 64px 24px; color: var(--muted); font-size: 15px; line-height: 1.6; display: flex; flex-direction: column; align-items: center; }
  .empty-icon { font-size: 48px; margin-bottom: 16px; color: var(--border2); }

  /* Code block */
  .code-block { background: var(--surface3); border: 1px solid var(--border); border-radius: 8px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--text); line-height: 1.6; white-space: pre-wrap; overflow-x: auto; }

  /* AI prose */
  .ai-prose { font-size: 14px; line-height: 1.7; color: var(--text); white-space: pre-wrap; }
`;
