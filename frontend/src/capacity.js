import { STATUS_STATES } from "@ds";

/* Índice (na série total histórico+projeção) em que a projeção cruza o limite
   operacional — alimenta o marco de saturação do TrajectoryChart. Interpola
   linearmente entre os dois pontos da projeção; vazio se não cruza no horizonte. */
export function saturation({ hist = [], proj = [], op }) {
  if (!hist.length || proj.length < 2 || !op) return {};
  const ti = hist.length - 1;
  for (let i = 1; i < proj.length; i++) {
    if (proj[i] >= op) {
      const a = proj[i - 1], b = proj[i];
      const f = b === a ? 0 : (op - a) / (b - a);
      return { satIndex: ti + i - 1 + f };
    }
  }
  return {};
}

/* Rótulo de runway: glifo + texto, nunca só cor. */
export function runwayLabel(r, t) {
  const g = (STATUS_STATES[r.st] || STATUS_STATES.info).glyph;
  if (r.st === "nocollect") return `${g} ${t("sem coleta 26 h")}`;
  if (r.st === "stale") return `${g} ${t("instável")}`;
  return `${g} ${r.days} ${t("dias")}`;
}

/* Alternativa textual obrigatória do gráfico (ariaText). */
export function trajectoryText(r, fmt) {
  const base = `${r.name}: ${fmt(r.usage)} de ${fmt(r.op)} (limite operacional), ${fmt(r.tech)} (limite técnico)`;
  return r.days ? `${base}; pode atingir o limite operacional em ${r.days} dias, confiança ${r.conf}.` : `${base}.`;
}
