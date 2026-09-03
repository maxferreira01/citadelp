import React, { useState } from 'react';
export function Button({ variant = 'primary', size = 'md', disabled = false, block = false, type = 'button', onClick, children, style }) {
  const [hover, setHover] = useState(false);
  const [press, setPress] = useState(false);
  const sizes = { sm: { padding: '5px 11px', fontSize: 12 }, md: { padding: '8px 14px', fontSize: 13 }, lg: { padding: '11px 16px', fontSize: 13.5 } };
  const v = {
    primary: { background: press ? 'var(--action-press)' : hover ? 'var(--action-hover)' : 'var(--action)', color: '#fff', border: '1px solid transparent' },
    secondary: { background: hover ? 'var(--selection)' : 'var(--surface)', color: 'var(--action)', border: '1px solid var(--action)' },
    ghost: { background: hover ? 'var(--selection)' : 'transparent', color: 'var(--action)', border: '1px solid transparent' },
    danger: { background: press ? '#8E2E1E' : hover ? '#9E3322' : 'var(--state-crit)', color: '#fff', border: '1px solid transparent' },
  }[variant];
  return (
    <button type={type} disabled={disabled} onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => { setHover(false); setPress(false); }}
      onMouseDown={() => setPress(true)} onMouseUp={() => setPress(false)}
      style={{ fontFamily: 'var(--font-ui)', fontWeight: 600, borderRadius: 'var(--radius-md)', cursor: disabled ? 'not-allowed' : 'pointer', display: block ? 'flex' : 'inline-flex', width: block ? '100%' : undefined, alignItems: 'center', justifyContent: 'center', gap: 8, transition: 'background var(--motion-fast) var(--ease)', opacity: disabled ? 'var(--opacity-disabled)' : 1, ...sizes[size], ...v, ...style }}>
      {children}
    </button>
  );
}
