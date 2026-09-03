import React from 'react';
export function TrajectoryChart({ history = [], projection = [], opLimit, techLimit, max, yMin, width = 800, height = 210, todayLabel = 'hoje', satLabel, satIndex, xLabels = [], events = [], dark = false, ariaText, style }) {
  const M = max || (techLimit ? techLimit * 1.08 : Math.max(...history, ...projection) * 1.15);
  const m0 = yMin != null ? yMin : Math.max(0, Math.min(...history, ...(projection.length ? projection : history)) * 0.9);
  const n = history.length + projection.length - 1;
  const px = 34, pr = 44, pb = 26, pt = 14;
  const iw = width - px - pr, ih = height - pt - pb;
  const X = (i) => px + (i / Math.max(1, n)) * iw;
  const Y = (v) => pt + ih - ((v - m0) / (M - m0)) * ih;
  const ti = history.length - 1;
  const ink = dark ? '#E7ECF3' : 'var(--cap-limit-tech)';
  const mut = dark ? '#7A8FA3' : 'var(--text-muted)';
  const line = dark ? '#7FC7E8' : 'var(--cap-consumed)';
  const amber = dark ? '#E0A34E' : 'var(--cap-limit-op)';
  const histPts = history.map((v, i) => `${X(i)},${Y(v)}`).join(' ');
  const projPts = projection.map((v, i) => `${X(ti + i)},${Y(v)}`).join(' ');
  const last = projection.length ? projection[projection.length - 1] : history[ti];
  const spread = (M - m0) * 0.08;
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} fontFamily="var(--font-mono)" role="img" aria-label={ariaText} style={{ display: 'block', ...style }}>
      {techLimit && <><line x1={px} y1={Y(techLimit)} x2={width - pr} y2={Y(techLimit)} stroke={ink} strokeWidth="1.3" /><text x={width - pr + 4} y={Y(techLimit) + 3} fontSize="9.5" fill={ink}>{techLimit}</text></>}
      {opLimit && <><line x1={px} y1={Y(opLimit)} x2={width - pr} y2={Y(opLimit)} stroke={amber} strokeWidth="1" strokeDasharray="5 4" /><text x={width - pr + 4} y={Y(opLimit) + 3} fontSize="9.5" fill={amber}>{opLimit}</text></>}
      <line x1={px} y1={pt + ih} x2={width - pr} y2={pt + ih} stroke={dark ? '#1D3448' : 'var(--hairline)'} />
      {projection.length > 1 && <polygon points={`${X(ti)},${Y(history[ti])} ${X(n)},${Y(last + spread)} ${X(n)},${Y(Math.max(0, last - spread))}`} fill={line} opacity=".13" />}
      <polyline points={histPts} fill="none" stroke={line} strokeWidth="2.2" />
      {projection.length > 1 && <polyline points={projPts} fill="none" stroke={line} strokeWidth="1.5" strokeDasharray="6 4" />}
      <line x1={X(ti)} y1={pt - 4} x2={X(ti)} y2={pt + ih} stroke={ink} strokeWidth="1.5" />
      <text x={X(ti) + 5} y={pt - 2} fontSize="10" fill={ink}>{todayLabel}</text>
      {satIndex != null && <>
        <circle cx={X(satIndex)} cy={opLimit ? Y(opLimit) : Y(last)} r="4.5" fill={amber} />
        <line x1={X(satIndex)} y1={opLimit ? Y(opLimit) : Y(last)} x2={X(satIndex)} y2={pt + ih} stroke={amber} strokeDasharray="2 3" />
        {satLabel && <text x={X(satIndex) + 8} y={(opLimit ? Y(opLimit) : Y(last)) - 6} fontSize="10" fill={amber}>{satLabel}</text>}
      </>}
      {events.map((ev, i) => <g key={i}><path d={`M${X(ev.index)} ${pt + ih - 7} l5 5 l-5 5 l-5 -5 z`} fill={ink} /><text x={X(ev.index) + 9} y={pt + ih + 1} fontSize="9" fill={mut}>{ev.label}</text></g>)}
      {xLabels.map((l, i) => <text key={i} x={px + (i / Math.max(1, xLabels.length - 1)) * iw} y={height - 8} fontSize="9.5" fill={mut}>{l}</text>)}
    </svg>
  );
}
