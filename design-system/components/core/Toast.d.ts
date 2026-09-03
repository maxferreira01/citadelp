/** Notificação transitória. Sinais operacionais NÃO terminam em toast — use com actionLabel apontando para investigação/plano. */
export interface ToastProps {
  kind?: 'info' | 'ok' | 'warn' | 'crit' | 'nocollect' | 'stale' | 'divergent';
  title: string;
  detail?: string;
  /** Todo sinal leva a uma ação — rotule o próximo passo */
  actionLabel?: string;
  onAction?: () => void;
  onClose?: () => void;
  style?: React.CSSProperties;
}
