import React from 'react';
export const STATUS_STATES = {
  info: { glyph: 'ℹ', color: 'var(--state-info)', bg: 'var(--state-info-bg)', border: 'solid', pt: 'informativo', en: 'info' },
  ok: { glyph: '●', color: 'var(--state-ok)', bg: 'var(--state-ok-bg)', border: 'solid', pt: 'saudável', en: 'healthy' },
  warn: { glyph: '◆', color: 'var(--state-warn)', bg: 'var(--state-warn-bg)', border: 'solid', pt: 'atenção', en: 'watch' },
  crit: { glyph: '▲', color: 'var(--state-crit)', bg: 'var(--state-crit-bg)', border: 'solid', pt: 'crítico', en: 'critical' },
  emergency: { glyph: '▲▲', color: 'var(--state-emergency)', bg: 'var(--state-emergency-bg)', border: 'solid', pt: 'emergência', en: 'emergency' },
  unknown: { glyph: '?', color: 'var(--state-unknown)', bg: 'var(--state-unknown-bg)', border: 'dashed', pt: 'desconhecido', en: 'unknown' },
  unavailable: { glyph: '⊘', color: 'var(--state-unavailable)', bg: 'var(--state-unavailable-bg)', border: 'solid', pt: 'indisponível', en: 'unavailable' },
  nocollect: { glyph: '◌', color: 'var(--state-nocollect)', bg: 'var(--state-nocollect-bg)', border: 'dotted', pt: 'sem coleta', en: 'no data' },
  stale: { glyph: '◐', color: 'var(--state-stale)', bg: 'var(--state-stale-bg)', border: 'dashed', pt: 'desatualizado', en: 'stale' },
  divergent: { glyph: '≠', color: 'var(--state-divergent)', bg: 'var(--state-divergent-bg)', border: 'dashed', pt: 'divergente', en: 'divergent' },
};
export function StatusBadge({ state = 'info', label, lang = 'pt', filled = false, glyphOnly = false, style }) {
  const s = STATUS_STATES[state] || STATUS_STATES.info;
  const text = label != null ? label : s[lang] || s.pt;
  if (glyphOnly) return <span title={text} style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: s.color, ...style }}>{s.glyph}</span>;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, border: `1px ${s.border} ${s.color}`, background: filled ? s.bg : 'transparent', color: s.color, borderRadius: 'var(--radius-sm)', padding: '2px 8px', font: '500 11px var(--font-mono)', letterSpacing: '.04em', whiteSpace: 'nowrap', ...style }}>
      <span aria-hidden="true">{s.glyph}</span>{text}
    </span>
  );
}
