/** Diálogo modal para confirmação e formulários curtos; investigação profunda usa painel lateral, não modal. */
export interface ModalProps {
  open?: boolean;
  title: string;
  children?: React.ReactNode;
  /** Botões (ex.: <Button/>) alinhados à direita */
  footer?: React.ReactNode;
  onClose?: () => void;
  width?: number;
  /** Renderiza no fluxo (specimens/documentação) em vez de overlay fixo */
  inline?: boolean;
  style?: React.CSSProperties;
}
