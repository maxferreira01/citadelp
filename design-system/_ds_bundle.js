/* @ds-bundle: {"format":4,"namespace":"CIDADELADesignSystem_99bf85","components":[{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"DataTable","sourcePath":"components/core/DataTable.jsx"},{"name":"Modal","sourcePath":"components/core/Modal.jsx"},{"name":"Select","sourcePath":"components/core/Select.jsx"},{"name":"STATUS_STATES","sourcePath":"components/core/StatusBadge.jsx"},{"name":"StatusBadge","sourcePath":"components/core/StatusBadge.jsx"},{"name":"Tabs","sourcePath":"components/core/Tabs.jsx"},{"name":"TextField","sourcePath":"components/core/TextField.jsx"},{"name":"Toast","sourcePath":"components/core/Toast.jsx"},{"name":"DomainTile","sourcePath":"components/dominio/DomainTile.jsx"},{"name":"ProvenanceChip","sourcePath":"components/dominio/ProvenanceChip.jsx"},{"name":"ProvenancePanel","sourcePath":"components/dominio/ProvenanceChip.jsx"},{"name":"RunwayBar","sourcePath":"components/dominio/RunwayBar.jsx"},{"name":"TrajectoryChart","sourcePath":"components/dominio/TrajectoryChart.jsx"}],"sourceHashes":{"components/core/Button.jsx":"0cd8388e487e","components/core/DataTable.jsx":"d62ddaa31937","components/core/Modal.jsx":"980b51384049","components/core/Select.jsx":"4d4cfd018de0","components/core/StatusBadge.jsx":"c83453630c82","components/core/Tabs.jsx":"bd467091e111","components/core/TextField.jsx":"e36b8f82793b","components/core/Toast.jsx":"ed5f543226c5","components/dominio/DomainTile.jsx":"cd09a1950850","components/dominio/ProvenanceChip.jsx":"88abd53bdd12","components/dominio/RunwayBar.jsx":"ba60e32fedb2","components/dominio/TrajectoryChart.jsx":"c56b37beb0dc","ui_kits/citadel/Login.jsx":"defb035f142d","ui_kits/citadel/TresOlhos.jsx":"84ff680d1b94","ui_kits/citadel/doc-page.js":"371bab66f42d","ui_kits/citadel/i18n.jsx":"01cf09792dec"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.CIDADELADesignSystem_99bf85 = window.CIDADELADesignSystem_99bf85 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Button.jsx
try { (() => {
const {
  useState
} = React;
function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  block = false,
  type = 'button',
  onClick,
  children,
  style
}) {
  const [hover, setHover] = useState(false);
  const [press, setPress] = useState(false);
  const sizes = {
    sm: {
      padding: '5px 11px',
      fontSize: 12
    },
    md: {
      padding: '8px 14px',
      fontSize: 13
    },
    lg: {
      padding: '11px 16px',
      fontSize: 13.5
    }
  };
  const v = {
    primary: {
      background: press ? 'var(--action-press)' : hover ? 'var(--action-hover)' : 'var(--action)',
      color: '#fff',
      border: '1px solid transparent'
    },
    secondary: {
      background: hover ? 'var(--selection)' : 'var(--surface)',
      color: 'var(--action)',
      border: '1px solid var(--action)'
    },
    ghost: {
      background: hover ? 'var(--selection)' : 'transparent',
      color: 'var(--action)',
      border: '1px solid transparent'
    },
    danger: {
      background: press ? '#8E2E1E' : hover ? '#9E3322' : 'var(--state-crit)',
      color: '#fff',
      border: '1px solid transparent'
    }
  }[variant];
  return /*#__PURE__*/React.createElement("button", {
    type: type,
    disabled: disabled,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => {
      setHover(false);
      setPress(false);
    },
    onMouseDown: () => setPress(true),
    onMouseUp: () => setPress(false),
    style: {
      fontFamily: 'var(--font-ui)',
      fontWeight: 600,
      borderRadius: 'var(--radius-md)',
      cursor: disabled ? 'not-allowed' : 'pointer',
      display: block ? 'flex' : 'inline-flex',
      width: block ? '100%' : undefined,
      alignItems: 'center',
      justifyContent: 'center',
      gap: 8,
      transition: 'background var(--motion-fast) var(--ease)',
      opacity: disabled ? 'var(--opacity-disabled)' : 1,
      ...sizes[size],
      ...v,
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/DataTable.jsx
try { (() => {
function DataTable({
  columns = [],
  rows = [],
  density = 'comfortable',
  selectedId,
  onRowClick,
  style
}) {
  const rowH = density === 'compact' ? 'var(--row-compact)' : 'var(--row-comfortable)';
  return /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse',
      background: 'var(--surface)',
      border: '1px solid var(--hairline)',
      fontFamily: 'var(--font-ui)',
      fontSize: density === 'compact' ? 12 : 12.5,
      ...style
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, columns.map(c => /*#__PURE__*/React.createElement("th", {
    key: c.key,
    style: {
      font: '600 10px var(--font-mono)',
      letterSpacing: '.11em',
      textTransform: 'uppercase',
      color: 'var(--text-muted)',
      textAlign: c.align || 'left',
      padding: '8px 12px',
      borderBottom: '1.5px solid var(--hairline-strong)',
      whiteSpace: 'nowrap',
      width: c.width
    }
  }, c.label)))), /*#__PURE__*/React.createElement("tbody", null, rows.map(r => {
    const sel = r.id === selectedId;
    return /*#__PURE__*/React.createElement("tr", {
      key: r.id,
      onClick: onRowClick ? () => onRowClick(r.id) : undefined,
      style: {
        height: rowH,
        cursor: onRowClick ? 'pointer' : 'default',
        background: sel ? 'var(--selection)' : 'transparent',
        boxShadow: sel ? 'inset 2px 0 var(--action)' : 'none'
      }
    }, columns.map(c => /*#__PURE__*/React.createElement("td", {
      key: c.key,
      style: {
        padding: '0 12px',
        borderBottom: '1px solid var(--hairline)',
        textAlign: c.align || 'left',
        fontFamily: c.mono ? 'var(--font-mono)' : 'inherit',
        fontFeatureSettings: c.mono ? '"tnum"' : undefined,
        fontSize: c.mono ? '.96em' : 'inherit',
        whiteSpace: 'nowrap',
        color: 'var(--ink)'
      }
    }, r[c.key])));
  })));
}
Object.assign(__ds_scope, { DataTable });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/DataTable.jsx", error: String((e && e.message) || e) }); }

// components/core/Modal.jsx
try { (() => {
function Modal({
  open = true,
  title,
  children,
  footer,
  onClose,
  width = 560,
  inline = false,
  style
}) {
  if (!open) return null;
  const panel = /*#__PURE__*/React.createElement("div", {
    role: "dialog",
    "aria-modal": !inline,
    "aria-label": title,
    style: {
      width,
      maxWidth: '92%',
      background: 'var(--surface)',
      border: '1px solid var(--hairline)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-overlay)',
      overflow: 'hidden',
      fontFamily: 'var(--font-ui)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '14px 18px',
      borderBottom: '1px solid var(--hairline)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '700 15px var(--font-brand)',
      color: 'var(--ink)'
    }
  }, title), onClose && /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    "aria-label": "Fechar",
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--text-faint)',
      cursor: 'pointer',
      fontSize: 15
    }
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '16px 18px',
      fontSize: 13,
      color: 'var(--ink)',
      lineHeight: 1.55
    }
  }, children), footer && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'flex-end',
      gap: 8,
      padding: '12px 18px',
      borderTop: '1px solid var(--hairline)',
      background: 'var(--bg-page)'
    }
  }, footer));
  if (inline) return panel;
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(4,28,43,.45)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation()
  }, panel));
}
Object.assign(__ds_scope, { Modal });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Modal.jsx", error: String((e && e.message) || e) }); }

// components/core/Select.jsx
try { (() => {
function Select({
  label,
  value,
  options = [],
  disabled = false,
  onChange,
  style
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'block',
      fontFamily: 'var(--font-ui)',
      ...style
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      font: '600 10.5px var(--font-ui)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      color: 'var(--text-muted)',
      marginBottom: 5
    }
  }, label), /*#__PURE__*/React.createElement("select", {
    value: value,
    disabled: disabled,
    onChange: onChange ? e => onChange(e.target.value) : undefined,
    style: {
      width: '100%',
      boxSizing: 'border-box',
      border: '1px solid var(--hairline)',
      borderRadius: 'var(--radius-md)',
      padding: '8px 10px',
      font: '400 13px var(--font-ui)',
      color: 'var(--ink)',
      background: 'var(--surface)',
      opacity: disabled ? 'var(--opacity-disabled)' : 1
    },
    onFocus: e => {
      e.target.style.outline = 'var(--focus-outline)';
      e.target.style.outlineOffset = 'var(--focus-offset)';
    },
    onBlur: e => {
      e.target.style.outline = 'none';
    }
  }, options.map(o => /*#__PURE__*/React.createElement("option", {
    key: o.value,
    value: o.value
  }, o.label))));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Select.jsx", error: String((e && e.message) || e) }); }

// components/core/StatusBadge.jsx
try { (() => {
const STATUS_STATES = {
  info: {
    glyph: 'ℹ',
    color: 'var(--state-info)',
    bg: 'var(--state-info-bg)',
    border: 'solid',
    pt: 'informativo',
    en: 'info'
  },
  ok: {
    glyph: '●',
    color: 'var(--state-ok)',
    bg: 'var(--state-ok-bg)',
    border: 'solid',
    pt: 'saudável',
    en: 'healthy'
  },
  warn: {
    glyph: '◆',
    color: 'var(--state-warn)',
    bg: 'var(--state-warn-bg)',
    border: 'solid',
    pt: 'atenção',
    en: 'watch'
  },
  crit: {
    glyph: '▲',
    color: 'var(--state-crit)',
    bg: 'var(--state-crit-bg)',
    border: 'solid',
    pt: 'crítico',
    en: 'critical'
  },
  emergency: {
    glyph: '▲▲',
    color: 'var(--state-emergency)',
    bg: 'var(--state-emergency-bg)',
    border: 'solid',
    pt: 'emergência',
    en: 'emergency'
  },
  unknown: {
    glyph: '?',
    color: 'var(--state-unknown)',
    bg: 'var(--state-unknown-bg)',
    border: 'dashed',
    pt: 'desconhecido',
    en: 'unknown'
  },
  unavailable: {
    glyph: '⊘',
    color: 'var(--state-unavailable)',
    bg: 'var(--state-unavailable-bg)',
    border: 'solid',
    pt: 'indisponível',
    en: 'unavailable'
  },
  nocollect: {
    glyph: '◌',
    color: 'var(--state-nocollect)',
    bg: 'var(--state-nocollect-bg)',
    border: 'dotted',
    pt: 'sem coleta',
    en: 'no data'
  },
  stale: {
    glyph: '◐',
    color: 'var(--state-stale)',
    bg: 'var(--state-stale-bg)',
    border: 'dashed',
    pt: 'desatualizado',
    en: 'stale'
  },
  divergent: {
    glyph: '≠',
    color: 'var(--state-divergent)',
    bg: 'var(--state-divergent-bg)',
    border: 'dashed',
    pt: 'divergente',
    en: 'divergent'
  }
};
function StatusBadge({
  state = 'info',
  label,
  lang = 'pt',
  filled = false,
  glyphOnly = false,
  style
}) {
  const s = STATUS_STATES[state] || STATUS_STATES.info;
  const text = label != null ? label : s[lang] || s.pt;
  if (glyphOnly) return /*#__PURE__*/React.createElement("span", {
    title: text,
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
      color: s.color,
      ...style
    }
  }, s.glyph);
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      border: `1px ${s.border} ${s.color}`,
      background: filled ? s.bg : 'transparent',
      color: s.color,
      borderRadius: 'var(--radius-sm)',
      padding: '2px 8px',
      font: '500 11px var(--font-mono)',
      letterSpacing: '.04em',
      whiteSpace: 'nowrap',
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true"
  }, s.glyph), text);
}
Object.assign(__ds_scope, { STATUS_STATES, StatusBadge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/StatusBadge.jsx", error: String((e && e.message) || e) }); }

// components/core/Tabs.jsx
try { (() => {
function Tabs({
  items = [],
  active,
  onChange,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: 'flex',
      gap: 20,
      borderBottom: '1px solid var(--hairline)',
      fontFamily: 'var(--font-ui)',
      fontSize: 12.5,
      ...style
    }
  }, items.map(it => {
    const on = it.id === active;
    return /*#__PURE__*/React.createElement("button", {
      key: it.id,
      role: "tab",
      "aria-selected": on,
      onClick: onChange ? () => onChange(it.id) : undefined,
      style: {
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: '0 0 8px',
        fontFamily: 'inherit',
        fontSize: 'inherit',
        fontWeight: on ? 600 : 400,
        color: on ? 'var(--ink)' : 'var(--text-muted)',
        boxShadow: on ? 'inset 0 -2px var(--action)' : 'none'
      }
    }, it.label, it.count != null && /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 10.5,
        marginLeft: 6,
        color: on ? 'var(--action)' : 'var(--text-faint)'
      }
    }, it.count));
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tabs.jsx", error: String((e && e.message) || e) }); }

// components/core/TextField.jsx
try { (() => {
function TextField({
  label,
  value,
  placeholder,
  hint,
  error,
  mono = false,
  disabled = false,
  onChange,
  type = 'text',
  style
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'block',
      fontFamily: 'var(--font-ui)',
      ...style
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      font: '600 10.5px var(--font-ui)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      color: 'var(--text-muted)',
      marginBottom: 5
    }
  }, label), /*#__PURE__*/React.createElement("input", {
    type: type,
    value: value,
    placeholder: placeholder,
    disabled: disabled,
    readOnly: !onChange,
    onChange: onChange ? e => onChange(e.target.value) : undefined,
    style: {
      width: '100%',
      boxSizing: 'border-box',
      border: `1px solid ${error ? 'var(--state-crit)' : 'var(--hairline)'}`,
      borderRadius: 'var(--radius-md)',
      padding: '9px 12px',
      font: `400 13px ${mono ? 'var(--font-mono)' : 'var(--font-ui)'}`,
      color: 'var(--ink)',
      background: disabled ? 'var(--surface-sunken)' : 'var(--surface)',
      opacity: disabled ? 'var(--opacity-disabled)' : 1,
      outline: 'none'
    },
    onFocus: e => {
      e.target.style.outline = 'var(--focus-outline)';
      e.target.style.outlineOffset = 'var(--focus-offset)';
    },
    onBlur: e => {
      e.target.style.outline = 'none';
    }
  }), error ? /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 11.5,
      color: 'var(--state-crit)',
      marginTop: 4
    }
  }, "\u25B2 ", error) : hint ? /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 11.5,
      color: 'var(--text-muted)',
      marginTop: 4
    }
  }, hint) : null);
}
Object.assign(__ds_scope, { TextField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/TextField.jsx", error: String((e && e.message) || e) }); }

// components/core/Toast.jsx
try { (() => {
function Toast({
  kind = 'info',
  title,
  detail,
  actionLabel,
  onAction,
  onClose,
  style
}) {
  const s = __ds_scope.STATUS_STATES[kind] || __ds_scope.STATUS_STATES.info;
  return /*#__PURE__*/React.createElement("div", {
    role: "status",
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 10,
      background: 'var(--surface)',
      border: '1px solid var(--hairline)',
      borderLeft: `3px solid ${s.color}`,
      borderRadius: 'var(--radius-md)',
      boxShadow: 'var(--shadow-2)',
      padding: '10px 14px',
      maxWidth: 420,
      fontFamily: 'var(--font-ui)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      fontFamily: 'var(--font-mono)',
      color: s.color,
      fontSize: 13,
      lineHeight: '18px'
    }
  }, s.glyph), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12.5,
      fontWeight: 600,
      color: 'var(--ink)'
    }
  }, title), detail && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11.5,
      color: 'var(--text-muted)',
      marginTop: 2,
      lineHeight: 1.45
    }
  }, detail), actionLabel && /*#__PURE__*/React.createElement("button", {
    onClick: onAction,
    style: {
      background: 'none',
      border: 'none',
      padding: 0,
      marginTop: 6,
      font: '600 11.5px var(--font-ui)',
      color: 'var(--link)',
      cursor: 'pointer'
    }
  }, actionLabel, " \u2192")), onClose && /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    "aria-label": "Fechar",
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--text-faint)',
      cursor: 'pointer',
      fontSize: 14,
      lineHeight: '18px',
      padding: 0
    }
  }, "\u2715"));
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Toast.jsx", error: String((e && e.message) || e) }); }

