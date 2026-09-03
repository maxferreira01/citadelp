/* MEISTRE ✦ — assistente (funcional via API). Responde com os dados carregados na sessão. */
import React, { useState } from "react";
import { Button, ProvenanceChip, TextField } from "@ds";
import { useT } from "../i18n.jsx";
import { Cap, Card } from "../ui.jsx";

const MEISTRE_CTX = `Você é o Meistre ✦, assistente da plataforma CITADEL (TOTVS Cloud, infraestrutura de redes, 12 datacenters). Tom: direto, técnico, calmo, orientado a ação; PT-BR; sem linguagem medieval; cite a procedência (OBS/CALC/EST-mock) e diga quando um dado é simulado. Dados carregados na sessão:
[OBS · varredura Slack #alert-float-ip 20mai-27jul/2026] 55 alertas de float IP. Ranking bruto: TECE C1=12, TESP3 C2=11, TESP3 C3=7, TESP6 C3=6. Expurgando 18 esperados (janelas de RDM 549523 em mai e limpeza de disco NSX 21-22 jun): TESP3 C3=7, TESP6 C3=6, TESP3 C2=5, TESP3 C1=5. TESP03=27 alertas no total (79% de julho). 32% dos disparos entre 00h-06h. Storm 21 jul 10:51-10:52: 5 clusters TESP3 em 60s, correlato INC12065 (FW físico CPU 100%, packet buffer, vlan 1019/seginfo). Storm TESP6 20 mai (11 disparos, perda de pacote) sem tratamento registrado. Alerta 27 jul 02:18 ficou 13h42 sem atuação. Melhorias propostas em 30 jun e pendentes: confirmação em 2 passadas, check_icmp, sonda TCP.
[EST · mock] Capacidade: NSX T1 TESP07 184/190 (38 dias, conf 84%); NSX IP Set TESP02 8106/9200 (132d); ACI MAC_PER_IP sem coleta 26h. Tesouro: expansão NSX T1 R$387 mil em cotação.
Pergunta do usuário: `;

export default function Meistre() {
  const t = useT();
  const [q, setQ] = useState("");
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);
  const ask = async (e) => {
    e?.preventDefault();
    const question = q.trim();
    if (!question || busy) return;
    setLog((l) => [...l, { r: "user", t: question }]);
    setQ(""); setBusy(true);
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: "claude-sonnet-4-6", max_tokens: 1000, messages: [{ role: "user", content: MEISTRE_CTX + question }] }),
      });
      const data = await res.json();
      const text = (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n");
      setLog((l) => [...l, { r: "ai", t: text || "Sem resposta. Tente reformular." }]);
    } catch {
      setLog((l) => [...l, { r: "ai", t: "Falha ao consultar o Meistre. Verifique a conexão e tente novamente." }]);
    }
    setBusy(false);
  };
  return (
    <div className="stack">
      <Card>
        <div className="card-head"><Cap>meistre — assistente da plataforma</Cap><ProvenanceChip method="OBS" source="responde com os dados carregados na sessão" /></div>
        <p className="sm muted" style={{ marginTop: 10 }}>
          Pergunte sobre os sinais do Corvo, capacidade ou próximos passos. Exemplos: "quem mais alarmou em julho sem contar RDM?" · "resuma o storm de 21 jul para o gestor" · "o que está pendente no monitor de float IP?"
        </p>
      </Card>
      <Card className="chat">
        {log.length === 0 && <div className="faint sm" style={{ margin: "auto" }}>{t("✦ Faça a primeira pergunta.")}</div>}
        {log.map((m, i) => (
          <div key={i} className={"bubble " + m.r}>{m.r === "ai" && <span style={{ color: "var(--action)", fontWeight: 600 }}>✦ </span>}{m.t}</div>
        ))}
        {busy && <div className="num muted" style={{ fontSize: 12 }}>✦ {t("consultando…")}</div>}
      </Card>
      <form onSubmit={ask} style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
        <TextField value={q} placeholder={t("Pergunte ao Meistre…")} onChange={setQ} style={{ flex: 1 }} />
        <Button type="submit" disabled={busy}>{busy ? "…" : t("Perguntar")}</Button>
      </form>
    </div>
  );
}
