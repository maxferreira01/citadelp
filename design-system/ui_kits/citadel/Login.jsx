// CITADEL — tela de login (base aprovada: 4b, destaques agregados — sem nomes de recurso nem valores)
// theme: 'dark' (padrão, painel NOC) | 'light'
const { Button, TextField } = window.CIDADELADesignSystem_99bf85;
const { TrajectoryChart } = window.CIDADELADesignSystem_99bf85;

function LangToggle({ lang, onChange, dark }) {
  const opt = (l) => ({
    background: lang === l ? (dark ? 'rgba(255,255,255,.14)' : 'var(--selection)') : 'transparent',
    color: dark ? '#E7ECF3' : 'var(--ink)', border: 'none', cursor: 'pointer',
    font: '600 10.5px var(--font-mono)', letterSpacing: '.08em', padding: '3px 8px', borderRadius: 4,
  });
  return (
    <span role="group" aria-label="idioma / language" style={{ display: 'inline-flex', gap: 2, border: `1px solid ${dark ? '#2C4A63' : 'var(--hairline)'}`, borderRadius: 6, padding: 2 }}>
      <button style={opt('pt')} onClick={() => onChange('pt')}>PT</button>
      <button style={opt('en')} onClick={() => onChange('en')}>EN</button>
    </span>
  );
}
window.LangToggle = LangToggle;

function ThemeToggle({ theme, onChange }) {
  return (
    <button onClick={() => onChange(theme === 'dark' ? 'light' : 'dark')} aria-label="tema claro/escuro"
      title={theme === 'dark' ? 'tema claro' : 'tema escuro'}
      style={{ border: '1px solid var(--hairline)', background: 'transparent', color: 'var(--ink)', borderRadius: 6, padding: '3px 9px', cursor: 'pointer', font: '600 11px var(--font-mono)' }}>
      {theme === 'dark' ? '☀' : '☾'}
    </button>
  );
}
window.ThemeToggle = ThemeToggle;

