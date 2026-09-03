import { createContext, useContext } from "react";

/* PT-BR é o padrão; EN é opção. Chave = texto em PT; sem entrada = mesma string.
   Tom (readme do DS): direto, técnico, calmo, orientado a ação. */
export const EN = {
  // login (tela 4b)
  "Bem-vindo de volta": "Welcome back", "plataforma interna · TOTVS Cloud": "internal platform · TOTVS Cloud", "nota do dia": "note of the day",
  "Veja o limite antes de alcançá-lo.": "See the limit before you reach it.",
  "risco mais próximo": "nearest risk", "dias": "days", "hoje": "today",
  "até o limite operacional mais próximo\nem um domínio de produção": "until the nearest operational limit\nin a production domain",
  "recursos saturam em menos de 90 dias": "resources saturate in under 90 days",
  "coletores sem coleta há mais de 24 h": "collectors silent for over 24 h",
  "sinais de float IP analisados no trimestre": "float IP signals analysed this quarter",
  "coleta contínua · 46 de 48 coletores respondendo": "continuous collection · 46 of 48 collectors responding",
  "projeção 12 m · cone P10–P90": "12-mo forecast · P10–P90 cone",
  "Entrar": "Sign in", "Acesso restrito às equipes de infraestrutura, operações e gestão.": "Access restricted to infrastructure, operations and management teams.",
  "Continuar com SSO TOTVS": "Continue with TOTVS SSO", "ou": "or", "Usuário corporativo": "Corporate user", "Senha": "Password",
  "status da plataforma": "platform status", "coletores respondendo": "collectors responding",
  "varredura Corvo (Slack)": "Raven sweep (Slack)", "sincronização CMDB": "CMDB sync", "há 9 min": "9 min ago",
  "Uso interno · dados classificados": "Internal use · classified data",
  "Login Google indisponível — defina": "Google sign-in unavailable — set", "no .env do backend.": "in the backend .env.",
  "Falha no login Google. Tente novamente.": "Google sign-in failed. Try again.",
  // sidebar
  "Conselho": "Council", "Três Olhos": "Three Eyes", "Corvo": "Raven", "Vigia": "Watch", "Muralha": "The Wall",
  "Domínios": "Domains", "Arquivo": "Archive", "Tesouro": "Treasury", "Campanhas": "Campaigns",
  "visão executiva": "executive view", "capacidade e previsão": "capacity & forecast", "sinais e integrações": "signals & integrations",
  "Checkmk · downtimes reais": "Checkmk · live downtimes", "limites de plataforma": "platform limits",
  "datacenters e topologia": "datacenters & topology", "wiki e runbooks": "wiki & runbooks",
  "orçamento e cotações": "budget & quotes", "planos de ação": "action plans", "Sair": "Sign out", "módulos": "modules",
  // shell
  "procedência": "provenance", "ações": "actions", "ocultar painel lateral": "hide side rail", "mostrar painel lateral": "show side rail",
  "borda tracejada âmbar = dado simulado (EST · mock)": "dashed amber border = simulated data (EST · mock)",
  "sólida = observado · pontilhada = sem coleta": "solid = observed · dotted = no data",
  // títulos
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
  // três olhos
  "runways por recurso": "runways per resource", "sem coleta 26 h": "no data 26 h", "instável": "unstable",
  // vigia
  "downtimes ativos": "active downtimes", "sites federados": "federated sites", "todos os sites": "all sites",
  "host + serviço": "host + service", "só host": "host only", "só serviço": "service only", "Atualizar": "Refresh",
  "silenciados agora": "silenced now", "Nenhum downtime ativo no recorte.": "No active downtime in this view.",
  "host inteiro": "entire host", "remover": "remove", "novo silêncio": "new silence", "Silenciar": "Silence",
  "silêncio por RDM (lote)": "RDM silence (batch)", "Aplicar janela": "Apply window", "minutos": "minutes", "serviços": "services",
  "comentário (obrigatório)": "comment (required)", "vazio = host inteiro": "empty = entire host",
  "carregando…": "loading…", "sites com erro na consulta": "sites with query errors", "o backend (:5533) está de pé?": "is the backend (:5533) up?",
  // meistre
  "Perguntar": "Ask", "Pergunte ao Meistre…": "Ask Meistre…", "✦ Faça a primeira pergunta.": "✦ Ask the first question.", "consultando…": "querying…",
};

/* Nota do dia — citação sem comentário (kit do DS + a frase da equipe). Rotaciona pelo dia do mês. */
export const QUOTES = [
  { q: "O que não é medido é negociado no susto.", en: "What is not measured gets negotiated in a panic.", who: "Engenharia de Redes · TOTVS Cloud" },
  { q: "Talk is cheap. Show me the code.", who: "Linus Torvalds" },
  { q: "Everything fails, all the time.", who: "Werner Vogels" },
  { q: "In God we trust; all others must bring data.", who: "W. Edwards Deming" },
  { q: "Hope is not a strategy.", who: "SRE proverb · Google" },
];
export const quoteOfDay = (lang) => {
  const it = QUOTES[new Date().getDate() % QUOTES.length];
  return { text: (lang === "en" && it.en) || it.q, who: it.who };
};

export const LangCtx = createContext(["pt", () => {}]);
export const useLang = () => useContext(LangCtx);
export const useT = () => {
  const [lang] = useContext(LangCtx);
  return (s) => (lang === "en" && EN[s]) || s;
};
