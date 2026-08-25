import React, { useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import totvsBranco from "./assets/logo-totvs-branco.svg";
import totvsAzul from "./assets/logo-totvs-azul-escuro.svg";

/* ============================================================================
   CITADEL v0.1 — plataforma completa (protótipo navegável)
   ----------------------------------------------------------------------------
   Login (tela 4b) → shell (layout 5a: sidebar 228 + painel + rail 316)
   Módulos: Conselho · Três Olhos · Corvo · Muralha · Domínios · Arquivo ·
            Tesouro · Campanhas — e Meistre ✦ (assistente FUNCIONAL via API).

   PROCEDÊNCIA:
   · OBS — CORVO usa 55 alertas REAIS da varredura do Slack #alert-float-ip
     (20 mai – 27 jul 2026) e as atuações registradas no canal.
   · CALC — agregações com regra declarada.
   · MAN — janelas de RDM classificadas pelo relato humano do canal.
   · EST/mock — capacidade, limites, domínios, tesouro e arquivo são dados
     SIMULADOS (borda tracejada âmbar + chip "EST · mock") até os coletores
     reais (nsx_collector, fortigate-fisico, ACI) alimentarem o backend.
   ========================================================================== */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
:root{
--petrol-900:#002233;--petrol-800:#06344C;--petrol-700:#0B4364;--petrol-500:#0F5E8C;--petrol-400:#3D7FA6;--petrol-300:#6FA3C2;--petrol-200:#A3C4D9;--petrol-100:#D0E0EC;--petrol-50:#E6EEF4;
--amber-500:#B4690E;--amber-300:#E0A34E;--amber-100:#F6E8D3;
--state-info:#275FA8;--state-info-bg:#E8EFF8;--state-ok:#2F7D4F;--state-ok-bg:#E7F2EB;
--state-warn:#96690A;--state-warn-bg:#F6EDD8;--state-crit:#B23A26;--state-crit-bg:#F8E9E6;
--state-emergency:#7C1128;--state-emergency-bg:#F6E3E8;--state-stale:#8A6D3B;
--state-nocollect:#7A828C;--state-nocollect-bg:#EEF0F2;
--dq-observed:#0F5E8C;--dq-calculated:#2E3B4C;--dq-estimated:#96690A;--dq-manual:#6C5A9E;
--cap-limit-op:#B4690E;--cap-limit-tech:#111823;
--bg-page:#F1F3F7;--surface:#FFFFFF;--surface-sunken:#E9ECF2;--hairline:#D6DCE5;--hairline-strong:#111823;
--ink:#111823;--text-muted:#5B6675;--text-faint:#77828F;
--brand:#002233;--action:#0F5E8C;--action-hover:#0B4364;--selection:#E6EEF4;
--font-ui:'Archivo',system-ui,sans-serif;--font-mono:'JetBrains Mono',ui-monospace,'SF Mono',monospace;
--radius:6px;--sidebar-w:228px;--rail-w:316px;
}
[data-theme="dark"]{
--bg-page:#0F141B;--surface:#141C27;--surface-sunken:#0C1219;--hairline:#263344;--hairline-strong:#E7ECF3;
--ink:#E7ECF3;--text-muted:#8FA0B5;--text-faint:#67788C;--brand:#E7ECF3;--action:#5D9FC9;--action-hover:#7FC7E8;--selection:#16304A;
--state-warn:#E0A34E;--state-warn-bg:#2E2210;--state-crit:#E76A54;--state-crit-bg:#331410;
--state-emergency:#E88AA0;--state-emergency-bg:#33101B;--state-ok:#8FD0A9;--state-ok-bg:#12281B;
--state-nocollect:#8FA3B5;--state-nocollect-bg:#18202A;--state-stale:#B9A06A;
--dq-observed:#7FC7E8;--dq-calculated:#98A2AE;--dq-estimated:#E0A34E;--dq-manual:#C79AD4;
--cap-limit-op:#E0A34E;--cap-limit-tech:#E7ECF3;--petrol-900:#E7ECF3;--petrol-50:#16304A;
}
*{box-sizing:border-box}
.num{font-family:var(--font-mono);font-feature-settings:'tnum'}
button{font-family:var(--font-ui)}
button:focus-visible,a:focus-visible{outline:2px solid var(--action);outline-offset:2px}
a{color:var(--action);text-decoration:none}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-thumb{background:var(--hairline);border-radius:6px}
.shell{display:grid;grid-template-columns:var(--sidebar-w) minmax(0,1fr) var(--rail-w);min-height:100vh;background:var(--bg-page);font-family:var(--font-ui);color:var(--ink)}
.rail{display:flex}
.shell.norail{grid-template-columns:var(--sidebar-w) minmax(0,1fr)}
.shell.norail .rail{display:none}
.login-grid{display:grid;grid-template-columns:minmax(0,1fr) 500px;min-height:100vh;font-family:var(--font-ui)}
.tscroll{overflow-x:auto}
@media (max-width:1440px){.shell{grid-template-columns:var(--sidebar-w) minmax(0,1fr)}.shell .rail{display:none}}
@media (max-width:1100px){.login-grid{grid-template-columns:minmax(0,1fr)}}
`;

/* ============================== DADOS ===================================== */
/* CORVO — OBS: 55 alertas reais parseados da varredura do canal.            */
const RAW = `jul|27 02:18|TESP3|2|5301|128|369|0|0
jul|24 05:19|TESP3|3|4428|59|490|0|0
jul|24 02:18|TESP3|3|4428|59|495|0|0
jul|23 17:18|TESP3|3|4427|59|493|0|0
jul|21 10:52|TESP3|2|4778|446|3286|1|0
jul|21 10:52|TESP3|3|4079|186|2729|0|0
jul|21 10:52|TESP3|4|3652|178|2902|0|0
jul|21 10:52|TESP3|1|3248|178|2246|0|0
jul|21 10:51|TESP3|5|1450|73|1350|0|0
jul|20 15:50|TESP5|3|5001|37|387|0|0
jul|16 01:46|TESP2|3|4798|237|304|0|0
jul|15 02:40|TESP3|4|3905|43|321|0|0
jul|14 16:29|TESP4|1|1492|103|404|0|0
jul|14 08:42|TESP3|1|3499|138|480|0|0
jul|14 08:42|TESP3|2|5249|130|487|0|0
jul|13 23:41|TESP3|2|5249|130|484|0|0
jul|10 04:29|TESP2|3|4806|238|338|0|0
jul|09 18:45|TESP3|2|5263|136|488|0|0
jul|09 18:44|TESP3|1|3502|141|483|0|0
jun|30 00:20|TESP3|1|3564|143|494|0|0
jun|30 00:19|TESP3|5|1679|16|496|0|0
jun|23 16:35|TESP3|3|4465|66|391|0|0
jun|22 00:38|TESP3|2|5340|156|2326|0|1
jun|22 00:32|TESP3|2|5340|156|4383|0|1
jun|22 00:25|TESP3|2|5340|156|5214|0|1
jun|22 00:18|TESP3|2|5340|156|5179|0|1
jun|22 00:11|TESP3|2|5340|156|5068|0|1
jun|21 23:59|TESP3|1|3616|145|473|0|0
jun|21 23:22|TESP3|2|5340|156|490|0|1
jun|21 09:14|TESP3|3|4484|63|359|0|0
jun|20 14:07|TESP3|3|4497|64|366|0|0
mai|25 00:38|TECE|1|3944|655|0|1|1
mai|25 00:32|TECE|1|3944|655|0|1|1
mai|25 00:26|TECE|1|3944|655|0|1|1
mai|25 00:20|TECE|1|3944|655|0|1|1
mai|25 00:14|TECE|1|3944|655|0|1|1
mai|25 00:08|TECE|1|3944|655|0|1|1
mai|25 00:02|TECE|1|3931|653|3|1|1
mai|24 23:56|TECE|1|3944|655|0|1|1
mai|24 23:50|TECE|1|3963|636|0|1|1
mai|24 23:44|TECE|1|4018|580|0|1|1
mai|24 23:37|TECE|1|4116|483|0|1|1
mai|24 23:31|TECE|1|4220|379|0|1|1
mai|21 06:00|TESP6|3|5668|82|303|0|0
mai|20 23:40|TESP6|3|5443|307|1|1|0
mai|20 23:34|TESP6|3|5389|361|0|1|0
mai|20 23:33|TESP6|2|6070|302|1|1|0
mai|20 23:32|TESP6|1|7068|308|0|1|0
mai|20 23:28|TESP6|3|5389|361|1|1|0
mai|20 23:27|TESP6|2|6060|312|0|1|0
mai|20 23:26|TESP6|1|7064|312|0|1|0
mai|20 23:22|TESP6|3|5388|362|1|1|0
mai|20 23:21|TESP6|2|6060|311|1|1|0
mai|20 23:20|TESP6|1|7062|314|5|1|0
mai|20 23:16|TESP6|3|5383|367|33|1|0`;
const ALERTS = RAW.split("\n").map((l) => {
  const [m, d, e, c, s, f, hl, pl, exp] = l.split("|");
  return { m, d, e, c, s: +s, f: +f, hl: +hl, pl: pl === "1", exp: exp === "1" };
});
const MONTHS = ["mai", "jun", "jul"];

/* Atuações humanas — OBS (mensagens do canal). */
const ACTIONS = [
  { ts: "27 jul 16:21", who: "Bruno (gestor)", what: "Cobra análise do alerta TESP3 C2 de 02:18 — 14 h após o disparo." },
  { ts: "21 jul 11:52", who: "Max", what: "RCA do storm: FW físico a 100 % de CPU, packet buffer, pico CPS/PPS, vlan 1019. INC12065." },
  { ts: "14 jul 09:57", who: "Max", what: "Mapeia >50 VMs internas impactadas (devops-workspace, LAB_DB_CORE_TEAM, TDEVOPS)." },
  { ts: "30 jun 09:28", who: "Max", what: "Classifica falso positivo (CoPP) e propõe: 2 passadas, check_icmp, sonda TCP." },
  { ts: "22 jun 10:52", who: "Bruno (gestor)", what: "Processo: RDMs futuras devem incluir task para desabilitar o alert-ip." },
  { ts: "25 mai 00:42", who: "Junovan", what: "RDM 549523: schedule de silêncio falhou; alarmes desativados manualmente." },
];

/* TRÊS OLHOS / MURALHA / DOMÍNIOS / TESOURO / ARQUIVO — EST · mock.          */
const LIMITS = [
  // NSX-T · Tier-1 Routers: linhas reais por site via /nsx/t1/resumo (Muralha).
  { plat: "NSX-T", res: "NAT Rules", edge: "TESP03", use: 17097, op: 25000, vendor: 30000, src: "config-max VMware" },
  { plat: "Palo Alto", res: "Sessões vsys1", edge: "TESP02", use: 690000, op: 2000000, vendor: 4000000, src: "datasheet PA-5260" },
  { plat: "Palo Alto", res: "Regras de firewall", edge: "TESP02", use: 48, op: 85, vendor: 100, src: "premissa (%)" },
  { plat: "FortiGate", res: "Firewall Policies", edge: "TESP04", use: 3400, op: 10000, vendor: 20000, src: "datasheet 600F" },
  { plat: "ACI", res: "Portas Leaf 25G", edge: "TESP07", use: 30, op: 48, vendor: 48, src: "inventário físico" },
];
const DOMAINS = [
  { e: "TESP02", city: "São Paulo · Ascenty", st: "ok", note: "IPs públicos 64 %" },
  { e: "TESP03", city: "São Paulo · Megatelecom", st: "crit", note: "ofensor Corvo · C3 recorrente" },
  { e: "TESP04", city: "São Paulo · UPX", st: "warn", note: "FW CPU instável (14 jul)" },
  { e: "TESP05", city: "São Paulo", st: "ok", note: "1 alerta em jul" },
  { e: "TESP06", city: "São Paulo", st: "warn", note: "storm 20 mai sem desfecho" },
  { e: "TESP07", city: "São Paulo", st: "crit", note: "NSX T1 · 38 d" },
  { e: "TECE01", city: "Fortaleza", st: "ok", note: "RDM 549523 concluída" },
  { e: "TBSP01", city: "São Paulo", st: "nocollect", note: "sem coleta 26 h" },
];
const CAMPAIGNS = [
  { t: "Investigar recorrência TESP3 C3 (7 alertas expurgados)", col: "aberto", src: "OBS", owner: "Redes" },
  { t: "Monitor float IP: 2 passadas + check_icmp + sonda TCP", col: "aberto", src: "OBS", owner: "Max" },
  { t: "Silenciamento automático de alertas na abertura de RDM", col: "andamento", src: "OBS", owner: "Davi" },
  { t: "Corrigir listagem de VMs no anexo do bot", col: "andamento", src: "OBS", owner: "N2" },
  { t: "Expansão NSX T1 TESP07 (+50 · R$ 387.000)", col: "aberto", src: "EST", owner: "Arquitetura" },
  { t: "RCA storm TESP6 20 mai (11 disparos, sem tratamento)", col: "aberto", src: "OBS", owner: "Redes" },
  { t: "Reconciliar IPAM × planilha (blocos /24)", col: "concluido", src: "EST", owner: "Max" },
];
const BUDGET = [
  { cat: "Circuitos e operadoras", plan: 4200000, real: 2310000 },
  { cat: "Licenciamento NSX/Palo/Forti", plan: 3800000, real: 2960000 },
  { cat: "Expansões de hardware", plan: 2600000, real: 940000 },
];
const RUNBOOKS = [
  { t: "Convenção de nomenclatura — hosts & proxies SSH", tags: "ssh · nomenclatura" },
  { t: "Baseline de métricas Palo Alto — o que observar", tags: "palo · observability" },
  { t: "Procedimento: silêncio de alertas em janela de RDM", tags: "checkmk · rdm" },
  { t: "Float IP — anatomia do alerta e triagem", tags: "corvo · floatip" },
];
const MODULES = [
  { id: "conselho", n: "Conselho", d: "visão executiva", count: 2 },
  { id: "tresolhos", n: "Três Olhos", d: "capacidade e previsão", count: 4 },
  { id: "corvo", n: "Corvo", d: "sinais e integrações", count: 55, hot: true },
  { id: "vigia", n: "Vigia", d: "Checkmk · downtimes reais" },
  { id: "muralha", n: "Muralha", d: "limites de plataforma", count: 3 },
  { id: "dominios", n: "Domínios", d: "datacenters e topologia" },
  { id: "arquivo", n: "Arquivo", d: "wiki e runbooks" },
  { id: "tesouro", n: "Tesouro", d: "orçamento e cotações", count: 3 },
  { id: "campanhas", n: "Campanhas", d: "planos de ação", count: 5 },
];
const GLYPH = { ok: "●", warn: "◆", crit: "▲", emergency: "▲▲", stale: "◐", nocollect: "◌", info: "ℹ" };
const SCOLOR = { ok: "var(--state-ok)", warn: "var(--state-warn)", crit: "var(--state-crit)", emergency: "var(--state-emergency)", stale: "var(--state-stale)", nocollect: "var(--state-nocollect)", info: "var(--state-info)" };
const fmt = (n) => n.toLocaleString("pt-BR");
const brl = (n) => "R$ " + (n / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 0 }) + " mil";

/* ============================== i18n ====================================== */
const EN = {
  // login
  "Bem-vindo de volta": "Welcome back", "plataforma interna": "internal platform", "nota do dia": "note of the day",
  "Veja o limite antes de alcançá-lo.": "See the limit before you reach it.",
  "“O que não é medido é negociado no susto.”": "“What is not measured gets negotiated in a panic.”",
  "Entrar": "Sign in", "Acesso restrito às equipes de infraestrutura, operações e gestão.": "Access restricted to infrastructure, operations and management teams.",
  "Continuar com SSO TOTVS": "Continue with TOTVS SSO", "ou": "or", "Usuário corporativo": "Corporate user", "Senha": "Password",
  "status da plataforma": "platform status", "coletores respondendo": "collectors responding",
  "varredura Corvo (Slack)": "Raven sweep (Slack)", "sincronização CMDB": "CMDB sync", "uso interno": "internal use",
  // sidebar
  "Conselho": "Council", "Três Olhos": "Three Eyes", "Corvo": "Raven", "Vigia": "Watch", "Muralha": "The Wall",
  "Domínios": "Domains", "Arquivo": "Archive", "Tesouro": "Treasury", "Campanhas": "Campaigns",
  "visão executiva": "executive view", "capacidade e previsão": "capacity & forecast", "sinais e integrações": "signals & integrations",
  "Checkmk · downtimes reais": "Checkmk · live downtimes", "limites de plataforma": "platform limits",
  "datacenters e topologia": "datacenters & topology", "wiki e runbooks": "wiki & runbooks",
  "orçamento e cotações": "budget & quotes", "planos de ação": "action plans", "Sair": "Sign out",
  // shell
  "procedência": "provenance", "ações": "actions", "ocultar painel lateral": "hide side rail", "mostrar painel lateral": "show side rail",
  // titles
  "Conselho — visão executiva": "Council — executive view", "síntese para decisão · 27 jul 2026": "decision brief · Jul 27 2026",
  "Três Olhos — capacidade e previsão": "Three Eyes — capacity & forecast", "trajetórias, runways e limites": "trajectories, runways and limits",
  "Corvo — sinais": "Raven — signals", "raio-x do canal #alert-float-ip · funcionalidade piloto": "x-ray of #alert-float-ip · pilot feature",
  "Vigia — Checkmk federado": "Watch — federated Checkmk", "downtimes reais em 5 sites · criar, listar e remover silêncios": "live downtimes across 5 sites · create, list and remove silences",
  "Muralha — limites de plataforma": "The Wall — platform limits", "uso × alvo operacional × fabricante": "usage × operational target × vendor",
  "Domínios — datacenters": "Domains — datacenters", "estado por edge": "state per edge",
  "Arquivo — runbooks": "Archive — runbooks", "fonte de verdade operacional": "operational source of truth",
  "Tesouro — orçamento e cotações": "Treasury — budget & quotes", "orçado × realizado 2026": "planned × actual 2026",
  "Campanhas — planos de ação": "Campaigns — action plans", "todo sinal leva a uma ação": "every signal leads to an action",
  "Meistre — assistente": "Meistre — assistant", "consultas em linguagem natural sobre a plataforma": "natural-language queries about the platform",
  // vigia
  "downtimes ativos": "active downtimes", "sites federados": "federated sites", "todos os sites": "all sites",
  "host + serviço": "host + service", "só host": "host only", "só serviço": "service only", "Atualizar": "Refresh",
  "silenciados agora": "silenced now", "Nenhum downtime ativo no recorte.": "No active downtime in this view.",
  "host inteiro": "entire host", "remover": "remove", "novo silêncio": "new silence", "Silenciar": "Silence",
  "silêncio por RDM (lote)": "RDM silence (batch)", "Aplicar janela": "Apply window",
  "comentário (obrigatório)": "comment (required)", "serviços (vírgula) — vazio = host inteiro": "services (comma) — empty = entire host",
  "carregando…": "loading…",
};
const LangCtx = React.createContext(["pt", () => {}]);
const useT = () => {
  const [lang] = React.useContext(LangCtx);
  return (s) => (lang === "en" && EN[s]) || s;
};
function LangBtn({ style }) {
  const [lang, setLang] = React.useContext(LangCtx);
  return (
    <button onClick={() => setLang(lang === "pt" ? "en" : "pt")} title={lang === "pt" ? "switch to English" : "mudar para português"}
      style={{ border: "1px solid var(--hairline)", background: "transparent", color: "var(--ink)", borderRadius: 6, padding: "3px 9px", cursor: "pointer", font: "600 11px var(--font-mono)", ...style }}>
      {lang === "pt" ? "EN" : "PT"}
    </button>
  );
}

/* ============================== logos ===================================== */
/* Marca CITADEL (glifo próprio) + logo oficial TOTVS (pack de assets da marca). */
const Logo = ({ size = 26, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-label="CITADEL" role="img">
    <path d="M4 28V12h4V8h3v4h3V8h4v4h3V8h3v4h4v16h-9v-7a3 3 0 0 0-6 0v7H4Z" fill={color} />
    <path d="M14 4h4v4h-4z" fill={color} opacity=".55" />
  </svg>
);
const TotvsLogo = ({ white, height = 20, style }) => (
  <img src={white ? totvsBranco : totvsAzul} alt="TOTVS" style={{ height, display: "block", ...style }} />
);

/* ============================== átomos ==================================== */
const Cap = ({ children, style }) => <div style={{ font: "600 10.5px var(--font-ui)", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--text-muted)", ...style }}>{children}</div>;
const Card = ({ children, style, mock }) => (
  <section style={{ background: "var(--surface)", border: `1px ${mock ? "dashed var(--dq-estimated)" : "solid var(--hairline)"}`, borderRadius: "var(--radius)", padding: 18, ...style }}>{children}</section>
);
const Chip = ({ m, s }) => (
  <span style={{ display: "inline-flex", alignItems: "center", gap: 6, border: `1px ${m === "EST" ? "dashed var(--dq-estimated)" : "solid var(--hairline)"}`, borderRadius: 4, padding: "2px 8px", font: "400 10.5px var(--font-mono)", color: "var(--text-muted)", whiteSpace: "nowrap", background: "var(--surface)" }}>
    <b style={{ fontWeight: 700, letterSpacing: ".08em", color: m === "OBS" ? "var(--dq-observed)" : m === "MAN" ? "var(--dq-manual)" : m === "EST" ? "var(--dq-estimated)" : "var(--dq-calculated)" }}>{m}</b>{s}
  </span>
);
const St = ({ st, label }) => (
  <span style={{ display: "inline-flex", alignItems: "center", gap: 5, color: SCOLOR[st], font: "500 11px var(--font-mono)", whiteSpace: "nowrap" }}>
    <span aria-hidden>{GLYPH[st]}</span>{label}
  </span>
);
const Btn = ({ children, sec, onClick, style, disabled }) => (
  <button onClick={onClick} disabled={disabled} style={{
    border: sec ? "1px solid var(--hairline)" : "1px solid var(--action)", cursor: disabled ? "wait" : "pointer",
    background: sec ? "var(--surface)" : "var(--action)", color: sec ? "var(--ink)" : "#fff",
    borderRadius: "var(--radius)", padding: "8px 14px", font: "600 12.5px var(--font-ui)", ...style,
  }}>{children}</button>
);

/* API CITADEL — proxy do vite: /api/* → uvicorn :5533 */
async function api(path, opts = {}) {
  const token = sessionStorage.getItem("citadel_token");
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...opts,
  });
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail || ""; } catch { /* corpo não-JSON */ }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* NSX T1 — OBS · nsx-collector → InfluxDB (read-model /nsx/t1/*).            */
/* Limite operacional de T1: 2.000 por datacenter (premissa MAN de arquitetura). */
const NSX_T1_OP_LIMIT = 2000;
/* Regressão linear sobre o histórico diário → projeção (CALC) em 3 passos de 30 d. */
function projetar(hist, op) {
  const n = hist.length;
  if (n < 7) return { proj: hist.length ? [hist[n - 1]] : [], days: null, conf: "—" };
  const xs = hist.map((_, i) => i), mx = (n - 1) / 2, my = hist.reduce((a, b) => a + b, 0) / n;
  let sxy = 0, sxx = 0, sst = 0;
  xs.forEach((x, i) => { sxy += (x - mx) * (hist[i] - my); sxx += (x - mx) ** 2; sst += (hist[i] - my) ** 2; });
  const slope = sxx ? sxy / sxx : 0, last = hist[n - 1];
  const r2 = sst ? Math.max(0, Math.min(1, (slope * slope * sxx) / sst)) : 0;
  const proj = [last, ...[30, 60, 90].map((d) => Math.round(last + slope * d))];
  const days = slope > 0 && last < op ? Math.round((op - last) / slope) : null;
  return { proj, days, conf: `${Math.round(r2 * 100)}%` };
}
function useNsxT1(site) {
  const [sites, setSites] = useState([]);
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  React.useEffect(() => {
    let vivo = true;
    (async () => {
      setBusy(true); setErr("");
      try {
        const resumo = await api("/nsx/t1/resumo");
        if (!vivo) return;
        setSites(resumo);
        const alvo = resumo.find((r) => r.site === site) || resumo[0];
        if (!alvo) { setData(null); setBusy(false); return; }
        const [hist, t0, vrf] = await Promise.all([
          api(`/nsx/t1/historico?site=${encodeURIComponent(alvo.site)}&dias=90`),
          api(`/nsx/t1/por-t0?site=${encodeURIComponent(alvo.site)}`),
          api(`/nsx/t1/por-vrf?site=${encodeURIComponent(alvo.site)}`),
        ]);
        if (!vivo) return;
        const serie = hist.map((h) => h.total).filter((v) => v != null);
        const tech = alvo.nsx_max || 4000, op = NSX_T1_OP_LIMIT;
        const usage = alvo.total ?? alvo.nsx_current ?? 0;
        const { proj, days, conf } = projetar(serie, op);
        const st = usage >= op ? "crit" : usage >= op * 0.85 ? "warn" : "ok";
        setData({ id: "nsxt1", name: `NSX T1 Gateways · ${alvo.site}`, site: alvo.site, usage, op, tech, days, conf, st, hist: serie, proj, t0, vrf, resumo: alvo });
      } catch (e) { if (vivo) setErr(String(e.message || e)); }
      if (vivo) setBusy(false);
    })();
    return () => { vivo = false; };
  }, [site]);
  return { sites, data, busy, err };
}
/* Barras horizontais count/limit, cor por usage_pct (molde do ranking do Corvo). */
function T1Bars({ rows, nameKey, title }) {
  const data = rows.map((r) => ({ k: r[nameKey], n: r.t1_count, lim: r.limit, pct: r.usage_pct }));
  const cor = (pct) => pct >= 90 ? "var(--state-crit)" : pct >= 70 ? "var(--cap-limit-op)" : "var(--petrol-500)";
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between" }}><Cap>{title} — {rows.length}</Cap><Chip m="OBS" s="nsx-collector → InfluxDB" /></div>
      {!rows.length ? <div style={{ marginTop: 10, color: "var(--state-nocollect)", fontFamily: "var(--font-mono)", fontSize: 12 }}>◌ sem coleta</div> : (
        <div style={{ height: Math.max(120, data.length * 26 + 30), marginTop: 10 }}>
          <ResponsiveContainer>
            <BarChart data={data} layout="vertical" margin={{ left: 4, right: 64, top: 2, bottom: 0 }}>
              <CartesianGrid horizontal={false} stroke="var(--hairline)" />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10.5, fontFamily: "var(--font-mono)" }} stroke="var(--text-faint)" />
              <YAxis type="category" dataKey="k" width={170} tick={{ fontSize: 10.5, fontFamily: "var(--font-mono)" }} stroke="var(--text-faint)" />
              <Tooltip cursor={{ fill: "var(--selection)" }} contentStyle={{ fontFamily: "var(--font-mono)", fontSize: 11, border: "1px solid var(--hairline)", borderRadius: 6, background: "var(--surface)", color: "var(--ink)" }} formatter={(v, _n, it) => [`${v} de ${it.payload.lim} (${it.payload.pct} %)`, "T1"]} />
              <Bar dataKey="n" radius={[0, 3, 3, 0]}>
                {data.map((r, i) => <Cell key={i} fill={cor(r.pct)} />)}
                <LabelList dataKey="n" position="right" content={({ x, y, width, height, value, index }) => <text x={x + width + 4} y={y + height / 2 + 4} style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, fill: "var(--ink)" }}>{value}/{data[index].lim}</text>} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}

/* Trajetória — sólida=observado · tracejada=projetado · âmbar=limite op.     */
function Trajectory({ hist, proj, op, tech, h = 150 }) {
  if (!hist.length) return <div style={{ height: h, display: "grid", placeItems: "center", color: "var(--state-nocollect)", border: "1px dotted var(--state-nocollect)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 12 }}>◌ sem coleta</div>;
  const all = [...hist, ...proj, op, tech];
  const min = Math.min(...all) * 0.96, max = Math.max(...all) * 1.03;
  const W = 640, n = hist.length + proj.length - 1;
  const x = (i) => 34 + (i * (W - 50)) / n;
  const y = (v) => 12 + (h - 34) * (1 - (v - min) / (max - min));
  const path = (arr, off = 0) => arr.map((v, i) => `${i ? "L" : "M"}${x(i + off)},${y(v)}`).join(" ");
  const nowX = x(hist.length - 1);
  return (
    <svg viewBox={`0 0 ${W} ${h}`} style={{ width: "100%", height: "auto", display: "block" }} role="img" aria-label="trajetória do recurso: histórico sólido, projeção tracejada, limites operacional e técnico">
      <line x1={34} x2={W - 12} y1={y(op)} y2={y(op)} stroke="var(--cap-limit-op)" strokeDasharray="5 4" strokeWidth="1.3" />
      <text x={W - 12} y={y(op) - 4} textAnchor="end" style={{ font: "600 9.5px var(--font-mono)", fill: "var(--cap-limit-op)" }}>limite op · {fmt(op)}</text>
      <line x1={34} x2={W - 12} y1={y(tech)} y2={y(tech)} stroke="var(--cap-limit-tech)" strokeWidth="1.3" />
      <text x={W - 12} y={y(tech) - 4} textAnchor="end" style={{ font: "600 9.5px var(--font-mono)", fill: "var(--cap-limit-tech)" }}>limite téc · {fmt(tech)}</text>
      <line x1={nowX} x2={nowX} y1={8} y2={h - 16} stroke="var(--ink)" strokeWidth="1" opacity=".55" />
      <text x={nowX + 4} y={16} style={{ font: "500 9.5px var(--font-mono)", fill: "var(--text-muted)" }}>hoje</text>
      <path d={path(hist)} fill="none" stroke="var(--action)" strokeWidth="2" />
      <path d={path(proj, hist.length - 1)} fill="none" stroke="var(--action)" strokeWidth="1.6" strokeDasharray="6 5" opacity=".85" />
    </svg>
  );
}

/* ====================== LOGIN GOOGLE (GIS + backend) ====================== */
function GoogleSignIn({ onUser }) {
  const ref = React.useRef(null);
  const [state, setState] = useState("carregando");
  React.useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const cfg = await api("/auth/config");
        if (dead) return;
        if (!cfg.google) { setState("ausente"); return; }
        const s = document.createElement("script");
        s.src = "https://accounts.google.com/gsi/client";
        s.async = true;
        s.onload = () => {
          if (dead || !window.google) return;
          window.google.accounts.id.initialize({
            client_id: cfg.google_client_id,
            callback: async (resp) => {
              try {
                const out = await api("/auth/google", { method: "POST", body: JSON.stringify({ credential: resp.credential }) });
                sessionStorage.setItem("citadel_token", out.token);
                onUser(out.user);
              } catch { setState("erro"); }
            },
          });
          window.google.accounts.id.renderButton(ref.current, { theme: "outline", size: "large", width: 380 });
          setState("pronto");
        };
        s.onerror = () => !dead && setState("erro");
        document.head.appendChild(s);
      } catch { !dead && setState("ausente"); }
    })();
    return () => { dead = true; };
  }, []);
  return (
    <div style={{ marginTop: 14 }}>
      <div ref={ref} style={{ display: state === "pronto" ? "flex" : "none", justifyContent: "center" }} />
      {state === "ausente" && (
        <div style={{ fontSize: 11, color: "var(--text-muted)", textAlign: "center", border: "1px dashed var(--hairline)", borderRadius: 6, padding: "9px 10px" }}>
          Login Google indisponível — defina <span className="num">GOOGLE_CLIENT_ID</span> no .env do backend.
        </div>
      )}
      {state === "erro" && (
        <div style={{ fontSize: 11, color: "var(--state-crit)", textAlign: "center", padding: "6px 0" }}>Falha no login Google. Tente novamente.</div>
      )}
    </div>
  );
}

/* ============================== LOGIN (4b) ================================ */
function Login({ onEnter, theme, setTheme }) {
  const t = useT();
  return (
    <div className="login-grid">
      <div style={{ background: "linear-gradient(160deg,#041C2B 0%,#0A2438 100%)", color: "#E7ECF3", padding: "40px 48px", display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 22 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <TotvsLogo white height={26} />
            <span style={{ font: "600 10.5px var(--font-mono)", letterSpacing: ".2em", color: "#8299B0" }}>CLOUD</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 22 }}>
            <Logo size={40} color="#F0B45F" />
            <span style={{ font: "700 42px/1 var(--font-ui)", letterSpacing: ".02em" }}>CITADEL</span>
          </div>
          <div style={{ fontSize: 13.5, color: "#9FB2C4", marginTop: 9 }}>{t("Veja o limite antes de alcançá-lo.")}</div>
        </div>
        <div>
          <div style={{ font: "600 10.5px var(--font-ui)", letterSpacing: ".14em", textTransform: "uppercase", color: "#8299B0" }}>risco mais próximo · 27 jul 2026</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginTop: 10 }}>
            <span className="num" style={{ font: "700 82px/.9 var(--font-ui)", color: "#F0B45F" }}>38</span>
            <div>
              <div style={{ font: "700 20px var(--font-ui)", color: "#F0B45F" }}>dias</div>
              <div style={{ fontSize: 13, color: "#E7ECF3", marginTop: 4, lineHeight: 1.5 }}>até o limite operacional mais próximo<br />em um domínio de produção</div>
            </div>
          </div>
          <div style={{ marginTop: 16, maxWidth: 660 }}>
            <Trajectory hist={[152, 154, 158, 163, 168, 172, 176, 181, 184]} proj={[184, 190, 197, 205]} op={190} tech={200} h={140} />
          </div>
        </div>
        <div style={{ display: "flex", borderTop: "1px solid #1D3448", borderBottom: "1px solid #1D3448", padding: "14px 0" }}>
          {[["3", "#E7ECF3", "recursos saturam em menos de 90 dias"], ["2", "#D9B36C", "coletores sem coleta há mais de 24 h"], ["55", "#7FC7E8", "sinais de float IP analisados no trimestre"]].map(([n, c, txt], i) => (
            <div key={i} style={{ flex: 1, padding: "0 16px", borderLeft: i ? "1px solid #1D3448" : "none", paddingLeft: i ? 16 : 0 }}>
              <div className="num" style={{ font: "700 21px var(--font-ui)", color: c }}>{n}</div>
              <div style={{ fontSize: 11.5, color: "#9FB2C4", lineHeight: 1.4, marginTop: 3 }}>{txt}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", font: "400 10.5px var(--font-mono)", color: "#7A8FA3" }}>
          <span>coleta contínua · 46 de 48 coletores respondendo</span>
          <span>projeção 12 m · cone P10–P90</span>
        </div>
      </div>
      <div style={{ background: "var(--surface)", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: "34px 48px", gap: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ display: "inline-flex", gap: 9, alignItems: "center", font: "600 15px var(--font-ui)", color: "var(--ink)" }}><Logo size={20} color="var(--action)" />{t("Bem-vindo de volta")}</span>
          <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
            <span style={{ font: "400 10.5px var(--font-mono)", color: "var(--text-muted)" }}>{t("plataforma interna")}</span>
            <LangBtn />
            <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")} title="tema claro/escuro" style={{ border: "1px solid var(--hairline)", background: "transparent", color: "var(--ink)", borderRadius: 6, padding: "3px 9px", cursor: "pointer", font: "600 11px var(--font-mono)" }}>{theme === "dark" ? "☀" : "☾"}</button>
          </span>
        </div>
        <div style={{ borderTop: "1px solid var(--hairline)", borderBottom: "1px solid var(--hairline)", padding: "15px 0" }}>
          <Cap>{t("nota do dia")}</Cap>
          <p style={{ font: "400 15.5px/1.5 var(--font-ui)", color: "var(--petrol-900)", margin: "9px 0 0" }}>{t("“O que não é medido é negociado no susto.”")}</p>
          <div style={{ font: "400 10.5px var(--font-mono)", color: "var(--text-muted)", marginTop: 8 }}>Engenharia de Redes · TOTVS Cloud</div>
        </div>
        <div>
          <div style={{ font: "700 22px var(--font-ui)", color: "var(--petrol-900)" }}>{t("Entrar")}</div>
          <p style={{ fontSize: 12.5, color: "var(--text-muted)", margin: "5px 0 0" }}>{t("Acesso restrito às equipes de infraestrutura, operações e gestão.")}</p>
          <Btn onClick={onEnter} style={{ width: "100%", marginTop: 18, padding: "11px 12px", fontSize: 13.5 }}>{t("Continuar com SSO TOTVS")}</Btn>
          <GoogleSignIn onUser={() => onEnter()} />
          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "16px 0", color: "var(--text-muted)", fontSize: 11 }}>
            <span style={{ flex: 1, height: 1, background: "var(--hairline)" }} />{t("ou")}<span style={{ flex: 1, height: 1, background: "var(--hairline)" }} />
          </div>
          <label style={{ display: "block", fontSize: 11.5, color: "var(--text-muted)" }}>{t("Usuário corporativo")}
            <input defaultValue="m.ferreira" className="num" style={{ display: "block", width: "100%", marginTop: 5, padding: "9px 10px", border: "1px solid var(--hairline)", borderRadius: 6, background: "var(--bg-page)", color: "var(--ink)", fontSize: 13 }} />
          </label>
          <label style={{ display: "block", fontSize: 11.5, color: "var(--text-muted)", marginTop: 13 }}>{t("Senha")}
            <input type="password" defaultValue="**********" style={{ display: "block", width: "100%", marginTop: 5, padding: "9px 10px", border: "1px solid var(--hairline)", borderRadius: 6, background: "var(--bg-page)", color: "var(--ink)", fontSize: 13 }} />
          </label>
          <Btn sec onClick={onEnter} style={{ width: "100%", marginTop: 16, padding: "11px 12px", fontSize: 13.5 }}>{t("Entrar")}</Btn>
        </div>
        <div>
          <Cap>{t("status da plataforma")}</Cap>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "7px 12px", fontSize: 12, marginTop: 9 }}>
            <span style={{ color: "var(--text-muted)" }}>{t("coletores respondendo")}</span><span className="num">46 / 48</span>
            <span style={{ color: "var(--text-muted)" }}>{t("varredura Corvo (Slack)")}</span><span className="num">27 jul 20:40</span>
            <span style={{ color: "var(--text-muted)" }}>{t("sincronização CMDB")}</span><span className="num">há 9 min</span>
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", borderTop: "1px solid var(--hairline)", paddingTop: 13, fontSize: 11, color: "var(--text-muted)" }}>
          <span>{t("uso interno")}</span><span className="num">CITADEL v0.1 · protótipo</span>
        </div>
      </div>
    </div>
  );
}

/* ============================ MÓDULOS ===================================== */
function Conselho({ go }) {
  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Card mock>
          <div style={{ display: "flex", justifyContent: "space-between" }}><Cap>capacidade — risco mais próximo</Cap><Chip m="EST" s="mock" /></div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginTop: 10 }}>
            <span className="num" style={{ font: "700 44px/1 var(--font-ui)", color: "var(--cap-limit-op)" }}>38</span>
            <div style={{ fontSize: 13 }}>dias · NSX T1 · TESP07<br /><span style={{ color: "var(--text-muted)", fontSize: 11.5 }}>confiança 84 % · expansão cotada no Tesouro</span></div>
          </div>
          <a href="#" onClick={(e) => { e.preventDefault(); go("tresolhos"); }} style={{ fontSize: 12.5, display: "inline-block", marginTop: 10 }}>Abrir Três Olhos</a>
        </Card>
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between" }}><Cap>sinais — ofensor do trimestre</Cap><Chip m="OBS" s="Slack · 55 alertas" /></div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginTop: 10 }}>
            <span className="num" style={{ font: "700 44px/1 var(--font-ui)", color: "var(--brand)" }}>TESP3</span>
            <div style={{ fontSize: 13 }}>27 alertas de float IP · C3 lidera expurgando RDMs<br /><span style={{ color: "var(--text-muted)", fontSize: 11.5 }}>alerta de 27 jul ficou 13 h 42 sem atuação</span></div>
          </div>
          <a href="#" onClick={(e) => { e.preventDefault(); go("corvo"); }} style={{ fontSize: 12.5, display: "inline-block", marginTop: 10 }}>Abrir Corvo</a>
        </Card>
      </div>
      <Card>
        <Cap>o que exige decisão esta semana</Cap>
        <div style={{ display: "grid", gap: 0, marginTop: 8 }}>
          {[
            ["▲", "crit", "Expansão NSX T1 TESP07 — aprovar cotação de R$ 387 mil antes de 05 ago para manter runway.", "EST"],
            ["◆", "warn", "TESP3 C3: 7 alertas fora de janela em jun–jul — designar responsável pela investigação.", "OBS"],
            ["◆", "warn", "Storm TESP6 de 20 mai segue sem RCA registrado no canal.", "OBS"],
          ].map(([g, st, txt, m], i) => (
            <div key={i} style={{ display: "flex", gap: 10, alignItems: "baseline", padding: "9px 0", borderTop: i ? "1px solid var(--hairline)" : "none", fontSize: 12.5 }}>
              <span style={{ color: SCOLOR[st], fontFamily: "var(--font-mono)" }}>{g}</span>
              <span style={{ flex: 1 }}>{txt}</span><Chip m={m} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function TresOlhos() {
  const [site, setSite] = useState("");
  const nsx = useNsxT1(site);
  const n = nsx.data;
  const r = n || { id: "nsxt1", name: "NSX T1 Gateways", hist: [], proj: [], op: 3200, tech: 4000, days: null, conf: "—" };
  const alerta = n && n.days != null && n.days <= 180;
  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div style={{ background: alerta ? "var(--state-crit-bg)" : "var(--surface)", border: `1px solid ${alerta ? "var(--state-crit)" : "var(--hairline)"}`, borderRadius: "var(--radius)", padding: "11px 15px", display: "flex", alignItems: "center", gap: 13, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "var(--font-mono)", color: alerta ? "var(--state-crit)" : "var(--text-muted)", fontSize: 15 }}>{alerta ? "▲" : "●"}</span>
        <div style={{ flex: 1, minWidth: 200 }}>
          {nsx.err ? <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--state-crit)" }}>NSX T1: {nsx.err}</div>
            : !n ? <div style={{ fontSize: 13.5, fontWeight: 600 }}>{nsx.busy ? "carregando capacity de T1…" : "◌ sem coleta de T1"}</div>
            : <>
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>{n.days != null ? `NSX T1 pode atingir o limite operacional em ${n.days} dias.` : "NSX T1 sem tendência de esgotamento no horizonte projetado."}</div>
              <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 2 }}>{n.site} · {fmt(n.usage)} de {fmt(n.op)} T1 (limite 2k/DC · config-max {fmt(n.tech)}) · projeção 90 d, confiança {n.conf}</div>
            </>}
        </div>
        {nsx.sites.length > 1 && (
          <select value={n ? n.site : site} onChange={(e) => setSite(e.target.value)} style={{ font: "500 12px var(--font-mono)", padding: "4px 8px", border: "1px solid var(--hairline)", borderRadius: 4, background: "var(--surface)", color: "var(--ink)" }}>
            {nsx.sites.map((x) => <option key={x.site} value={x.site}>{x.site} · {fmt(x.total ?? 0)}</option>)}
          </select>
        )}
        <Chip m="OBS" s="nsx-collector → InfluxDB" />
      </div>
      <Card mock={!n}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
          <span style={{ font: "600 14px var(--font-ui)", color: "var(--petrol-900)" }}>{r.name}</span>
          {r.days != null && <span className="num" style={{ font: "700 14px var(--font-mono)", color: "var(--cap-limit-op)" }}>{r.days} dias · {r.conf}</span>}
        </div>
        <Trajectory hist={r.hist} proj={r.proj} op={r.op} tech={r.tech} h={170} />
        {n && <div style={{ marginTop: 6, display: "flex", gap: 8, flexWrap: "wrap" }}><Chip m="OBS" s="histórico diário · nsx_t1_totals" /><Chip m="CALC" s="projeção linear 90 d" /><Chip m="MAN" s="limite op = 2.000 T1 por datacenter" /></div>}
      </Card>
      {n && (
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 14 }}>
          <T1Bars rows={n.t0} nameKey="t0_name" title={`T1 por T0 · ${n.site}`} />
          <T1Bars rows={n.vrf} nameKey="vrf_name" title={`T1 por VRF · ${n.site}`} />
        </div>
      )}
    </div>
  );
}

function Corvo() {
  const [months, setMonths] = useState(new Set(MONTHS));
  const [hideExp, setHideExp] = useState(true);
  const view = useMemo(() => {
    const inP = ALERTS.filter((a) => months.has(a.m));
    const rows = hideExp ? inP.filter((a) => !a.exp) : inP;
    const agg = {};
    rows.forEach((a) => { const k = `${a.e} C${a.c}`; agg[k] = agg[k] || { k, e: a.e, n: 0 }; agg[k].n++; });
    const rank = Object.values(agg).sort((x, y) => y.n - x.n);
    return { rows, rank, total: rows.length, excluded: inP.length - rows.length, top: rank[0] };
  }, [months, hideExp]);
  const tgl = (m) => setMonths((p) => { const n = new Set(p); n.has(m) ? n.delete(m) : n.add(m); return n; });
  const TgBtn = ({ on, onClick, children }) => (
    <button onClick={onClick} aria-pressed={on} style={{ font: "500 11.5px var(--font-ui)", padding: "5px 11px", borderRadius: 4, cursor: "pointer", border: "1px solid " + (on ? "var(--action)" : "var(--hairline)"), background: on ? "var(--selection)" : "var(--surface)", color: on ? "var(--action)" : "var(--text-muted)" }}>{children}</button>
  );
  return (
    <div style={{ display: "grid", gap: 14 }}>
      <Card style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", padding: "12px 16px" }}>
        <Cap style={{ marginRight: 2 }}>ofensores · alert float ip</Cap>
        {MONTHS.map((m) => <TgBtn key={m} on={months.has(m)} onClick={() => tgl(m)}>{m} 2026</TgBtn>)}
        <span style={{ width: 1, alignSelf: "stretch", background: "var(--hairline)", margin: "0 4px" }} />
        <TgBtn on={hideExp} onClick={() => setHideExp((v) => !v)}>excluir esperados (RDM)</TgBtn>
        <span style={{ marginLeft: "auto" }}><Chip m="OBS" s="varredura Slack 27 jul" /></span>
      </Card>
      {view.total === 0 ? (
        <Card style={{ textAlign: "center", padding: 36, color: "var(--text-muted)" }}>Nenhum alerta no recorte. Selecione ao menos um mês.</Card>
      ) : (
        <>
          <Card style={{ display: "flex", gap: 24, alignItems: "center", flexWrap: "wrap" }}>
            <div>
              <div className="num" style={{ font: "700 40px/1 var(--font-ui)", color: "var(--brand)" }}>{view.top.k}</div>
              <Cap style={{ marginTop: 4 }}>maior ofensor do recorte</Cap>
            </div>
            <p style={{ margin: 0, fontSize: 13.5, flex: 1, minWidth: 260 }}>
              <b className="num">{view.top.n} de {view.total}</b> alertas ({Math.round((100 * view.top.n) / view.total)} %)
              {hideExp && view.excluded > 0 && <> — expurgados <b className="num">{view.excluded}</b> disparos de janelas de manutenção (flag MAN via relato do canal)</>}.
              {" "}TESP03 alarma em todos os meses independentemente de manutenção; o storm de perda de pacote do TESP06 em 20 mai segue sem tratamento registrado.
            </p>
          </Card>
          <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 14 }}>
            <Card>
              <Cap>ranking — {view.total} alertas</Cap>
              <div style={{ height: Math.max(180, view.rank.length * 30 + 30), marginTop: 10 }}>
                <ResponsiveContainer>
                  <BarChart data={view.rank} layout="vertical" margin={{ left: 4, right: 30, top: 2, bottom: 0 }}>
                    <CartesianGrid horizontal={false} stroke="var(--hairline)" />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10.5, fontFamily: "var(--font-mono)" }} stroke="var(--text-faint)" />
                    <YAxis type="category" dataKey="k" width={80} tick={{ fontSize: 10.5, fontFamily: "var(--font-mono)" }} stroke="var(--text-faint)" />
                    <Tooltip cursor={{ fill: "var(--selection)" }} contentStyle={{ fontFamily: "var(--font-mono)", fontSize: 11, border: "1px solid var(--hairline)", borderRadius: 6, background: "var(--surface)", color: "var(--ink)" }} formatter={(v) => [v + " alertas", ""]} />
                    <Bar dataKey="n" radius={[0, 3, 3, 0]}>
                      {view.rank.map((r, i) => <Cell key={i} fill={i === 0 ? "var(--petrol-700)" : r.e === "TESP3" ? "var(--petrol-500)" : "var(--petrol-200)"} />)}
                      <LabelList dataKey="n" position="right" style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, fill: "var(--ink)" }} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card>
              <div style={{ display: "flex", justifyContent: "space-between" }}><Cap>atuações registradas no canal</Cap><Chip m="OBS" /></div>
              <div style={{ marginTop: 10 }}>
                {ACTIONS.map((a, i) => (
                  <div key={i} style={{ display: "grid", gridTemplateColumns: "82px 1fr", gap: 10, padding: "8px 0", borderTop: i ? "1px solid var(--hairline)" : "none", fontSize: 12 }}>
                    <span className="num" style={{ color: "var(--text-faint)", fontSize: 11 }}>{a.ts}</span>
                    <span><b style={{ fontWeight: 600 }}>{a.who}</b> — {a.what}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function Muralha() {
  const [nsx, setNsx] = useState([]);
  const [err, setErr] = useState("");
  React.useEffect(() => { api("/nsx/t1/resumo").then(setNsx).catch((e) => setErr(String(e.message || e))); }, []);
  const linhasNsx = nsx.map((r) => ({ plat: "NSX-T", res: "Tier-1 Routers", edge: r.site, use: r.total ?? r.nsx_current ?? 0, op: NSX_T1_OP_LIMIT, vendor: r.nsx_max || 4000, src: "premissa arquitetura · 2k/DC" }));
  const linhas = [...linhasNsx, ...LIMITS];
  return (
    <Card mock style={{ padding: 0, overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", padding: "15px 18px 10px", gap: 8, flexWrap: "wrap" }}>
        <Cap>limites de plataforma — uso × operacional × fabricante</Cap>
        <span style={{ display: "inline-flex", gap: 6 }}><Chip m="OBS" s={err ? `NSX T1 indisponível: ${err}` : `NSX T1 · ${nsx.length} sites`} /><Chip m="EST" s="demais — mock" /></span>
      </div>
      <div className="tscroll">
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
        <thead><tr style={{ borderTop: "1px solid var(--hairline)", borderBottom: "1px solid var(--hairline-strong)" }}>
          {["plataforma", "recurso", "edge", "uso", "limite op", "fabricante", "folga op", "fonte do limite"].map((h, i) => (
            <th key={i} style={{ textAlign: i >= 3 && i <= 6 ? "right" : "left", padding: "7px 14px", font: "600 10px var(--font-ui)", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--text-muted)", whiteSpace: "nowrap" }}>{h}</th>
          ))}
        </tr></thead>
        <tbody>{linhas.map((l, i) => {
          const slack = Math.round(100 * (1 - l.use / l.op));
          const st = slack < 10 ? "crit" : slack < 35 ? "warn" : "ok";
          return (
            <tr key={i} style={{ borderBottom: "1px solid var(--hairline)" }}>
              <td style={{ padding: "8px 14px" }}>{l.plat}</td>
              <td style={{ padding: "8px 14px" }}>{l.res}</td>
              <td className="num" style={{ padding: "8px 14px" }}>{l.edge}</td>
              <td className="num" style={{ padding: "8px 14px", textAlign: "right" }}>{fmt(l.use)}</td>
              <td className="num" style={{ padding: "8px 14px", textAlign: "right", color: "var(--cap-limit-op)" }}>{fmt(l.op)}</td>
              <td className="num" style={{ padding: "8px 14px", textAlign: "right" }}>{fmt(l.vendor)}</td>
              <td className="num" style={{ padding: "8px 14px", textAlign: "right" }}><St st={st} label={slack + " %"} /></td>
              <td style={{ padding: "8px 14px", fontSize: 11.5, color: "var(--text-muted)" }}>{l.src}</td>
            </tr>
          );
        })}</tbody>
      </table>
      </div>
      <div style={{ padding: "10px 18px 14px", fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>limite operacional ≠ limite de fabricante — premissa auditada, editável com histórico</div>
    </Card>
  );
}

function Dominios() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(230px,1fr))", gap: 12 }}>
      {DOMAINS.map((d) => (
        <Card key={d.e} mock={d.e !== "TESP03" && d.e !== "TESP06"} style={{ padding: 16, borderStyle: d.st === "nocollect" ? "dotted" : undefined, borderColor: d.st === "nocollect" ? "var(--state-nocollect)" : undefined }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <span className="num" style={{ font: "700 16px var(--font-mono)", color: "var(--petrol-900)" }}>{d.e}</span>
            <St st={d.st} label={{ ok: "saudável", warn: "atenção", crit: "crítico", nocollect: "sem coleta" }[d.st]} />
          </div>
          <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 4 }}>{d.city}</div>
          <div style={{ fontSize: 12, marginTop: 9, paddingTop: 9, borderTop: "1px solid var(--hairline)" }}>{d.note}</div>
          <div style={{ marginTop: 9 }}><Chip m={d.e === "TESP03" || d.e === "TESP06" ? "OBS" : "EST"} s={d.e === "TESP03" || d.e === "TESP06" ? "Corvo" : "mock"} /></div>
        </Card>
      ))}
    </div>
  );
}

function Campanhas() {
  const cols = [["aberto", "Aberto"], ["andamento", "Em andamento"], ["concluido", "Concluído"]];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 14 }}>
      {cols.map(([id, label]) => (
        <div key={id}>
          <Cap style={{ marginBottom: 8 }}>{label} · {CAMPAIGNS.filter((c) => c.col === id).length}</Cap>
          <div style={{ display: "grid", gap: 10 }}>
            {CAMPAIGNS.filter((c) => c.col === id).map((c, i) => (
              <Card key={i} mock={c.src === "EST"} style={{ padding: 14 }}>
                <div style={{ fontSize: 12.5, lineHeight: 1.45 }}>{c.t}</div>
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10, alignItems: "center" }}>
                  <Chip m={c.src} s={c.src === "OBS" ? "canal Slack" : "mock"} />
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{c.owner}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function Tesouro() {
  return (
    <Card mock>
      <div style={{ display: "flex", justifyContent: "space-between" }}><Cap>orçado × realizado 2026 — rede e segurança</Cap><Chip m="EST" s="mock" /></div>
      <div style={{ display: "grid", gap: 14, marginTop: 14 }}>
        {BUDGET.map((b, i) => {
          const p = Math.round((100 * b.real) / b.plan);
          return (
            <div key={i}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, marginBottom: 5 }}>
                <span>{b.cat}</span>
                <span className="num" style={{ color: "var(--text-muted)" }}>{brl(b.real)} de {brl(b.plan)} · {p} %</span>
              </div>
              <div style={{ height: 9, background: "var(--surface-sunken)", borderRadius: 4, position: "relative" }}>
                <div style={{ position: "absolute", inset: "0 auto 0 0", width: p + "%", background: p > 85 ? "var(--cap-limit-op)" : "var(--action)", borderRadius: 4 }} />
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: 16, paddingTop: 12, borderTop: "1px solid var(--hairline)", fontSize: 12.5 }}>
        Cotação em decisão: <b>expansão NSX T1 TESP07</b> — <span className="num">R$ 387.000</span> · runway pós-expansão 300+ dias.
      </div>
    </Card>
  );
}

function Arquivo() {
  return (
    <Card mock style={{ padding: 0, overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", padding: "15px 18px 10px" }}>
        <Cap>runbooks e fonte de verdade</Cap><Chip m="EST" s="mock — migração do wiki pendente" />
      </div>
      {RUNBOOKS.map((r, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "11px 18px", borderTop: "1px solid var(--hairline)", fontSize: 12.5 }}>
          <a href="#" onClick={(e) => e.preventDefault()}>{r.t}</a>
          <span className="num" style={{ fontSize: 10.5, color: "var(--text-faint)" }}>{r.tags}</span>
        </div>
      ))}
    </Card>
  );
}

/* ----------------- VIGIA — gateway Checkmk federado (OBS) ----------------- */
const inputCss = { padding: "8px 10px", border: "1px solid var(--hairline)", borderRadius: 6, background: "var(--bg-page)", color: "var(--ink)", fontSize: 12.5, fontFamily: "var(--font-ui)" };

function Vigia() {
  const t = useT();
  const [sites, setSites] = useState([]);
  const [dt, setDt] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [fSite, setFSite] = useState("");
  const [fTipo, setFTipo] = useState("all");
  const [nv, setNv] = useState({ site: "", host_name: "", minutes: 60, comment: "", servicos: "" });
  const [rdm, setRdm] = useState({ rdm: "", minutes: 120, plan: "" });

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
  React.useEffect(() => { load(); }, []);

  const criar = async () => {
    if (!nv.site || !nv.host_name || !nv.comment) { setMsg("preencha site, host e comentário"); return; }
    setBusy(true); setMsg("");
    try {
      const servicos = nv.servicos.split(",").map((s) => s.trim()).filter(Boolean);
      await api("/checkmk/downtimes", {
        method: "POST",
        body: JSON.stringify({ site: nv.site, host_name: nv.host_name, minutes: +nv.minutes, comment: nv.comment, servicos: servicos.length ? servicos : null }),
      });
      setMsg(`downtime criado: ${nv.host_name} · ${nv.minutes} min`);
      setNv({ site: "", host_name: "", minutes: 60, comment: "", servicos: "" });
      load();
    } catch (e) { setMsg("erro: " + e.message); }
    setBusy(false);
  };

  const remover = async (item, forcar = false) => {
    setBusy(true); setMsg("");
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
        setMsg("remoção cancelada");
      } else setMsg(r.ok ? `removido: ${item.host}${item.servico ? " · " + item.servico : ""}` : "falhou: " + (r.erro || "confira o site"));
      load();
    } catch (e) { setMsg("erro: " + e.message); }
    setBusy(false);
  };

  const rdmCriar = async () => {
    const plan = rdm.plan.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
      const [site, host, servs] = l.split(/\s+/);
      return { site, host, services: servs ? servs.split(",").filter(Boolean) : null };
    });
    if (!rdm.rdm || !plan.length) { setMsg("informe a RDM e ao menos uma linha: site host [serv1,serv2]"); return; }
    setBusy(true); setMsg("");
    try {
      const out = await api("/checkmk/downtimes/rdm", { method: "POST", body: JSON.stringify({ rdm: rdm.rdm, minutes: +rdm.minutes, plan }) });
      setMsg(out.ok ? `RDM ${rdm.rdm}: ${out.receipts.length} silêncios aplicados` : `RDM ${rdm.rdm}: parcial — confira os recibos no backend`);
      setRdm({ rdm: "", minutes: 120, plan: "" });
      load();
    } catch (e) { setMsg("erro: " + e.message); }
    setBusy(false);
  };

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <Card style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", padding: "12px 16px" }}>
        <Cap style={{ marginRight: 2 }}>{t("downtimes ativos")} · {sites.length} {t("sites federados")}</Cap>
        <select value={fSite} onChange={(e) => { setFSite(e.target.value); load(e.target.value, fTipo); }} style={inputCss}>
          <option value="">{t("todos os sites")}</option>
          {sites.map((s) => <option key={s.id} value={s.id}>{s.id}</option>)}
        </select>
        <select value={fTipo} onChange={(e) => { setFTipo(e.target.value); load(fSite, e.target.value); }} style={inputCss}>
          <option value="all">{t("host + serviço")}</option>
          <option value="host">{t("só host")}</option>
          <option value="service">{t("só serviço")}</option>
        </select>
        <Btn sec onClick={() => load()} disabled={busy} style={{ marginLeft: "auto" }}>{busy ? "…" : t("Atualizar")}</Btn>
        <Chip m="OBS" s="Checkmk · tempo real" />
      </Card>
      {err && <Card style={{ borderColor: "var(--state-crit)", color: "var(--state-crit)", fontSize: 12.5 }}>Falha ao consultar a API: {err} — o backend (:5533) está de pé?</Card>}
      {msg && <Card style={{ padding: "10px 16px", fontSize: 12.5, fontFamily: "var(--font-mono)" }}>{msg}</Card>}
      {dt && dt.erros.length > 0 && (
        <Card style={{ borderColor: "var(--state-warn)", padding: "10px 16px", fontSize: 12 }}>
          {dt.erros.map((e, i) => <div key={i}><St st="warn" label={e.site} /> <span style={{ color: "var(--text-muted)" }}>{e.erro}</span></div>)}
        </Card>
      )}
      <Card style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "15px 18px 10px" }}>
          <Cap>{t("silenciados agora")} · {dt ? dt.total : "…"}</Cap><Chip m="OBS" s="gateway federado" />
        </div>
        {!dt || dt.itens.length === 0 ? (
          <div style={{ padding: "22px 18px", textAlign: "center", color: "var(--text-muted)", fontSize: 12.5 }}>{dt ? t("Nenhum downtime ativo no recorte.") : t("carregando…")}</div>
        ) : (
          <div className="tscroll">
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
            <thead><tr style={{ borderTop: "1px solid var(--hairline)", borderBottom: "1px solid var(--hairline-strong)" }}>
              {["site", "host", "serviço", "autor", "comentário", ""].map((h, i) => (
                <th key={i} style={{ textAlign: "left", padding: "7px 14px", font: "600 10px var(--font-ui)", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--text-muted)" }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>{dt.itens.map((it, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--hairline)" }}>
                <td className="num" style={{ padding: "8px 14px" }}>{it.site}</td>
                <td className="num" style={{ padding: "8px 14px" }}>{it.host}</td>
                <td style={{ padding: "8px 14px" }}>{it.servico || <span style={{ color: "var(--text-faint)" }}>{t("host inteiro")}</span>}</td>
                <td style={{ padding: "8px 14px" }}>{it.autor}</td>
                <td style={{ padding: "8px 14px", color: "var(--text-muted)", maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{it.comentario}</td>
                <td style={{ padding: "8px 14px", textAlign: "right" }}><Btn sec disabled={busy} onClick={() => remover(it)} style={{ padding: "4px 10px", fontSize: 11 }}>{t("remover")}</Btn></td>
              </tr>
            ))}</tbody>
          </table>
          </div>
        )}
      </Card>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 14 }}>
        <Card>
          <Cap>{t("novo silêncio")}</Cap>
          <div style={{ display: "grid", gap: 9, marginTop: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 9 }}>
              <select value={nv.site} onChange={(e) => setNv({ ...nv, site: e.target.value })} style={inputCss}>
                <option value="">site…</option>
                {sites.map((s) => <option key={s.id} value={s.id}>{s.id}</option>)}
              </select>
              <input placeholder="host" value={nv.host_name} onChange={(e) => setNv({ ...nv, host_name: e.target.value })} style={inputCss} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "110px 1fr", gap: 9 }}>
              <input type="number" min={1} value={nv.minutes} onChange={(e) => setNv({ ...nv, minutes: e.target.value })} style={inputCss} title="minutos" />
              <input placeholder={t("serviços (vírgula) — vazio = host inteiro")} value={nv.servicos} onChange={(e) => setNv({ ...nv, servicos: e.target.value })} style={inputCss} />
            </div>
            <input placeholder={t("comentário (obrigatório)")} value={nv.comment} onChange={(e) => setNv({ ...nv, comment: e.target.value })} style={inputCss} />
            <Btn onClick={criar} disabled={busy}>{t("Silenciar")}</Btn>
          </div>
        </Card>
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between" }}><Cap>{t("silêncio por RDM (lote)")}</Cap><Chip m="OBS" s="mata o storm 24–25 mai" /></div>
          <div style={{ display: "grid", gap: 9, marginTop: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 110px", gap: 9 }}>
              <input placeholder="RDM (ex.: 549523)" value={rdm.rdm} onChange={(e) => setRdm({ ...rdm, rdm: e.target.value })} style={inputCss} />
              <input type="number" min={1} value={rdm.minutes} onChange={(e) => setRdm({ ...rdm, minutes: e.target.value })} style={inputCss} title="minutos" />
            </div>
            <textarea rows={4} placeholder={"uma linha por alvo: site host [serv1,serv2]\ntesp3 fw01-tesp3\ntesp5 edge02 CPU,Memory"} value={rdm.plan} onChange={(e) => setRdm({ ...rdm, plan: e.target.value })} style={{ ...inputCss, fontFamily: "var(--font-mono)", resize: "vertical" }} />
            <Btn onClick={rdmCriar} disabled={busy}>{t("Aplicar janela")}</Btn>
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------- MEISTRE ✦ (funcional) -------------------------- */
const MEISTRE_CTX = `Você é o Meistre ✦, assistente da plataforma CITADEL (TOTVS Cloud, infraestrutura de redes, 12 datacenters). Tom: direto, técnico, calmo, orientado a ação; PT-BR; sem linguagem medieval; cite a procedência (OBS/CALC/EST-mock) e diga quando um dado é simulado. Dados carregados na sessão:
[OBS · varredura Slack #alert-float-ip 20mai-27jul/2026] 55 alertas de float IP. Ranking bruto: TECE C1=12, TESP3 C2=11, TESP3 C3=7, TESP6 C3=6. Expurgando 18 esperados (janelas de RDM 549523 em mai e limpeza de disco NSX 21-22 jun): TESP3 C3=7, TESP6 C3=6, TESP3 C2=5, TESP3 C1=5. TESP03=27 alertas no total (79% de julho). 32% dos disparos entre 00h-06h. Storm 21 jul 10:51-10:52: 5 clusters TESP3 em 60s, correlato INC12065 (FW físico CPU 100%, packet buffer, vlan 1019/seginfo). Storm TESP6 20 mai (11 disparos, perda de pacote) sem tratamento registrado. Alerta 27 jul 02:18 ficou 13h42 sem atuação. Melhorias propostas em 30 jun e pendentes: confirmação em 2 passadas, check_icmp, sonda TCP.
[EST · mock] Capacidade: NSX T1 TESP07 184/190 (38 dias, conf 84%); NSX IP Set TESP02 8106/9200 (132d); ACI MAC_PER_IP sem coleta 26h. Tesouro: expansão NSX T1 R$387 mil em cotação.
Pergunta do usuário: `;

function Meistre() {
  const [q, setQ] = useState("");
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);
  const ask = async () => {
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
    <div style={{ display: "grid", gap: 14 }}>
      <Card>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <Cap>meistre — assistente da plataforma</Cap>
          <Chip m="OBS" s="responde com os dados carregados na sessão" />
        </div>
        <p style={{ fontSize: 12.5, color: "var(--text-muted)", margin: "10px 0 0" }}>
          Pergunte sobre os sinais do Corvo, capacidade ou próximos passos. Exemplos: "quem mais alarmou em julho sem contar RDM?" · "resuma o storm de 21 jul para o gestor" · "o que está pendente no monitor de float IP?"
        </p>
      </Card>
      <Card style={{ minHeight: 220, display: "flex", flexDirection: "column", gap: 12 }}>
        {log.length === 0 && <div style={{ margin: "auto", color: "var(--text-faint)", fontSize: 12.5 }}>✦ Faça a primeira pergunta.</div>}
        {log.map((m, i) => (
          <div key={i} style={{ alignSelf: m.r === "user" ? "flex-end" : "flex-start", maxWidth: "82%", background: m.r === "user" ? "var(--selection)" : "var(--bg-page)", border: "1px solid var(--hairline)", borderRadius: 8, padding: "9px 13px", fontSize: 12.5, whiteSpace: "pre-wrap", lineHeight: 1.55 }}>
            {m.r === "ai" && <span style={{ color: "var(--action)", fontWeight: 600 }}>✦ </span>}{m.t}
          </div>
        ))}
        {busy && <div style={{ color: "var(--text-muted)", fontSize: 12, fontFamily: "var(--font-mono)" }}>✦ consultando…</div>}
      </Card>
      <div style={{ display: "flex", gap: 8 }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="Pergunte ao Meistre…" style={{ flex: 1, padding: "10px 13px", border: "1px solid var(--hairline)", borderRadius: 6, background: "var(--surface)", color: "var(--ink)", fontSize: 13, fontFamily: "var(--font-ui)" }} />
        <Btn onClick={ask} disabled={busy}>{busy ? "…" : "Perguntar"}</Btn>
      </div>
    </div>
  );
}

/* ============================ SHELL (5a) ================================== */
const TITLES = {
  conselho: ["Conselho — visão executiva", "síntese para decisão · 27 jul 2026"],
  tresolhos: ["Três Olhos — capacidade e previsão", "trajetórias, runways e limites"],
  corvo: ["Corvo — sinais", "raio-x do canal #alert-float-ip · funcionalidade piloto"],
  vigia: ["Vigia — Checkmk federado", "downtimes reais em 5 sites · criar, listar e remover silêncios"],
  muralha: ["Muralha — limites de plataforma", "uso × alvo operacional × fabricante"],
  dominios: ["Domínios — datacenters", "estado por edge"],
  arquivo: ["Arquivo — runbooks", "fonte de verdade operacional"],
  tesouro: ["Tesouro — orçamento e cotações", "orçado × realizado 2026"],
  campanhas: ["Campanhas — planos de ação", "todo sinal leva a uma ação"],
  meistre: ["Meistre — assistente", "consultas em linguagem natural sobre a plataforma"],
};
const RAIL = {
  corvo: { prov: [["origem", "Slack C05JX7J5MMY"], ["última varredura", "27 jul 20:40"], ["método", "OBS · parser v1"], ["esperados (MAN)", "18 alertas"]], acts: ["Abrir plano p/ TESP3 C3", "Exportar raio-x (PDF)", "Agendar varredura diária"] },
  vigia: { prov: [["origem", "API Checkmk · 5 sites"], ["método", "OBS · gateway federado"], ["transporte", "REST + Livestatus query"]], acts: [] },
  tresolhos: { prov: [["origem", "mock — brief/planilhas"], ["método", "EST · linear v1"], ["confiança", "79–91 %"]], acts: ["Abrir plano de ação", "Comparar domínios"] },
  conselho: { prov: [["capacidade", "EST · mock"], ["sinais", "OBS · Slack"], ["tesouro", "EST · mock"]], acts: ["Exportar resumo executivo"] },
  muralha: { prov: [["limites op", "MAN · premissa auditada"], ["uso", "EST · mock"]], acts: ["Editar premissa de limite"] },
  dominios: { prov: [["TESP03/06", "OBS · Corvo"], ["demais", "EST · mock"]], acts: ["Ver topologia"] },
  arquivo: { prov: [["conteúdo", "EST · mock"]], acts: ["Novo runbook"] },
  tesouro: { prov: [["valores", "EST · mock"]], acts: ["Registrar cotação"] },
  campanhas: { prov: [["cards OBS", "derivados do canal"], ["cards EST", "mock"]], acts: ["Nova campanha"] },
  meistre: { prov: [["modelo", "claude-sonnet-4-6"], ["contexto", "dados da sessão"]], acts: [] },
};

function Shell({ theme, setTheme, onLogout }) {
  const [mod, setMod] = useState("corvo");
  const [railOn, setRailOn] = useState(true);
  const t = useT();
  const [title, sub] = TITLES[mod];
  const rail = RAIL[mod];
  const Body = { conselho: Conselho, tresolhos: TresOlhos, corvo: Corvo, vigia: Vigia, muralha: Muralha, dominios: Dominios, arquivo: Arquivo, tesouro: Tesouro, campanhas: Campanhas, meistre: Meistre }[mod];
  return (
    <div className={"shell" + (railOn ? "" : " norail")}>
      {/* sidebar 228 */}
      <div style={{ background: "var(--surface)", borderRight: "1px solid var(--hairline)", display: "flex", flexDirection: "column", position: "sticky", top: 0, height: "100vh" }}>
        <div style={{ padding: "16px 16px 13px", borderBottom: "1px solid var(--hairline)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <TotvsLogo white={theme === "dark"} height={15} />
            <span style={{ font: "600 9.5px var(--font-mono)", letterSpacing: ".2em", color: "var(--text-muted)" }}>CLOUD</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 9 }}>
            <Logo size={22} color="var(--action)" />
            <span style={{ font: "700 19px var(--font-ui)", letterSpacing: ".03em", color: "var(--petrol-900)" }}>CITADEL</span>
          </div>
        </div>
        <nav style={{ paddingTop: 8, flex: 1, overflowY: "auto" }}>
          {MODULES.map((m) => {
            const on = m.id === mod;
            return (
              <button key={m.id} onClick={() => setMod(m.id)} style={{
                display: "grid", gridTemplateColumns: "1fr auto", gap: "0 8px", alignItems: "baseline", width: "100%", textAlign: "left",
                padding: "8px 16px", border: "none", cursor: "pointer", background: on ? "var(--selection)" : "transparent",
                boxShadow: on ? "inset 2px 0 var(--action)" : "none",
              }}>
                <span style={{ font: `${on ? 600 : 500} 13px var(--font-ui)`, color: on ? "var(--petrol-900)" : "var(--ink)" }}>{t(m.n)}</span>
                <span className="num" style={{ fontSize: 10.5, color: m.hot ? "var(--state-warn)" : m.count ? "var(--text-muted)" : "transparent" }}>{m.count || "·"}</span>
                <span style={{ fontSize: 10.5, color: "var(--text-muted)", gridColumn: "1/2" }}>{t(m.d)}</span>
              </button>
            );
          })}
        </nav>
        <div style={{ borderTop: "1px solid var(--hairline)", padding: "12px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
          <button onClick={() => setMod("meistre")} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, color: "var(--action)", fontWeight: 600, background: mod === "meistre" ? "var(--selection)" : "transparent", border: "none", cursor: "pointer", padding: "6px 8px", margin: "0 -8px", borderRadius: 6, textAlign: "left" }}>
            ✦ Meistre<span className="num" style={{ marginLeft: "auto", fontSize: 10, color: "var(--text-muted)", fontWeight: 400 }}>⌘J</span>
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: 8, borderTop: "1px solid var(--hairline)", paddingTop: 10 }}>
            <span style={{ width: 24, height: 24, borderRadius: "50%", background: "var(--selection)", color: "var(--petrol-900)", font: "600 10px var(--font-ui)", display: "flex", alignItems: "center", justifyContent: "center" }}>MF</span>
            <span style={{ fontSize: 11.5, lineHeight: 1.3 }}>m.ferreira<br /><a href="#" onClick={(e) => { e.preventDefault(); onLogout(); }} style={{ fontSize: 10.5 }}>{t("Sair")}</a></span>
            <LangBtn style={{ marginLeft: "auto", padding: "2px 8px" }} />
            <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")} title="tema" style={{ border: "1px solid var(--hairline)", background: "transparent", color: "var(--ink)", borderRadius: 6, padding: "2px 8px", cursor: "pointer", font: "600 11px var(--font-mono)" }}>{theme === "dark" ? "☀" : "☾"}</button>
          </div>
        </div>
      </div>
      {/* painel central */}
      <div style={{ minWidth: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "13px 24px", borderBottom: "1px solid var(--hairline)", background: "var(--surface)", position: "sticky", top: 0, zIndex: 2, display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ font: "600 15px var(--font-ui)", color: "var(--petrol-900)" }}>{t(title)}</div>
            <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 2 }}>{t(sub)}</div>
          </div>
          <button onClick={() => setRailOn((v) => !v)} title={railOn ? t("ocultar painel lateral") : t("mostrar painel lateral")}
            style={{ border: "1px solid var(--hairline)", background: railOn ? "var(--selection)" : "transparent", color: "var(--ink)", borderRadius: 6, padding: "3px 9px", cursor: "pointer", font: "600 12px var(--font-mono)" }}>◧</button>
        </div>
        <div style={{ padding: "18px 24px 40px", flex: 1, minWidth: 0 }}><Body go={setMod} /></div>
      </div>
      {/* rail 316 */}
      <div className="rail" style={{ borderLeft: "1px solid var(--hairline)", background: "var(--surface)", padding: "18px 20px", position: "sticky", top: 0, height: "100vh", flexDirection: "column", gap: 18 }}>
        <div>
          <Cap>{t("procedência")}</Cap>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "7px 10px", fontSize: 11.5, marginTop: 9 }}>
            {rail.prov.map(([k, v], i) => <React.Fragment key={i}><span style={{ color: "var(--text-muted)" }}>{k}</span><span className="num" style={{ textAlign: "right" }}>{v}</span></React.Fragment>)}
          </div>
        </div>
        {rail.acts.length > 0 && (
          <div>
            <Cap>{t("ações")}</Cap>
            <div style={{ display: "grid", gap: 8, marginTop: 9 }}>
              {rail.acts.map((a, i) => <Btn key={i} sec={i > 0} style={{ width: "100%" }}>{a}</Btn>)}
            </div>
          </div>
        )}
        <div style={{ marginTop: "auto", fontSize: 10.5, color: "var(--text-faint)", fontFamily: "var(--font-mono)", lineHeight: 1.6 }}>
          borda tracejada âmbar = dado simulado (EST · mock)<br />sólida = observado · pontilhada = sem coleta
        </div>
      </div>
    </div>
  );
}

/* ================================ APP ===================================== */
export default function CitadelApp() {
  const [authed, setAuthed] = useState(false);
  const [theme, setTheme] = useState("light");
  const [lang, setLangState] = useState(() => localStorage.getItem("citadel_lang") || "pt");
  const setLang = (l) => { localStorage.setItem("citadel_lang", l); setLangState(l); };
  return (
    <LangCtx.Provider value={[lang, setLang]}>
      <div data-theme={theme} style={{ minHeight: "100vh", background: "var(--bg-page)" }}>
        <style>{CSS}</style>
        {authed
          ? <Shell theme={theme} setTheme={setTheme} onLogout={() => setAuthed(false)} />
          : <Login onEnter={() => setAuthed(true)} theme={theme} setTheme={setTheme} />}
      </div>
    </LangCtx.Provider>
  );
}
