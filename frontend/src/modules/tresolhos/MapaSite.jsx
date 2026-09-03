/* (1) Mapa do site: um bloco por T0 (par de edges), pilha até 600, VRFs até 200. */
import React, { useState } from "react";
import { ProvenanceChip, StatusBadge } from "@ds";
import { fmt } from "../../mock.js";
import { Cap, Card } from "../../ui.jsx";
import { T0_LIMIT, VRF_LIMIT, stT1, stLabel, STATE_COLOR } from "./useNsxT1.js";

/* Pilha de um T0: um só matiz, escuro → claro (direto, vrf_1, vrf_2…) — parte-de-um-todo, não categoria. */
export const PILHA = ["var(--cap-consumed)", "var(--petrol-400)", "var(--petrol-200)", "var(--petrol-100)"];

function Segs({ t, onHover }) {
  const partes = [{ k: "direto no T0", n: t.t1_direct, c: PILHA[0] }, ...t.vrfs.map((v, i) => ({ k: v.vrf_name, n: v.t1_count, c: PILHA[Math.min(i + 1, PILHA.length - 1)] }))];
  const esc = Math.max(T0_LIMIT, t.t1_count);
  let acc = 0;
  return (
    <div className="track" style={{ height: 14, marginTop: 8 }}>
      {partes.filter((x) => x.n > 0).map((x, i) => {
        const l = (acc / esc) * 100, w = (x.n / esc) * 100; acc += x.n;
        return (
          <div key={x.k} title={`${x.k}: ${x.n} T1`} onMouseEnter={() => onHover(`${t.t0_name} · ${x.k}: ${x.n} T1`)} onMouseLeave={() => onHover(null)}
            style={{ position: "absolute", top: 0, bottom: 0, left: `${l}%`, width: `calc(${w}% - 2px)`, background: x.c, borderRadius: i === 0 ? "4px 0 0 4px" : 0, boxShadow: "2px 0 0 var(--surface)" }} />
        );
      })}
      <div title={`limite ${T0_LIMIT}`} style={{ position: "absolute", top: -3, bottom: -3, left: `${(T0_LIMIT / esc) * 100}%`, width: 2, background: "var(--cap-limit-op)" }} />
    </div>
  );
}

/* direto no T0 / cada VRF: mini-barra até 200 + glifo de estado */
function Linha({ nome, n, cor, title }) {
  const p = n / VRF_LIMIT, st = stT1(p * 100);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8, alignItems: "center", fontSize: 11, fontFamily: "var(--font-mono)" }}>
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}><span title={title}>{nome}</span><span className="num">{n}/{VRF_LIMIT}</span></div>
        <div className="track" style={{ height: 6, marginTop: 2 }}>
          <div title={`${nome}: ${n}/${VRF_LIMIT}`} style={{ position: "absolute", inset: "0 auto 0 0", width: `${Math.min(100, p * 100)}%`, background: cor, borderRadius: 3 }} />
        </div>
      </div>
      <StatusBadge state={st} glyphOnly />
    </div>
  );
}

export default function MapaSite({ site, t0, vrf }) {
  const [hov, setHov] = useState(null);
  const porT0 = t0.map((t) => ({ ...t, vrfs: vrf.filter((v) => v.t0_parent === t.t0_name) }));
  const soltas = vrf.filter((v) => !t0.some((t) => t.t0_name === v.t0_parent));
  return (
    <Card>
      <div className="card-head">
        <Cap>1 · mapa do site — T1 por par de edges (T0) e por VRF · {site}</Cap>
        <span className="row" style={{ gap: 6 }}><ProvenanceChip method="OBS" source="per_t0 + per_vrf" /><ProvenanceChip method="MAN" source="600/T0 = 200 direto + 200/VRF" /></span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 12, marginTop: 12 }}>
        {porT0.map((t) => {
          const st = stT1(t.usage_pct);
          return (
            <div key={t.t0_name} className="t0-card" style={{ "--t0-color": STATE_COLOR[st] }}>
              <div className="card-head">
                <span style={{ font: "600 12.5px var(--font-ui)" }}>{t.t0_name}</span>
                <StatusBadge state={st} label={`${fmt(t.t1_count)} / ${T0_LIMIT} · ${stLabel[st]}`} />
              </div>
              <Segs t={t} onHover={setHov} />
              <div className="stack" style={{ gap: 5, marginTop: 10 }}>
                <Linha nome="direto no T0" n={t.t1_direct} cor={PILHA[0]} />
                {t.vrfs.map((v, i) => (
                  <Linha key={v.vrf_name} n={v.t1_count} cor={PILHA[Math.min(i + 1, PILHA.length - 1)]}
                    nome={`${v.vrf_name.replace(t.t0_name + "-", "").replace(t.t0_name + "_", "")}${v.parent_inferido ? " ˙" : ""}`}
                    title={v.parent_inferido ? "T0 pai inferido pelo nome (collector gravou '-')" : undefined} />
                ))}
              </div>
            </div>
          );
        })}
        {soltas.length > 0 && (
          <div style={{ border: "1px dashed var(--hairline)", borderRadius: "var(--radius-md)", padding: "10px 12px", fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            <div style={{ font: "600 12.5px var(--font-ui)", color: "var(--ink)" }}>VRFs sem T0 resolvido</div>
            <div style={{ marginTop: 4 }}>o collector gravou t0_parent = "-" e o nome não bate com nenhum T0 do site</div>
            {soltas.map((v) => <div key={v.vrf_name} style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}><span>{v.vrf_name}</span><span className="num">{v.t1_count}/{VRF_LIMIT}</span></div>)}
          </div>
        )}
      </div>
      <div className="legend" style={{ marginTop: 10 }}>
        <span><i style={{ background: PILHA[0] }} />direto no T0</span>
        <span><i style={{ background: PILHA[1] }} />vrf_1</span>
        <span><i style={{ background: PILHA[2] }} />vrf_2</span>
        <span><i style={{ width: 2, background: "var(--cap-limit-op)" }} />limite 600</span>
        <span style={{ marginLeft: "auto" }}>{hov || " "}</span>
      </div>
    </Card>
  );
}
