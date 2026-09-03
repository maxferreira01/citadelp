/* VIGIA — gateway Checkmk federado (OBS): downtimes reais, criar/listar/remover, lote por RDM. */
import React, { useEffect, useState } from "react";
import { Button, DataTable, ProvenanceChip, Select, TextField, Toast } from "@ds";
import { api } from "../api.js";
import { useT } from "../i18n.jsx";
import { Banner, Cap, Card, TextArea } from "../ui.jsx";

const COLS = [
  { key: "site", label: "site", mono: true },
  { key: "host", label: "host", mono: true },
  { key: "servico", label: "serviço" },
  { key: "autor", label: "autor" },
  { key: "comentario", label: "comentário" },
  { key: "acao", label: "", align: "right" },
];

export default function Vigia() {
  const t = useT();
  const [sites, setSites] = useState([]);
  const [dt, setDt] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState(null); // { kind, text } → Toast
  const [fSite, setFSite] = useState("");
  const [fTipo, setFTipo] = useState("all");
  const [nv, setNv] = useState({ site: "", host_name: "", minutes: "60", comment: "", servicos: "" });
  const [rdm, setRdm] = useState({ rdm: "", minutes: "120", plan: "" });
  const ok = (text) => setMsg({ kind: "ok", text });
  const warn = (text) => setMsg({ kind: "warn", text });
  const fail = (text) => setMsg({ kind: "crit", text });

  const load = async (site = fSite, tipo = fTipo) => {
    setBusy(true); setErr("");
    try {
      const qs = new URLSearchParams();
      if (site) qs.set("site", site);
      if (tipo !== "all") qs.set("tipo", tipo);
      const [s, d] = await Promise.all([
        api("/checkmk/sites"),
        api("/checkmk/downtimes" + (qs.toString() ? `?${qs}` : "")),
      ]);
      setSites(s); setDt(d);
    } catch (e) { setErr(String(e.message || e)); }
    setBusy(false);
  };
  useEffect(() => { load(); }, []);

  const criar = async () => {
    if (!nv.site || !nv.host_name || !nv.comment) { warn("preencha site, host e comentário"); return; }
    setBusy(true); setMsg(null);
    try {
      const servicos = nv.servicos.split(",").map((s) => s.trim()).filter(Boolean);
      await api("/checkmk/downtimes", {
        method: "POST",
        body: JSON.stringify({ site: nv.site, host_name: nv.host_name, minutes: +nv.minutes, comment: nv.comment, servicos: servicos.length ? servicos : null }),
      });
      ok(`downtime criado: ${nv.host_name} · ${nv.minutes} min`);
      setNv({ site: "", host_name: "", minutes: "60", comment: "", servicos: "" });
      load();
    } catch (e) { fail("erro: " + e.message); }
    setBusy(false);
  };

  const remover = async (item, forcar = false) => {
    setBusy(true); setMsg(null);
    try {
      const out = await api("/checkmk/downtimes/remover", {
        method: "POST",
        body: JSON.stringify({ alvos: [{ site: item.site, id: String(item.id), host: item.host, servico: item.servico }], forcar_por_host: forcar }),
      });
      const r = out.recibos[0];
      if (r.requer_confirmacao && !forcar) {
        if (window.confirm(`Remoção por ID não resolveu neste site. Remover por host apaga ${r.atingidos ?? "TODOS os"} downtimes de ${item.host}. Continuar?`)) {
          await remover(item, true);
          return;
        }
        warn("remoção cancelada");
      } else if (r.ok) ok(`removido: ${item.host}${item.servico ? " · " + item.servico : ""}`);
      else fail("falhou: " + (r.erro || "confira o site"));
      load();
    } catch (e) { fail("erro: " + e.message); }
    setBusy(false);
  };

  const rdmCriar = async () => {
    const plan = rdm.plan.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
      const [site, host, servs] = l.split(/\s+/);
      return { site, host, services: servs ? servs.split(",").filter(Boolean) : null };
    });
    if (!rdm.rdm || !plan.length) { warn("informe a RDM e ao menos uma linha: site host [serv1,serv2]"); return; }
    setBusy(true); setMsg(null);
    try {
      const out = await api("/checkmk/downtimes/rdm", { method: "POST", body: JSON.stringify({ rdm: rdm.rdm, minutes: +rdm.minutes, plan }) });
      if (out.ok) ok(`RDM ${rdm.rdm}: ${out.receipts.length} silêncios aplicados`);
      else warn(`RDM ${rdm.rdm}: parcial — confira os recibos no backend`);
      setRdm({ rdm: "", minutes: "120", plan: "" });
      load();
    } catch (e) { fail("erro: " + e.message); }
    setBusy(false);
  };

  const siteOpts = sites.map((s) => ({ value: s.id, label: s.id }));
  const rows = (dt?.itens || []).map((it, i) => ({
    id: `${it.site}·${it.id}·${it.servico || ""}·${i}`,
    site: it.site,
    host: it.host,
    servico: it.servico || <span className="faint">{t("host inteiro")}</span>,
    autor: it.autor,
    comentario: <span className="muted" title={it.comentario} style={{ display: "inline-block", maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", verticalAlign: "bottom" }}>{it.comentario}</span>,
    acao: <Button size="sm" variant="secondary" disabled={busy} onClick={() => remover(it)}>{t("remover")}</Button>,
  }));

  return (
    <div className="stack">
      <Card className="row" style={{ padding: "12px 16px" }}>
        <Cap style={{ marginRight: 2 }}>{t("downtimes ativos")} · {sites.length} {t("sites federados")}</Cap>
        <Select value={fSite} options={[{ value: "", label: t("todos os sites") }, ...siteOpts]} onChange={(v) => { setFSite(v); load(v, fTipo); }} style={{ width: 170 }} />
        <Select value={fTipo} options={[{ value: "all", label: t("host + serviço") }, { value: "host", label: t("só host") }, { value: "service", label: t("só serviço") }]}
          onChange={(v) => { setFTipo(v); load(fSite, v); }} style={{ width: 150 }} />
        <Button variant="secondary" size="sm" onClick={() => load()} disabled={busy} style={{ marginLeft: "auto" }}>{busy ? "…" : t("Atualizar")}</Button>
        <ProvenanceChip method="OBS" source="Checkmk · tempo real" />
      </Card>

      {err && <Banner state="crit" title={`Falha ao consultar a API: ${err}`} meta={t("o backend (:5533) está de pé?")} />}
      {dt?.erros?.length > 0 && <Banner state="warn" title={t("sites com erro na consulta")} meta={dt.erros.map((e) => `${e.site}: ${e.erro}`).join(" · ")} />}

      <Card flush>
        <div className="card-head"><Cap>{t("silenciados agora")} · {dt ? dt.total : "…"}</Cap><ProvenanceChip method="OBS" source="gateway federado" /></div>
        {rows.length === 0
          ? <div className="muted sm" style={{ padding: "22px 18px", textAlign: "center", borderTop: "var(--border-hairline)" }}>{dt ? t("Nenhum downtime ativo no recorte.") : t("carregando…")}</div>
          : <div className="tscroll"><DataTable columns={COLS} rows={rows} density="compact" style={{ border: 0, borderTop: "1px solid var(--hairline)" }} /></div>}
      </Card>

      <div className="cols-2">
        <Card>
          <Cap>{t("novo silêncio")}</Cap>
          <div className="stack" style={{ gap: 9, marginTop: 12 }}>
            <div className="cols-2" style={{ gap: 9 }}>
              <Select label="site" value={nv.site} options={[{ value: "", label: "site…" }, ...siteOpts]} onChange={(v) => setNv({ ...nv, site: v })} />
              <TextField label="host" value={nv.host_name} mono onChange={(v) => setNv({ ...nv, host_name: v })} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "110px 1fr", gap: 9 }}>
              <TextField label={t("minutos")} type="number" value={nv.minutes} mono onChange={(v) => setNv({ ...nv, minutes: v })} />
              <TextField label={t("serviços")} placeholder={t("vazio = host inteiro")} value={nv.servicos} onChange={(v) => setNv({ ...nv, servicos: v })} />
            </div>
            <TextField label={t("comentário (obrigatório)")} value={nv.comment} onChange={(v) => setNv({ ...nv, comment: v })} />
            <Button onClick={criar} disabled={busy}>{t("Silenciar")}</Button>
          </div>
        </Card>
        <Card>
          <div className="card-head"><Cap>{t("silêncio por RDM (lote)")}</Cap><ProvenanceChip method="OBS" source="mata o storm 24–25 mai" /></div>
          <div className="stack" style={{ gap: 9, marginTop: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 110px", gap: 9 }}>
              <TextField label="RDM" placeholder="ex.: 549523" value={rdm.rdm} mono onChange={(v) => setRdm({ ...rdm, rdm: v })} />
              <TextField label={t("minutos")} type="number" value={rdm.minutes} mono onChange={(v) => setRdm({ ...rdm, minutes: v })} />
            </div>
            <TextArea label="alvos" placeholder={"uma linha por alvo: site host [serv1,serv2]\ntesp3 fw01-tesp3\ntesp5 edge02 CPU,Memory"} value={rdm.plan} onChange={(v) => setRdm({ ...rdm, plan: v })} />
            <Button onClick={rdmCriar} disabled={busy}>{t("Aplicar janela")}</Button>
          </div>
        </Card>
      </div>

      {msg && <div className="toasts"><Toast kind={msg.kind} title={msg.text} onClose={() => setMsg(null)} /></div>}
    </div>
  );
}