function CitadelLogin({ lang, setLang, onEnter, theme = 'dark', setTheme }) {
  const t = window.CitadelI18n.t(lang);
  const quote = window.CitadelI18n.quotes[new Date().getDate() % window.CitadelI18n.quotes.length];
  const dark = theme === 'dark';
  // paleta do painel esquerdo — dark NOC vs light análise
  const P = dark ? {
    bg: 'linear-gradient(160deg,#041C2B 0%,#0A2438 100%)', ink: '#E7ECF3', sub: '#9FB2C4', cap: '#8299B0',
    mut: '#7A8FA3', hair: '#1D3448', amber: '#F0B45F', ok: '#8FD0A9', cyan: '#7FC7E8', gold: '#D9B36C',
    logo: '../../assets/logos/logo-totvs-branco.svg',
  } : {
    bg: 'linear-gradient(160deg,#E9EEF3 0%,#F4F6F9 100%)', ink: 'var(--ink)', sub: 'var(--text-muted)', cap: 'var(--text-muted)',
    mut: 'var(--text-faint)', hair: 'var(--hairline)', amber: 'var(--cap-limit-op)', ok: 'var(--state-ok)', cyan: 'var(--action)', gold: 'var(--state-stale)',
    logo: '../../assets/logos/logo-totvs-azul-escuro.svg',
  };
  const cap = { font: '600 10.5px var(--font-ui)', letterSpacing: '.14em', textTransform: 'uppercase', color: P.cap };
  const stat = (n, color, txt) => (
    <div style={{ flex: 1, padding: '0 16px', borderLeft: `1px solid ${P.hair}` }}>
      <div style={{ font: '700 21px var(--font-ui)', fontStretch: '114%', color }}>{n}</div>
      <div style={{ fontSize: 11.5, color: P.sub, lineHeight: 1.4, marginTop: 3 }}>{txt}</div>
    </div>
  );
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 556px', height: '100%', fontFamily: 'var(--font-ui)' }}>
      <div style={{ background: P.bg, color: P.ink, padding: '38px 46px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 18, minWidth: 0 }}>
        <div>
          <img src={P.logo} alt="TOTVS" style={{ height: 15, display: 'block', opacity: .9 }} />
          <div style={{ font: '700 40px/1 var(--font-brand)', letterSpacing: '.02em', marginTop: 24, color: dark ? P.ink : 'var(--petrol-900)' }}>CITADEL</div>
          <div style={{ font: '400 13.5px/1.5 var(--font-ui)', color: P.sub, marginTop: 9 }}>{t('tagline')}</div>
        </div>
        <div>
          <div style={cap}>{t('nearestRisk')} · 27 jul 2026</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginTop: 10 }}>
            <span style={{ font: '700 84px/.9 var(--font-ui)', fontStretch: '124%', color: P.amber }}>38</span>
            <div>
              <div style={{ font: '700 21px var(--font-ui)', fontStretch: '112%', color: P.amber }}>{t('days')}</div>
              <div style={{ fontSize: 13.5, lineHeight: 1.5, color: P.ink, marginTop: 4, whiteSpace: 'pre-line' }}>{t('heroDetail')}</div>
            </div>
          </div>
          <div style={{ marginTop: 14 }}>
            <TrajectoryChart dark={dark} height={150} width={780}
              history={[152, 154, 158, 163, 168, 172, 176, 181, 184]} projection={[184, 190, 197, 205]}
              opLimit={190} techLimit={200} satIndex={9.05} satLabel={lang === 'pt' ? '28 ago · 84%' : 'Aug 28 · 84%'}
              todayLabel={t('today')} xLabels={lang === 'pt' ? ['jan', 'abr', 'jul', 'set', 'dez'] : ['Jan', 'Apr', 'Jul', 'Sep', 'Dec']}
              ariaText={t('alertTitle')} />
          </div>
        </div>
        <div>
          <div style={cap}>{t('whatChanges')}</div>
          <div style={{ display: 'grid', gridTemplateColumns: '52px 1fr', gap: '8px 12px', fontSize: 12.5, marginTop: 10, lineHeight: 1.45 }}>
            <span style={{ font: '600 11px var(--font-mono)', color: P.amber }}>AGO</span><span>{t('ev1')}</span>
            <span style={{ font: '600 11px var(--font-mono)', color: P.ok }}>SET</span><span>{t('ev2')}</span>
            <span style={{ font: '600 11px var(--font-mono)', color: P.cyan }}>NOV</span><span>{t('ev3')}</span>
          </div>
        </div>
        <div style={{ display: 'flex', borderTop: `1px solid ${P.hair}`, borderBottom: `1px solid ${P.hair}`, padding: '14px 0' }}>
          <div style={{ flex: 1, paddingRight: 16 }}>
            <div style={{ font: '700 21px var(--font-ui)', fontStretch: '114%', color: P.ink }}>3</div>
            <div style={{ fontSize: 11.5, color: P.sub, lineHeight: 1.4, marginTop: 3 }}>{t('st1')}</div>
          </div>
          {stat('2', P.gold, t('st2'))}
          {stat('3', P.cyan, t('st3'))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={cap}>{t('provFooter')}</span>
          <span style={{ font: '400 10.5px var(--font-mono)', color: P.mut }}>{t('coneNote')}</span>
        </div>
      </div>
      <div style={{ background: 'var(--surface)', borderLeft: dark ? 'none' : '1px solid var(--hairline)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '34px 52px', gap: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ font: '650 15px var(--font-ui)', fontStretch: '110%', color: 'var(--ink)' }}>{t('welcome')}</span>
          <span style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
            <span style={{ font: '400 10.5px var(--font-mono)', color: 'var(--text-muted)' }}>{t('internal')}</span>
            <LangToggle lang={lang} onChange={setLang} />
            {setTheme && <ThemeToggle theme={theme} onChange={setTheme} />}
          </span>
        </div>
        <div style={{ borderTop: '1px solid var(--hairline)', borderBottom: '1px solid var(--hairline)', padding: '15px 0' }}>
          <div style={{ font: '600 10.5px var(--font-ui)', letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{t('noteOfDay')}</div>
          <p style={{ font: '400 16px/1.5 var(--font-ui)', color: 'var(--petrol-900)', margin: '9px 0 0' }}>“{quote.q}”</p>
          <div style={{ font: '400 10.5px var(--font-mono)', color: 'var(--text-muted)', marginTop: 8 }}>{quote.who}</div>
        </div>
        <div>
          <div style={{ font: '700 23px var(--font-brand)', color: 'var(--petrol-900)' }}>{t('signIn')}</div>
          <p style={{ fontSize: 12.5, color: 'var(--text-muted)', margin: '5px 0 0' }}>{t('restricted')}</p>
          <Button block style={{ marginTop: 18, padding: '11px 12px', fontSize: 13.5 }} onClick={onEnter}>{t('sso')}</Button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '16px 0', color: 'var(--text-muted)', fontSize: 11 }}>
            <span style={{ flex: 1, height: 1, background: 'var(--hairline)' }}></span>{t('or')}<span style={{ flex: 1, height: 1, background: 'var(--hairline)' }}></span>
          </div>
          <TextField label={t('user')} value="m.ferreira" mono />
          <div style={{ marginTop: 13 }}><TextField label={t('pass')} value="••••••••••" type="password" mono hint="" /></div>
          <Button variant="secondary" block style={{ marginTop: 16, padding: '11px 12px', fontSize: 13.5 }} onClick={onEnter}>{t('signIn')}</Button>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 14, fontSize: 12 }}>
            <a href="#" onClick={(e) => e.preventDefault()}>{t('requestAccess')}</a>
            <a href="#" onClick={(e) => e.preventDefault()}>{t('collectorStatus')}</a>
          </div>
        </div>
        <div>
          <div style={{ font: '600 10.5px var(--font-ui)', letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{t('platformStatus')}</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '7px 12px', fontSize: 12, marginTop: 9 }}>
            <span style={{ color: 'var(--text-muted)' }}>{t('respondingCollectors')}</span><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>46 / 48</span>
            <span style={{ color: 'var(--text-muted)' }}>{t('cmdbSync')}</span><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>{lang === 'pt' ? 'há 9 min' : '9 min ago'}</span>
            <span style={{ color: 'var(--text-muted)' }}>{t('ipamSync')}</span><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>{lang === 'pt' ? 'há 12 min' : '12 min ago'}</span>
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--hairline)', paddingTop: 13 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t('internalUse')}</span>
          <span style={{ font: '400 10.5px var(--font-mono)', color: 'var(--text-muted)' }}>CITADEL v0.1</span>
        </div>
      </div>
    </div>
  );
}
window.CitadelLogin = CitadelLogin;
