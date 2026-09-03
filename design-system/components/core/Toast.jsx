import React from 'react';
import { STATUS_STATES } from './StatusBadge.jsx';
export function Toast({ kind = 'info', title, detail, actionLabel, onAction, onClose, style }) {
  const s = STATUS_STATES[kind] || STATUS_STATES.info;
  return (
    <div role="status" style={{ display: 'flex', alignItems: 'flex-start', gap: 10, background: 'var(--surface)', border: '1px solid var(--hairline)', borderLeft: `3px solid ${s.color}`, borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-2)', padding: '10px 14px', maxWidth: 420, fontFamily: 'var(--font-ui)', ...style }}>
      <span aria-hidden="true" style={{ fontFamily: 'var(--font-mono)', color: s.color, fontSize: 13, lineHeight: '18px' }}>{s.glyph}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--ink)' }}>{title}</div>
        {detail && <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 2, lineHeight: 1.45 }}>{detail}</div>}
        {actionLabel && <button onClick={onAction} style={{ background: 'none', border: 'none', padding: 0, marginTop: 6, font: '600 11.5px var(--font-ui)', color: 'var(--link)', cursor: 'pointer' }}>{actionLabel} →</button>}
      </div>
      {onClose && <button onClick={onClose} aria-label="Fechar" style={{ background: 'none', border: 'none', color: 'var(--text-faint)', cursor: 'pointer', fontSize: 14, lineHeight: '18px', padding: 0 }}>✕</button>}
    </div>
  );
}