// components/dominio/DomainTile.jsx
try { (() => {
const {
  useState
} = React;
function DomainTile({
  code,
  state = 'ok',
  days,
  note,
  usagePct,
  env,
  selected = false,
  dark = false,
  onClick,
  style
}) {
  const s = __ds_scope.STATUS_STATES[state] || __ds_scope.STATUS_STATES.ok;
  const [hover, setHover] = useState(false);
  const bd = dark ? '#1D3448' : 'var(--hairline)';
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      textAlign: 'left',
      border: `1px ${state === 'nocollect' ? 'dashed' : 'solid'} ${selected ? 'var(--action)' : bd}`,
      borderRadius: 'var(--radius-md)',
      padding: '11px 12px',
      background: selected ? 'var(--selection)' : hover ? dark ? 'rgba(255,255,255,.05)' : 'var(--bg-page)' : dark ? 'rgba(255,255,255,.025)' : 'var(--surface)',
      cursor: onClick ? 'pointer' : 'default',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      fontFamily: 'var(--font-ui)',
      width: '100%',
      transition: 'background var(--motion-fast) var(--ease)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline'
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      font: '700 12px var(--font-mono)',
      color: dark ? '#E7ECF3' : 'var(--ink)'
    }
  }, code), /*#__PURE__*/React.createElement("span", {
    style: {
      font: '500 10.5px var(--font-mono)',
      color: s.color
    }
  }, s.glyph, env && /*#__PURE__*/React.createElement("span", {
    style: {
      color: dark ? '#7A8FA3' : 'var(--text-faint)'
    }
  }, " ", env))), days && /*#__PURE__*/React.createElement("span", {
    style: {
      font: '700 15px var(--font-mono)',
      color: s.color
    }
  }, days), usagePct != null && /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    height: "4",
    style: {
      display: 'block'
    }
  }, /*#__PURE__*/React.createElement("rect", {
    width: "100%",
    height: "4",
    rx: "2",
    fill: dark ? '#16304A' : 'var(--cap-available)'
  }), /*#__PURE__*/React.createElement("rect", {
    width: `${usagePct}%`,
    height: "4",
    rx: "2",
    fill: s.color
  })), note && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10.5,
      color: dark ? '#7A8FA3' : 'var(--text-muted)',
      lineHeight: 1.35
    }
  }, note));
}
Object.assign(__ds_scope, { DomainTile });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/dominio/DomainTile.jsx", error: String((e && e.message) || e) }); }

// components/dominio/ProvenanceChip.jsx
try { (() => {
const METHODS = {
  OBS: {
    color: 'var(--dq-observed)',
    pt: 'observado',
    en: 'observed'
  },
  CALC: {
    color: 'var(--dq-calculated)',
    pt: 'calculado',
    en: 'calculated'
  },
  EST: {
    color: 'var(--dq-estimated)',
    pt: 'estimado',
    en: 'estimated'
  },
  MAN: {
    color: 'var(--dq-manual)',
    pt: 'manual',
    en: 'manual'
  }
};
function ProvenanceChip({
  method = 'OBS',
  source,
  age,
  confidence,
  stale = false,
  lang = 'pt',
  style
}) {
  const m = METHODS[method] || METHODS.OBS;
  return /*#__PURE__*/React.createElement("span", {
    title: `${m[lang]}${source ? ' · ' + source : ''}`,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 7,
      border: `1px ${stale ? 'dashed var(--dq-stale)' : 'solid var(--hairline)'}`,
      background: 'var(--surface)',
      borderRadius: 'var(--radius-sm)',
      padding: '3px 9px',
      font: '400 11px var(--font-mono)',
      color: 'var(--text-muted)',
      whiteSpace: 'nowrap',
      ...style
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      fontWeight: 700,
      letterSpacing: '.08em',
      color: stale ? 'var(--dq-stale)' : m.color
    }
  }, stale ? '◐' : method), source, age && /*#__PURE__*/React.createElement("span", null, "\xB7 ", age), confidence != null && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink)'
    }
  }, "\xB7 ", confidence));
}
function ProvenancePanel({
  rows = [],
  title = 'procedência',
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-ui)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '600 10.5px var(--font-ui)',
      letterSpacing: 'var(--tracking-caps)',
      textTransform: 'uppercase',
      color: 'var(--text-muted)'
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr auto',
      gap: '6px 10px',
      fontSize: 11.5,
      marginTop: 9
    }
  }, rows.map(([k, v], i) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: i
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)'
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      color: 'var(--ink)',
      textAlign: 'right'
    }
  }, v)))));
}
Object.assign(__ds_scope, { ProvenanceChip, ProvenancePanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/dominio/ProvenanceChip.jsx", error: String((e && e.message) || e) }); }

// components/dominio/RunwayBar.jsx
try { (() => {
function RunwayBar({
  usage,
  opLimit,
  techLimit,
  label,
  caption,
  days,
  confidence,
  state = 'ok',
  nocollect = false,
  height = 12,
  style
}) {
  const max = techLimit || opLimit || usage;
  const pct = v => Math.max(0, Math.min(100, v / max * 100));
  const stateColor = {
    ok: 'var(--state-ok)',
    warn: 'var(--state-warn)',
    crit: 'var(--state-crit)',
    emergency: 'var(--state-emergency)',
    stale: 'var(--state-stale)',
    nocollect: 'var(--state-nocollect)'
  }[state] || 'var(--state-ok)';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-ui)',
      ...style
    }
  }, (label || days) && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline',
      marginBottom: 5,
      gap: 12
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12.5,
      color: 'var(--ink)',
      minWidth: 0,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, label), days && /*#__PURE__*/React.createElement("span", {
    style: {
      font: '600 11.5px var(--font-mono)',
      color: stateColor,
      whiteSpace: 'nowrap'
    }
  }, days, confidence != null && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)',
      fontWeight: 400
    }
  }, " \xB7 ", confidence))), /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    height: height + 8,
    style: {
      display: 'block'
    },
    role: "img",
    "aria-label": caption || label
  }, /*#__PURE__*/React.createElement("rect", {
    x: "0",
    y: "4",
    width: "100%",
    height: height,
    rx: height / 2,
    fill: "var(--cap-available)"
  }), nocollect ? /*#__PURE__*/React.createElement("rect", {
    x: "0",
    y: "4",
    width: "30%",
    height: height,
    rx: height / 2,
    fill: "none",
    stroke: "var(--state-nocollect)",
    strokeDasharray: "3 3"
  }) : /*#__PURE__*/React.createElement("rect", {
    x: "0",
    y: "4",
    width: `${pct(usage)}%`,
    height: height,
    rx: height / 2,
    fill: "var(--cap-consumed)"
  }), opLimit && /*#__PURE__*/React.createElement("line", {
    x1: `${pct(opLimit)}%`,
    x2: `${pct(opLimit)}%`,
    y1: "0",
    y2: height + 8,
    stroke: "var(--cap-limit-op)",
    strokeWidth: "2",
    strokeDasharray: "3 2"
  }), techLimit && /*#__PURE__*/React.createElement("line", {
    x1: "99.7%",
    x2: "99.7%",
    y1: "0",
    y2: height + 8,
    stroke: "var(--cap-limit-tech)",
    strokeWidth: "2.5"
  })), caption && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      font: '400 10.5px var(--font-mono)',
      color: 'var(--text-muted)',
      marginTop: 3
    }
  }, caption));
}
Object.assign(__ds_scope, { RunwayBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/dominio/RunwayBar.jsx", error: String((e && e.message) || e) }); }

// components/dominio/TrajectoryChart.jsx
try { (() => {
function TrajectoryChart({
  history = [],
  projection = [],
  opLimit,
  techLimit,
  max,
  yMin,
  width = 800,
  height = 210,
  todayLabel = 'hoje',
  satLabel,
  satIndex,
  xLabels = [],
  events = [],
  dark = false,
  ariaText,
  style
}) {
  const M = max || (techLimit ? techLimit * 1.08 : Math.max(...history, ...projection) * 1.15);
  const m0 = yMin != null ? yMin : Math.max(0, Math.min(...history, ...(projection.length ? projection : history)) * 0.9);
  const n = history.length + projection.length - 1;
  const px = 34,
    pr = 44,
    pb = 26,
    pt = 14;
  const iw = width - px - pr,
    ih = height - pt - pb;
  const X = i => px + i / Math.max(1, n) * iw;
  const Y = v => pt + ih - (v - m0) / (M - m0) * ih;
  const ti = history.length - 1;
  const ink = dark ? '#E7ECF3' : 'var(--cap-limit-tech)';
  const mut = dark ? '#7A8FA3' : 'var(--text-muted)';
  const line = dark ? '#7FC7E8' : 'var(--cap-consumed)';
  const amber = dark ? '#E0A34E' : 'var(--cap-limit-op)';
  const histPts = history.map((v, i) => `${X(i)},${Y(v)}`).join(' ');
  const projPts = projection.map((v, i) => `${X(ti + i)},${Y(v)}`).join(' ');
  const last = projection.length ? projection[projection.length - 1] : history[ti];
  const spread = (M - m0) * 0.08;
  return /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    viewBox: `0 0 ${width} ${height}`,
    fontFamily: "var(--font-mono)",
    role: "img",
    "aria-label": ariaText,
    style: {
      display: 'block',
      ...style
    }
  }, techLimit && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("line", {
    x1: px,
    y1: Y(techLimit),
    x2: width - pr,
    y2: Y(techLimit),
    stroke: ink,
    strokeWidth: "1.3"
  }), /*#__PURE__*/React.createElement("text", {
    x: width - pr + 4,
    y: Y(techLimit) + 3,
    fontSize: "9.5",
    fill: ink
  }, techLimit)), opLimit && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("line", {
    x1: px,
    y1: Y(opLimit),
    x2: width - pr,
    y2: Y(opLimit),
    stroke: amber,
    strokeWidth: "1",
    strokeDasharray: "5 4"
  }), /*#__PURE__*/React.createElement("text", {
    x: width - pr + 4,
    y: Y(opLimit) + 3,
    fontSize: "9.5",
    fill: amber
  }, opLimit)), /*#__PURE__*/React.createElement("line", {
    x1: px,
    y1: pt + ih,
    x2: width - pr,
    y2: pt + ih,
    stroke: dark ? '#1D3448' : 'var(--hairline)'
  }), projection.length > 1 && /*#__PURE__*/React.createElement("polygon", {
    points: `${X(ti)},${Y(history[ti])} ${X(n)},${Y(last + spread)} ${X(n)},${Y(Math.max(0, last - spread))}`,
    fill: line,
    opacity: ".13"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: histPts,
    fill: "none",
    stroke: line,
    strokeWidth: "2.2"
  }), projection.length > 1 && /*#__PURE__*/React.createElement("polyline", {
    points: projPts,
    fill: "none",
    stroke: line,
    strokeWidth: "1.5",
    strokeDasharray: "6 4"
  }), /*#__PURE__*/React.createElement("line", {
    x1: X(ti),
    y1: pt - 4,
    x2: X(ti),
    y2: pt + ih,
    stroke: ink,
    strokeWidth: "1.5"
  }), /*#__PURE__*/React.createElement("text", {
    x: X(ti) + 5,
    y: pt - 2,
    fontSize: "10",
    fill: ink
  }, todayLabel), satIndex != null && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
    cx: X(satIndex),
    cy: opLimit ? Y(opLimit) : Y(last),
    r: "4.5",
    fill: amber
  }), /*#__PURE__*/React.createElement("line", {
    x1: X(satIndex),
    y1: opLimit ? Y(opLimit) : Y(last),
    x2: X(satIndex),
    y2: pt + ih,
    stroke: amber,
    strokeDasharray: "2 3"
  }), satLabel && /*#__PURE__*/React.createElement("text", {
    x: X(satIndex) + 8,
    y: (opLimit ? Y(opLimit) : Y(last)) - 6,
    fontSize: "10",
    fill: amber
  }, satLabel)), events.map((ev, i) => /*#__PURE__*/React.createElement("g", {
    key: i
  }, /*#__PURE__*/React.createElement("path", {
    d: `M${X(ev.index)} ${pt + ih - 7} l5 5 l-5 5 l-5 -5 z`,
    fill: ink
  }), /*#__PURE__*/React.createElement("text", {
    x: X(ev.index) + 9,
    y: pt + ih + 1,
    fontSize: "9",
    fill: mut
  }, ev.label))), xLabels.map((l, i) => /*#__PURE__*/React.createElement("text", {
    key: i,
    x: px + i / Math.max(1, xLabels.length - 1) * iw,
    y: height - 8,
    fontSize: "9.5",
    fill: mut
  }, l)));
}
Object.assign(__ds_scope, { TrajectoryChart });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/dominio/TrajectoryChart.jsx", error: String((e && e.message) || e) }); }

