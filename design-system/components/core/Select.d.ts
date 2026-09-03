/** Select nativo estilizado — período, ambiente, ordenação. Para domínios use DomainTile/seletor do kit. */
export interface SelectProps {
  label?: string;
  value?: string;
  options: { value: string; label: string }[];
  disabled?: boolean;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
}
