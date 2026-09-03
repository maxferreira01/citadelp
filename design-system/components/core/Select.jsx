import React from 'react';
export function Select({ label, value, options = [], disabled = false, onChange, style }) {
  return (
    <label style={{ display: 'block', fontFamily: 'var(--font-ui)', ...style }}>
      {label && <span style={{ display: 'block', font: '600 10.5px var(--font-ui)', letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 5 }}>{label}</span>}
      <select value={value} disabled={disabled} onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        style={{ width: '100%', boxSizing: 'border-box', border: '1px solid var(--hairline)', borderRadius: 'var(--radius-md)', padding: '8px 10px', font: '400 13px var(--font-ui)', color: 'var(--ink)', background: 'var(--surface)', opacity: disabled ? 'var(--opacity-disabled)' : 1 }}
        onFocus={(e) => { e.target.style.outline = 'var(--focus-outline)'; e.target.style.outlineOffset = 'var(--focus-offset)'; }}
        onBlur={(e) => { e.target.style.outline = 'none'; }}>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}