// ui_kits/citadel/Login.jsx
try { (() => {
// CITADEL — tela de login (base aprovada: 4b, destaques agregados — sem nomes de recurso nem valores)
// theme: 'dark' (padrão, painel NOC) | 'light'
const {
  Button,
  TextField
} = window.CIDADELADesignSystem_99bf85;
const {
  TrajectoryChart
} = window.CIDADELADesignSystem_99bf85;
function LangToggle({
  lang,
  onChange,
  dark
}) {
  const opt = l => ({
    background: lang === l ? dark ? 'rgba(255,255,255,.14)' : 'var(--selection)' : 'transparent',
    color: dark ? '#E7ECF3' : 'var(--ink)',
    border: 'none',
    cursor: 'pointer',
    font: '600 10.5px var(--font-mono)',
    letterSpacing: '.08em',
    padding: '3px 8px',
    borderRadius: 4
  });
  return /*#__PURE__*/React.createElement("span", {
    role: "group",
    "aria-label": "idioma / language",
    style: {
      display: 'inline-flex',
      gap: 2,
      border: `1px solid ${dark ? '#2C4A63' : 'var(--hairline)'}`,
      borderRadius: 6,
      padding: 2
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: opt('pt'),
    onClick: () => onChange('pt')
  }, "PT"), /*#__PURE__*/React.createElement("button", {
    style: opt('en'),
    onClick: () => onChange('en')
  }, "EN"));
}
window.LangToggle = LangToggle;
function ThemeToggle({
  theme,
  onChange
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: () => onChange(theme === 'dark' ? 'light' : 'dark'),
    "aria-label": "tema claro/escuro",
    title: theme === 'dark' ? 'tema claro' : 'tema escuro',
    style: {
      border: '1px solid var(--hairline)',
      background: 'transparent',
      color: 'var(--ink)',
      borderRadius: 6,
      padding: '3px 9px',
      cursor: 'pointer',
      font: '600 11px var(--font-mono)'
    }
  }, theme === 'dark' ? '☀' : '☾');
}
window.ThemeToggle = ThemeToggle;
function CitadelLogin({
  lang,
  setLang,
  onEnter,
  theme = 'dark',
  setTheme
}) {
  const t = window.CitadelI18n.t(lang);
  const quote = window.CitadelI18n.quotes[new Date().getDate() % window.CitadelI18n.quotes.length];
  const dark = theme === 'dark';
  // paleta do painel esquerdo — dark NOC vs light análise
  const P = dark ? {
    bg: 'linear-gradient(160deg,#041C2B 0%,#0A2438 100%)',
    ink: '#E7ECF3',
    sub: '#9FB2C4',
    cap: '#8299B0',
    mut: '#7A8FA3',
    hair: '#1D3448',
    amber: '#F0B45F',
    ok: '#8FD0A9',
    cyan: '#7FC7E8',
    gold: '#D9B36C',
    logo: '../../assets/logos/logo-totvs-branco.svg'
  } : {
    bg: 'linear-gradient(160deg,#E9EEF3 0%,#F4F6F9 100%)',
    ink: 'var(--ink)',
    sub: 'var(--text-muted)',
    cap: 'var(--text-muted)',
    mut: 'var(--text-faint)',
    hair: 'var(--hairline)',
    amber: 'var(--cap-limit-op)',
    ok: 'var(--state-ok)',
    cyan: 'var(--action)',
    gold: 'var(--state-stale)',
    logo: '../../assets/logos/logo-totvs-azul-escuro.svg'
  };
  const cap = {
    font: '600 10.5px var(--font-ui)',
    letterSpacing: '.14em',
    textTransform: 'uppercase',
    color: P.cap
  };
  const stat = (n, color, txt) => /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: '0 16px',
      borderLeft: `1px solid ${P.hair}`
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '700 21px var(--font-ui)',
      fontStretch: '114%',
      color
    }
  }, n), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11.5,
      color: P.sub,
      lineHeight: 1.4,
      marginTop: 3
    }
  }, txt));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 556px',
      height: '100%',
      fontFamily: 'var(--font-ui)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: P.bg,
      color: P.ink,
      padding: '38px 46px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      gap: 18,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("img", {
    src: P.logo,
    alt: "TOTVS",
    style: {
      height: 15,
      display: 'block',
      opacity: .9
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      font: '700 40px/1 var(--font-brand)',
      letterSpacing: '.02em',
      marginTop: 24,
      color: dark ? P.ink : 'var(--petrol-900)'
    }
  }, "CITADEL"), /*#__PURE__*/React.createElement("div", {
    style: {
      font: '400 13.5px/1.5 var(--font-ui)',
      color: P.sub,
      marginTop: 9
    }
  }, t('tagline'))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: cap
  }, t('nearestRisk'), " \xB7 27 jul 2026"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 16,
      marginTop: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '700 84px/.9 var(--font-ui)',
      fontStretch: '124%',
      color: P.amber
    }
  }, "38"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '700 21px var(--font-ui)',
      fontStretch: '112%',
      color: P.amber
    }
  }, t('days')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13.5,
      lineHeight: 1.5,
      color: P.ink,
      marginTop: 4,
      whiteSpace: 'pre-line'
    }
  }, t('heroDetail')))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14
    }
  }, /*#__PURE__*/React.createElement(TrajectoryChart, {
    dark: dark,
    height: 150,
    width: 780,
    history: [152, 154, 158, 163, 168, 172, 176, 181, 184],
    projection: [184, 190, 197, 205],
    opLimit: 190,
    techLimit: 200,
    satIndex: 9.05,
    satLabel: lang === 'pt' ? '28 ago · 84%' : 'Aug 28 · 84%',
    todayLabel: t('today'),
    xLabels: lang === 'pt' ? ['jan', 'abr', 'jul', 'set', 'dez'] : ['Jan', 'Apr', 'Jul', 'Sep', 'Dec'],
    ariaText: t('alertTitle')
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: cap
  }, t('whatChanges')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '52px 1fr',
      gap: '8px 12px',
      fontSize: 12.5,
      marginTop: 10,
      lineHeight: 1.45
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '600 11px var(--font-mono)',
      color: P.amber
    }
  }, "AGO"), /*#__PURE__*/React.createElement("span", null, t('ev1')), /*#__PURE__*/React.createElement("span", {
    style: {
      font: '600 11px var(--font-mono)',
      color: P.ok
    }
  }, "SET"), /*#__PURE__*/React.createElement("span", null, t('ev2')), /*#__PURE__*/React.createElement("span", {
    style: {
      font: '600 11px var(--font-mono)',
      color: P.cyan
    }
  }, "NOV"), /*#__PURE__*/React.createElement("span", null, t('ev3')))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      borderTop: `1px solid ${P.hair}`,
      borderBottom: `1px solid ${P.hair}`,
      padding: '14px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      paddingRight: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '700 21px var(--font-ui)',
      fontStretch: '114%',
      color: P.ink
    }
  }, "3"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11.5,
      color: P.sub,
      lineHeight: 1.4,
      marginTop: 3
    }
  }, t('st1'))), stat('2', P.gold, t('st2')), stat('3', P.cyan, t('st3'))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: cap
  }, t('provFooter')), /*#__PURE__*/React.createElement("span", {
    style: {
      font: '400 10.5px var(--font-mono)',
      color: P.mut
    }
  }, t('coneNote')))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface)',
      borderLeft: dark ? 'none' : '1px solid var(--hairline)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '34px 52px',
      gap: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '650 15px var(--font-ui)',
      fontStretch: '110%',
      color: 'var(--ink)'
    }
  }, t('welcome')), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      gap: 8,
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '400 10.5px var(--font-mono)',
      color: 'var(--text-muted)'
    }
  }, t('internal')), /*#__PURE__*/React.createElement(LangToggle, {
    lang: lang,
    onChange: setLang
  }), setTheme && /*#__PURE__*/React.createElement(ThemeToggle, {
    theme: theme,
    onChange: setTheme
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--hairline)',
      borderBottom: '1px solid var(--hairline)',
      padding: '15px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '600 10.5px var(--font-ui)',
      letterSpacing: '.16em',
      textTransform: 'uppercase',
      color: 'var(--text-muted)'
    }
  }, t('noteOfDay')), /*#__PURE__*/React.createElement("p", {
    style: {
      font: '400 16px/1.5 var(--font-ui)',
      color: 'var(--petrol-900)',
      margin: '9px 0 0'
    }
  }, "\u201C", quote.q, "\u201D"), /*#__PURE__*/React.createElement("div", {
    style: {
      font: '400 10.5px var(--font-mono)',
      color: 'var(--text-muted)',
      marginTop: 8
    }
  }, quote.who)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '700 23px var(--font-brand)',
      color: 'var(--petrol-900)'
    }
  }, t('signIn')), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 12.5,
      color: 'var(--text-muted)',
      margin: '5px 0 0'
    }
  }, t('restricted')), /*#__PURE__*/React.createElement(Button, {
    block: true,
    style: {
      marginTop: 18,
      padding: '11px 12px',
      fontSize: 13.5
    },
    onClick: onEnter
  }, t('sso')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      margin: '16px 0',
      color: 'var(--text-muted)',
      fontSize: 11
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      height: 1,
      background: 'var(--hairline)'
    }
  }), t('or'), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      height: 1,
      background: 'var(--hairline)'
    }
  })), /*#__PURE__*/React.createElement(TextField, {
    label: t('user'),
    value: "m.ferreira",
    mono: true
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 13
    }
  }, /*#__PURE__*/React.createElement(TextField, {
    label: t('pass'),
    value: "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",
    type: "password",
    mono: true,
    hint: ""
  })), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    block: true,
    style: {
      marginTop: 16,
      padding: '11px 12px',
      fontSize: 13.5
    },
    onClick: onEnter
  }, t('signIn')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      marginTop: 14,
      fontSize: 12
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => e.preventDefault()
  }, t('requestAccess')), /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => e.preventDefault()
  }, t('collectorStatus')))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '600 10.5px var(--font-ui)',
      letterSpacing: '.16em',
      textTransform: 'uppercase',
      color: 'var(--text-muted)'
    }
  }, t('platformStatus')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr auto',
      gap: '7px 12px',
      fontSize: 12,
      marginTop: 9
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)'
    }
  }, t('respondingCollectors')), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      color: 'var(--ink)'
    }
  }, "46 / 48"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)'
    }
  }, t('cmdbSync')), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      color: 'var(--ink)'
    }
  }, lang === 'pt' ? 'há 9 min' : '9 min ago'), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)'
    }
  }, t('ipamSync')), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      color: 'var(--ink)'
    }
  }, lang === 'pt' ? 'há 12 min' : '12 min ago'))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderTop: '1px solid var(--hairline)',
      paddingTop: 13
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--text-muted)'
    }
  }, t('internalUse')), /*#__PURE__*/React.createElement("span", {
    style: {
      font: '400 10.5px var(--font-mono)',
      color: 'var(--text-muted)'
    }
  }, "CITADEL v0.1"))));
}
window.CitadelLogin = CitadelLogin;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/citadel/Login.jsx", error: String((e && e.message) || e) }); }

