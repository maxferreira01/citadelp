/* CORVO — sinais: raio-x do #alert-float-ip (OBS · 55 alertas reais). */
import React, { useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import { ProvenanceChip } from "@ds";
import { ALERTS, MONTHS, ACTIONS } from "../mock.js";
import { Cap, Card, Metric, ToggleChip } from "../ui.jsx";

const tick = { fontSize: 10.5, fontFamily: "var(--font-mono)" };

export default function Corvo() {
  const [months, setMonths] = useState(new Set(MONTHS));
  const [hideExp, setHideExp] = useState(true);
  const view = useMemo(() => {
    const inP = ALERTS.filter((a) => months.has(a.m));
    const rows = hideExp ? inP.filter((a) => !a.exp) : inP;
    const agg = {};
    rows.forEach((a) => { const k = `${a.e} C${a.c}`; agg[k] = agg[k] || { k, e: a.e, n: 0 }; agg[k].n++; });
    const rank = Object.values(agg).sort((x, y) => y.n - x.n);
    return { rows, rank, total: rows.length, excluded: inP.length - rows.length, top: rank[0] };
  }, [months, hideExp]);
  const tgl = (m) => setMonths((p) => { const n = new Set(p); n.has(m) ? n.delete(m) : n.add(m); return n; });

  return (
    <div className="stack">
      <Card className="row" style={{ padding: "12px 16px" }}>
        <Cap style={{ marginRight: 2 }}>ofensores · alert float ip</Cap>
        {MONTHS.map((m) => <ToggleChip key={m} on={months.has(m)} onClick={() => tgl(m)}>{m} 2026</ToggleChip>)}
        <span style={{ width: 1, alignSelf: "stretch", background: "var(--hairline)", margin: "0 4px" }} />
        <ToggleChip on={hideExp} onClick={() => setHideExp((v) => !v)}>excluir esperados (RDM)</ToggleChip>
        <span style={{ marginLeft: "auto" }}><ProvenanceChip method="OBS" source="varredura Slack" age="27 jul" /></span>
      </Card>
      {view.total === 0 ? (
        <Card className="muted" style={{ textAlign: "center", padding: 36 }}>Nenhum alerta no recorte. Selecione ao menos um mês.</Card>
      ) : (
        <>
          <Card className="row" style={{ gap: 24 }}>
            <div>
              <Metric size={40} color="var(--brand)">{view.top.k}</Metric>
              <Cap style={{ marginTop: 4 }}>maior ofensor do recorte</Cap>
            </div>
            <p style={{ flex: 1, minWidth: 260 }}>
              <b className="num">{view.top.n} de {view.total}</b> alertas ({Math.round((100 * view.top.n) / view.total)} %)
              {hideExp && view.excluded > 0 && <> — expurgados <b className="num">{view.excluded}</b> disparos de janelas de manutenção (flag MAN via relato do canal)</>}.
              {" "}TESP03 alarma em todos os meses independentemente de manutenção; o storm de perda de pacote do TESP06 em 20 mai segue sem tratamento registrado.
            </p>
          </Card>
          <div className="cols-2">
            <Card>
              <Cap>ranking — {view.total} alertas</Cap>
              <div style={{ height: Math.max(180, view.rank.length * 30 + 30), marginTop: 10 }}>
                <ResponsiveContainer>
                  <BarChart data={view.rank} layout="vertical" margin={{ left: 4, right: 30, top: 2, bottom: 0 }}>
                    <CartesianGrid horizontal={false} stroke="var(--hairline)" />
                    <XAxis type="number" allowDecimals={false} tick={tick} stroke="var(--text-faint)" />
                    <YAxis type="category" dataKey="k" width={80} tick={tick} stroke="var(--text-faint)" />
                    <Tooltip cursor={{ fill: "var(--selection)" }} formatter={(v) => [v + " alertas", ""]}
                      contentStyle={{ fontFamily: "var(--font-mono)", fontSize: 11, border: "1px solid var(--hairline)", borderRadius: "var(--radius-md)", background: "var(--surface)", color: "var(--ink)" }} />
                    <Bar dataKey="n" radius={[0, 3, 3, 0]}>
                      {view.rank.map((r, i) => <Cell key={r.k} fill={i === 0 ? "var(--petrol-700)" : r.e === "TESP3" ? "var(--petrol-500)" : "var(--petrol-200)"} />)}
                      <LabelList dataKey="n" position="right" style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, fill: "var(--ink)" }} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card>
              <div className="card-head"><Cap>atuações registradas no canal</Cap><ProvenanceChip method="OBS" /></div>
              <div className="list" style={{ marginTop: 10 }}>
                {ACTIONS.map((a) => (
                  <div key={a.ts} style={{ display: "grid", gridTemplateColumns: "82px 1fr", gap: 10, padding: "8px 0", fontSize: 12 }}>
                    <span className="num faint" style={{ fontSize: 11 }}>{a.ts}</span>
                    <span><b style={{ fontWeight: 600 }}>{a.who}</b> — {a.what}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
