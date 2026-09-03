import React from 'react';
export function TextField({ label, value, placeholder, hint, error, mono = false, disabled = false, onChange, type = 'text', style }) {
  return (
    <label style={{ display: 'block', fontFamily: 'var(--font-ui)', ...style }}>
      {label && <span style={{ display: 'block', font: '600 10.5px var(--font-ui)', letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 5 }}>{label}</span>}
      <input type={type} value={value} placeholder={placeholder} disabled={disabled} readOnly={!onChange}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        style={{ width: '100%', boxSizing: 'border-box', border: `1px solid ${error ? 'var(--state-crit)' : 'var(--hairline)'}`, borderRadius: 'var(--radius-md)', padding: '9px 12px', font: `400 13px ${mono ? 'var(--font-mono)' : 'var(--font-ui)'}`, color: 'var(--ink)', background: disabled ? 'var(--surface-sunken)' : 'var(--surface)', opacity: disabled ? 'var(--opacity-disabled)' : 1, outline: 'none' }}
        onFocus={(e) => { e.target.style.outline = 'var(--focus-outline)'; e.target.style.outlineOffset = 'var(--focus-offset)'; }}
        onBlur={(e) => { e.target.style.outline = 'none'; }} />
      {error ? <span style={{ display: 'block', fontSize: 11.5, color: 'var(--state-crit)', marginTop: 4 }}>▲ {error}</span>
        : hint ? <span style={{ display: 'block', fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>{hint}</span> : null}
    </label>
  );
}