// ui_kits/citadel/TresOlhos.jsx
try { (() => {
// CITADEL — Três Olhos (layout aprovado 5a: sidebar + painel + rail); primeiro item do módulo = alerta ativo
const {
  Button,
  Tabs,
  StatusBadge,
  RunwayBar,
  ProvenanceChip,
  ProvenancePanel,
  TrajectoryChart
} = window.CIDADELADesignSystem_99bf85;
const RES = [{
  id: 'nsxt1',
  pt: 'NSX T1 · Cluster_1',
  en: 'NSX T1 · Cluster_1',
  usage: 184,
  op: 190,
  tech: 200,
  days: {
    pt: '▲ 38 dias',
    en: '▲ 38 days'
  },
  conf: '84%',
  state: 'crit'
}, {
  id: 'ipset',
  pt: 'NSX IP Set',
  en: 'NSX IP Set',
  usage: 8106,
  op: 9200,
  tech: 9600,
  days: {
    pt: '◆ 132 dias',
    en: '◆ 132 days'
  },
  conf: '91%',
  state: 'warn'
}, {
  id: 'lsp',
  pt: 'Logical Switch Ports',
  en: 'Logical Switch Ports',
  usage: 20626,
  op: 24500,
  tech: 26000,
  days: {
    pt: '◆ 156 dias',
    en: '◆ 156 days'
  },
  conf: '88%',
  state: 'warn'
}, {
  id: 'nat',
  pt: 'NSX NAT Rules',
  en: 'NSX NAT Rules',
  usage: 17097,
  op: 25000,
  tech: 26500,
  days: {
    pt: '● 310 dias',
    en: '● 310 days'
  },
  conf: '79%',
  state: 'ok'
}, {
  id: 'fw',
  pt: 'FW físico — memória',
  en: 'Physical FW — memory',
  usage: 69.5,
  op: 85,
  tech: 100,
  days: {
    pt: '◐ instável',
    en: '◐ unstable'
  },
  conf: '—',
  state: 'stale'
}, {
  id: 'aci',
  pt: 'ACI — MAC_PER-IP',
  en: 'ACI — MAC_PER-IP',
  usage: 0,
  op: 0,
  tech: 100,
  days: {
    pt: '◌ sem coleta 26 h',
    en: '◌ no data 26 h'
  },
  conf: '—',
  state: 'nocollect',
  nocollect: true
}];
function Sidebar({
  lang,
  setLang,
  onLogout,
  t
}) {
  const mods = window.CitadelI18n.modules;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface)',
      borderRight: '1px solid var(--hairline)',
      display: 'flex',
      flexDirection: 'column',
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '16px 16px 12px',
      borderBottom: '1px solid var(--hairline)'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logos/logo-totvs-azul-escuro.svg",
    alt: "TOTVS",
    style: {
      height: 12,
      display: 'block',
      opacity: .85
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      font: '700 19px var(--font-brand)',
      letterSpacing: '.03em',
      color: 'var(--petrol-900)',
      marginTop: 9
    }
  }, "CITADEL")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 12px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      border: '1px solid var(--hairline)',
      borderRadius: 6,
      padding: '7px 10px',
      font: '400 11.5px var(--font-mono)',
      color: 'var(--text-muted)',
      background: 'var(--bg-page)'
    }
  }, t('search'), /*#__PURE__*/React.createElement("b", {
    style: {
      marginLeft: 'auto',
      border: '1px solid var(--hairline)',
      borderRadius: 3,
      padding: '0 5px',
      fontSize: 10
    }
  }, "/"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '13px 16px 11px',
      borderBottom: '1px solid var(--hairline)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: '600 10px var(--font-ui)',
      letterSpacing: '.14em',
      textTransform: 'uppercase',
      color: 'var(--text-muted)'
    }
  }, t('activeDomain')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginTop: 7
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '700 14px var(--font-mono)',
      color: 'var(--petrol-900)'
    }
  }, "TESP07"), /*#__PURE__*/React.createElement(StatusBadge, {
    state: "crit",
    label: "38 d",
    style: {
      padding: '1px 6px',
      fontSize: 10
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 11,
      color: 'var(--text-muted)'
    }
  }, "\u25BE"))), /*#__PURE__*/React.createElement("nav", {
    style: {
      paddingTop: 8,
      flex: 1,
      minHeight: 0,
      overflow: 'hidden'
    }
  }, mods.map(m => {
    const on = m.id === 'tresolhos';
    return /*#__PURE__*/React.createElement("div", {
      key: m.id,
      title: on ? undefined : t('underConstruction'),
      style: {
        padding: '8px 16px',
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gap: '1px 8px',
        alignItems: 'baseline',
        background: on ? 'var(--selection)' : 'transparent',
        boxShadow: on ? 'inset 2px 0 var(--action)' : 'none',
        cursor: on ? 'default' : 'not-allowed',
        opacity: on ? 1 : .78
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        font: `${on ? 600 : 500} 13px var(--font-ui)`,
        color: on ? 'var(--petrol-900)' : 'var(--ink)'
      }
    }, lang === 'pt' ? m.pt : m.en), /*#__PURE__*/React.createElement("span", {
      style: {
        font: '500 10.5px var(--font-mono)',
        color: m.hot ? 'var(--state-warn)' : m.count ? 'var(--text-muted)' : 'transparent'
      }
    }, m.count || '·'), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10.5,
        color: 'var(--text-muted)',
        gridColumn: '1/2'
      }
    }, lang === 'pt' ? m.dpt : m.den));
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--hairline)',
      padding: '12px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      fontSize: 12,
      color: 'var(--action)',
      fontWeight: 600
    }
  }, "\u2726 Meistre", /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      font: '400 10.5px var(--font-mono)',
      color: 'var(--text-muted)',
      fontWeight: 400
    }
  }, "\u2318J")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      borderTop: '1px solid var(--hairline)',
      paddingTop: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 24,
      height: 24,
      borderRadius: '50%',
      background: 'var(--selection)',
      color: 'var(--petrol-900)',
      font: '600 10px var(--font-ui)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, "MF"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11.5,
      color: 'var(--ink)',
      lineHeight: 1.25
    }
  }, "m.ferreira", /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => {
      e.preventDefault();
      onLogout();
    },
    style: {
      fontSize: 10.5
    }
  }, t('logout'))), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto'
    }
  }, /*#__PURE__*/React.createElement(window.LangToggle, {
    lang: lang,
    onChange: setLang
  })))));
}
function CitadelTresOlhos({
  lang,
  setLang,
  onLogout
}) {
  const t = window.CitadelI18n.t(lang);
  const [view, setView] = React.useState('alert');
  const [selRes, setSelRes] = React.useState('nsxt1');
  const cap = {
    font: '600 10.5px var(--font-ui)',
    letterSpacing: '.14em',
    textTransform: 'uppercase',
    color: 'var(--text-muted)'
  };
  const views = [{
    id: 'alert',
    label: lang === 'pt' ? '▲ Alerta: NSX T1 — 38 d' : '▲ Alert: NSX T1 — 38 d'
  }, {
    id: 'overview',
    label: t('overview')
  }, {
    id: 'fleet',
    label: t('fleetCompare')
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'var(--sidebar-w) 1fr var(--rail-w)',
      height: '100%',
      minWidth: 1280,
      fontFamily: 'var(--font-ui)',
      background: 'var(--bg-page)'
    }
  }, /*#__PURE__*/React.createElement(Sidebar, {
    lang: lang,
    setLang: setLang,
    onLogout: onLogout,
    t: t
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      padding: '12px 24px',
      borderBottom: '1px solid var(--hairline)',
      background: 'var(--surface)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '400 11px var(--font-mono)',
      color: 'var(--text-muted)'
    }
  }, t('breadcrumb')), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '500 11px var(--font-mono)',
      border: '1px solid var(--hairline)',
      borderRadius: 6,
      padding: '5px 10px',
      color: 'var(--petrol-900)',
      whiteSpace: 'nowrap'
    }
  }, t('period')), /*#__PURE__*/React.createElement("span", {
    style: {
      font: '500 11px var(--font-mono)',
      border: '1px solid var(--hairline)',
      borderRadius: 6,
      padding: '5px 10px',
      color: 'var(--text-muted)',
      whiteSpace: 'nowrap'
    }
  }, t('production'), " \u25BE"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm"
  }, t('export')))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '16px 24px',
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    items: views,
    active: view,
    onChange: setView
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--state-crit-bg)',
      border: '1px solid var(--state-crit)',
      borderRadius: 'var(--radius-md)',
      padding: '12px 16px',
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      color: 'var(--state-crit)',
      fontSize: 15
    }
  }, "\u25B2"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13.5,
      fontWeight: 600,
      color: 'var(--ink)'
    }
  }, t('alertTitle')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11.5,
      color: 'var(--text-muted)',
      marginTop: 2
    }
  }, t('alertMeta'))), /*#__PURE__*/React.createElement(ProvenanceChip, {
    method: "OBS",
    source: lang === 'pt' ? 'coletor NSX' : 'NSX collector',
    age: lang === 'pt' ? 'há 7 min' : '7 min ago',
    confidence: "84%"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface)',
      border: '1px solid var(--hairline)',
      borderRadius: 'var(--radius-md)',
      padding: '14px 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline',
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: '650 14px var(--font-ui)',
      fontStretch: '110%',
      color: 'var(--petrol-900)'
    }
  }, "NSX Tier-1 Gateways \xB7 T0-Cluster_1"), /*#__PURE__*/React.createElement("span", {
    style: {
      font: '700 14px var(--font-mono)',
      color: 'var(--cap-limit-op)'
    }
  }, lang === 'pt' ? '38 dias · 84%' : '38 days · 84%')), /*#__PURE__*/React.createElement(TrajectoryChart, {
    height: 190,
    width: 830,
    history: [152, 154, 158, 163, 168, 172, 176, 181, 184],
    projection: [184, 190, 197, 205],
    opLimit: 190,
    techLimit: 200,
    satIndex: 9.05,
    satLabel: lang === 'pt' ? '28 ago' : 'Aug 28',
    todayLabel: t('today'),
    xLabels: lang === 'pt' ? ['jan', 'mar', 'mai', 'jul', 'set', 'nov'] : ['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov'],
    events: [{
      index: 9.6,
      label: lang === 'pt' ? 'expansão (set)' : 'expansion (Sep)'
    }],
    ariaText: t('alertTitle')
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...cap,
      marginBottom: 8
    }
  }, t('runways')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 11
    }
  }, RES.map(r => /*#__PURE__*/React.createElement("div", {
    key: r.id,
    onClick: () => setSelRes(r.id),
    style: {
      cursor: 'pointer',
      padding: '4px 8px',
      margin: '0 -8px',
      borderRadius: 6,
      background: selRes === r.id ? 'var(--selection)' : 'transparent'
    }
  }, /*#__PURE__*/React.createElement(RunwayBar, {
    height: 9,
    label: /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: r.id === selRes ? 600 : 400
      }
    }, lang === 'pt' ? r.pt : r.en),
    usage: r.usage,
    opLimit: r.op || undefined,
    techLimit: r.tech,
    nocollect: r.nocollect,
    days: r.days[lang],
    confidence: r.conf !== '—' ? r.conf : undefined,
    state: r.state
  }))))))), /*#__PURE__*/React.createElement("div", {
    style: {
      borderLeft: '1px solid var(--hairline)',
      background: 'var(--surface)',
      padding: '16px 20px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      gap: 16,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: cap
  }, t('scenarios')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12.5,
      lineHeight: 1.55,
      marginTop: 10,
      paddingBottom: 11,
      borderBottom: '1px solid var(--hairline)'
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      font: '600 11px var(--font-mono)',
      color: 'var(--cap-limit-op)'
    }
  }, "AGO"), " \xB7 ", lang === 'pt' ? 'migração TESP02 → TESP07' : 'TESP02 → TESP07 migration', /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)'
    }
  }, lang === 'pt' ? 'antecipa a saturação para ' : 'moves saturation up to ', /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--cap-limit-op)'
    }
  }, lang === 'pt' ? '19 ago' : 'Aug 19'), " (P90)")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12.5,
      lineHeight: 1.55,
      marginTop: 11,
      paddingBottom: 11,
      borderBottom: '1px solid var(--hairline)'
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      font: '600 11px var(--font-mono)',
      color: 'var(--state-ok)'
    }
  }, "SET"), " \xB7 ", lang === 'pt' ? 'expansão contratada' : 'contracted expansion', /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)'
    }
  }, "+50 T1 \xB7 ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)'
    }
  }, "R$ 387.000"), " \xB7 runway 300+ d")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12.5,
      lineHeight: 1.55,
      marginTop: 11
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      font: '600 11px var(--font-mono)',
      color: 'var(--action)'
    }
  }, "NOV"), " \xB7 ", lang === 'pt' ? 'renovação Operadora A' : 'Carrier A renewal', /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)'
    }
  }, "SLA 99,95% \xB7 ", lang === 'pt' ? 'cotação no Tesouro' : 'quote in Treasury'))), /*#__PURE__*/React.createElement(ProvenancePanel, {
    title: t('provenance'),
    rows: [[t('origin'), lang === 'pt' ? 'coletor NSX · API' : 'NSX collector · API'], [t('lastCollect'), lang === 'pt' ? 'há 7 min' : '7 min ago'], [t('methodConf'), 'OBS · 84%'], [t('owner'), lang === 'pt' ? 'Eng. de Redes' : 'Network Eng.']]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    block: true
  }, t('openPlan')), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    block: true
  }, t('compareDomains')))));
}
window.CitadelTresOlhos = CitadelTresOlhos;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/citadel/TresOlhos.jsx", error: String((e && e.message) || e) }); }

