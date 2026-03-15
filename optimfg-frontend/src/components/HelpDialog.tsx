import { HelpCircle, X } from 'lucide-react';
import { useState, type ReactNode } from 'react';

interface HelpDialogProps {
  title: string;
  children: ReactNode;
  style?: React.CSSProperties;
}

export default function HelpDialog({ title, children, style }: HelpDialogProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button 
        className="btn btn-primary btn-sm" 
        onClick={() => setOpen(true)}
        style={{ 
          position: 'absolute', 
          top: 0, 
          right: 0,
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          ...style
        }}
        title="Page Help"
      >
        <HelpCircle size={14} /> <span style={{ fontSize: 13 }}>Help</span>
      </button>

      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text)' }}>
                <HelpCircle size={18} color="var(--accent)" />
                {title}
              </div>
              <button className="modal-close" onClick={() => setOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              {children}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
