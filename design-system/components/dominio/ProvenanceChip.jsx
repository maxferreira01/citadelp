import React from 'react';
const METHODS = {
  OBS: { color: 'var(--dq-observed)', pt: 'observado', en: 'observed' },
  CALC: { color: 'var(--dq-calculated)', pt: 'calculado', en: 'calculated' },
  EST: { color: 'var(--dq-estimated)', pt: 'estimado', en: 'estimated' },
  MAN: { color: 'var(--dq-manual)', pt: 'manual', en: 'manual' },
};
export function ProvenanceChip({ method = 'OBS', source, age, confidence, stale = false, lang = 'pt', style }) {
  const m = METHODS[method] || METHODS.OBS;
  return (
    <span title={`${m[lang]}${source ? ' · ' + source : ''}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 7, border: `1px ${stale ? 'dashed var(--dq-stale)' : 'solid var(--hairline)'}`, background: 'var(--surface)', borderRadius: 'var(--radius-sm)', padding: '3px 9px', font: '400 11px var(--font-mono)', color: 'var(--text-muted)', whiteSpace: 'nowrap', ...style }}>
      <b style={{ fontWeight: 700, letterSpacing: '.08em', color: stale ? 'var(--dq-stale)' : m.color }}>{stale ? '◐' : method}</b>
      {source}{age && <span>· {age}</span>}{confidence != null && <span style={{ color: 'var(--ink)' }}>· {confidence}</span>}
    </span>
  );
}
export function ProvenancePanel({ rows = [], title = 'procedência', style }) {
  return (
    <div style={{ fontFamily: 'var(--font-ui)', ...style }}>
      <div style={{ font: '600 10.5px var(--font-ui)', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{title}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '6px 10px', fontSize: 11.5, marginTop: 9 }}>
        {rows.map(([k, v], i) => <React.Fragment key={i}><span style={{ color: 'var(--text-muted)' }}>{k}</span><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink)', textAlign: 'right' }}>{v}</span></React.Fragment>)}
      </div>
    </div>
  );
}
