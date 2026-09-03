# CITADEL — Design System

Plataforma interna de gestão de infraestrutura de redes e datacenters (TOTVS Cloud, ~12 datacenters). Consolida capacidade, limites de plataforma (NSX/Palo Alto/FortiGate), inventário/CMDB, IPAM, circuitos, colocation, orçamento/cotações, planos de ação, wiki/runbooks e procedência de dados.

**Marca:** CITADEL (inglês, decisão 27/07/2026) · assinatura "Conhecimento, capacidade e decisão." / "Knowledge, capacity, decision." · **Direção visual:** B — "Horizonte" × identidade TOTVS. Plataforma bilíngue PT/EN.

## Decisões aprovadas
- Login = tela **4b** (métrica herói + nota do dia), destaques pré-login **agregados** (sem nomes de recurso/R$)
- Layout de app = tela **5a** (sidebar 228px + painel + rail 316px)
- Tipografia: **TOTVS Bold** (marca/títulos, extraída de totvs.com.br) + **Archivo** (interface) + **JetBrains Mono** (dados)
- Light E dark intencionais (light = análise, dark = NOC); densidade confortável 44px padrão, compacta 36px como toggle
- Só wordmark tipográfico (sem símbolo); acentos = paleta derivada do logo (petróleo #002233 → ação #0F5E8C + âmbar #B4690E); paleta viva do site TOTVS registrada só como referência (`--totvs-*`)
- Primeiro item de Três Olhos = **alerta ativo** (NSX T1 · 38 d)

## Princípios
1. Trajetória, não só estado · 2. Todo dado tem procedência · 3. Todo sinal leva a uma ação · 4. Profundidade progressiva · 5. Densidade sem ruído · 6. Uma verdade, várias perspectivas · 7. O desconhecido também é um estado

## Módulos (nome nunca sem descritor; PT/EN)
CIDADELA/CITADEL entrada global · CONSELHO/COUNCIL visão executiva · TRÊS OLHOS/THREE EYES capacidade e previsão · CORVO/RAVEN sinais · MURALHA/WALL limites de plataforma · DOMÍNIOS/DOMAINS datacenters · ARQUIVO/ARCHIVE runbooks · MEISTRE/MAESTER assistente · TESOURO/TREASURY orçamento · CAMPANHAS/CAMPAIGNS planos de ação

## CONTENT FUNDAMENTALS
- PT-BR padrão, EN como opção; **direto, técnico, calmo, orientado a ação; sem alarmismo, sem linguagem medieval/cinematográfica**. Referência geek é conceitual, nunca ilustrada.
- Frases declarativas com número + prazo + confiança: "NSX T1 pode atingir o limite operacional em 38 dias." · "Esta previsão utiliza 12 meses de histórico e possui 84% de confiança." · "A coleta está desatualizada. O último dado válido foi recebido há 6 horas."
- NUNCA: "O reino está em perigo", "A Muralha está prestes a cair", "Envie um corvo".
- Voz institucional impessoal; usuário tratado por "você" implícito (imperativos: "Abrir plano de ação"). Sem emoji (exceto ✦ do Meistre como glifo próprio). Caps só em rótulos-caption (tracking .14em). Datas "27 jul 2026"; números com vírgula decimal em PT; unidades sempre visíveis (d, Gbps, R$).
- Todo alerta traz origem + idade + confiança + próximo passo; ausência de dado é comunicada explicitamente ("sem coleta há 26 h"), nunca omitida.

## VISUAL FOUNDATIONS
- **Cores:** petróleo #002233 (marca) → #0F5E8C (ação); âmbar #B4690E só para limites/proximidade; 10 estados semânticos com glifo+cor+texto (ℹ●◆▲▲▲?⊘◌◐≠); capacidade (consumida/reservada/projetada/limites) e qualidade do dado (OBS/CALC/EST/MAN) têm tokens próprios. Vermelho/amarelo/verde nunca sozinhos.
- **Tipo:** TOTVS Bold 700 títulos; Archivo interface (expandida 124% para números-héroi); JetBrains Mono para todo dado técnico com 'tnum'. Corpo 13,5px; tabelas 12,5/12px.
- **Superfícies:** flat, sem gradientes (única exceção: painel escuro do login, gradiente 160° #041C2B→#0A2438); cards = superfície branca + hairline 1px + raio 6, **sem sombra**; sombra só em overlay (modal, toast, paleta). Dark mode recalibrado (#0F141B página, #141C27 superfície), não invertido.
- **Espaçamento:** base 4px; layout 5a: sidebar 228 + conteúdo + rail 316; página 24px; linhas 44/36px.
- **Interação:** hover = tint (selection #E6EEF4) ou darken da ação; press = darken adicional; sem shrink/bounce. Foco 2px petróleo offset 2 sempre visível. Seleção = fundo selection + trilho interno 2px petróleo à esquerda. Movimento 120/200ms cubic-bezier(.2,.6,.2,1), respeita reduced-motion; sem animação decorativa.
- **Gráficos:** linha sólida = observado; tracejada = projetado; cone translúcido = incerteza (P10–P90); linha do agora vertical tinta; limite op âmbar tracejado; limite téc tinta sólida; losango = evento futuro. Todo gráfico com alternativa textual (`ariaText`).
- **Bordas com significado:** sólida = dado ok; dashed = desatualizado/desconhecido/divergente; dotted = sem coleta.

## ICONOGRAPHY
- **Glifos de estado próprios** (unicode, do sistema): ℹ ● ◆ ▲ ▲▲ ? ⊘ ◌ ◐ ≠ + ✦ (Meistre) — são a iconografia primária em tabelas e badges.
- Ícones de interface: **Lucide via CDN** (`unpkg.com/lucide`), traço 1,75px, metáforas de trajetória/tempo — **substituição temporária sinalizada**; conjunto próprio é backlog. Sem emoji, sem ícones desenhados à mão.
- Logos TOTVS oficiais em `assets/logos/` (SVG azul-escuro/branco/preto + BUs); fonte TOTVS Bold em `assets/fonts/`; paleta oficial em `assets/cores/totvscolors.css`. Logo CITADEL não existe — wordmark tipográfico apenas; nunca desenhar símbolo sem aprovação.

## Uso no app (`citadelp/frontend`)
O frontend importa o DS **direto desta pasta** (alias `@ds` no `vite.config.js`); não existe cópia em `frontend/src/`.

```js
import "@ds/styles.css";                       // tokens — uma vez, em main.jsx
import { Button, StatusBadge } from "@ds";     // componentes — sempre pelo index.js
import logo from "@ds/assets/logos/logo-totvs-branco.svg";
```

- **Nunca** importar de `@ds/components/...` (regra do `_adherence.oxlintrc.json`); `index.js` é o único ponto de entrada.
- O que o DS ainda não tem (banner de alerta, filtro liga/desliga, área de texto, "sem coleta", layout do login 4b e do shell 5a) vive em `frontend/src/ui.jsx` + `app.css`, **só com tokens** — candidato a subir para cá quando estabilizar.
- Marca: só wordmark tipográfico em `--font-brand` (TOTVS Bold). O glifo de castelo do protótipo anterior foi removido; o favicon é um "C" tipográfico sobre petróleo.
- `_ds_bundle.js` e `support.js` são **gerados** pela ferramenta de design e servem só aos specimens HTML (`guidelines/cards/`, `components/*.card.html`, `ui_kits/citadel/index.html`, abertos direto do disco). O app não os usa. Ao alterar um componente em `components/`, o specimen fica defasado até regenerar o bundle.
- Não veio do repo original: `uploads/` (57 MB — planilhas de indicadores com dados reais, template PPT, PNGs) e o `.thumbnail` binário. Os dados de domínio extraídos dessas planilhas estão resumidos em `guidelines/dados-dominio.md`.

## Índice
- `index.js` — barrel dos 12 componentes (ponto único de importação do app)
- `styles.css` → `tokens/` (fonts, colors, typography, spacing, effects)
- `guidelines/cards/` — 15 specimens (Colors ×7, Type ×3, Spacing ×3, Brand ×2)
- `components/core/` — Button, TextField, Select, Tabs, StatusBadge, DataTable, Toast, Modal
- `components/dominio/` — RunwayBar, ProvenanceChip(+Panel), DomainTile, TrajectoryChart
- `ui_kits/citadel/` — Login → Três Olhos interativo, PT/EN (`index.html`)
- `Exploracao Visual Cidadela.html` — canvas com toda a exploração (direções A/B/C, logins, layouts)
- `guidelines/marca-totvs.md` · `guidelines/dados-dominio.md` — notas de marca e domínio
- `SKILL.md` — uso como Agent Skill

### Adições intencionais
Componentes autorais (nenhum inventário de origem existia): set mínimo core + 4 de domínio derivados dos estudos do brief (Capacity Runway, Data Provenance, Domain Selector, trajetória). Backlog: Muralha/Tesouro/Entrada global, command palette, tabela hierárquica, painel lateral, filtros salvos.

## Fontes fornecidas
- github.com/maxferreira01/citadel — vazio na leitura (21/07/2026); reservado à implementação. Org totvs-cloud (nsx_collector, fortigate-fisico…) confirma o stack de coletores — explore para aprofundar.
- Template PPT TOTVS (111 págs., Verdana = regra de slides, não de produto), planilhas de indicadores (TESP02–07, edges V41), logos/fonte/cores extraídos de totvs.com.br.
- Identidade do template intencionalmente não copiada (instrução do brief).
