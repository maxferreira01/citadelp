import React from 'react';
export function DataTable({ columns = [], rows = [], density = 'comfortable', selectedId, onRowClick, style }) {
  const rowH = density === 'compact' ? 'var(--row-compact)' : 'var(--row-comfortable)';
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--surface)', border: '1px solid var(--hairline)', fontFamily: 'var(--font-ui)', fontSize: density === 'compact' ? 12 : 12.5, ...style }}>
      <thead><tr>
        {columns.map((c) => (
          <th key={c.key} style={{ font: '600 10px var(--font-mono)', letterSpacing: '.11em', textTransform: 'uppercase', color: 'var(--text-muted)', textAlign: c.align || 'left', padding: '8px 12px', borderBottom: '1.5px solid var(--hairline-strong)', whiteSpace: 'nowrap', width: c.width }}>{c.label}</th>
        ))}
      </tr></thead>
      <tbody>
        {rows.map((r) => {
          const sel = r.id === selectedId;
          return (
            <tr key={r.id} onClick={onRowClick ? () => onRowClick(r.id) : undefined}
              style={{ height: rowH, cursor: onRowClick ? 'pointer' : 'default', background: sel ? 'var(--selection)' : 'transparent', boxShadow: sel ? 'inset 2px 0 var(--action)' : 'none' }}>
              {columns.map((c) => (
                <td key={c.key} style={{ padding: '0 12px', borderBottom: '1px solid var(--hairline)', textAlign: c.align || 'left', fontFamily: c.mono ? 'var(--font-mono)' : 'inherit', fontFeatureSettings: c.mono ? '"tnum"' : undefined, fontSize: c.mono ? '.96em' : 'inherit', whiteSpace: 'nowrap', color: 'var(--ink)' }}>{r[c.key]}</td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
