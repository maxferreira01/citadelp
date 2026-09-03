/** Botão CITADEL. Primário = ação principal única da vista; secundário = alternativas; ghost = ações de linha/tabela; danger = destrutivas (raro).
 * @startingPoint section="Componentes" subtitle="Ação primária, secundária, ghost e danger" viewport="360x64" */
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  /** Ocupa a largura do contêiner (formulários, rails) */
  block?: boolean;
  type?: 'button' | 'submit';
  onClick?: () => void;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