// ui_kits/citadel/doc-page.js
try { (() => {
// @ds-adherence-ignore -- omelette starter scaffold (raw elements/hex/px by design)
// Copied omelette starter. Re-running copy_starter_component with this kind overwrites this file with the latest version (page content is unaffected).
/* BEGIN USAGE */
/**
 * <doc-page> — paged-document shell for printable HTML.
 *
 * FIRST, decide how the document paginates — up front, before building:
 *
 * - FLOWING document (the default): write the whole document as one
 *   normal HTML flow inside <doc-page>; the browser's print engine
 *   splits it onto pages at export. Use for long-form documents with a
 *   single text flow: reports, memos, letters, essays.
 * - EXPLICIT pagination: a fixed set of pre-paginated pages, one
 *   <section class="page"> child per page. Use when the user asks for a
 *   specific page count, or the design implies one: a one-page resume, a
 *   two-sided flier, a poster, a certificate, a brochure — any richly
 *   laid-out document without a single text flow.
 * - If in doubt, ask the user as part of the build.
 *
 * PAGE SIZING — paper differs by country (letter vs A4), so the printed
 * sheet is not one fixed truth:
 * - FLOWING documents pin NO paper size: the print engine paginates
 *   onto the user's real paper, and the content reflows to it.
 * - EXPLICITLY PAGINATED documents print each page at a FIXED page box
 *   with overflow hidden — letter by default, size="a4" for a clearly
 *   metric user, the user's chosen paper when they export. Design each
 *   page to FILL that box, fitting letter and A4 alike without overlap.
 * - width/height pin an explicit fixed size, ONLY when the user gives
 *   one.
 * Never write your own @page rule or hard-code paper dimensions in the
 * content.
 *
 * Sizing modes (attributes):
 *   (none)                      — portrait: flowing docs use the user's
 *           paper; explicitly paginated pages use the named size box
 *           (letter unless size="a4")
 *   orientation="landscape"     — the same, landscape
 *   width / height              — explicit fixed size, ONLY when the user
 *           gives one (e.g. width="22in" height="30in" for a 22×30
 *           poster): the page IS the design's size, printed at true
 *           dimensions (or scaled onto the user's paper at print time).
 *           Any absolute CSS length: px/in/mm/cm/pt/pc.
 * The component announces the chosen mode to the host app at runtime (a
 * meta tag it injects), so the print path can inject the user's true
 * paper size.
 *
 * On screen the document renders on a desk background: a flowing
 * document as one tall scrolling sheet (Google Docs' pageless view);
 * explicitly paginated documents as one card per page.
 *
 * EXPLICIT pagination usage:
 *   <style>doc-page:not(:defined){visibility:hidden}</style>
 *   <doc-page>
 *     <section class="page" id="p1">…one page's design…</section>
 *     <section class="page" id="p2">…</section>
 *   </doc-page>
 *   <script src="doc-page.js"></script>
 * How the page box works, concretely: each .page prints as ONE full-bleed
 * sheet at a FIXED physical size — letter by default (set size="a4" for
 * a clearly metric user), the user's chosen paper when they export —
 * with overflow hidden. Nothing scrolls and nothing reflows onto a next
 * sheet: content that misses the box is CLIPPED. Design each page to
 * FILL that page box, and to fit it — letter and A4 alike — without
 * overlap. Each page is a size container; don't size anything in
 * viewport units (they track the window, not the page), and never set
 * width or height on the .page section itself (the component sizes the
 * page box; an authored height like 100% is meaningless at print and is
 * overridden). The component owns the page box, the screen card chrome,
 * and the page breaks (never add your own break-before/after). Don't mix
 * .page sections with flowing content or header/footer slots in the same
 * document.
 *
 * FLOWING usage:
 *   <style>doc-page:not(:defined){visibility:hidden}</style>
 *   <doc-page margin="0.75in">
 *     <h1>Title</h1>
 *     <p>…body…</p>
 *   </doc-page>
 *   <script src="doc-page.js"></script>
 * There is no manual page-splitting — the browser's print engine
 * paginates at export. Standard break-hygiene rules (`break-inside:
 * avoid` on figures, code blocks, images and table rows; `orphans/
 * widows: 3`) are applied so paragraphs and groups split cleanly. On
 * screen and at print, headings default to `text-wrap: balance` and
 * body text to `text-wrap: pretty`; the defaults have zero specificity,
 * so any text-wrap you declare wins.
 *
 * Other attributes:
 *   size    — letter | a4 | legal (default letter). Flowing documents:
 *           preview proportion only — it does NOT pin their printed
 *           paper (the print dialog's paper governs); leave it alone
 *           there. Explicitly paginated documents: it sets the page box
 *           the cards and the pinned @page share (the export dialog's
 *           choice overrides both at print) — set size="a4" for a
 *           clearly metric user. Scaled-fit: names the sheet the fit is
 *           computed against, same a4-for-metric-users advice.
 *   content-width / content-height — the design's own fixed dimensions
 *           (CSS lengths), for scaling a fixed-size design ONTO the
 *           named sheet: content lays out at exactly this size, and the
 *           component scales it to fit that sheet's printable area
 *           (centered horizontally, top-aligned; the export dialog
 *           re-fits to the user's actual paper choice where available).
 *           Both must be set; they do not change the page box. For pages
 *           WITHOUT running header/footer slots.
 *   margin  — printable inset on every page of a FLOWING document
 *           (default 0.75in); margin="0" makes pages full-bleed.
 *           Explicitly paginated pages are always full-bleed.
 *
 * Running header/footer (flowing documents only): give an element
 * `slot="header"` or `slot="footer"` and it repeats on every printed
 * page via `position: fixed`. To keep body text from sliding under it,
 * the component prints inside a single-cell table whose <thead>/<tfoot>
 * are spacers sized to the header/footer height — browsers repeat
 * thead/tfoot on every page, so each sheet's content starts below the
 * header and ends above the footer. On screen the header/footer render
 * once at the top/bottom of the sheet.
 *
 * At print the component injects `@page { margin: 0 }` (which leaves
 * Chrome no margin box to draw its date/URL/page-count header in) and
 * moves the visual margin onto the sheet's own padding. It also marks
 * the document as owning its print CSS (a
 * `meta[name="omelette-owns-print"]` it injects at runtime), so the
 * PDF export never injects page-geometry CSS of its own on top.
 *
 * Print best practices for the content you author:
 * - Multi-column text: use CSS columns (`column-count` +
 *   `column-gap`), never side-by-side flex/grid columns — only real
 *   CSS columns flow and break across pages. `column-span: all` lets
 *   a heading span the columns; `hyphens: auto` (needs `lang` on
 *   the html element) keeps narrow columns readable.
 * - Page breaks in flowing documents: `break-before: page` on an
 *   element that must start a new page (a chapter, an appendix). Add
 *   your own kept-together blocks (callouts, stat tiles, cards) to a
 *   `break-inside: avoid` rule, and keep each one shorter than a page.
 * - Extend `orphans: 3; widows: 3` to any custom text blocks you add
 *   (p and li are covered by default).
 * - Give long tables a <thead> — browsers repeat it on every printed
 *   page.
 * - No `position: fixed`/`sticky` and no viewport units in content:
 *   fixed elements stamp every printed page (running headers/footers go
 *   in the component's slots) and `100vh` mis-sizes at print.
 *
 * Author content as static HTML so the user can click-to-edit any text
 * directly. Do not set width/padding/background on the document body —
 * the component owns the sheet box.
 */
/* END USAGE */

(() => {
  const PAPER = {
    letter: ['8.5in', '11in'],
    a4: ['210mm', '297mm'],
    legal: ['8.5in', '14in']
  };
  const CSS_LENGTH = /^\d+(\.\d+)?(px|in|mm|cm|pt|pc)$/;
  // Unitless "0" is a valid CSS length and the natural way to write
  // margin="0"; normalise it to 0px so max()/calc() (which reject a bare
  // number) keep working.
  const safeLen = (v, fb) => {
    v = (v || '').trim();
    return v === '0' ? '0px' : CSS_LENGTH.test(v) ? v : fb;
  };
  // WebKit (Safari and every iOS browser shell) never repeats a table's
  // thead/tfoot on printed pages (WebKit bug 17205), so the spacer-borne
  // vertical margins of a FLOWING document reach only the first page
  // there. Engine check, not browser check: vendor is 'Apple Computer,
  // Inc.' exactly for WebKit and 'Google Inc.' for Blink.
  const WK_PRINT = /apple/i.test(navigator.vendor || '');
  // CSS length → px number (CSS absolute units are exact: 1in = 96px).
  // Returns NaN for anything safeLen would reject — callers gate on it.
  const PX_PER = {
    px: 1,
    in: 96,
    mm: 96 / 25.4,
    cm: 96 / 2.54,
    pt: 96 / 72,
    pc: 16
  };
  const toPx = v => {
    const m = /^(\d+(?:\.\d+)?)(px|in|mm|cm|pt|pc)$/.exec((v || '').trim());
    return m ? parseFloat(m[1]) * PX_PER[m[2]] : NaN;
  };
  const stylesheet = `
    :host {
      position: relative;
      display: block;
      /* When the viewport is narrower than the page, grow to wrap the
       * sheet (plus this padding) instead of staying viewport-width, so
       * the desk background and right margin reach the sheet's far edge
       * in the horizontal scroll. */
      min-width: max-content;
      min-height: 100vh;
      background: #f5f5f4;
      padding: 48px 24px;
      box-sizing: border-box;
      font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
      --doc-page-w: 8.5in;
      --doc-page-h: 11in;
      --doc-page-margin: 0.75in;
      --doc-hdr-h: 0px;
      --doc-ftr-h: 0px;
      --doc-hdr-pad: 0px;
      --doc-ftr-pad: 0px;
    }
    .sheet {
      width: var(--doc-page-w);
      margin: 0 auto;
      background: #fff;
      box-shadow: 0 2px 10px rgba(20, 20, 19, 0.12);
      border-radius: 7px;
      box-sizing: border-box;
      padding: var(--doc-page-margin);
    }
    .frame { width: 100%; border-collapse: collapse; }
    /* Scaled-fit mode (content-width/content-height): the inner .fit box
     * lays the content out at its authored fixed size and scales it onto
     * the printable area; .fit-box reserves the scaled footprint in flow
     * (transforms don't affect layout) and centers it. Without the mode,
     * both divs are unstyled block pass-throughs. */
    /* Explicit pagination: direct .page children are the pages. The sheet
     * becomes a transparent stack and each page carries the card look on
     * screen; at print each page is exactly one full-bleed sheet. The
     * ::slotted defaults are deliberately weak (document CSS wins), so
     * authored page styling can override any of this. */
    .sheet.paginated {
      background: transparent;
      box-shadow: none;
      border-radius: 0;
      padding: 0;
    }
    .paginated ::slotted(.page) {
      position: relative;
      display: block;
      width: 100%;
      aspect-ratio: var(--doc-page-ar);
      container-type: size;
      overflow: hidden;
      box-sizing: border-box;
      background: #fff;
      border-radius: 7px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
      print-color-adjust: exact;
      -webkit-print-color-adjust: exact;
      break-inside: avoid;
    }
    .paginated ::slotted(.page:not(:first-child)) { margin-top: 1rem; }
    @media print {
      .sheet.paginated { padding: 0; }
      /* The flowing-document vertical inset lives on the repeating
       * thead/tfoot spacers, not the sheet padding — they must go too,
       * or each full-sheet .page is pushed ~margin down and spills onto
       * a second sheet. Paginated pages are full-bleed by definition
       * (content owns its insets). */
      .sheet.paginated .hdr-space,
      .sheet.paginated .ftr-space { height: 0; }
      .paginated ::slotted(.page) {
        border-radius: 0 !important;
        box-shadow: none !important;
        margin: 0 !important;
        /* Physical page-box sizing, no viewport units: Safari resolves
         * 100vh against the window, not the page box, so a vh-sized card
         * paginates wrong there. --doc-page-w/h are the named size by
         * default and are overridden to the user's chosen paper by the
         * export path, so every card is exactly one sheet either way.
         * Width + height (same source values as @page size) rather than
         * width + aspect-ratio: the ratio is a 6-decimal rounding of the
         * same division, and a few millionths of overflow would spill a
         * blank sheet after every page. The screen-only aspect-ratio
         * (preview proportions) must not leak into print. cqh typography
         * tracks the same box.
         *
         * Every declaration is !important: per CSS Scoping, unimportant
         * shadow ::slotted rules LOSE to the document context, so a page
         * section's authored inline style would silently beat this print
         * geometry. A model-authored height:100% did exactly that — the
         * percentage resolves as auto in the all-auto print ancestry, the
         * base rule's size containment turns auto into ZERO, and
         * overflow:hidden then paints nothing: a blank PDF with perfect
         * page boxes. At print the component's geometry is the design's
         * whole contract, so it must win over any authored sizing. */
        aspect-ratio: auto !important;
        width: var(--doc-page-w) !important;
        height: var(--doc-page-h) !important;
        overflow: hidden !important;
      }
      .paginated ::slotted(.page:not(:first-child)) {
        break-before: page !important;
        margin-top: 0 !important;
      }
    }
    .fit-mode .fit-box {
      width: calc(var(--doc-fit-w) * var(--doc-fit-scale));
      height: calc(var(--doc-fit-h) * var(--doc-fit-scale));
      margin: 0 auto;
      break-inside: avoid;
    }
    .fit-mode .fit {
      width: var(--doc-fit-w);
      height: var(--doc-fit-h);
      transform: scale(var(--doc-fit-scale));
      transform-origin: top left;
    }
    .frame td, .frame th { padding: 0; text-align: left; font-weight: inherit; }
    .hdr-space { height: var(--doc-hdr-h); }
    .ftr-space { height: var(--doc-ftr-h); }
    ::slotted([slot="header"]),
    ::slotted([slot="footer"]) { display: block; box-sizing: border-box; }
    @media print {
      :host { background: none; padding: 0; min-width: 0; min-height: 0; }
      .sheet {
        width: auto; margin: 0; box-shadow: none; border-radius: 0;
        padding: 0 var(--doc-page-margin);
      }
      /* The thead/tfoot spacers repeat on every page, so they carry the
       * vertical page margin (which the sheet's own padding cannot, since
       * that padding is consumed once on the first/last page). The running
       * header/footer are fixed inside that band. */
      /* The 0.35in is breathing room between a running header/footer and
       * the body; without one the spacer is exactly the page margin, so a
       * margin="0" full-bleed document gets truly full-bleed pages. */
      .hdr-space { height: max(var(--doc-page-margin), calc(var(--doc-hdr-h) + var(--doc-hdr-pad))); }
      .ftr-space { height: max(var(--doc-page-margin), calc(var(--doc-ftr-h) + var(--doc-ftr-pad))); }
      /* WebKit flowing documents: @page carries the vertical margin (see
       * _syncPrintPageRule), so the spacers keep only whatever a running
       * header/footer needs BEYOND it — page 1 would otherwise double its
       * top inset. Paginated sheets already zero their spacers above. */
      .sheet.wk-print:not(.paginated) .hdr-space { height: max(0px, calc(max(var(--doc-page-margin), calc(var(--doc-hdr-h) + var(--doc-hdr-pad))) - var(--doc-page-margin))); }
      .sheet.wk-print:not(.paginated) .ftr-space { height: max(0px, calc(max(var(--doc-page-margin), calc(var(--doc-ftr-h) + var(--doc-ftr-pad))) - var(--doc-page-margin))); }
      ::slotted([slot="header"]) {
        position: fixed; top: 0; left: 0; right: 0; margin: 0;
        padding: calc(var(--doc-page-margin) * 0.45) var(--doc-page-margin) 0;
      }
      ::slotted([slot="footer"]) {
        position: fixed; bottom: 0; left: 0; right: 0; margin: 0;
        padding: 0 var(--doc-page-margin) calc(var(--doc-page-margin) * 0.45);
      }
    }
  `;
  class DocPage extends HTMLElement {
    static get observedAttributes() {
      return ['size', 'width', 'height', 'margin', 'orientation', 'content-width', 'content-height'];
    }
    constructor() {
      super();
      this._root = this.attachShadow({
        mode: 'open'
      });
      this._mo = typeof MutationObserver === 'function' ? new MutationObserver(() => this._scheduleMeasure()) : null;
    }

    /** The named paper's [w, h], swapped when orientation="landscape".
     *  Only the named size swaps — explicit width/height are exact values
     *  the author already oriented. */
    _paperSize() {
      const named = PAPER[(this.getAttribute('size') || '').toLowerCase()] || PAPER.letter;
      const landscape = (this.getAttribute('orientation') || '').trim().toLowerCase() === 'landscape';
      return landscape ? [named[1], named[0]] : named;
    }
    get pageWidth() {
      return safeLen(this.getAttribute('width'), this._paperSize()[0]);
    }
    get pageHeight() {
      return safeLen(this.getAttribute('height'), this._paperSize()[1]);
    }
    get pageMargin() {
      return safeLen(this.getAttribute('margin'), '0.75in');
    }

    /** Scaled-fit mode's content box [w, h] as CSS lengths, or null when
     *  the mode is off (either attribute missing/invalid/zero — a partial
     *  declaration falls back to normal flow rather than guessing). */
    _contentFit() {
      const w = safeLen(this.getAttribute('content-width'), null);
      const h = safeLen(this.getAttribute('content-height'), null);
      if (!w || !h) return null;
      const wPx = toPx(w),
        hPx = toPx(h);
      return wPx > 0 && hPx > 0 ? [w, h, wPx, hPx] : null;
    }
    connectedCallback() {
      if (!this._sheet) this._render();
      this._syncSize();
      this._syncPrintPageRule();
      this._ensureTextWrapDefaults();
      this._ensureOwnsPrintMeta();
      this._syncFixedSizeMeta();
      this._syncPrintSizingMeta();
      if (this._mo) this._mo.observe(this, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true
      });
      this._onResize = () => this._scheduleMeasure();
      window.addEventListener('resize', this._onResize);
      if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(() => this._scheduleMeasure());
      }
      this._scheduleMeasure();
    }
    disconnectedCallback() {
      window.removeEventListener('resize', this._onResize);
      if (this._mo) this._mo.disconnect();
      if (this._raf) {
        cancelAnimationFrame(this._raf);
        this._raf = null;
      }
      // Drop the head rules when the last doc-page leaves, so a deleted
      // document's @page geometry and text-wrap defaults can't apply to
      // whatever replaces it.
      const survivor = document.querySelector('doc-page');
      if (!survivor) {
        ['doc-page-print', 'doc-page-text-wrap', 'doc-page-owns-print', 'doc-page-fixed-size', 'doc-page-print-sizing'].forEach(id => {
          const tag = document.getElementById(id);
          if (tag) tag.remove();
        });
        // A live deck-stage deferred its own print-sizing meta to ours —
        // hand the page-global meta over so the deck isn't left unmarked.
        const deck = document.querySelector('deck-stage');
        if (deck && typeof deck._ensurePrintSizingMeta === 'function') {
          deck._ensurePrintSizingMeta();
        }
      } else {
        // A departed owner hands each page-global meta to whatever
        // doc-page remains (or it's removed).
        if (typeof survivor._syncFixedSizeMeta === 'function') {
          survivor._syncFixedSizeMeta();
        }
        if (typeof survivor._syncPrintSizingMeta === 'function') {
          survivor._syncPrintSizingMeta();
        }
      }
    }
    attributeChangedCallback() {
      if (!this._sheet) return;
      this._syncSize();
      this._syncPrintPageRule();
      this._syncFixedSizeMeta();
      this._syncPrintSizingMeta();
      this._scheduleMeasure();
    }
    _render() {
      this._root.innerHTML = `
        <style>${stylesheet}</style>
        <style id="vars"></style>
        <div class="sheet" data-screen-label="Document">
          <table class="frame" role="presentation">
            <thead><tr><th><div class="hdr-space"><slot name="header"></slot></div></th></tr></thead>
            <tbody><tr><td class="body"><div class="fit-box"><div class="fit"><slot></slot></div></div></td></tr></tbody>
            <tfoot><tr><td><div class="ftr-space"><slot name="footer"></slot></div></td></tr></tfoot>
          </table>
        </div>`;
      this._sheet = this._root.querySelector('.sheet');
      this._vars = this._root.getElementById('vars');
    }

    /** Runtime sizing lives in a shadow <style> :host rule, never on the
     *  light-DOM host element, so serialize-persist can't write it back. */
    _syncSize(hdrH, ftrH) {
      // Scaled-fit mode: content at its authored size, scaled onto the
      // printable area (page minus margins on both axes). The factor is a
      // plain number var so calc(length * number) stays valid; 4 decimals
      // keeps the shadow style stable across re-measures. Upscaling is
      // allowed — print transforms are vector, so text and CSS stay crisp
      // (raster images soften, which the catalog bullet warns about).
      const fit = this._contentFit();
      let fitVars = '';
      if (fit) {
        const marginPx = toPx(this.pageMargin) || 0;
        const availW = toPx(this.pageWidth) - 2 * marginPx;
        const availH = toPx(this.pageHeight) - 2 * marginPx;
        const scale = Math.min(availW / fit[2], availH / fit[3]);
        if (scale > 0 && Number.isFinite(scale)) {
          fitVars = '--doc-fit-w:' + fit[0] + ';' + '--doc-fit-h:' + fit[1] + ';' + '--doc-fit-scale:' + scale.toFixed(4) + ';';
        }
      }
      this._sheet.classList.toggle('fit-mode', !!fitVars);
      // Numeric w/h ratio for the paginated page cards' aspect-ratio —
      // aspect-ratio takes a number, not a length ratio, so compute it
      // here (CSS length division isn't portable). 6 decimals keeps the
      // shadow style stable across re-syncs.
      const arW = toPx(this.pageWidth);
      const arH = toPx(this.pageHeight);
      const ar = arW > 0 && arH > 0 ? (arW / arH).toFixed(6) : '0.772727';
      this._vars.textContent = ':host{' + fitVars + '--doc-page-ar:' + ar + ';' + '--doc-page-w:' + this.pageWidth + ';' + '--doc-page-h:' + this.pageHeight + ';' + '--doc-page-margin:' + this.pageMargin + ';' + '--doc-hdr-h:' + (hdrH || 0) + 'px;' + '--doc-ftr-h:' + (ftrH || 0) + 'px;' + '--doc-hdr-pad:' + (hdrH ? '0.35in' : '0px') + ';' + '--doc-ftr-pad:' + (ftrH ? '0.35in' : '0px') + '}';
    }

    /** @page is a no-op inside shadow DOM, so the rule lives in <head>.
     *  Re-appended on every sync so it stays last in source order — the
     *  @page cascade is source-order per descriptor, so this rule wins
     *  over any other @page rule in the document.
     *
     *  The @page SIZE is pinned where the page box IS part of the design:
     *  explicit-fixed-size mode (width + height authored), scaled-fit
     *  mode (the named sheet the fit targets), and explicit pagination
     *  (the named size the cards share — so card and sheet agree on
     *  every print path, and the export path's chosen paper overrides
     *  BOTH with one later rule). For FLOWING documents no paper size is
     *  emitted at all — the true size comes from the user's preference,
     *  injected by the export path or chosen in the print dialog — so a
     *  flowing document never fights the paper it lands on.
     *  margin: 0 is emitted in every mode: it leaves Chrome no margin box
     *  to draw its date/URL/page-count header in, and the visual margin
     *  lives on the sheet's own padding. */
    _syncPrintPageRule() {
      const id = 'doc-page-print';
      let tag = document.getElementById(id);
      if (!tag) {
        tag = document.createElement('style');
        tag.id = id;
      }
      document.head.appendChild(tag);
      // Three print-geometry regimes:
      // - true-size: the page IS the design — pin its exact size.
      // - scaled-fit (content-width/height): the fit factor is computed
      //   against the NAMED paper's printable area, so that paper must
      //   stay pinned or the scaled content overflows a smaller sheet
      //   (the export path re-fits and re-pins at print time on top).
      // - default modes: no paper size — but landscape still needs the
      //   paper-agnostic 'size: landscape' keyword, because the size
      //   descriptor is what carries orientation; without it a landscape
      //   document prints portrait whenever nothing injects a size.
      const landscape = (this.getAttribute('orientation') || '').trim().toLowerCase() === 'landscape';
      // Explicit pagination pins the page box to the SAME values that
      // size the cards (the named size by default, the export path's
      // chosen paper when its later rule overrides both) — card and
      // sheet agree on every print path, and a mismatched real paper
      // shrinks-to-fit in the dialog instead of clipping a Letter card
      // on A4. Declared before the paginated read below so both derive
      // from one check.
      const paginatedNow = this.querySelector(':scope > .page') !== null;
      const sizeDescriptor = this._trueSizePx() ? 'size: ' + this.pageWidth + ' ' + this.pageHeight + '; ' : this._contentFit() ? 'size: ' + this.pageWidth + ' ' + this.pageHeight + '; ' : paginatedNow ? 'size: ' + this.pageWidth + ' ' + this.pageHeight + '; ' : landscape ? 'size: landscape; ' : '';
      // WebKit never repeats the thead/tfoot spacers that carry a flowing
      // document's vertical page margins (see WK_PRINT above), so pages
      // after the first print edge-to-edge there. Carry the VERTICAL
      // margins on @page for WebKit instead, and the shadow print CSS
      // trims the first-page spacers by the same amount (.sheet.wk-print
      // rules). Horizontal inset stays on the sheet's own padding in
      // every engine. Blink keeps margin: 0 (a nonzero margin there
      // re-opens the box Chrome draws its header furniture in). One cost,
      // learned in testing: Safari's own date/URL headers are a USER
      // dialog setting ("Print headers and footers") that renders in the
      // margin area when room exists — margin: 0 only suppressed it by
      // leaving no room, and no CSS controls it. The export dialog's
      // Safari guide teaches turning the setting off for flowing
      // documents. Explicitly paginated and fixed-size documents keep
      // margin: 0 everywhere: their pages ARE the sheet.
      const wkFlowing = WK_PRINT && !paginatedNow && !this._trueSizePx() && !this._contentFit();
      const marginDescriptor = wkFlowing ? 'margin: ' + this.pageMargin + ' 0; ' : 'margin: 0; ';
      // Shadow-internal marker (never serialized), kept in lockstep with
      // the @page decision above: the print CSS trims the first-page
      // spacers ONLY while @page actually carries the margins — a
      // true-size or scaled-fit sheet keeps margin: 0 and must keep its
      // spacers too. Re-synced here so attribute changes and pagination
      // flips move both together.
      if (this._sheet) this._sheet.classList.toggle('wk-print', wkFlowing);
      tag.textContent = '@page { ' + sizeDescriptor + marginDescriptor + '} ' + '@media print { html, body { margin: 0 !important; padding: 0 !important; background: none !important; height: auto !important; overflow: visible !important; } ' + 'h1,h2,h3,h4,h5,h6 { break-after: avoid; } ' + 'figure,pre,blockquote,img,svg,tr { break-inside: avoid; } ' + 'p,li { orphans: 3; widows: 3; } ' + '* { -webkit-print-color-adjust: exact; print-color-adjust: exact; ' + 'backdrop-filter: none !important; -webkit-backdrop-filter: none !important; } ' + '*, *::before, *::after { animation-delay: -99s !important; animation-duration: .001s !important; ' + 'animation-iteration-count: 1 !important; animation-fill-mode: both !important; ' + 'animation-play-state: running !important; transition-duration: 0s !important; } }';
    }

    /** Typographic defaults for document text: balance headings, avoid
     *  widowed/orphaned words in body copy (browsers without text-wrap
     *  support drop the declarations). Zero-specificity via :where() so
     *  any text-wrap authored on those elements wins; document-level so the
     *  rules reach the slotted (light DOM) content — shadow styles can't.
     *  data-omelette-injected marks the tag for the host editor to strip
     *  at serialize, so it is never written back as authored source. */
    _ensureTextWrapDefaults() {
      if (document.getElementById('doc-page-text-wrap')) return;
      const tag = document.createElement('style');
      tag.id = 'doc-page-text-wrap';
      tag.setAttribute('data-omelette-injected', '');
      tag.textContent = ':where(h1,h2,h3,h4,h5,h6){text-wrap:balance}' + ':where(p,li,blockquote,figcaption){text-wrap:pretty}';
      document.head.appendChild(tag);
    }

    /** Declares that this document owns its print CSS. The instant-PDF
     *  export checks for the meta by NAME PRESENCE alone (content is
     *  ignored) and skips its automatic print-CSS injections, so the
     *  component's @page geometry is never overridden by a heuristic.
     *  data-omelette-injected keeps it out of serialized source. */
    _ensureOwnsPrintMeta() {
      if (document.getElementById('doc-page-owns-print')) return;
      const tag = document.createElement('meta');
      tag.id = 'doc-page-owns-print';
      tag.name = 'omelette-owns-print';
      tag.content = 'true';
      tag.setAttribute('data-omelette-injected', '');
      document.head.appendChild(tag);
    }

    /** This page's valid true-size page box (explicit width AND height)
     *  as [w, h] px ints, or null when the mode is off. */
    _trueSizePx() {
      if (!safeLen(this.getAttribute('width'), null) || !safeLen(this.getAttribute('height'), null)) return null;
      const w = Math.round(toPx(this.pageWidth));
      const h = Math.round(toPx(this.pageHeight));
      return w > 0 && h > 0 ? [w, h] : null;
    }

    /** True-size pages (explicit width AND height) also declare the page
     *  box as the preview size: the in-app preview reads
     *  meta[name="omelette-fixed-size"] (content "W,H" in px ints) and
     *  scales the sheet into view — without it an 18in poster previews at
     *  true size with scrollbars. Never overrides an author-set meta
     *  (only the component's own id is managed). The meta is page-global
     *  while doc-page instances are not, so every sync recomputes the
     *  page-wide owner — the first connected true-size doc-page — and a
     *  non-true-size sibling's sync can never delete the owner's meta.
     *  Removed when no true-size page remains (the owner's disconnect
     *  re-syncs via any survivor) or when an author-set meta exists. */
    _syncFixedSizeMeta() {
      const id = 'doc-page-fixed-size';
      const own = document.getElementById(id);
      const authored = document.querySelector('meta[name="omelette-fixed-size"]:not([data-omelette-injected])');
      // The page-wide owner, not this instance: an upgraded true-size page
      // anywhere in the document keeps the meta alive and sized.
      let box = null;
      for (const el of document.querySelectorAll('doc-page')) {
        box = typeof el._trueSizePx === 'function' ? el._trueSizePx() : null;
        if (box) break;
      }
      if (!box || authored) {
        if (own) own.remove();
        return;
      }
      const tag = own || document.createElement('meta');
      tag.id = id;
      tag.name = 'omelette-fixed-size';
      tag.content = box[0] + ',' + box[1];
      tag.setAttribute('data-omelette-injected', '');
      if (!own) document.head.appendChild(tag);
    }

    /** This page's print-sizing mode: 'fixed' when an explicit width AND
     *  height are authored (the page is the design's own size), else the
     *  default paper in the authored orientation. */
    _printSizingMode() {
      if (this._trueSizePx()) return 'fixed';
      const landscape = (this.getAttribute('orientation') || '').trim().toLowerCase() === 'landscape';
      return landscape ? 'default-landscape' : 'default-portrait';
    }

    /** Announces the print-sizing mode to the host app:
     *  meta[name="omelette-print-sizing"] with content 'default-portrait',
     *  'default-landscape', or 'fixed' (fixed pages also carry the
     *  omelette-fixed-size meta with the page box in px). The export path
     *  probes it to decide what true paper size to inject at print time —
     *  in the default modes the component emits no paper size of its own.
     *  Same page-global ownership rules as the fixed-size meta above:
     *  first connected doc-page owns it, an authored meta is never
     *  overridden, removed when no doc-page remains. */
    _syncPrintSizingMeta() {
      const id = 'doc-page-print-sizing';
      const own = document.getElementById(id);
      const authored = document.querySelector('meta[name="omelette-print-sizing"]:not([data-omelette-injected])');
      // A fixed page wins outright (mirroring the fixed-size loop above,
      // so the two metas can never contradict each other in a mixed
      // multi-page document); otherwise the first page's mode holds.
      let mode = null;
      for (const el of document.querySelectorAll('doc-page')) {
        if (typeof el._printSizingMode !== 'function') continue;
        const m = el._printSizingMode();
        if (m === 'fixed') {
          mode = m;
          break;
        }
        if (mode === null) mode = m;
      }
      if (!mode || authored) {
        if (own) own.remove();
        return;
      }
      // A deck-stage that connected first injected its own meta and
      // defers to any existing one — take it over, or the document ends
      // up with two conflicting injected metas (a doc-page page is the
      // document; the deck re-ensures its meta if every doc-page leaves).
      const deckMeta = document.getElementById('deck-stage-print-sizing');
      if (deckMeta) deckMeta.remove();
      const tag = own || document.createElement('meta');
      tag.id = id;
      tag.name = 'omelette-print-sizing';
      tag.content = mode;
      tag.setAttribute('data-omelette-injected', '');
      if (!own) document.head.appendChild(tag);
    }
    _scheduleMeasure() {
      if (this._raf) return;
      this._raf = requestAnimationFrame(() => {
        this._raf = null;
        this._measure();
      });
    }

    /** Slot heights feed the print spacers (--doc-hdr-h / --doc-ftr-h), so
     *  they re-measure on content mutation, resize, and font load. The
     *  same pass detects explicit pagination (direct .page children) and
     *  toggles the sheet between the flowing-document card and the
     *  page-per-card stack — content edits can add or remove pages at any
     *  time, so this tracks the same mutations the measurement does. */
    _measure() {
      const hdr = this.querySelector(':scope > [slot="header"]');
      const ftr = this.querySelector(':scope > [slot="footer"]');
      const wasPaginated = this._sheet.classList.contains('paginated');
      this._sheet.classList.toggle('paginated', this.querySelector(':scope > .page') !== null);
      // The WebKit @page margin is flowing-only, so a pagination flip
      // must re-emit the rule (content edits can add or remove .page
      // sections at any time).
      if (this._sheet.classList.contains('paginated') !== wasPaginated) {
        this._syncPrintPageRule();
      }
      this._syncSize(hdr ? hdr.offsetHeight : 0, ftr ? ftr.offsetHeight : 0);
    }
  }
  if (!customElements.get('doc-page')) {
    customElements.define('doc-page', DocPage);
  }
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/citadel/doc-page.js", error: String((e && e.message) || e) }); }

// ui_kits/citadel/i18n.jsx
try { (() => {
// CITADEL — dicionário PT/EN + dados mockados compartilhados do kit
window.CitadelI18n = {
  modules: [{
    id: 'conselho',
    pt: 'Conselho',
    en: 'Council',
    dpt: 'visão executiva',
    den: 'executive view',
    count: 2
  }, {
    id: 'tresolhos',
    pt: 'Três Olhos',
    en: 'Three Eyes',
    dpt: 'capacidade e previsão',
    den: 'capacity & forecast',
    count: 4
  }, {
    id: 'corvo',
    pt: 'Corvo',
    en: 'Raven',
    dpt: 'sinais e integrações',
    den: 'signals & integrations',
    count: 12,
    hot: true
  }, {
    id: 'muralha',
    pt: 'Muralha',
    en: 'Wall',
    dpt: 'limites de plataforma',
    den: 'platform limits',
    count: 3
  }, {
    id: 'dominios',
    pt: 'Domínios',
    en: 'Domains',
    dpt: 'datacenters e topologia',
    den: 'datacenters & topology'
  }, {
    id: 'arquivo',
    pt: 'Arquivo',
    en: 'Archive',
    dpt: 'wiki e runbooks',
    den: 'wiki & runbooks'
  }, {
    id: 'tesouro',
    pt: 'Tesouro',
    en: 'Treasury',
    dpt: 'orçamento e cotações',
    den: 'budget & quotes',
    count: 3
  }, {
    id: 'campanhas',
    pt: 'Campanhas',
    en: 'Campaigns',
    dpt: 'planos de ação',
    den: 'action plans',
    count: 7
  }],
  s: {
    tagline: {
      pt: 'Veja o limite antes de alcançá-lo.',
      en: 'See the limit before you reach it.'
    },
    signature: {
      pt: 'Conhecimento, capacidade e decisão.',
      en: 'Knowledge, capacity, decision.'
    },
    nearestRisk: {
      pt: 'risco mais próximo',
      en: 'nearest risk'
    },
    days: {
      pt: 'dias',
      en: 'days'
    },
    heroDetail: {
      pt: 'até o limite operacional mais próximo\nem um domínio de produção',
      en: 'until the nearest operational limit\nin a production domain'
    },
    whatChanges: {
      pt: 'o que muda a projeção',
      en: 'what changes the forecast'
    },
    ev1: {
      pt: 'janela de migração programada',
      en: 'scheduled migration window'
    },
    ev2: {
      pt: 'expansão contratada',
      en: 'contracted expansion'
    },
    ev3: {
      pt: 'renovação de contrato',
      en: 'contract renewal'
    },
    st1: {
      pt: 'recursos saturam em menos de 90 dias',
      en: 'resources saturate in under 90 days'
    },
    st2: {
      pt: 'coletores sem coleta há mais de 24 h',
      en: 'collectors silent for over 24 h'
    },
    st3: {
      pt: 'cotações aguardando decisão',
      en: 'quotes awaiting decision'
    },
    provFooter: {
      pt: 'coleta contínua · 46 de 48 coletores respondendo',
      en: 'continuous collection · 46 of 48 collectors responding'
    },
    coneNote: {
      pt: 'projeção 12 m · cone P10–P90',
      en: '12-mo forecast · P10–P90 cone'
    },
    noteOfDay: {
      pt: 'nota do dia',
      en: 'note of the day'
    },
    welcome: {
      pt: 'Bem-vindo de volta',
      en: 'Welcome back'
    },
    internal: {
      pt: 'plataforma interna · TOTVS Cloud',
      en: 'internal platform · TOTVS Cloud'
    },
    signIn: {
      pt: 'Entrar',
      en: 'Sign in'
    },
    restricted: {
      pt: 'Acesso restrito às equipes de infraestrutura, operações e gestão.',
      en: 'Restricted to infrastructure, operations and management teams.'
    },
    sso: {
      pt: 'Continuar com SSO TOTVS',
      en: 'Continue with TOTVS SSO'
    },
    or: {
      pt: 'ou',
      en: 'or'
    },
    user: {
      pt: 'Usuário corporativo',
      en: 'Corporate username'
    },
    pass: {
      pt: 'Senha',
      en: 'Password'
    },
    show: {
      pt: 'mostrar',
      en: 'show'
    },
    requestAccess: {
      pt: 'Solicitar acesso',
      en: 'Request access'
    },
    collectorStatus: {
      pt: 'Status dos coletores',
      en: 'Collector status'
    },
    platformStatus: {
      pt: 'status da plataforma',
      en: 'platform status'
    },
    respondingCollectors: {
      pt: 'Coletores respondendo',
      en: 'Collectors responding'
    },
    cmdbSync: {
      pt: 'Última sincronização CMDB',
      en: 'Last CMDB sync'
    },
    ipamSync: {
      pt: 'Última sincronização IPAM',
      en: 'Last IPAM sync'
    },
    ago: {
      pt: 'há',
      en: ''
    },
    internalUse: {
      pt: 'Uso interno · dados classificados',
      en: 'Internal use · classified data'
    },
    activeDomain: {
      pt: 'domínio ativo',
      en: 'active domain'
    },
    all: {
      pt: 'todos',
      en: 'all'
    },
    search: {
      pt: 'buscar…',
      en: 'search…'
    },
    logout: {
      pt: 'sair',
      en: 'sign out'
    },
    activeAlert: {
      pt: 'Alerta ativo',
      en: 'Active alert'
    },
    overview: {
      pt: 'Visão geral',
      en: 'Overview'
    },
    fleetCompare: {
      pt: 'Comparação de domínios',
      en: 'Domain comparison'
    },
    alertTitle: {
      pt: 'NSX T1 pode atingir o limite operacional em 38 dias',
      en: 'NSX T1 may reach its operational limit in 38 days'
    },
    alertMeta: {
      pt: 'TESP07 · produção · previsão com 84% de confiança · 12 meses de histórico',
      en: 'TESP07 · production · forecast at 84% confidence · 12 months of history'
    },
    openPlan: {
      pt: 'Abrir plano de ação',
      en: 'Open action plan'
    },
    seeEvidence: {
      pt: 'Ver evidências',
      en: 'View evidence'
    },
    assign: {
      pt: 'Atribuir responsável',
      en: 'Assign owner'
    },
    runways: {
      pt: 'runways por recurso · ordenado por tempo até saturação',
      en: 'runways per resource · sorted by time to saturation'
    },
    scenarios: {
      pt: 'cenários & eventos',
      en: 'scenarios & events'
    },
    provenance: {
      pt: 'procedência',
      en: 'provenance'
    },
    origin: {
      pt: 'Origem',
      en: 'Origin'
    },
    lastCollect: {
      pt: 'Última coleta',
      en: 'Last collected'
    },
    methodConf: {
      pt: 'Método · confiança',
      en: 'Method · confidence'
    },
    owner: {
      pt: 'Responsável',
      en: 'Owner'
    },
    compareDomains: {
      pt: 'Comparar domínios',
      en: 'Compare domains'
    },
    breadcrumb: {
      pt: 'Domínios › TESP07 › NSX › capacidade',
      en: 'Domains › TESP07 › NSX › capacity'
    },
    today: {
      pt: 'hoje',
      en: 'today'
    },
    period: {
      pt: '−12 m ◂ hoje ▸ +6 m',
      en: '−12 mo ◂ today ▸ +6 mo'
    },
    production: {
      pt: 'produção',
      en: 'production'
    },
    export: {
      pt: 'Exportar',
      en: 'Export'
    },
    trajTab: {
      pt: 'Trajetória',
      en: 'Trajectory'
    },
    evTab: {
      pt: 'Eventos',
      en: 'Events'
    },
    rbTab: {
      pt: 'Runbooks',
      en: 'Runbooks'
    },
    histTab: {
      pt: 'Histórico',
      en: 'History'
    },
    underConstruction: {
      pt: 'módulo em desenho — use Três Olhos',
      en: 'module in design — use Three Eyes'
    }
  },
  quotes: [{
    q: 'Talk is cheap. Show me the code.',
    who: 'Linus Torvalds'
  }, {
    q: 'Everything fails, all the time.',
    who: 'Werner Vogels'
  }, {
    q: 'In God we trust; all others must bring data.',
    who: 'W. Edwards Deming'
  }, {
    q: 'Hope is not a strategy.',
    who: 'SRE proverb · Google'
  }]
};
window.CitadelI18n.t = lang => key => {
  const e = window.CitadelI18n.s[key];
  return e ? e[lang] || e.pt : key;
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/citadel/i18n.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Button = __ds_scope.Button;

__ds_ns.DataTable = __ds_scope.DataTable;

__ds_ns.Modal = __ds_scope.Modal;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.STATUS_STATES = __ds_scope.STATUS_STATES;

__ds_ns.StatusBadge = __ds_scope.StatusBadge;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.TextField = __ds_scope.TextField;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.DomainTile = __ds_scope.DomainTile;

__ds_ns.ProvenanceChip = __ds_scope.ProvenanceChip;

__ds_ns.ProvenancePanel = __ds_scope.ProvenancePanel;

__ds_ns.RunwayBar = __ds_scope.RunwayBar;

__ds_ns.TrajectoryChart = __ds_scope.TrajectoryChart;

})();
