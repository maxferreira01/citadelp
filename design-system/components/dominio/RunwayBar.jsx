import React from 'react';
export function RunwayBar({ usage, opLimit, techLimit, label, caption, days, confidence, state = 'ok', nocollect = false, height = 12, style }) {
  const max = techLimit || opLimit || usage;
  const pct = (v) => Math.max(0, Math.min(100, (v / max) * 100));
  const stateColor = { ok: 'var(--state-ok)', warn: 'var(--state-warn)', crit: 'var(--state-crit)', emergency: 'var(--state-emergency)', stale: 'var(--state-stale)', nocollect: 'var(--state-nocollect)' }[state] || 'var(--state-ok)';
  return (
    <div style={{ fontFamily: 'var(--font-ui)', ...style }}>
      {(label || days) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5, gap: 12 }}>
          {label && <span style={{ fontSize: 12.5, color: 'var(--ink)', minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</span>}
          {days && <span style={{ font: '600 11.5px var(--font-mono)', color: stateColor, whiteSpace: 'nowrap' }}>{days}{confidence != null && <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> · {confidence}</span>}</span>}
        </div>
      )}
      <svg width="100%" height={height + 8} style={{ display: 'block' }} role="img" aria-label={caption || label}>
        <rect x="0" y="4" width="100%" height={height} rx={height / 2} fill="var(--cap-available)" />
        {nocollect
          ? <rect x="0" y="4" width="30%" height={height} rx={height / 2} fill="none" stroke="var(--state-nocollect)" strokeDasharray="3 3" />
          : <rect x="0" y="4" width={`${pct(usage)}%`} height={height} rx={height / 2} fill="var(--cap-consumed)" />}
        {opLimit && <line x1={`${pct(opLimit)}%`} x2={`${pct(opLimit)}%`} y1="0" y2={height + 8} stroke="var(--cap-limit-op)" strokeWidth="2" strokeDasharray="3 2" />}
        {techLimit && <line x1="99.7%" x2="99.7%" y1="0" y2={height + 8} stroke="var(--cap-limit-tech)" strokeWidth="2.5" />}
      </svg>
      {caption && <div style={{ display: 'flex', justifyContent: 'space-between', font: '400 10.5px var(--font-mono)', color: 'var(--text-muted)', marginTop: 3 }}>{caption}</div>}
    </div>
  );
}
