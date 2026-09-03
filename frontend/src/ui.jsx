/* Composições do app sobre o design system: o que o DS ainda não tem
   (banner, toggle, área de texto, "sem coleta") e átomos de layout (Cap, Card,
   wordmark). Tudo em tokens; nada de hex/px de marca aqui. */
import React from "react";
import { STATUS_STATES } from "@ds";
import totvsBranco from "@ds/assets/logos/logo-totvs-branco.svg";
import totvsAzul from "@ds/assets/logos/logo-totvs-azul-escuro.svg";
import { useLang } from "./i18n.jsx";

const cx = (...a) => a.filter(Boolean).join(" ");

export const Cap = ({ children, style, className }) => <div className={cx("cap", className)} style={style}>{children}</div>;

/* Card: superfície branca + hairline, sem sombra. `mock` = EST simulado (tracejado âmbar); `nocollect` = pontilhado. */
export const Card = ({ children, style, mock, nocollect, flush, className }) => (
  <section className={cx("card", mock && "mock", nocollect && "nocollect", flush && "flush", className)} style={style}>{children}</section>
);

/* Marca: só wordmark tipográfico em TOTVS Bold — não existe símbolo (decisão 27/07/2026). */
export const Wordmark = ({ size = 19, style }) => <span className="wordmark" style={{ fontSize: size, ...style }}>CITADEL</span>;
export const TotvsLogo = ({ white, height = 15, style }) => <img src={white ? totvsBranco : totvsAzul} alt="TOTVS" style={{ height, display: "block", ...style }} />;

/* Número-herói: Archivo expandida 124 %, numerais tabulares. */
export const Metric = ({ children, size = 44, color, style }) => <span className="hero num" style={{ fontSize: size, color, ...style }}>{children}</span>;

export function LangToggle() {
  const [lang, setLang] = useLang();
  return (
    <span role="group" aria-label="idioma / language" className="seg">
      {["pt", "en"].map((l) => <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}>{l.toUpperCase()}</button>)}
    </span>
  );
}
export function ThemeToggle({ theme, onChange }) {
  const dark = theme === "dark";
  return (
    <button type="button" className="iconbtn" onClick={() => onChange(dark ? "light" : "dark")} aria-label="tema claro/escuro" title={dark ? "tema claro" : "tema escuro"}>
      {dark ? "☀" : "☾"}
    </button>
  );
}

/* Banner de estado: glifo + cor + texto; origem/idade/confiança no `meta`, ação/chip nos filhos. */
export function Banner({ state = "info", title, meta, children }) {
  const s = STATUS_STATES[state] || STATUS_STATES.info;
  return (
    <div className="banner" role={state === "crit" || state === "emergency" ? "alert" : "status"} style={{ "--b-color": s.color, "--b-bg": s.bg }}>
      <span className="glyph" aria-hidden="true">{s.glyph}</span>
      <div style={{ flex: 1, minWidth: 200 }}>
        <div style={{ fontWeight: 600 }}>{title}</div>
        {meta && <div className="xs muted" style={{ marginTop: 2 }}>{meta}</div>}
      </div>
      {children}
    </div>
  );
}

export const ToggleChip = ({ on, onClick, children }) => <button type="button" className="toggle" aria-pressed={on} onClick={onClick}>{children}</button>;

/* O desconhecido também é um estado: ausência de dado é comunicada, nunca omitida. */
export const NoData = ({ height = 150, label = "◌ sem coleta" }) => <div className="nodata" role="status" style={{ height }}>{label}</div>;

export function TextArea({ label, value, onChange, placeholder, rows = 4 }) {
  return (
    <label className="field">
      {label && <span>{label}</span>}
      <textarea rows={rows} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}
