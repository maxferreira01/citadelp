/** Gráfico-assinatura da CITADEL: histórico sólido, linha do agora, projeção tracejada com cone de incerteza, limites op/téc e marco de saturação. Sempre forneça ariaText.
 * @startingPoint section="Capacidade" subtitle="Trajetória com cone de confiança e limites" viewport="640x220" */
export interface TrajectoryChartEvent { index: number; label: string }
export interface TrajectoryChartProps {
  /** Série observada (histórico até hoje) */
  history: number[];
  /** Série projetada a partir de hoje (1º ponto = hoje) */
  projection?: number[];
  opLimit?: number;
  techLimit?: number;
  /** Teto do eixo Y; default téc×1,08 */
  max?: number;
  width?: number;
  height?: number;
  todayLabel?: string;
  /** Rótulo do marco de saturação (ex.: "28 ago · 84%") */
  satLabel?: string;
  /** Índice (na série total) onde a projeção cruza o limite operacional */
  satIndex?: number;
  /** Piso do eixo Y; default ~min(história)×0,9 — evita gráfico achatado */
  yMin?: number;
  xLabels?: string[];
  /** Losangos de eventos futuros */
  events?: TrajectoryChartEvent[];
  /** Paleta para fundos escuros */
  dark?: boolean;
  /** Alternativa textual obrigatória (ex.: "pode atingir 190 em 28/08, confiança 84%") */
  ariaText?: string;
  style?: React.CSSProperties;
}
