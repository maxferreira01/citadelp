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

/* Alternativa textual obrigatória do gráfico (ariaText). */
export function trajectoryText(r, fmt) {
  const base = `${r.name}: ${fmt(r.usage)} de ${fmt(r.op)} (limite operacional), ${fmt(r.tech)} (limite técnico)`;
  return r.days ? `${base}; pode atingir o limite operacional em ${r.days} dias, confiança ${r.conf}.` : `${base}.`;
}
