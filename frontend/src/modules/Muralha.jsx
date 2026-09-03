/* MURALHA — limites de plataforma: uso × alvo operacional × fabricante (EST · mock). */
import React from "react";
import { DataTable, ProvenanceChip, StatusBadge } from "@ds";
import { LIMITS, fmt } from "../mock.js";
import { Cap, Card } from "../ui.jsx";

const COLS = [
  { key: "plat", label: "plataforma" },
  { key: "res", label: "recurso" },
  { key: "edge", label: "edge", mono: true },
  { key: "use", label: "uso", align: "right", mono: true },
  { key: "op", label: "limite op", align: "right", mono: true },
  { key: "vendor", label: "fabricante", align: "right", mono: true },
  { key: "slack", label: "folga op", align: "right" },
  { key: "src", label: "fonte do limite" },
];

export default function Muralha() {
  const rows = LIMITS.map((l) => {
    const slack = Math.round(100 * (1 - l.use / l.op));
    const st = slack < 10 ? "crit" : slack < 35 ? "warn" : "ok";
    return {
      id: `${l.plat}·${l.res}·${l.edge}`,
      plat: l.plat, res: l.res, edge: l.edge, use: fmt(l.use),
      op: <span style={{ color: "var(--cap-limit-op)" }}>{fmt(l.op)}</span>,
      vendor: fmt(l.vendor),
      slack: <StatusBadge state={st} label={`${slack} %`} />,
      src: <span className="xs muted">{l.src}</span>,
    };
  });
  return (
    <Card mock flush>
      <div className="card-head"><Cap>limites de plataforma — uso × operacional × fabricante</Cap><ProvenanceChip method="EST" source="mock — aguardando coletores" /></div>
      <div className="tscroll"><DataTable columns={COLS} rows={rows} density="compact" style={{ border: 0, borderTop: "1px solid var(--hairline)" }} /></div>
      <div className="card-foot">limite operacional ≠ limite de fabricante — premissa auditada, editável com histórico</div>
    </Card>
  );
}
