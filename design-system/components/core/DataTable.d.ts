/** Tabela densa CITADEL — cabeçalho caps mono, linha selecionada com trilho petróleo, densidade 44/36px.
 * @startingPoint section="Componentes" subtitle="Tabela densa com seleção e densidade 44/36" viewport="680x220" */
export interface DataTableColumn {
  key: string;
  label: string;
  align?: 'left' | 'right' | 'center';
  /** JetBrains Mono + numerais tabulares (números, IPs, datas) */
  mono?: boolean;
  width?: number | string;
}
export interface DataTableProps {
  columns: DataTableColumn[];
  /** Cada linha: { id, [colKey]: ReactNode } */
  rows: Array<{ id: string } & Record<string, React.ReactNode>>;
  density?: 'comfortable' | 'compact';
  selectedId?: string;
  onRowClick?: (id: string) => void;
  style?: React.CSSProperties;
}
