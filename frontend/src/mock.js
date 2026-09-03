/* ============================== DADOS =====================================
   PROCEDÊNCIA:
   · OBS — CORVO usa 55 alertas REAIS da varredura do Slack #alert-float-ip
     (20 mai – 27 jul 2026) e as atuações registradas no canal.
   · CALC — agregações com regra declarada.
   · MAN — janelas de RDM classificadas pelo relato humano do canal.
   · EST/mock — capacidade, limites, domínios, tesouro e arquivo são dados
     SIMULADOS (borda tracejada âmbar + chip "EST · mock") até os coletores
     reais (nsx_collector, fortigate-fisico, ACI) alimentarem o backend.
   ========================================================================== */

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
export const ALERTS = RAW.split("\n").map((l) => {
  const [m, d, e, c, s, f, hl, pl, exp] = l.split("|");
  return { m, d, e, c, s: +s, f: +f, hl: +hl, pl: pl === "1", exp: exp === "1" };
});
export const MONTHS = ["mai", "jun", "jul"];

/* Atuações humanas — OBS (mensagens do canal). */
export const ACTIONS = [
  { ts: "27 jul 16:21", who: "Bruno (gestor)", what: "Cobra análise do alerta TESP3 C2 de 02:18 — 14 h após o disparo." },
  { ts: "21 jul 11:52", who: "Max", what: "RCA do storm: FW físico a 100 % de CPU, packet buffer, pico CPS/PPS, vlan 1019. INC12065." },
  { ts: "14 jul 09:57", who: "Max", what: "Mapeia >50 VMs internas impactadas (devops-workspace, LAB_DB_CORE_TEAM, TDEVOPS)." },
  { ts: "30 jun 09:28", who: "Max", what: "Classifica falso positivo (CoPP) e propõe: 2 passadas, check_icmp, sonda TCP." },
  { ts: "22 jun 10:52", who: "Bruno (gestor)", what: "Processo: RDMs futuras devem incluir task para desabilitar o alert-ip." },
  { ts: "25 mai 00:42", who: "Junovan", what: "RDM 549523: schedule de silêncio falhou; alarmes desativados manualmente." },
];

/* MURALHA / DOMÍNIOS / TESOURO / ARQUIVO — EST · mock.
   Três Olhos NÃO usa mais mock: lê /nsx/t1/* (OBS · nsx-collector → InfluxDB).            */
