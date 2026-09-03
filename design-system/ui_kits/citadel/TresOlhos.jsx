// CITADEL — Três Olhos (layout aprovado 5a: sidebar + painel + rail); primeiro item do módulo = alerta ativo
const { Button, Tabs, StatusBadge, RunwayBar, ProvenanceChip, ProvenancePanel, TrajectoryChart } = window.CIDADELADesignSystem_99bf85;

const RES = [
  { id: 'nsxt1', pt: 'NSX T1 · Cluster_1', en: 'NSX T1 · Cluster_1', usage: 184, op: 190, tech: 200, days: { pt: '▲ 38 dias', en: '▲ 38 days' }, conf: '84%', state: 'crit' },
  { id: 'ipset', pt: 'NSX IP Set', en: 'NSX IP Set', usage: 8106, op: 9200, tech: 9600, days: { pt: '◆ 132 dias', en: '◆ 132 days' }, conf: '91%', state: 'warn' },
  { id: 'lsp', pt: 'Logical Switch Ports', en: 'Logical Switch Ports', usage: 20626, op: 24500, tech: 26000, days: { pt: '◆ 156 dias', en: '◆ 156 days' }, conf: '88%', state: 'warn' },
  { id: 'nat', pt: 'NSX NAT Rules', en: 'NSX NAT Rules', usage: 17097, op: 25000, tech: 26500, days: { pt: '● 310 dias', en: '● 310 days' }, conf: '79%', state: 'ok' },
  { id: 'fw', pt: 'FW físico — memória', en: 'Physical FW — memory', usage: 69.5, op: 85, tech: 100, days: { pt: '◐ instável', en: '◐ unstable' }, conf: '—', state: 'stale' },
  { id: 'aci', pt: 'ACI — MAC_PER-IP', en: 'ACI — MAC_PER-IP', usage: 0, op: 0, tech: 100, days: { pt: '◌ sem coleta 26 h', en: '◌ no data 26 h' }, conf: '—', state: 'nocollect', nocollect: true },
];

