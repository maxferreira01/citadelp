/* CONSELHO — visão executiva: dois números-héroi (capacidade EST, sinais OBS) + decisões. */
import React from "react";
import { Button, ProvenanceChip, StatusBadge } from "@ds";
import { CAPACITY, DECISIONS } from "../mock.js";
import { Cap, Card, Metric } from "../ui.jsx";

export default function Conselho({ go }) {
  const risk = CAPACITY[0];
  return (
    <div className="stack">
      <div className="cols-2">
        <Card mock>
          <div className="card-head"><Cap>capacidade — risco mais próximo</Cap><ProvenanceChip method="EST" source="mock" /></div>
          <div className="metric-row">
            <Metric color="var(--cap-limit-op)">{risk.days}</Metric>
            <div style={{ fontSize: 13 }}>dias · NSX T1 · TESP07<br /><span className="xs muted">confiança {risk.conf} · expansão cotada no Tesouro</span></div>
          </div>
          <Button variant="ghost" size="sm" style={{ marginTop: 10, marginLeft: -11 }} onClick={() => go("tresolhos")}>Abrir Três Olhos →</Button>
        </Card>
        <Card>
          <div className="card-head"><Cap>sinais — ofensor do trimestre</Cap><ProvenanceChip method="OBS" source="Slack · 55 alertas" /></div>
          <div className="metric-row">
            <Metric color="var(--brand)">TESP3</Metric>
            <div style={{ fontSize: 13 }}>27 alertas de float IP · C3 lidera expurgando RDMs<br /><span className="xs muted">alerta de 27 jul ficou 13 h 42 sem atuação</span></div>
          </div>
          <Button variant="ghost" size="sm" style={{ marginTop: 10, marginLeft: -11 }} onClick={() => go("corvo")}>Abrir Corvo →</Button>
        </Card>
      </div>
      <Card>
        <Cap>o que exige decisão esta semana</Cap>
        <div className="list" style={{ marginTop: 8 }}>
          {DECISIONS.map(([st, txt, m]) => (
            <div key={txt} className="sm" style={{ display: "flex", gap: 10, alignItems: "baseline", padding: "9px 0" }}>
              <StatusBadge state={st} glyphOnly /><span style={{ flex: 1 }}>{txt}</span><ProvenanceChip method={m} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
