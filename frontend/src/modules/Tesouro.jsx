/* TESOURO — orçado × realizado (EST · mock). RunwayBar: realizado = consumido,
   85 % do orçado = limite operacional (âmbar), orçado = limite técnico (tinta). */
import React from "react";
import { ProvenanceChip, RunwayBar, STATUS_STATES } from "@ds";
import { BUDGET, brl } from "../mock.js";
import { Cap, Card } from "../ui.jsx";

export default function Tesouro() {
  return (
    <Card mock>
      <div className="card-head"><Cap>orçado × realizado 2026 — rede e segurança</Cap><ProvenanceChip method="EST" source="mock" /></div>
      <div className="stack" style={{ marginTop: 14 }}>
        {BUDGET.map((b) => {
          const p = Math.round((100 * b.real) / b.plan);
          const st = p > 85 ? "warn" : "ok";
          return (
            <RunwayBar key={b.cat} height={9} label={b.cat} usage={b.real} opLimit={b.plan * 0.85} techLimit={b.plan}
              days={`${STATUS_STATES[st].glyph} ${p} %`} state={st}
              caption={<><span>{brl(b.real)}</span><span>op 85 %</span><span>{brl(b.plan)}</span></>} />
          );
        })}
      </div>
      <div className="sm" style={{ marginTop: 16, paddingTop: 12, borderTop: "var(--border-hairline)" }}>
        Cotação em decisão: <b>expansão NSX T1 TESP07</b> — <span className="num">R$ 387.000</span> · runway pós-expansão 300+ dias.
      </div>
    </Card>
  );
}
