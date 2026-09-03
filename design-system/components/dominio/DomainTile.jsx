import React, { useState } from 'react';
import { STATUS_STATES } from '../core/StatusBadge.jsx';
export function DomainTile({ code, state = 'ok', days, note, usagePct, env, selected = false, dark = false, onClick, style }) {
  const s = STATUS_STATES[state] || STATUS_STATES.ok;
  const [hover, setHover] = useState(false);
  const bd = dark ? '#1D3448' : 'var(--hairline)';
  return (
    <button onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{ textAlign: 'left', border: `1px ${state === 'nocollect' ? 'dashed' : 'solid'} ${selected ? 'var(--action)' : bd}`, borderRadius: 'var(--radius-md)', padding: '11px 12px', background: selected ? 'var(--selection)' : hover ? (dark ? 'rgba(255,255,255,.05)' : 'var(--bg-page)') : dark ? 'rgba(255,255,255,.025)' : 'var(--surface)', cursor: onClick ? 'pointer' : 'default', display: 'flex', flexDirection: 'column', gap: 6, fontFamily: 'var(--font-ui)', width: '100%', transition: 'background var(--motion-fast) var(--ease)', ...style }}>
      <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <b style={{ font: '700 12px var(--font-mono)', color: dark ? '#E7ECF3' : 'var(--ink)' }}>{code}</b>
        <span style={{ font: '500 10.5px var(--font-mono)', color: s.color }}>{s.glyph}{env && <span style={{ color: dark ? '#7A8FA3' : 'var(--text-faint)' }}> {env}</span>}</span>
      </span>
      {days && <span style={{ font: '700 15px var(--font-mono)', color: s.color }}>{days}</span>}
      {usagePct != null && (
        <svg width="100%" height="4" style={{ display: 'block' }}><rect width="100%" height="4" rx="2" fill={dark ? '#16304A' : 'var(--cap-available)'} /><rect width={`${usagePct}%`} height="4" rx="2" fill={s.color} /></svg>
      )}
      {note && <span style={{ fontSize: 10.5, color: dark ? '#7A8FA3' : 'var(--text-muted)', lineHeight: 1.35 }}>{note}</span>}
    </button>
  );
}
