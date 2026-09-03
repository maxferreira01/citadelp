# UI Kit — CITADEL

Recriação navegável das duas telas aprovadas na exploração (canvas `Exploracao Visual Cidadela.html`):

- **Login** (base 4b) — painel escuro com métrica herói **agregada** (sem nome de recurso nem R$, decisão 27/07), nota do dia (citação, sem comentário), SSO TOTVS. Clique em SSO/Entrar → plataforma.
- **Três Olhos / Three Eyes** (base 5a) — sidebar com módulos PT/EN, **primeira vista = alerta ativo** (NSX T1 · 38 d), gráfico de trajetória, runways clicáveis, rail com cenários/procedência/ações. "Sair" volta ao login.

Toggle **PT/EN** persiste em `localStorage` (`citadel-kit-lang`). Módulos fora de Três Olhos ficam desabilitados com tooltip.

Composição: só componentes do bundle (`Button`, `TextField`, `Tabs`, `StatusBadge`, `RunwayBar`, `ProvenanceChip/Panel`, `TrajectoryChart`) + tokens de `styles.css`. Dados mockados do brief + planilhas anexadas (TESP07 NSX T1 184/190/200 etc.).
