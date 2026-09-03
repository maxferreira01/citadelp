// CITADEL Design System — ponto único de importação.
// Regra do _adherence.oxlintrc.json: o app importa daqui, nunca de components/** direto.
// Tokens: importar `styles.css` (→ tokens/fonts, colors, typography, spacing, effects).

export { Button } from './components/core/Button.jsx';
export { TextField } from './components/core/TextField.jsx';
export { Select } from './components/core/Select.jsx';
export { Tabs } from './components/core/Tabs.jsx';
export { StatusBadge, STATUS_STATES } from './components/core/StatusBadge.jsx';
export { DataTable } from './components/core/DataTable.jsx';
export { Toast } from './components/core/Toast.jsx';
export { Modal } from './components/core/Modal.jsx';

export { RunwayBar } from './components/dominio/RunwayBar.jsx';
export { ProvenanceChip, ProvenancePanel } from './components/dominio/ProvenanceChip.jsx';
export { DomainTile } from './components/dominio/DomainTile.jsx';
export { TrajectoryChart } from './components/dominio/TrajectoryChart.jsx';
