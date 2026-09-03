/* (3) Trajetória 90 d com os eventos (▲ created ▼ deleted) sobre a linha.
   Sólida = observado · tracejada = projetado (CALC, linear) · âmbar = limite op. */
import React, { useState } from "react";
import { ProvenanceChip } from "@ds";
import { fmt } from "../../mock.js";
import { Cap, Card, NoData } from "../../ui.jsx";

const fmtD = (iso) => new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });

export default function TrajetoriaEventos({ site, hist, datas, proj, op, eventos, days, conf }) {
  const [hov, setHov] = useState(null);
  const h = 190, W = 640;
  if (!hist.length) return <Card><Cap>3 · trajetória · {site}</Cap><NoData height={80} /></Card>;
  const all = [...hist, ...proj];
  const min = Math.min(...all) * 0.985, max = Math.max(...all) * 1.01;
  const lo = Math.min(min, max - 1), hi = max;
  const PASSO = 30; // projetar() devolve pontos a cada 30 d: a projeção ocupa 90 d de largura, como o histórico
  const n = hist.length - 1 + (proj.length - 1) * PASSO;
  const x = (i) => 40 + (i * (W - 56)) / Math.max(1, n);
  const y = (v) => 14 + (h - 40) * (1 - (v - lo) / (hi - lo));
  const path = (arr, off = 0, passo = 1) => arr.map((v, i) => `${i ? "L" : "M"}${x(off + i * passo)},${y(v)}`).join(" ");
  const d0 = new Date(datas[0]), d1 = new Date(datas[datas.length - 1]);
  const idx = (iso) => { const t = new Date(iso); return Math.max(0, Math.min(hist.length - 1, Math.round(((t - d0) / (d1 - d0 || 1)) * (hist.length - 1)))); };
  const evs = eventos.map((e) => ({ ...e, i: idx(e.quando) }));
  const opDentro = op >= lo && op <= hi;
  const criados = eventos.filter((e) => e.event === "created").length, removidos = eventos.filter((e) => e.event === "deleted").length;
  const lbl = { font: "500 9.5px var(--font-mono)", fill: "var(--text-faint)" };
  return (
    <Card>
      <div className="card-head">
        <Cap>3 · trajetória 90 d com eventos · {site}</Cap>
        <span className="row" style={{ gap: 6 }}>
          {days != null && <span className="num" style={{ fontWeight: 700, fontSize: 13, color: "var(--cap-limit-op)" }}>{days} dias · {conf}</span>}
          <ProvenanceChip method="OBS" source={`${criados} created · ${removidos} deleted`} />
          <ProvenanceChip method="CALC" source="projeção linear" />
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${h}`} style={{ width: "100%", height: "auto", display: "block", marginTop: 8 }} role="img"
        aria-label={`total de T1 por dia em ${site}, com eventos de criação e remoção; ${days != null ? `pode atingir o limite operacional em ${days} dias, confiança ${conf}` : "sem tendência de esgotamento no horizonte"}`}>
        {[0, .5, 1].map((f) => { const v = lo + (hi - lo) * f; return <g key={f}><line x1={40} x2={W - 16} y1={y(v)} y2={y(v)} stroke="var(--hairline)" strokeDasharray="2 3" /><text x={36} y={y(v) + 3} textAnchor="end" style={{ font: "500 9px var(--font-mono)", fill: "var(--text-faint)" }}>{fmt(Math.round(v))}</text></g>; })}
        {opDentro && <><line x1={40} x2={W - 16} y1={y(op)} y2={y(op)} stroke="var(--cap-limit-op)" strokeDasharray="5 4" strokeWidth="1.3" /><text x={W - 16} y={y(op) - 4} textAnchor="end" style={{ font: "600 9.5px var(--font-mono)", fill: "var(--cap-limit-op)" }}>limite op · {fmt(op)}</text></>}
        {!opDentro && <text x={W - 16} y={12} textAnchor="end" style={{ font: "600 9.5px var(--font-mono)", fill: "var(--cap-limit-op)" }}>limite op · {fmt(op)} ↑ (faltam {fmt(op - hist[hist.length - 1])})</text>}
        <path d={path(hist)} fill="none" stroke="var(--cap-consumed)" strokeWidth="2" />
        <path d={path(proj, hist.length - 1, PASSO)} fill="none" stroke="var(--cap-consumed)" strokeWidth="1.6" strokeDasharray="6 5" opacity=".8" />
        <line x1={x(hist.length - 1)} x2={x(hist.length - 1)} y1={10} y2={h - 22} stroke="var(--ink)" opacity=".4" />
        <text x={x(hist.length - 1) - 4} y={h - 24} textAnchor="end" style={{ font: "500 9.5px var(--font-mono)", fill: "var(--text-muted)" }}>hoje · {fmtD(datas[datas.length - 1])}</text>
        {evs.map((e, k) => {
          const cx = x(e.i), cy = y(hist[e.i]), up = e.event === "created";
          return (
            <g key={k} onMouseEnter={() => setHov(e)} onMouseLeave={() => setHov(null)} style={{ cursor: "default" }}>
              <circle cx={cx} cy={cy} r={9} fill="transparent" />
              <path d={up ? `M${cx},${cy - 11} l5,8 h-10 z` : `M${cx},${cy + 11} l5,-8 h-10 z`} fill={up ? "var(--state-ok)" : "var(--state-crit)"} stroke="var(--surface)" strokeWidth="1.5" />
              <title>{`${fmtD(e.quando)} · ${e.event} · ${e.t1_name} → ${e.parent_name}`}</title>
            </g>
          );
        })}
        <text x={40} y={h - 6} style={lbl}>{fmtD(datas[0])}</text>
        <text x={W - 16} y={h - 6} textAnchor="end" style={lbl}>+90 d</text>
      </svg>
      <div className="legend" style={{ marginTop: 6 }}>
        <span style={{ color: "var(--state-ok)" }}>▲ created</span><span style={{ color: "var(--state-crit)" }}>▼ deleted</span><span>— observado · ‒ ‒ projetado</span>
        <span style={{ marginLeft: "auto", color: "var(--ink)" }}>{hov ? `${fmtD(hov.quando)} · ${hov.event} · ${hov.t1_name} → ${hov.parent_name} (${hov.edge_cluster_name})` : " "}</span>
      </div>
    </Card>
  );
}
