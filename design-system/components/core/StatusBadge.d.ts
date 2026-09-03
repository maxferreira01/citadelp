/** Estado semântico com glifo + cor + texto (nunca só cor). Bordas dashed/dotted reforçam desconhecido/sem-coleta.
 * @startingPoint section="Componentes" subtitle="10 estados com glifo, cor e texto" viewport="420x80" */
export interface StatusBadgeProps {
  state?: 'info' | 'ok' | 'warn' | 'crit' | 'emergency' | 'unknown' | 'unavailable' | 'nocollect' | 'stale' | 'divergent';
  /** Sobrescreve o rótulo padrão (ex.: "38 dias") */
  label?: string;
  /** Idioma dos rótulos padrão */
  lang?: 'pt' | 'en';
  /** Fundo tonal */
  filled?: boolean;
  /** Só o glifo (células densas); rótulo vira title */
  glyphOnly?: boolean;
  style?: React.CSSProperties;
}
