/* T1 criados e removidos por período — dinâmico em granularidade (dia · mês) e janela.
   Fonte: /nsx/t1/eventos (OBS · nsx-collector → InfluxDB), agregado no cliente.
   O snapshot de criação (CLI --criacao) dá o histórico completo desde o nascimento
   do site, mas só por mês e só quando existe; sem ele, a janela é a do Influx. */
import React, { useEffect, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import { ProvenanceChip } from "@ds";
import { api } from "../../api.js";
import { Cap, NoData, ToggleChip } from "../../ui.jsx";

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const JANELAS = { dia: [30, 90, 365], mes: [90, 365] };
const tick = { fontSize: 10, fontFamily: "var(--font-mono)" };
const tooltipCss = { fontFamily: "var(--font-mono)", fontSize: 11, border: "1px solid var(--hairline)", borderRadius: "var(--radius-md)", background: "var(--surface)", color: "var(--ink)" };

const rotulo = (k, gran) => (gran === "dia" ? `${k.slice(8, 10)}/${k.slice(5, 7)}` : `${MESES[+k.slice(5, 7) - 1]}/${k.slice(2, 4)}`);
const chaveDe = (iso, gran) => (gran === "dia" ? iso.slice(0, 10) : iso.slice(0, 7));

/* Baldes contíguos do início da janela até hoje — dia sem evento vale zero, e
   precisa aparecer: buraco escondido faz a série mentir sobre o ritmo. */
export function serie(eventos, gran, dias) {
  const fim = new Date(); fim.setUTCHours(0, 0, 0, 0);
  const ini = new Date(fim); ini.setUTCDate(ini.getUTCDate() - dias + 1);
  const mapa = new Map();
  for (const d = new Date(ini); d <= fim; d.setUTCDate(d.getUTCDate() + 1)) {
    const k = chaveDe(d.toISOString(), gran);
    if (!mapa.has(k)) mapa.set(k, { k, criados: 0, removidos: 0 });
  }
  for (const e of eventos) {
    const b = mapa.get(chaveDe(e.quando, gran));
    if (!b) continue;
    if (e.event === "created") b.criados++; else b.removidos++;
  }
  const hoje = chaveDe(new Date().toISOString(), gran);
  // o primeiro balde do mês pode estar cortado pelo início da janela — é parcial também
  const primeiro = chaveDe(ini.toISOString(), gran);
  const cortado = gran === "mes" && ini.getUTCDate() !== 1;
  return [...mapa.values()].map((b) => ({
    ...b,
    liquido: b.criados - b.removidos,
    parcial: b.k === hoje || (cortado && b.k === primeiro),
    rot: rotulo(b.k, gran),
  }));
}

export default function CriadosPorPeriodo({ site, media, fonte, porMesSnapshot }) {
  const [gran, setGran] = useState("mes");
  const [dias, setDias] = useState(365);
  const [tudo, setTudo] = useState(false); // histórico completo do snapshot (só por mês)
  const [eventos, setEventos] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let vivo = true;
    setEventos(null); setErr("");
    api(`/nsx/t1/eventos?site=${encodeURIComponent(site)}&dias=${dias}`)
      .then((d) => vivo && setEventos(d))
      .catch((e) => vivo && setErr(String(e.message || e)));
    return () => { vivo = false; };
  }, [site, dias]);

  useEffect(() => { if (gran === "dia") setTudo(false); }, [gran]);
  const janelas = JANELAS[gran] || JANELAS.mes;
  useEffect(() => { if (!janelas.includes(dias)) setDias(janelas[janelas.length - 1]); }, [gran]);

  const dados = useMemo(() => {
    if (tudo && porMesSnapshot?.length) {
      const hoje = new Date().toISOString().slice(0, 7);
      return porMesSnapshot.map((l) => ({ k: l.mes, criados: l.criados || 0, removidos: l.removidos || 0, liquido: (l.criados || 0) - (l.removidos || 0), parcial: l.mes === hoje, rot: rotulo(l.mes, "mes") }));
    }
    return eventos ? serie(eventos, gran, dias) : [];
  }, [eventos, gran, dias, tudo, porMesSnapshot]);

  const temRemocao = dados.some((d) => d.removidos > 0);
  const totalC = dados.reduce((a, d) => a + d.criados, 0);
  const totalR = dados.reduce((a, d) => a + d.removidos, 0);
  const rotulaBarra = dados.length <= 14;
  const muitos = dados.length > 12;
  /* Cobertura real: o Influx guarda menos do que a janela pedida (retenção).
     Dizer "365 d" quando só há 83 sugere um ano que não existe. */
  const primeiro = useMemo(() => (eventos?.length ? eventos.reduce((m, e) => (e.quando < m ? e.quando : m), eventos[0].quando).slice(0, 10) : null), [eventos]);
  const cobertura = primeiro ? Math.round((Date.now() - Date.parse(primeiro + "T00:00:00Z")) / 864e5) : null;
  const truncado = !tudo && cobertura != null && cobertura < dias - 2;
  const dataBR = (iso) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;

  return (
    <div style={{ marginTop: 10 }}>
      <div className="card-head">
        <Cap>T1 criados por {gran === "dia" ? "dia" : "mês"} · {site}</Cap>
        <span className="row" style={{ gap: 6 }}>
          <ToggleChip on={gran === "dia"} onClick={() => setGran("dia")}>dia</ToggleChip>
          <ToggleChip on={gran === "mes"} onClick={() => setGran("mes")}>mês</ToggleChip>
          <span style={{ width: 1, alignSelf: "stretch", background: "var(--hairline)", margin: "0 2px" }} />
          {janelas.map((d) => (
            <ToggleChip key={d} on={!tudo && dias === d} onClick={() => { setTudo(false); setDias(d); }}>{d} d</ToggleChip>
          ))}
          {gran === "mes" && porMesSnapshot?.length > 0 && (
            <ToggleChip on={tudo} onClick={() => setTudo(true)}>tudo</ToggleChip>
          )}
          {tudo
            ? <ProvenanceChip method="OBS" source="snapshot de criação · histórico completo" />
            : <ProvenanceChip method="OBS" source="eventos do collector" age={primeiro ? `desde ${dataBR(primeiro)}` : `${dias} d`} stale={truncado} />}
        </span>
      </div>

      {err && <div className="sm" role="alert" style={{ color: "var(--state-crit)", marginTop: 8 }}>▲ {err}</div>}
      {!err && !eventos && !tudo && <div className="muted sm" style={{ marginTop: 8 }}>carregando…</div>}
      {!err && dados.length > 0 && totalC + totalR === 0 && (
        <NoData height={90} label="◌ nenhum evento de T1 nesta janela" />
      )}
      {!err && dados.length > 0 && totalC + totalR > 0 && (
        <>
          <div className="row sm" style={{ gap: 14, marginTop: 6 }}>
            <span className="num"><b>{totalC}</b> criados</span>
            {temRemocao && <span className="num muted"><b>{totalR}</b> removidos</span>}
            <span className="num muted">líquido <b style={{ color: "var(--ink)" }}>{totalC - totalR >= 0 ? "+" : ""}{totalC - totalR}</b></span>
            {media != null && <span className="muted">média 3 m {media}/mês {fonte === "criacao" ? "(creation time)" : "(Influx)"}</span>}
          </div>
          <div style={{ height: gran === "dia" ? 190 : 175, marginTop: 6 }}>
            <ResponsiveContainer>
              <BarChart data={dados} margin={{ left: 4, right: 8, top: 18, bottom: 0 }} barCategoryGap={dados.length > 60 ? 0 : "10%"}>
                <CartesianGrid vertical={false} stroke="var(--hairline)" />
                <XAxis dataKey="rot" tick={tick} stroke="var(--text-faint)"
                  interval={dados.length > 60 ? Math.floor(dados.length / 12) : 0}
                  angle={muitos ? -35 : 0} textAnchor={muitos ? "end" : "middle"} height={muitos ? 42 : 24} />
                <YAxis allowDecimals={false} tick={tick} stroke="var(--text-faint)" width={36} />
                <Tooltip cursor={{ fill: "var(--selection)" }} contentStyle={tooltipCss}
                  labelFormatter={(l) => l}
                  formatter={(v, n, it) => [`${v}${n === "criados" && it.payload.removidos ? ` · líquido ${it.payload.liquido >= 0 ? "+" : ""}${it.payload.liquido}` : ""}${it.payload.parcial ? " (período incompleto)" : ""}`, n]} />
                <Bar dataKey="criados" name="criados" radius={[3, 3, 0, 0]}>
                  {dados.map((r) => <Cell key={r.k} fill="var(--cap-consumed)" fillOpacity={r.parcial ? 0.45 : 1} />)}
                  {rotulaBarra && <LabelList dataKey="criados" position="top" style={{ fontFamily: "var(--font-mono)", fontSize: 9.5, fill: "var(--ink)" }} />}
                </Bar>
                {temRemocao && (
                  <Bar dataKey="removidos" name="removidos" radius={[3, 3, 0, 0]}>
                    {dados.map((r) => <Cell key={r.k} fill="var(--petrol-300)" fillOpacity={r.parcial ? 0.45 : 1} />)}
                  </Bar>
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="legend">
            <span><i style={{ background: "var(--cap-consumed)" }} />criados</span>
            {temRemocao && <span><i style={{ background: "var(--petrol-300)" }} />removidos</span>}
            <span>barra clara = período incompleto</span>
            {truncado && <span style={{ marginLeft: "auto" }}>o Influx guarda {cobertura} d — a janela de {dias} d não acrescenta nada</span>}
            {!tudo && !truncado && <span style={{ marginLeft: "auto" }}>janela limitada pela retenção do Influx</span>}
          </div>
        </>
      )}
    </div>
  );
}