function Sidebar({ lang, setLang, onLogout, t }) {
  const mods = window.CitadelI18n.modules;
  return (
    <div style={{ background: 'var(--surface)', borderRight: '1px solid var(--hairline)', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid var(--hairline)' }}>
        <img src="../../assets/logos/logo-totvs-azul-escuro.svg" alt="TOTVS" style={{ height: 12, display: 'block', opacity: .85 }} />
        <div style={{ font: '700 19px var(--font-brand)', letterSpacing: '.03em', color: 'var(--petrol-900)', marginTop: 9 }}>CITADEL</div>
      </div>
      <div style={{ padding: '12px 12px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, border: '1px solid var(--hairline)', borderRadius: 6, padding: '7px 10px', font: '400 11.5px var(--font-mono)', color: 'var(--text-muted)', background: 'var(--bg-page)' }}>
          {t('search')}<b style={{ marginLeft: 'auto', border: '1px solid var(--hairline)', borderRadius: 3, padding: '0 5px', fontSize: 10 }}>/</b>
        </div>
      </div>
      <div style={{ padding: '13px 16px 11px', borderBottom: '1px solid var(--hairline)' }}>
        <div style={{ font: '600 10px var(--font-ui)', letterSpacing: '.14em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{t('activeDomain')}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 7 }}>
          <span style={{ font: '700 14px var(--font-mono)', color: 'var(--petrol-900)' }}>TESP07</span>
          <StatusBadge state="crit" label="38 d" style={{ padding: '1px 6px', fontSize: 10 }} />
          <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>▾</span>
        </div>
      </div>
      <nav style={{ paddingTop: 8, flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {mods.map((m) => {
          const on = m.id === 'tresolhos';
          return (
            <div key={m.id} title={on ? undefined : t('underConstruction')} style={{ padding: '8px 16px', display: 'grid', gridTemplateColumns: '1fr auto', gap: '1px 8px', alignItems: 'baseline', background: on ? 'var(--selection)' : 'transparent', boxShadow: on ? 'inset 2px 0 var(--action)' : 'none', cursor: on ? 'default' : 'not-allowed', opacity: on ? 1 : .78 }}>
              <span style={{ font: `${on ? 600 : 500} 13px var(--font-ui)`, color: on ? 'var(--petrol-900)' : 'var(--ink)' }}>{lang === 'pt' ? m.pt : m.en}</span>
              <span style={{ font: '500 10.5px var(--font-mono)', color: m.hot ? 'var(--state-warn)' : m.count ? 'var(--text-muted)' : 'transparent' }}>{m.count || '·'}</span>
              <span style={{ fontSize: 10.5, color: 'var(--text-muted)', gridColumn: '1/2' }}>{lang === 'pt' ? m.dpt : m.den}</span>
            </div>
          );
        })}
      </nav>
      <div style={{ borderTop: '1px solid var(--hairline)', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--action)', fontWeight: 600 }}>✦ Meistre<span style={{ marginLeft: 'auto', font: '400 10.5px var(--font-mono)', color: 'var(--text-muted)', fontWeight: 400 }}>⌘J</span></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, borderTop: '1px solid var(--hairline)', paddingTop: 10 }}>
          <span style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--selection)', color: 'var(--petrol-900)', font: '600 10px var(--font-ui)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>MF</span>
          <span style={{ fontSize: 11.5, color: 'var(--ink)', lineHeight: 1.25 }}>m.ferreira<br /><a href="#" onClick={(e) => { e.preventDefault(); onLogout(); }} style={{ fontSize: 10.5 }}>{t('logout')}</a></span>
          <span style={{ marginLeft: 'auto' }}><window.LangToggle lang={lang} onChange={setLang} /></span>
        </div>
      </div>
    </div>
  );
}

function CitadelTresOlhos({ lang, setLang, onLogout }) {
  const t = window.CitadelI18n.t(lang);
  const [view, setView] = React.useState('alert');
  const [selRes, setSelRes] = React.useState('nsxt1');
  const cap = { font: '600 10.5px var(--font-ui)', letterSpacing: '.14em', textTransform: 'uppercase', color: 'var(--text-muted)' };
  const views = [
    { id: 'alert', label: lang === 'pt' ? '▲ Alerta: NSX T1 — 38 d' : '▲ Alert: NSX T1 — 38 d' },
    { id: 'overview', label: t('overview') },
    { id: 'fleet', label: t('fleetCompare') },
  ];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'var(--sidebar-w) 1fr var(--rail-w)', height: '100%', minWidth: 1280, fontFamily: 'var(--font-ui)', background: 'var(--bg-page)' }}>
      <Sidebar lang={lang} setLang={setLang} onLogout={onLogout} t={t} />
      <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 24px', borderBottom: '1px solid var(--hairline)', background: 'var(--surface)' }}>
          <span style={{ font: '400 11px var(--font-mono)', color: 'var(--text-muted)' }}>{t('breadcrumb')}</span>
          <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ font: '500 11px var(--font-mono)', border: '1px solid var(--hairline)', borderRadius: 6, padding: '5px 10px', color: 'var(--petrol-900)', whiteSpace: 'nowrap' }}>{t('period')}</span>
            <span style={{ font: '500 11px var(--font-mono)', border: '1px solid var(--hairline)', borderRadius: 6, padding: '5px 10px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{t('production')} ▾</span>
            <Button variant="secondary" size="sm">{t('export')}</Button>
          </span>
        </div>
        <div style={{ padding: '16px 24px', display: 'flex', flexDirection: 'column', gap: 14, flex: 1, minHeight: 0 }}>
          <Tabs items={views} active={view} onChange={setView} />
          <div style={{ background: 'var(--state-crit-bg)', border: '1px solid var(--state-crit)', borderRadius: 'var(--radius-md)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--state-crit)', fontSize: 15 }}>▲</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--ink)' }}>{t('alertTitle')}</div>
              <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 2 }}>{t('alertMeta')}</div>
            </div>
            <ProvenanceChip method="OBS" source={lang === 'pt' ? 'coletor NSX' : 'NSX collector'} age={lang === 'pt' ? 'há 7 min' : '7 min ago'} confidence="84%" />
          </div>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--hairline)', borderRadius: 'var(--radius-md)', padding: '14px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
              <span style={{ font: '650 14px var(--font-ui)', fontStretch: '110%', color: 'var(--petrol-900)' }}>NSX Tier-1 Gateways · T0-Cluster_1</span>
              <span style={{ font: '700 14px var(--font-mono)', color: 'var(--cap-limit-op)' }}>{lang === 'pt' ? '38 dias · 84%' : '38 days · 84%'}</span>
            </div>
            <TrajectoryChart height={190} width={830}
              history={[152, 154, 158, 163, 168, 172, 176, 181, 184]} projection={[184, 190, 197, 205]}
              opLimit={190} techLimit={200} satIndex={9.05} satLabel={lang === 'pt' ? '28 ago' : 'Aug 28'} todayLabel={t('today')}
              xLabels={lang === 'pt' ? ['jan', 'mar', 'mai', 'jul', 'set', 'nov'] : ['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov']}
              events={[{ index: 9.6, label: lang === 'pt' ? 'expansão (set)' : 'expansion (Sep)' }]}
              ariaText={t('alertTitle')} />
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            <div style={{ ...cap, marginBottom: 8 }}>{t('runways')}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
              {RES.map((r) => (
                <div key={r.id} onClick={() => setSelRes(r.id)} style={{ cursor: 'pointer', padding: '4px 8px', margin: '0 -8px', borderRadius: 6, background: selRes === r.id ? 'var(--selection)' : 'transparent' }}>
                  <RunwayBar height={9} label={<span style={{ fontWeight: r.id === selRes ? 600 : 400 }}>{lang === 'pt' ? r.pt : r.en}</span>}
                    usage={r.usage} opLimit={r.op || undefined} techLimit={r.tech} nocollect={r.nocollect}
                    days={r.days[lang]} confidence={r.conf !== '—' ? r.conf : undefined} state={r.state} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div style={{ borderLeft: '1px solid var(--hairline)', background: 'var(--surface)', padding: '16px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 16, minHeight: 0 }}>
        <div>
          <div style={cap}>{t('scenarios')}</div>
          <div style={{ fontSize: 12.5, lineHeight: 1.55, marginTop: 10, paddingBottom: 11, borderBottom: '1px solid var(--hairline)' }}>
            <b style={{ font: '600 11px var(--font-mono)', color: 'var(--cap-limit-op)' }}>AGO</b> · {lang === 'pt' ? 'migração TESP02 → TESP07' : 'TESP02 → TESP07 migration'}<br />
            <span style={{ color: 'var(--text-muted)' }}>{lang === 'pt' ? 'antecipa a saturação para ' : 'moves saturation up to '}<b style={{ color: 'var(--cap-limit-op)' }}>{lang === 'pt' ? '19 ago' : 'Aug 19'}</b> (P90)</span>
          </div>
          <div style={{ fontSize: 12.5, lineHeight: 1.55, marginTop: 11, paddingBottom: 11, borderBottom: '1px solid var(--hairline)' }}>
            <b style={{ font: '600 11px var(--font-mono)', color: 'var(--state-ok)' }}>SET</b> · {lang === 'pt' ? 'expansão contratada' : 'contracted expansion'}<br />
            <span style={{ color: 'var(--text-muted)' }}>+50 T1 · <span style={{ fontFamily: 'var(--font-mono)' }}>R$ 387.000</span> · runway 300+ d</span>
          </div>
          <div style={{ fontSize: 12.5, lineHeight: 1.55, marginTop: 11 }}>
            <b style={{ font: '600 11px var(--font-mono)', color: 'var(--action)' }}>NOV</b> · {lang === 'pt' ? 'renovação Operadora A' : 'Carrier A renewal'}<br />
            <span style={{ color: 'var(--text-muted)' }}>SLA 99,95% · {lang === 'pt' ? 'cotação no Tesouro' : 'quote in Treasury'}</span>
          </div>
        </div>
        <ProvenancePanel title={t('provenance')} rows={[
          [t('origin'), lang === 'pt' ? 'coletor NSX · API' : 'NSX collector · API'],
          [t('lastCollect'), lang === 'pt' ? 'há 7 min' : '7 min ago'],
          [t('methodConf'), 'OBS · 84%'],
          [t('owner'), lang === 'pt' ? 'Eng. de Redes' : 'Network Eng.'],
        ]} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <Button block>{t('openPlan')}</Button>
          <Button variant="secondary" block>{t('compareDomains')}</Button>
        </div>
      </div>
    </div>
  );
}
window.CitadelTresOlhos = CitadelTresOlhos;
