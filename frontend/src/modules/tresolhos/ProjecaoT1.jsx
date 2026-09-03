/* Projeção (modelo da planilha "Capacity 2k29", linhas 1–18).
   Parte do edge produtivo (TESP7) com o realizado do Influx e projeta mês a mês:
   fase 1 = baseline + MI até o mês de corte; fase 2 = baseline do ano seguinte;
   capacity = 2.000 + extras (+400 por edge node) e troca de site quando nasce. */
import React, { useEffect, useRef, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import { Button, DataTable, ProvenanceChip, Select, StatusBadge, TextField } from "@ds";
import { api } from "../../api.js";
import { fmt } from "../../mock.js";
import { Banner, Cap, Card } from "../../ui.jsx";
import { EDGE_PRODUTIVO } from "./useNsxT1.js";
import CriadosPorPeriodo from "./CriadosPorPeriodo.jsx";

const PROJ_DEFAULT = {
  fase1: 139, mi: 16, fase1Ate: "2026-12", fase2: 130, meses: 24, limite: 2000,
  extras: [{ mes: "2026-10", t1: 400, desc: "TESP07 · EDGE NODE04" }, { mes: "2027-01", t1: 400, desc: "TESP07 · novo par (EDGE NODE05)" }],
  novoSite: { mes: "2027-06", nome: "TESP07B", capacity: 2400 },
};
const LS_PROJ = "citadel_proj_t1";
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const addMes = (ym, k) => { const [y, m] = ym.split("-").map(Number); const d = new Date(Date.UTC(y, m - 1 + k, 1)); return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`; };
const fmtYM = (ym) => { const [y, m] = ym.split("-"); return `${MESES[+m - 1]}/${y.slice(2)}`; };
const tick = { fontSize: 10, fontFamily: "var(--font-mono)" };
const tooltip = { fontFamily: "var(--font-mono)", fontSize: 11, border: "1px solid var(--hairline)", borderRadius: "var(--radius-md)", background: "var(--surface)", color: "var(--ink)" };

/* Séries por site: o site base congela quando o novo entra; o novo nasce em 0. */
export function projetarBruno(p, atual, inicioYM, base = EDGE_PRODUTIVO) {
  const series = [{ nome: base, acc: atual, cap: p.limite, ativo: true, pontos: [] }];
  const linhas = []; let esgotouEm = null;
  for (let k = 1; k <= p.meses; k++) {
    const ym = addMes(inicioYM, k);
    const cresc = ym <= p.fase1Ate ? p.fase1 + p.mi : p.fase2;
    const eventos = [];
    if (p.novoSite.nome && ym === p.novoSite.mes) {
      series.forEach((sr) => { sr.ativo = false; });
      series.push({ nome: p.novoSite.nome, acc: 0, cap: p.novoSite.capacity, ativo: true, pontos: [] });
      eventos.push(`${p.novoSite.nome} entra com ${fmt(p.novoSite.capacity)} — ${base} congela`);
    }
    const ativo = series[series.length - 1];
    p.extras.filter((e) => e.mes === ym).forEach((e) => { ativo.cap += +e.t1; eventos.push(`+${e.t1} ${e.desc}`); });
    ativo.acc += cresc;
    series.forEach((sr) => { while (sr.pontos.length < k - 1) sr.pontos.push({ ym: null, acc: null, cap: null }); sr.pontos.push({ ym, acc: sr.acc, cap: sr.cap }); });
    const restante = ativo.cap - ativo.acc;
    if (restante < 0 && !esgotouEm) esgotouEm = ym;
    linhas.push({ ym, site: ativo.nome, cresc, acc: ativo.acc, cap: ativo.cap, restante, eventos, total: series.reduce((t, sr) => t + sr.acc, 0) });
  }
  return { linhas, esgotouEm, series };
}

/* Mapa do que está por vir: uma linha por site (o produtivo congela, o novo nasce), capacity tracejada, crosshair. */
const SERIE_COR = ["var(--cap-consumed)", "var(--dq-manual)", "var(--petrol-300)"]; // site produtivo · novo site · 3º
function MapaPorVir({ r, esc }) {
  const [hi, setHi] = useState(null);
  const ref = useRef(null);
  const W = 640, h = 220, n = r.linhas.length;
  const x = (i) => 40 + (i * (W - 56)) / Math.max(1, n - 1);
  const y = (v) => 14 + (h - 44) * (1 - v / esc);
  const path = (pts, key) => { let d = "", pen = false; pts.forEach((pt, i) => { if (pt[key] == null) { pen = false; return; } d += `${pen ? "L" : "M"}${x(i)},${y(pt[key])}`; pen = true; }); return d; };
  const onMove = (e) => { const box = ref.current.getBoundingClientRect(); const px = ((e.clientX - box.left) / box.width) * W; const i = Math.round(((px - 40) / (W - 56)) * (n - 1)); setHi(Math.max(0, Math.min(n - 1, i))); };
  const li = hi != null ? r.linhas[hi] : null;
  const esg = r.esgotouEm ? r.linhas.findIndex((l) => l.ym === r.esgotouEm) : -1;
  return (
    <Card>
      <div className="card-head">
        <Cap>mapa do que está por vir — acumulado por site × capacity</Cap>
        <span className="legend">
          {r.series.map((sr, i) => <span key={sr.nome}><i style={{ width: 14, height: 2, background: SERIE_COR[i % SERIE_COR.length], verticalAlign: 3 }} />{sr.nome}</span>)}
          <span><i style={{ width: 14, height: 0, borderTop: "2px dashed var(--cap-limit-op)", verticalAlign: 3 }} />capacity</span>
        </span>
      </div>
      <svg ref={ref} viewBox={`0 0 ${W} ${h}`} onMouseMove={onMove} onMouseLeave={() => setHi(null)} style={{ width: "100%", height: "auto", display: "block", marginTop: 8, cursor: "crosshair" }} role="img" aria-label="T1 acumulados por mês, por site, contra a capacity disponível">
        {[0, .5, 1].map((f) => <g key={f}><line x1={40} x2={W - 16} y1={y(esc * f)} y2={y(esc * f)} stroke="var(--hairline)" strokeDasharray="2 3" /><text x={36} y={y(esc * f) + 3} textAnchor="end" style={{ font: "500 9px var(--font-mono)", fill: "var(--text-faint)" }}>{fmt(Math.round(esc * f))}</text></g>)}
        {r.linhas.map((l, i) => l.eventos.length ? <g key={"e" + i}><line x1={x(i)} x2={x(i)} y1={12} y2={h - 26} stroke="var(--state-info)" strokeDasharray="3 3" opacity=".7" /><title>{l.eventos.join(" · ")}</title></g> : null)}
        {r.series.map((sr, i) => (
          <g key={sr.nome}>
            <path d={path(sr.pontos, "cap")} fill="none" stroke="var(--cap-limit-op)" strokeWidth="1.4" strokeDasharray="5 4" opacity={i === r.series.length - 1 ? 1 : .55} />
            <path d={path(sr.pontos, "acc")} fill="none" stroke={SERIE_COR[i % SERIE_COR.length]} strokeWidth="2" />
          </g>
        ))}
        {esg >= 0 && <g><circle cx={x(esg)} cy={y(r.linhas[esg].acc)} r={5} fill="var(--state-crit)" stroke="var(--surface)" strokeWidth="1.5" /><text x={x(esg)} y={y(r.linhas[esg].acc) - 9} textAnchor="middle" style={{ font: "600 9.5px var(--font-mono)", fill: "var(--state-crit)" }}>{r.linhas[esg].site} esgota {fmtYM(r.esgotouEm)}</text></g>}
        {r.linhas.map((l, i) => (i % 3 === 0 || i === n - 1) ? <text key={"t" + i} x={x(i)} y={h - 8} textAnchor="middle" style={{ font: "500 9px var(--font-mono)", fill: "var(--text-faint)" }}>{fmtYM(l.ym)}</text> : null)}
        {hi != null && (
          <g>
            <line x1={x(hi)} x2={x(hi)} y1={10} y2={h - 26} stroke="var(--ink)" opacity=".5" />
            {r.series.map((sr, i) => sr.pontos[hi].acc != null && <circle key={sr.nome} cx={x(hi)} cy={y(sr.pontos[hi].acc)} r={4} fill={SERIE_COR[i % SERIE_COR.length]} stroke="var(--surface)" strokeWidth="1.5" />)}
          </g>
        )}
      </svg>
      <div className="num" style={{ marginTop: 6, minHeight: 18, fontSize: 11 }}>
        {li ? (
          <>
            <b>{fmtYM(li.ym)}</b>
            {r.series.map((sr, i) => sr.pontos[hi].acc != null && (
              <span key={sr.nome} style={{ marginLeft: 12 }}>
                <span style={{ color: SERIE_COR[i % SERIE_COR.length] }}>■</span> {sr.nome} {fmt(sr.pontos[hi].acc)} / {fmt(sr.pontos[hi].cap)}{" "}
                <span style={{ color: sr.pontos[hi].cap - sr.pontos[hi].acc < 0 ? "var(--state-crit)" : "var(--text-muted)" }}>({sr.pontos[hi].cap - sr.pontos[hi].acc >= 0 ? "+" : ""}{fmt(sr.pontos[hi].cap - sr.pontos[hi].acc)})</span>
              </span>
            ))}
            <span className="muted" style={{ marginLeft: 12 }}>total {fmt(li.total)}</span>
            {li.eventos.length > 0 && <span style={{ marginLeft: 12, color: "var(--state-info)" }}>{li.eventos.join(" · ")}</span>}
          </>
        ) : <span className="faint">passe o mouse para ler mês a mês · parâmetros acima recalculam ao vivo</span>}
      </div>
    </Card>
  );
}

const COLS_MES = [
  { key: "mes", label: "mês", mono: true }, { key: "site", label: "site ativo" }, { key: "cresc", label: "cresc. MoM", align: "right", mono: true },
  { key: "acc", label: "acumulado", align: "right", mono: true }, { key: "cap", label: "capacity", align: "right", mono: true },
  { key: "restante", label: "restante", align: "right" }, { key: "total", label: "total parque", align: "right", mono: true }, { key: "evento", label: "evento" },
];

export default function ProjecaoT1({ sites }) {
  const [p, setP] = useState(() => { try { return { ...PROJ_DEFAULT, ...JSON.parse(localStorage.getItem(LS_PROJ) || "{}") }; } catch { return PROJ_DEFAULT; } });
  const [rodou, setRodou] = useState(null);
  const [obs, setObs] = useState(null); // crescimento observado (OBS): creation time da Manager, ou Influx como fallback
  // site base da projeção: default = edge produtivo, mas dá para projetar qualquer um
  const [base, setBase] = useState(EDGE_PRODUTIVO);
  const prod = sites.find((s) => s.site === base) || sites.find((s) => s.site === EDGE_PRODUTIVO);
  const atual = prod?.total ?? 0;
  useEffect(() => {
    let vivo = true;
    setObs(null);
    api(`/nsx/t1/crescimento?site=${base}`).then((c) => {
      if (!vivo) return;
      setObs({ fonte: "criacao", porMes: Math.round(c.media_criados_3m || 0), mesesMedia: c.meses_fechados_na_media || [], snapshot: c.snapshot, snapshots: c.snapshots, primeiro: c.primeiro_t1, total: c.total_t1, sumiram: c.sumiram_desde_snapshot_anterior, porMesLista: c.por_mes });
    }).catch(() => {
      Promise.all([api(`/nsx/t1/historico?site=${base}&dias=120`), api(`/nsx/t1/eventos?site=${base}&dias=120`)]).then(([h, ev]) => {
        if (!vivo) return;
        const pts = h.filter((x) => x.total != null);
        if (pts.length < 2) return;
        const d0 = new Date(pts[0].quando), d1 = new Date(pts[pts.length - 1].quando), dias = Math.max(1, (d1 - d0) / 864e5);
        const meses = {};
        ev.forEach((e) => { const k = e.quando.slice(0, 7); meses[k] = meses[k] || { criados: 0, removidos: 0 }; meses[k][e.event === "created" ? "criados" : "removidos"]++; });
        setObs({ fonte: "influx", porMes: Math.round(((pts[pts.length - 1].total - pts[0].total) / dias) * 30.4), dias: Math.round(dias), de: pts[0].quando.slice(0, 10), t0: pts[0].total, t1: pts[pts.length - 1].total });
      }).catch(() => vivo && setObs(null));
    });
    return () => { vivo = false; };
  }, [base]);
  const hoje = new Date(); const inicioYM = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;
  const set = (k, v) => setP((o) => ({ ...o, [k]: v }));
  const num = (k) => (v) => set(k, +v);
  const setExtra = (i, k, v) => setP((o) => ({ ...o, extras: o.extras.map((e, j) => (j === i ? { ...e, [k]: v } : e)) }));
  const rodar = () => { setRodou(projetarBruno(p, atual, inicioYM, base)); try { localStorage.setItem(LS_PROJ, JSON.stringify(p)); } catch { /* sem storage */ } };
  useEffect(() => { if (rodou) setRodou(projetarBruno(p, atual, inicioYM, base)); }, [p, atual, base]); // recálculo ao vivo após a 1ª execução
  const r = rodou;
  const esc = r ? Math.max(...r.series.flatMap((sr) => sr.pontos.flatMap((pt) => [pt.acc || 0, pt.cap || 0]))) * 1.05 : 1;
  const linhasMes = r ? r.linhas.map((l) => {
    const st = l.restante < 0 ? "crit" : l.restante < l.cap * 0.15 ? "warn" : "ok";
    return { id: l.ym, mes: fmtYM(l.ym), site: l.site, cresc: `+${l.cresc}`, acc: fmt(l.acc), cap: <span style={{ color: "var(--cap-limit-op)" }}>{fmt(l.cap)}</span>, restante: <StatusBadge state={st} label={fmt(l.restante)} />, total: <span className="muted">{fmt(l.total)}</span>, evento: <span className="xs muted">{l.eventos.join(" · ")}</span> };
  }) : [];
  return (
    <div className="stack">
      <Card>
        <div className="card-head">
          <Cap>projeção — parte do site base{base === EDGE_PRODUTIVO ? " (edge produtivo)" : ""}</Cap>
          <span className="row" style={{ gap: 6 }}>
            {sites.length > 1 && (
              <Select value={base} options={sites.map((x) => ({ value: x.site, label: `${x.site} · ${fmt(x.total ?? 0)}` }))} onChange={setBase} style={{ width: 170 }} />
            )}
            <ProvenanceChip method="OBS" source={`${base} hoje = ${fmt(atual)} T1`} />
            <ProvenanceChip method="MAN" source="premissas da planilha Capacity 2k29" />
          </span>
        </div>
        {obs && obs.fonte === "criacao" && (
          <div className="num muted" style={{ marginTop: 8, fontSize: 11.5 }}>
            {base}: {fmt(obs.total)} T1 · primeiro T1 em {obs.primeiro?.slice(0, 10)} · snapshot {obs.snapshot?.slice(0, 16).replace("T", " ")} ({obs.snapshots} snapshot{obs.snapshots > 1 ? "s" : ""}{obs.sumiram ? ` · ${obs.sumiram} sumiram desde o anterior` : ""}) · atualizar: <code>scripts/nsx_t1capacity.py --site {base} --criacao</code>
          </div>
        )}
        {obs && obs.fonte === "influx" && (
          <div className="num" style={{ marginTop: 8, fontSize: 11.5, color: "var(--state-warn)" }}>
            ◐ sem snapshot de criação — usando o Influx (histórico desde {obs.de}). Rode <code>scripts/nsx_t1capacity.py --site {EDGE_PRODUTIVO} --criacao</code> para o histórico completo.
          </div>
        )}
        <CriadosPorPeriodo site={base} media={obs?.porMes} fonte={obs?.fonte} porMesSnapshot={obs?.fonte === "criacao" ? obs.porMesLista : null} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "10px 18px", marginTop: 12 }}>
          <div>
            <TextField label="crescimento/mês (baseline dez–mai)" type="number" mono value={String(p.fase1)} onChange={num("fase1")} />
            {obs && (
              <div className="row" style={{ marginTop: 6, gap: 6 }}>
                <ProvenanceChip method="OBS" source={obs.fonte === "criacao" ? `observado ${obs.porMes}/mês · média ${obs.mesesMedia.map(fmtYM).join(", ")} · creation time NSX` : `observado ${obs.porMes}/mês · ${fmt(obs.t0)}→${fmt(obs.t1)} em ${obs.dias} d (Influx)`} />
                <Button variant="secondary" size="sm" onClick={() => setP((o) => ({ ...o, fase1: obs.porMes, mi: 0 }))}>usar observado</Button>
              </div>
            )}
          </div>
          <TextField label="MI/mês (clientes até fim de 2026)" type="number" mono value={String(p.mi)} onChange={num("mi")} />
          <TextField label="fase 1 vale até" type="month" mono value={p.fase1Ate} onChange={(v) => set("fase1Ate", v)} />
          <TextField label="crescimento/mês depois (baseline 2k27)" type="number" mono value={String(p.fase2)} onChange={num("fase2")} />
          <TextField label="limite por datacenter" type="number" mono value={String(p.limite)} onChange={num("limite")} />
          <TextField label="horizonte (meses)" type="number" mono value={String(p.meses)} onChange={num("meses")} />
        </div>
        <div className="stack" style={{ gap: 8, marginTop: 14 }}>
          <Cap>T1 extras por edge (capacity que entra)</Cap>
          {p.extras.map((e, i) => (
            <div key={i} style={{ display: "grid", gridTemplateColumns: "150px 90px minmax(180px,1fr) auto", gap: 8, alignItems: "end" }}>
              <TextField type="month" mono value={e.mes} onChange={(v) => setExtra(i, "mes", v)} />
              <TextField type="number" mono value={String(e.t1)} onChange={(v) => setExtra(i, "t1", +v)} />
              <TextField value={e.desc} placeholder="descrição" onChange={(v) => setExtra(i, "desc", v)} />
              <Button variant="ghost" size="sm" onClick={() => setP((o) => ({ ...o, extras: o.extras.filter((_, j) => j !== i) }))} style={{ marginBottom: 2 }}>remover</Button>
            </div>
          ))}
          <div><Button variant="secondary" size="sm" onClick={() => setP((o) => ({ ...o, extras: [...o.extras, { mes: addMes(inicioYM, 3), t1: 400, desc: "" }] }))}>+ edge extra</Button></div>
          <Cap style={{ marginTop: 6 }}>novo site (zera a contagem)</Cap>
          <div style={{ display: "grid", gridTemplateColumns: "150px 150px 100px auto", gap: 8, alignItems: "end" }}>
            <TextField type="month" mono value={p.novoSite.mes} onChange={(v) => set("novoSite", { ...p.novoSite, mes: v })} />
            <TextField mono value={p.novoSite.nome} placeholder="nome (vazio = sem novo site)" onChange={(v) => set("novoSite", { ...p.novoSite, nome: v })} />
            <TextField type="number" mono value={String(p.novoSite.capacity)} onChange={(v) => set("novoSite", { ...p.novoSite, capacity: +v })} />
            <span className="muted sm" style={{ marginBottom: 10 }}>T1 de capacity</span>
          </div>
        </div>
        <div className="row" style={{ marginTop: 14, gap: 10 }}>
          <Button onClick={rodar} disabled={!prod}>Gerar previsão</Button>
          <Button variant="secondary" onClick={() => { setP(PROJ_DEFAULT); setRodou(null); try { localStorage.removeItem(LS_PROJ); } catch { /* sem storage */ } }}>Restaurar planilha</Button>
          {!prod && <span className="sm" style={{ color: "var(--state-crit)" }}>▲ sem dado de {base} no Influx</span>}
        </div>
      </Card>
      {r && (
        <>
          <Banner state={r.esgotouEm ? "warn" : "ok"}
            title={r.esgotouEm ? `Capacity do ${r.linhas.find((l) => l.ym === r.esgotouEm)?.site} esgota em ${fmtYM(r.esgotouEm)} com as premissas atuais.` : `Não esgota no horizonte de ${p.meses} meses.`}
            meta={`Última linha: ${fmt(r.linhas[r.linhas.length - 1].acc)} T1 em ${r.linhas[r.linhas.length - 1].site}, restante ${fmt(r.linhas[r.linhas.length - 1].restante)}.`} />
          <MapaPorVir r={r} esc={esc} />
          <Card flush>
            <div className="card-head"><Cap>mês a mês (mesmas linhas da planilha: acumulado · MoM · capacity normal · evento)</Cap></div>
            <div className="tscroll"><DataTable columns={COLS_MES} rows={linhasMes} density="compact" style={{ border: 0, borderTop: "1px solid var(--hairline)" }} /></div>
          </Card>
        </>
      )}
    </div>
  );
}
