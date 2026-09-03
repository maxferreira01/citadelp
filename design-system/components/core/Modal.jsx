import React from 'react';
export function Modal({ open = true, title, children, footer, onClose, width = 560, inline = false, style }) {
  if (!open) return null;
  const panel = (
    <div role="dialog" aria-modal={!inline} aria-label={title} style={{ width, maxWidth: '92%', background: 'var(--surface)', border: '1px solid var(--hairline)', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-overlay)', overflow: 'hidden', fontFamily: 'var(--font-ui)', ...style }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--hairline)' }}>
        <span style={{ font: '700 15px var(--font-brand)', color: 'var(--ink)' }}>{title}</span>
        {onClose && <button onClick={onClose} aria-label="Fechar" style={{ background: 'none', border: 'none', color: 'var(--text-faint)', cursor: 'pointer', fontSize: 15 }}>✕</button>}
      </div>
      <div style={{ padding: '16px 18px', fontSize: 13, color: 'var(--ink)', lineHeight: 1.55 }}>{children}</div>
      {footer && <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '12px 18px', borderTop: '1px solid var(--hairline)', background: 'var(--bg-page)' }}>{footer}</div>}
    </div>
  );
  if (inline) return panel;
  return <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(4,28,43,.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}><div onClick={(e) => e.stopPropagation()}>{panel}</div></div>;
}
