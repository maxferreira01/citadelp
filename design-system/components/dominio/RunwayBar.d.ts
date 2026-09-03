/** Runway compacto de capacidade: uso consumido + marcas de limite operacional (âmbar tracejado) e técnico (tinta sólida). Aparece em qualquer lista.
 * @startingPoint section="Capacidade" subtitle="Barra de runway com limites op/téc" viewport="520x84" */
export interface RunwayBarProps {
  /** Uso atual, na mesma unidade dos limites */
  usage: number;
  opLimit?: number;
  techLimit?: number;
  /** Rótulo à esquerda (ex.: "NSX T1 · Cluster_1") */
  label?: React.ReactNode;
  /** Linha mono abaixo da barra (ex.: <><span>0</span><span>op 190</span><span>téc 200</span></>) */
  caption?: React.ReactNode;
  /** Tempo restante (ex.: "▲ 38 dias") */
  days?: string;
  /** Confiança (ex.: "84%") */
  confidence?: string;
  state?: 'ok' | 'warn' | 'crit' | 'emergency' | 'stale' | 'nocollect';
  /** Sem coleta: trilho tracejado no lugar do preenchimento */
  nocollect?: boolean;
  height?: number;
  style?: React.CSSProperties;
}
