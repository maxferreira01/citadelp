/* (2) Medidor do parque: os sites numa régua 0–2.000, zona de atenção a 85 %. */
import React from "react";
import { ProvenanceChip, StatusBadge } from "@ds";
import { fmt } from "../../mock.js";
import { Cap, Card } from "../../ui.jsx";
import { NSX_T1_OP_LIMIT, stT1, STATE_COLOR } from "./useNsxT1.js";

export default function MedidorParque({ sites, sel, onSel }) {
  const rows = [...sites].sort((a, b) => (b.total ?? 0) - (a.total ?? 0));
  const esc = Math.max(NSX_T1_OP_LIMIT, ...rows.map((r) => r.total ?? 0)) * 1.06;
  const pos = (v) => `${(v / esc) * 100}%`;
  const total = rows.reduce((a, r) => a + (r.total ?? 0), 0);
  const grid = { display: "grid", gridTemplateColumns: "120px 1fr 120px", gap: "6px 12px", alignItems: "center" };
  return (
    <Card>
      <div className="card-head">
        <Cap>2 · parque — T1 por datacenter contra o limite de 2.000</Cap>
        <span className="row" style={{ gap: 6 }}><ProvenanceChip method="OBS" source={`${rows.length} sites · ${fmt(total)} T1`} /><ProvenanceChip method="MAN" source="2.000/DC · atenção a 85 %" /></span>
      </div>
      <div style={{ ...grid, marginTop: 12 }}>
        {rows.map((r) => {
          const v = r.total ?? 0, pct = (100 * v) / NSX_T1_OP_LIMIT, st = stT1(pct), ativo = r.site === sel;
          return (
            <React.Fragment key={r.site}>
              <button type="button" className="linkbtn" aria-pressed={ativo} onClick={() => onSel(r.site)}>{r.site}</button>
              <div className="track" title={`${r.site}: ${fmt(v)} de ${fmt(NSX_T1_OP_LIMIT)} (${Math.round(pct)} %)`} style={{ height: 16 }}>
                <div style={{ position: "absolute", top: 0, bottom: 0, left: pos(NSX_T1_OP_LIMIT * 0.85), right: `calc(100% - ${pos(NSX_T1_OP_LIMIT)})`, background: "var(--state-warn-bg)" }} />
                <div style={{ position: "absolute", top: 0, bottom: 0, left: pos(NSX_T1_OP_LIMIT), right: 0, background: "var(--state-crit-bg)", borderRadius: "0 4px 4px 0" }} />
                <div style={{ position: "absolute", top: 3, bottom: 3, left: 0, width: pos(v), background: st === "ok" ? "var(--cap-consumed)" : STATE_COLOR[st], borderRadius: "0 3px 3px 0", opacity: ativo ? 1 : .85 }} />
                <div style={{ position: "absolute", top: -2, bottom: -2, left: pos(NSX_T1_OP_LIMIT), width: 2, background: "var(--cap-limit-op)" }} />
              </div>
              <StatusBadge state={st} label={`${fmt(v)} · ${Math.round(pct)} %`} />
            </React.Fragment>
          );
        })}
      </div>
      <div style={{ ...grid, gap: "0 12px", marginTop: 4 }}>
        <span />
        <div style={{ position: "relative", height: 12, fontSize: 9.5, fontFamily: "var(--font-mono)", color: "var(--text-faint)" }}>
          <span style={{ position: "absolute", left: 0 }}>0</span>
          <span style={{ position: "absolute", left: pos(NSX_T1_OP_LIMIT * 0.85), transform: "translateX(-50%)" }}>85 %</span>
          <span style={{ position: "absolute", left: pos(NSX_T1_OP_LIMIT), transform: "translateX(-50%)", color: "var(--cap-limit-op)" }}>2.000</span>
        </div>
        <span />
      </div>
    </Card>
  );
}
