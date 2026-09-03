/** Abas sublinhadas com contador opcional (contadores são compromissos, não decoração). */
export interface TabsProps {
  items: { id: string; label: string; count?: number | string }[];
  active: string;
  onChange?: (id: string) => void;
  style?: React.CSSProperties;
}
