/** Procedência do dado (princípio 2): método OBS/CALC/EST/MAN + fonte + idade + confiança. ProvenancePanel = versão em grade para rails.
 * @startingPoint section="Capacidade" subtitle="Chip de procedência OBS/CALC/EST/MAN" viewport="440x60" */
export interface ProvenanceChipProps {
  method?: 'OBS' | 'CALC' | 'EST' | 'MAN';
  /** Fonte (ex.: "coletor NSX") */
  source?: string;
  /** Idade da coleta (ex.: "há 7 min") */
  age?: string;
  /** Confiança (ex.: "84%") */
  confidence?: string;
  /** Dado desatualizado: borda dashed + ◐ */
  stale?: boolean;
  lang?: 'pt' | 'en';
  style?: React.CSSProperties;
}
export interface ProvenancePanelProps {
  /** Pares [rótulo, valor] */
  rows: [string, React.ReactNode][];
  title?: string;
  style?: React.CSSProperties;
}
