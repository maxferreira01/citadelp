/* Tabela no formato da planilha de capacity (Edge/Node/Limite/VRF/Dia/Mes/Ano/Qtd). */
import React, { useEffect, useState } from "react";
import { Button, DataTable, ProvenanceChip, StatusBadge } from "@ds";
import { api } from "../../api.js";
import { fmt } from "../../mock.js";
import { Cap, Card, ToggleChip } from "../../ui.jsx";
import { stT1 } from "./useNsxT1.js";

const COLS = [
  { key: "edge", label: "Edge", mono: true },
  { key: "node", label: "Node" },
  { key: "limite_node", label: "Limite-node", align: "right", mono: true },
  { key: "vrf", label: "vrf-number" },
  { key: "limite_vrf", label: "limite-vrf", align: "right", mono: true },
  { key: "dia", label: "Dia", align: "right", mono: true },
  { key: "mes", label: "Mes", align: "right", mono: true },
  { key: "ano", label: "Ano", align: "right", mono: true },
  { key: "qtd", label: "Qtd-vrf", align: "right" },
  { key: "total", label: "Total", align: "right", mono: true },
];
const CSV_HEAD = ["Edge", "Node", "Limite-node", "vrf-number", "limite-vrf", "Dia", "Mes", "Ano", "Qtd-vrf", "Total"];

export default function TabelaT1({ site }) {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");
  const [todos, setTodos] = useState(false);
  useEffect(() => {
    setRows(null); setErr("");
    api("/nsx/t1/tabela" + (todos ? "" : `?site=${encodeURIComponent(site)}`)).then(setRows).catch((e) => setErr(String(e.message || e)));
  }, [site, todos]);
  const csv = () => {
    const linhas = [CSV_HEAD.join(";"), ...(rows || []).map((r) => [r.edge, r.node, r.limite_node ?? "", r.vrf, r.limite_vrf ?? "", r.dia, r.mes, r.ano, r.qtd, r.total_edge ?? ""].join(";"))].join("\n");
    navigator.clipboard?.writeText(linhas);
  };
  const data = (rows || []).map((r, i) => {
    const direto = r.vrf === "(direto no T0)";
    const st = stT1((r.limite_vrf ? r.qtd / r.limite_vrf : 0) * 100);
    return {
      id: `${r.edge}·${r.node}·${r.vrf}·${i}`,
      edge: r.edge,
      node: direto ? <b>{r.node}</b> : r.node,
      limite_node: r.limite_node ?? "—",
      vrf: <span className={direto ? "muted" : undefined}>{r.vrf}{r.parent_inferido && <StatusBadge state="warn" label="pai inferido" style={{ marginLeft: 6 }} />}</span>,
      limite_vrf: r.limite_vrf ?? "—",
      dia: r.dia, mes: r.mes, ano: r.ano,
      qtd: <StatusBadge state={st} label={String(r.qtd)} />,
      total: r.total_edge != null ? <b>{fmt(r.total_edge)}</b> : "—",
    };
  });
  return (
    <Card flush>
      <div className="card-head">
        <Cap>tabela de capacity — {todos ? "todos os sites" : site}</Cap>
        <span className="row">
          <ToggleChip on={todos} onClick={() => setTodos((v) => !v)}>todos os sites</ToggleChip>
          <Button variant="secondary" size="sm" onClick={csv} disabled={!rows}>copiar CSV (;)</Button>
          <ProvenanceChip method="OBS" source="nsx-collector → InfluxDB" />
        </span>
      </div>
      {err && <div className="sm" role="alert" style={{ padding: "0 18px 14px", color: "var(--state-crit)" }}>▲ {err}</div>}
      {!rows && !err && <div className="muted sm" style={{ padding: "0 18px 14px" }}>carregando…</div>}
      {rows && rows.length === 0 && <div className="muted" style={{ padding: "0 18px 14px" }}>sem linhas</div>}
      {rows && rows.length > 0 && <div className="tscroll"><DataTable columns={COLS} rows={data} density="compact" style={{ border: 0, borderTop: "1px solid var(--hairline)" }} /></div>}
      <div className="card-foot">Node = T0 (par de edges; Limite-node 600 só na linha do T0) · Node em negrito = T1 pendurados direto no T0 (limite 200, como uma VRF) · Dia/Mes/Ano = data do último ponto do collector</div>
    </Card>
  );
}
