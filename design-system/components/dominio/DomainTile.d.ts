/** Cartão de domínio/datacenter: código, estado, tempo até limite, barra de uso. Grade de tiles = visão da frota.
 * @startingPoint section="Capacidade" subtitle="Tile de datacenter com estado e runway" viewport="200x110" */
export interface DomainTileProps {
  /** Código do domínio (ex.: "TESP07") */
  code: string;
  state?: 'ok' | 'warn' | 'crit' | 'emergency' | 'stale' | 'nocollect' | 'unknown';
  /** Tempo até o limite (ex.: "38 d") */
  days?: string;
  note?: string;
  /** Uso 0–100 para a microbarra */
  usagePct?: number;
  /** Etiqueta de ambiente (ex.: "prod", "cont") */
  env?: string;
  selected?: boolean;
  /** Paleta para painéis escuros (login, NOC) */
  dark?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}
