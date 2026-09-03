/* TRÊS OLHOS — capacidade e previsão. Só o limite de T1 NSX, com dado real
   (OBS · nsx-collector → InfluxDB via /nsx/t1/*). Primeiro item = alerta ativo.
   Abas: painel (três leituras empilhadas) · tabela (formato da planilha) · previsão (Capacity 2k29). */
import React, { useState } from "react";
import { ProvenanceChip, Select, Tabs, TrajectoryChart } from "@ds";
import { useT } from "../i18n.jsx";
import { fmt } from "../mock.js";
import { saturation } from "../capacity.js";
import { Banner, Cap, Card, NoData } from "../ui.jsx";
import { useNsxT1, NSX_T1_OP_LIMIT } from "./tresolhos/useNsxT1.js";
import MapaSite from "./tresolhos/MapaSite.jsx";
import MedidorParque from "./tresolhos/MedidorParque.jsx";
import TrajetoriaEventos from "./tresolhos/TrajetoriaEventos.jsx";
import TabelaT1 from "./tresolhos/TabelaT1.jsx";
import ProjecaoT1 from "./tresolhos/ProjecaoT1.jsx";
import T1Bars from "./tresolhos/T1Bars.jsx";

const ABAS = [{ id: "painel", label: "Painel" }, { id: "tabela", label: "Tabela" }, { id: "projecao", label: "Previsão" }];

export default function TresOlhos() {
  const t = useT();
  const [site, setSite] = useState("");
  const [aba, setAba] = useState("painel");
  const nsx = useNsxT1(site);
  const n = nsx.data;
  const alerta = n && n.days != null && n.days <= 180;
  const estado = nsx.err ? "crit" : !n ? (nsx.busy ? "info" : "nocollect") : alerta ? "crit" : "ok";
  const titulo = nsx.err ? `NSX T1: ${nsx.err}`
    : !n ? (nsx.busy ? "Carregando capacity de T1…" : "Sem coleta de T1.")
    : n.days != null ? `NSX T1 pode atingir o limite operacional em ${n.days} dias.` : "NSX T1 sem tendência de esgotamento no horizonte projetado.";
  const meta = n ? `${n.site} · ${fmt(n.usage)} de ${fmt(n.op)} T1 (limite 2k/DC) · projeção 90 d, confiança ${n.conf}` : undefined;
  const legado = n && n.hist.length > 0;
  return (
    <div className="stack">
      <Tabs items={ABAS} active={aba} onChange={setAba} />
      {aba === "tabela" && (n ? <TabelaT1 site={n.site} /> : <NoData height={120} />)}
      {aba === "projecao" && <ProjecaoT1 sites={nsx.sites} />}
      {aba === "painel" && (
        <>
          <Banner state={estado} title={titulo} meta={meta}>
            {nsx.sites.length > 1 && (
              <Select value={n ? n.site : site} options={nsx.sites.map((x) => ({ value: x.site, label: `${x.site} · ${fmt(x.total ?? 0)}` }))} onChange={setSite} style={{ width: 170 }} />
            )}
            <ProvenanceChip method="OBS" source="nsx-collector → InfluxDB" />
          </Banner>
          {n && <MapaSite site={n.site} t0={n.t0} vrf={n.vrf} />}
          {nsx.sites.length > 0 && <MedidorParque sites={nsx.sites} sel={n ? n.site : ""} onSel={setSite} />}
          {n && <TrajetoriaEventos site={n.site} hist={n.hist} datas={n.datas} proj={n.proj} op={n.op} eventos={n.eventos} days={n.days} conf={n.conf} />}
          {n && (
            <details>
              <summary className="cap">versão anterior (trajetória simples + barras)</summary>
              <div className="stack" style={{ marginTop: 10 }}>
                <Card>
                  <div className="card-head" style={{ marginBottom: 8 }}>
                    <span style={{ font: "600 14px var(--font-ui)", color: "var(--brand)" }}>{n.name}</span>
                    {n.days != null && <span className="num" style={{ fontWeight: 700, fontSize: 14, color: "var(--cap-limit-op)" }}>{n.days} {t("dias")} · {n.conf}</span>}
                  </div>
                  {legado
                    ? <TrajectoryChart width={830} height={170} history={n.hist} projection={n.proj} opLimit={n.op} max={Math.max(n.op, ...n.hist, ...n.proj) * 1.04} todayLabel={t("hoje")}
                        {...saturation({ hist: n.hist, proj: n.proj, op: n.op })} satLabel={n.days != null ? `+${n.days} d · ${n.conf}` : undefined}
                        ariaText={`${n.name}: ${fmt(n.usage)} de ${fmt(NSX_T1_OP_LIMIT)} (limite operacional)${n.days != null ? `; pode atingir o limite em ${n.days} dias, confiança ${n.conf}` : ""}.`} />
                    : <NoData height={170} />}
                  <div className="row" style={{ marginTop: 6, gap: 8 }}><ProvenanceChip method="OBS" source="histórico diário · nsx_t1_totals" /><ProvenanceChip method="CALC" source="projeção linear 90 d" /><ProvenanceChip method="MAN" source="limite op = 2.000 T1 por datacenter" /></div>
                </Card>
                <div className="cols-2">
                  <T1Bars rows={n.t0} nameKey="t0_name" title={`T1 por T0 (par de edges · direto + VRFs · limite 600) · ${n.site}`} />
                  <T1Bars rows={n.vrf} nameKey="vrf_name" title={`T1 por VRF · ${n.site}`} />
                </div>
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
}
