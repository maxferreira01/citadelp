/* TRÊS OLHOS — capacidade e previsão. Primeiro item = alerta ativo (readme do DS).
   Trajetória: sólida = observado · tracejada = projetado · âmbar = limite op · tinta = limite téc. */
import React, { useState } from "react";
import { ProvenanceChip, RunwayBar, TrajectoryChart } from "@ds";
import { useT } from "../i18n.jsx";
import { CAPACITY, fmt } from "../mock.js";
import { saturation, runwayLabel, trajectoryText } from "../capacity.js";
import { Banner, Cap, Card, NoData } from "../ui.jsx";

export default function TresOlhos() {
  const t = useT();
  const [sel, setSel] = useState("nsxt1");
  const r = CAPACITY.find((x) => x.id === sel);
  const risk = CAPACITY[0];
  return (
    <div className="stack">
      <Banner state="crit" title={`NSX T1 pode atingir o limite operacional em ${risk.days} dias.`}
        meta={`TESP07 · ${risk.usage} de ${risk.op} T1 · projeção 12 m, confiança ${risk.conf}`}>
        <ProvenanceChip method="EST" source="mock — aguardando nsx_collector" />
      </Banner>
      <Card mock>
        <div className="card-head" style={{ marginBottom: 8 }}>
          <span style={{ font: "600 14px var(--font-ui)", color: "var(--brand)" }}>{r.name}</span>
          {r.days && <span className="num" style={{ fontWeight: 700, fontSize: 14, color: "var(--cap-limit-op)" }}>{r.days} {t("dias")} · {r.conf}</span>}
        </div>
        {r.hist.length
          ? <TrajectoryChart width={830} height={170} history={r.hist} projection={r.proj} opLimit={r.op} techLimit={r.tech} todayLabel={t("hoje")}
              {...saturation(r)} satLabel={r.days ? `+${r.days} d · ${r.conf}` : undefined} ariaText={trajectoryText(r, fmt)} />
          : <NoData height={170} label={runwayLabel(r, t)} />}
      </Card>
      <Card mock>
        <Cap style={{ marginBottom: 10 }}>{t("runways por recurso")}</Cap>
        <div role="listbox" aria-label={t("runways por recurso")} className="stack" style={{ gap: 4 }}>
          {CAPACITY.map((x) => (
            <div key={x.id} role="option" aria-selected={sel === x.id} tabIndex={0} className="runway"
              onClick={() => setSel(x.id)} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setSel(x.id)}>
              <RunwayBar height={9} label={<span style={{ fontWeight: sel === x.id ? 600 : 400 }}>{x.name}</span>}
                usage={x.usage} opLimit={x.op} techLimit={x.tech} nocollect={x.st === "nocollect"} state={x.st}
                days={runwayLabel(x, t)} confidence={x.conf !== "—" ? x.conf : undefined} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
