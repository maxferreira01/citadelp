/** Campo de texto com rótulo em caps, hint e erro. `mono` para valores técnicos (IP, CIDR, usuário). */
export interface TextFieldProps {
  label?: string;
  value?: string;
  placeholder?: string;
  /** Texto auxiliar abaixo do campo */
  hint?: string;
  /** Mensagem de erro (substitui o hint; borda crítica) */
  error?: string;
  /** Usa JetBrains Mono no valor */
  mono?: boolean;
  disabled?: boolean;
  type?: string;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
}