/* Herói do login e do Conselho — EST · mock agregado (sem nome de recurso no painel público). */
export const HERO = { days: 38, conf: "84%", usage: 184, op: 190, tech: 200, hist: [152, 154, 158, 163, 168, 172, 176, 181, 184], proj: [184, 190, 197, 205] };
export const LIMITS = [
  // NSX-T · Tier-1 Routers: linhas reais por site via /nsx/t1/resumo (Muralha).
  { plat: "NSX-T", res: "NAT Rules", edge: "TESP03", use: 17097, op: 25000, vendor: 30000, src: "config-max VMware" },
  { plat: "Palo Alto", res: "Sessões vsys1", edge: "TESP02", use: 690000, op: 2000000, vendor: 4000000, src: "datasheet PA-5260" },
  { plat: "Palo Alto", res: "Regras de firewall", edge: "TESP02", use: 48, op: 85, vendor: 100, src: "premissa (%)" },
  { plat: "FortiGate", res: "Firewall Policies", edge: "TESP04", use: 3400, op: 10000, vendor: 20000, src: "datasheet 600F" },
  { plat: "ACI", res: "Portas Leaf 25G", edge: "TESP07", use: 30, op: 48, vendor: 48, src: "inventário físico" },
];
export const DOMAINS = [
  { e: "TESP02", city: "São Paulo · Ascenty", st: "ok", note: "IPs públicos 64 %" },
  { e: "TESP03", city: "São Paulo · Megatelecom", st: "crit", note: "ofensor Corvo · C3 recorrente", obs: true },
  { e: "TESP04", city: "São Paulo · UPX", st: "warn", note: "FW CPU instável (14 jul)" },
  { e: "TESP05", city: "São Paulo", st: "ok", note: "1 alerta em jul" },
  { e: "TESP06", city: "São Paulo", st: "warn", note: "storm 20 mai sem desfecho", obs: true },
  { e: "TESP07", city: "São Paulo", st: "crit", note: "NSX T1 · 38 d" },
  { e: "TECE01", city: "Fortaleza", st: "ok", note: "RDM 549523 concluída" },
  { e: "TBSP01", city: "São Paulo", st: "nocollect", note: "sem coleta 26 h" },
];
export const CAMPAIGNS = [
  { t: "Investigar recorrência TESP3 C3 (7 alertas expurgados)", col: "aberto", src: "OBS", owner: "Redes" },
  { t: "Monitor float IP: 2 passadas + check_icmp + sonda TCP", col: "aberto", src: "OBS", owner: "Max" },
  { t: "Silenciamento automático de alertas na abertura de RDM", col: "andamento", src: "OBS", owner: "Davi" },
  { t: "Corrigir listagem de VMs no anexo do bot", col: "andamento", src: "OBS", owner: "N2" },
  { t: "Expansão NSX T1 TESP07 (+50 · R$ 387.000)", col: "aberto", src: "EST", owner: "Arquitetura" },
  { t: "RCA storm TESP6 20 mai (11 disparos, sem tratamento)", col: "aberto", src: "OBS", owner: "Redes" },
  { t: "Reconciliar IPAM × planilha (blocos /24)", col: "concluido", src: "EST", owner: "Max" },
];
export const BUDGET = [
  { cat: "Circuitos e operadoras", plan: 4200000, real: 2310000 },
  { cat: "Licenciamento NSX/Palo/Forti", plan: 3800000, real: 2960000 },
  { cat: "Expansões de hardware", plan: 2600000, real: 940000 },
];
export const RUNBOOKS = [
  { t: "Convenção de nomenclatura — hosts & proxies SSH", tags: "ssh · nomenclatura" },
  { t: "Baseline de métricas Palo Alto — o que observar", tags: "palo · observability" },
  { t: "Procedimento: silêncio de alertas em janela de RDM", tags: "checkmk · rdm" },
  { t: "Float IP — anatomia do alerta e triagem", tags: "corvo · floatip" },
];
/* CONSELHO — o que exige decisão (estado + texto + procedência). */
export const DECISIONS = [
  ["crit", "Expansão NSX T1 TESP07 — aprovar cotação de R$ 387 mil antes de 05 ago para manter runway.", "EST"],
  ["warn", "TESP3 C3: 7 alertas fora de janela em jun–jul — designar responsável pela investigação.", "OBS"],
  ["warn", "Storm TESP6 de 20 mai segue sem RCA registrado no canal.", "OBS"],
];

/* Módulos: nome nunca sem descritor (readme do DS). */
export const MODULES = [
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
export const TITLES = {
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
/* Rail: procedência (linhas do ProvenancePanel) + ações do módulo. */
export const RAIL = {
  corvo: { prov: [["origem", "Slack C05JX7J5MMY"], ["última varredura", "27 jul 20:40"], ["método", "OBS · parser v1"], ["esperados (MAN)", "18 alertas"]], acts: ["Abrir plano p/ TESP3 C3", "Exportar raio-x (PDF)", "Agendar varredura diária"] },
  vigia: { prov: [["origem", "API Checkmk · 5 sites"], ["método", "OBS · gateway federado"], ["transporte", "REST + Livestatus query"]], acts: [] },
  tresolhos: { prov: [["origem", "nsx-collector → InfluxDB"], ["método", "OBS · read-model /nsx/t1"], ["projeção", "CALC · linear 90 d"], ["limite op", "MAN · 2.000 T1/DC"]], acts: ["Abrir plano de ação", "Comparar domínios"] },
  conselho: { prov: [["capacidade", "EST · mock"], ["sinais", "OBS · Slack"], ["tesouro", "EST · mock"]], acts: ["Exportar resumo executivo"] },
  muralha: { prov: [["NSX T1", "OBS · /nsx/t1/resumo"], ["limites op", "MAN · premissa auditada"], ["demais", "EST · mock"]], acts: ["Editar premissa de limite"] },
  dominios: { prov: [["TESP03/06", "OBS · Corvo"], ["demais", "EST · mock"]], acts: ["Ver topologia"] },
  arquivo: { prov: [["conteúdo", "EST · mock"]], acts: ["Novo runbook"] },
  tesouro: { prov: [["valores", "EST · mock"]], acts: ["Registrar cotação"] },
  campanhas: { prov: [["cards OBS", "derivados do canal"], ["cards EST", "mock"]], acts: ["Nova campanha"] },
  meistre: { prov: [["modelo", "claude-sonnet-4-6"], ["contexto", "dados da sessão"]], acts: [] },
};

/* Formatação PT-BR: vírgula decimal, unidade sempre visível. */
export const fmt = (n) => n.toLocaleString("pt-BR");
export const brl = (n) => "R$ " + (n / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 0 }) + " mil";
