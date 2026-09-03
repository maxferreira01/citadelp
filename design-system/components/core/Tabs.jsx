import React from 'react';
export function Tabs({ items = [], active, onChange, style }) {
  return (
    <div role="tablist" style={{ display: 'flex', gap: 20, borderBottom: '1px solid var(--hairline)', fontFamily: 'var(--font-ui)', fontSize: 12.5, ...style }}>
      {items.map((it) => {
        const on = it.id === active;
        return (
          <button key={it.id} role="tab" aria-selected={on} onClick={onChange ? () => onChange(it.id) : undefined}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0 0 8px', fontFamily: 'inherit', fontSize: 'inherit', fontWeight: on ? 600 : 400, color: on ? 'var(--ink)' : 'var(--text-muted)', boxShadow: on ? 'inset 0 -2px var(--action)' : 'none' }}>
            {it.label}{it.count != null && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, marginLeft: 6, color: on ? 'var(--action)' : 'var(--text-faint)' }}>{it.count}</span>}
          </button>
        );
      })}
    </div>
  );
}
