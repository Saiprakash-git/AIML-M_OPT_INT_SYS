import { useState, useRef, useEffect } from 'react';
import { api } from '../api';
import type { ChatMessage } from '../types';
import { BarChart2, Zap, Trophy, Bot, User, Trash2, Send, MessageSquare } from 'lucide-react';
import FieldTooltip from '../components/InfoTooltip';

const PRE_PROMPTS: { label: string; icon: React.ReactNode; prompt: string }[] = [
  {
    icon: <BarChart2 size={16} />,
    label: 'Current System Status',
    prompt: 'What is the current state of my plant? Show me the latest Golden Signature scores, recent batch performance, and model accuracy.',
  },
  {
    icon: <Zap size={16} />,
    label: 'Best Energy Setting',
    prompt: 'Based on my historical batches and Golden Signatures, what are the best machine parameters to minimize energy consumption while keeping quality above 0.4?',
  },
  {
    icon: <Trophy size={16} />,
    label: 'Optimize for Quality',
    prompt: 'Looking at all my stored Golden Signatures and batch history, which configuration gave the highest quality score? What parameters should I use for a quality-priority run?',
  },
];

export default function AIChatbotView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text = input) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    const next: ChatMessage[] = [...messages, { role: 'user', content: trimmed }];
    setMessages(next);
    setInput('');
    setLoading(true);
    try {
      const res = await api.chat(next);
      setMessages([...next, { role: 'assistant', content: res.response }]);
    } catch (e: any) {
      setMessages([...next, { role: 'assistant', content: `⚠️ Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '24px 24px 16px', borderBottom: '1px solid var(--border)' }}>
          <div className="card-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center' }}>
            <MessageSquare size={16} color="var(--accent)" /> OptiMFG AI Assistant
            <FieldTooltip text="This AI acts as an expert consultant with real-time access to the plant's live data, Golden Signatures, and batch history." />
          </div>
          <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
            Ask anything about manufacturing optimization, machine parameters, Pareto fronts,
            Golden Signatures, or current plant state. The AI has access to <strong style={{ color: 'var(--accent)' }}>live data</strong> from your system.
          </p>

          {/* ── Pre-prompt chips ── */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {PRE_PROMPTS.map((p, i) => (
              <button
                key={i}
                className="btn btn-muted"
                style={{
                  fontSize: 12, padding: '8px 16px',
                  background: 'var(--surface2)',
                  borderColor: 'var(--border)',
                  color: 'var(--text2)',
                  display: 'flex', alignItems: 'center', gap: 8,
                  transition: 'all .15s',
                  borderRadius: 20,
                  boxShadow: 'none'
                }}
                onClick={() => send(p.prompt)}
                disabled={loading}
                title={p.prompt}
              >
                <span style={{ color: 'var(--accent)' }}>{p.icon}</span>
                <span style={{ fontWeight: 500 }}>{p.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Chat messages ── */}
        <div className="chat-wrap" style={{ flex: 1, height: 'auto' }}>
          <div className="chat-messages" style={{ padding: '24px', background: 'var(--bg)' }}>
            {messages.length === 0 && (
              <div className="empty-state" style={{ padding: '48px 24px' }}>
                <div className="empty-icon"><Bot size={48} color="var(--border2)" /></div>
                <div style={{ marginBottom: 12, fontSize: 16, fontWeight: 600, color: 'var(--text)' }}>How can I help you today?</div>
                <div style={{ fontSize: 13, color: 'var(--muted)', maxWidth: 400, margin: '0 auto', lineHeight: 1.6 }}>
                  Start a conversation above or type your question below. The AI can see your live Golden Signatures, batch history, model metrics, and plant config.
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}`}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  fontSize: 11, fontWeight: 600, color: m.role === 'user' ? '#E0E7FF' : 'var(--muted)', 
                  marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5
                }}>
                  {m.role === 'user' ? <><User size={12}/> YOU</> : <><Bot size={12}/> OPTIMFG AI</>}
                </div>
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{m.content}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble assistant">
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600, color: 'var(--muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  <Bot size={12}/> OPTIMFG AI
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text2)' }}>
                  <span className="spinner" />
                  <span style={{ fontSize: 13, fontWeight: 500 }}>Analyzing live system data...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-row" style={{ padding: '20px 24px', background: 'var(--surface)' }}>
            {messages.length > 0 && (
              <button
                className="btn btn-muted"
                onClick={() => setMessages([])}
                title="Clear Chat"
                style={{ padding: '12px', border: 'none', background: 'transparent', color: 'var(--muted)' }}
              >
                <Trash2 size={20} />
              </button>
            )}
            <input
              className="chat-input"
              style={{ padding: '14px 20px', fontSize: 15, borderRadius: 24, background: 'var(--surface2)', border: '1px solid var(--border)' }}
              placeholder="Ask about optimization, parameters, batch history..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
              disabled={loading}
            />
            <button
              className="btn btn-primary"
              style={{ borderRadius: 24, padding: '12px 24px', display: 'flex', alignItems: 'center', gap: 8 }}
              onClick={() => send()}
              disabled={loading || !input.trim()}
            >
              <Send size={16} /> Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
