/* MURALHA — limites de plataforma: uso × alvo operacional × fabricante.
   NSX T1 é real (OBS · /nsx/t1/resumo, uma linha por site); o resto ainda é EST · mock. */
import React, { useEffect, useState } from "react";
import { DataTable, ProvenanceChip, StatusBadge } from "@ds";
import { api } from "../api.js";
import { LIMITS, fmt } from "../mock.js";
import { Cap, Card } from "../ui.jsx";
import { NSX_T1_OP_LIMIT } from "./tresolhos/useNsxT1.js";

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
  const [nsx, setNsx] = useState([]);
  const [err, setErr] = useState("");
  useEffect(() => { api("/nsx/t1/resumo").then(setNsx).catch((e) => setErr(String(e.message || e))); }, []);
  const linhasNsx = nsx.map((r) => ({ plat: "NSX-T", res: "Tier-1 Routers", edge: r.site, use: r.total ?? r.nsx_current ?? 0, op: NSX_T1_OP_LIMIT, vendor: null, src: "premissa arquitetura · 2k/DC", obs: true }));
  const rows = [...linhasNsx, ...LIMITS].map((l) => {
    const slack = Math.round(100 * (1 - l.use / l.op));
    const st = slack < 10 ? "crit" : slack < 35 ? "warn" : "ok";
    return {
      id: `${l.plat}·${l.res}·${l.edge}`,
      plat: l.plat, res: l.res, edge: l.edge, use: fmt(l.use),
      op: <span style={{ color: "var(--cap-limit-op)" }}>{fmt(l.op)}</span>,
      vendor: l.vendor != null ? fmt(l.vendor) : "—",
      slack: <StatusBadge state={st} label={`${slack} %`} />,
      src: <span className="xs muted">{l.src}{l.obs ? "" : " · mock"}</span>,
    };
  });
  return (
    <Card mock flush>
      <div className="card-head">
        <Cap>limites de plataforma — uso × operacional × fabricante</Cap>
        <span className="row" style={{ gap: 6 }}>
          {err ? <StatusBadge state="unavailable" label={`NSX T1 indisponível: ${err}`} /> : <ProvenanceChip method="OBS" source={`NSX T1 · ${nsx.length} sites`} />}
          <ProvenanceChip method="EST" source="demais — mock" />
        </span>
      </div>
      <div className="tscroll"><DataTable columns={COLS} rows={rows} density="compact" style={{ border: 0, borderTop: "1px solid var(--hairline)" }} /></div>
      <div className="card-foot">limite operacional ≠ limite de fabricante — premissa auditada, editável com histórico</div>
    </Card>
  );
}
