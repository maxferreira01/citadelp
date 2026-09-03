/* ============================================================================
   CITADEL v0.1 — plataforma completa (protótipo navegável)
   ----------------------------------------------------------------------------
   Login (tela 4b) → shell (layout 5a: sidebar 228 + painel + rail 316)
   Módulos: Conselho · Três Olhos · Corvo · Vigia · Muralha · Domínios ·
            Arquivo · Tesouro · Campanhas — e Meistre ✦ (assistente via API).

   Design system: ../design-system (alias @ds) — tokens em @ds/styles.css,
   componentes em @ds (index.js). Composições do app em ./ui.jsx.
   Procedência dos dados: ver ./mock.js.
   ========================================================================== */
import React, { useState } from "react";
import { LangCtx } from "./i18n.jsx";
import Login from "./screens/Login.jsx";
import Shell from "./screens/Shell.jsx";

const read = (k, d) => { try { return localStorage.getItem(k) || d; } catch { return d; } };
const store = (k, v) => { try { localStorage.setItem(k, v); } catch { /* storage indisponível */ } };

export default function CitadelApp() {
  const [authed, setAuthed] = useState(false);
  const [theme, setThemeState] = useState(() => read("citadel_theme", "light")); // light = análise · dark = NOC
  const [lang, setLangState] = useState(() => read("citadel_lang", "pt"));
  const setTheme = (t) => { store("citadel_theme", t); setThemeState(t); };
  const setLang = (l) => { store("citadel_lang", l); setLangState(l); };
  return (
    <LangCtx.Provider value={[lang, setLang]}>
      <div className="app" data-theme={theme}>
        {authed
          ? <Shell theme={theme} setTheme={setTheme} onLogout={() => setAuthed(false)} />
          : <Login onEnter={() => setAuthed(true)} theme={theme} setTheme={setTheme} />}
      </div>
    </LangCtx.Provider>
  );
}
