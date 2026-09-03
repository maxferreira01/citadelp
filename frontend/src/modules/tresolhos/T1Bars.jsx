/* Barras horizontais count/limit, cor por usage_pct (molde do ranking do Corvo). */
import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import { ProvenanceChip } from "@ds";
import { Cap, Card, NoData } from "../../ui.jsx";

const tick = { fontSize: 10.5, fontFamily: "var(--font-mono)" };
const cor = (pct) => (pct >= 90 ? "var(--state-crit)" : pct >= 70 ? "var(--cap-limit-op)" : "var(--cap-consumed)");

export default function T1Bars({ rows, nameKey, title, semLimite }) {
  const data = rows.map((r) => ({ k: r[nameKey], n: r.t1_count, lim: semLimite ? null : r.limit, pct: semLimite ? 0 : r.usage_pct, direto: r.t1_direct, vrf: r.t1_via_vrf }));
  return (
    <Card>
      <div className="card-head"><Cap>{title} — {rows.length}</Cap><ProvenanceChip method="OBS" source="nsx-collector → InfluxDB" /></div>
      {!rows.length ? <NoData height={80} /> : (
        <div style={{ height: Math.max(120, data.length * 26 + 30), marginTop: 10 }}>
          <ResponsiveContainer>
            <BarChart data={data} layout="vertical" margin={{ left: 4, right: 64, top: 2, bottom: 0 }}>
              <CartesianGrid horizontal={false} stroke="var(--hairline)" />
              <XAxis type="number" allowDecimals={false} tick={tick} stroke="var(--text-faint)" />
              <YAxis type="category" dataKey="k" width={170} tick={tick} stroke="var(--text-faint)" />
              <Tooltip cursor={{ fill: "var(--selection)" }}
                contentStyle={{ fontFamily: "var(--font-mono)", fontSize: 11, border: "1px solid var(--hairline)", borderRadius: "var(--radius-md)", background: "var(--surface)", color: "var(--ink)" }}
                formatter={(v, _n, it) => [`${v} de ${it.payload.lim} (${it.payload.pct} %)` + (it.payload.direto != null ? ` · ${it.payload.direto} direto + ${it.payload.vrf} em VRF` : ""), "T1"]} />
              <Bar dataKey="n" radius={[0, 3, 3, 0]}>
                {data.map((r) => <Cell key={r.k} fill={cor(r.pct)} />)}
                <LabelList dataKey="n" position="right" content={({ x, y, width, height, value, index }) => (
                  <text x={x + width + 4} y={y + height / 2 + 4} style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, fill: "var(--ink)" }}>{data[index].lim != null ? `${value}/${data[index].lim}` : value}</text>
                )} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
