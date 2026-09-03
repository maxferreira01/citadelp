/* SHELL — layout 5a (aprovado): sidebar 228 + painel + rail 316.
   Sidebar: endosso TOTVS + wordmark, módulos (nome + descritor), Meistre, usuário.
   Rail: procedência do módulo (ProvenancePanel) + ações. */
import React, { useEffect, useState } from "react";
import { Button, ProvenancePanel } from "@ds";
import { useT } from "../i18n.jsx";
import { MODULES, TITLES, RAIL } from "../mock.js";
import { Cap, Wordmark, TotvsLogo, LangToggle, ThemeToggle } from "../ui.jsx";
import Conselho from "../modules/Conselho.jsx";
import TresOlhos from "../modules/TresOlhos.jsx";
import Corvo from "../modules/Corvo.jsx";
import Vigia from "../modules/Vigia.jsx";
import Muralha from "../modules/Muralha.jsx";
import Dominios from "../modules/Dominios.jsx";
import Arquivo from "../modules/Arquivo.jsx";
import Tesouro from "../modules/Tesouro.jsx";
import Campanhas from "../modules/Campanhas.jsx";
import Meistre from "../modules/Meistre.jsx";

const BODY = { conselho: Conselho, tresolhos: TresOlhos, corvo: Corvo, vigia: Vigia, muralha: Muralha, dominios: Dominios, arquivo: Arquivo, tesouro: Tesouro, campanhas: Campanhas, meistre: Meistre };

export default function Shell({ theme, setTheme, onLogout }) {
  const [mod, setMod] = useState("corvo");
  const [railOn, setRailOn] = useState(true);
  const t = useT();
  const [title, sub] = TITLES[mod];
  const rail = RAIL[mod];
  const Body = BODY[mod];

  useEffect(() => { // ⌘J / Ctrl+J → Meistre
    const h = (e) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "j") { e.preventDefault(); setMod("meistre"); } };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  return (
    <div className={"shell" + (railOn ? "" : " norail")}>
      <aside className="sidebar">
        <div className="sidebar-head">
          <div className="row" style={{ gap: 8 }}>
            <TotvsLogo white={theme === "dark"} height={12} style={{ opacity: .85 }} />
            <span className="num muted" style={{ fontSize: 9.5, fontWeight: 600, letterSpacing: ".2em" }}>CLOUD</span>
          </div>
          <Wordmark size={19} style={{ display: "block", marginTop: 9 }} />
        </div>
        <nav aria-label={t("módulos")}>
          {MODULES.map((m) => (
            <button key={m.id} type="button" className="nav-item" aria-current={m.id === mod ? "page" : undefined} onClick={() => setMod(m.id)}>
              <span>{t(m.n)}</span>
              <span className={"count" + (m.hot ? " hot" : "")}>{m.count ?? ""}</span>
              <small>{t(m.d)}</small>
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <button type="button" className="nav-item meistre" aria-current={mod === "meistre" ? "page" : undefined} onClick={() => setMod("meistre")}>
            <span>✦ Meistre</span><span className="count">⌘J</span>
          </button>
          <div className="row" style={{ borderTop: "var(--border-hairline)", paddingTop: 10, flexWrap: "nowrap" }}>
            <span className="avatar">MF</span>
            <span className="xs" style={{ lineHeight: 1.3 }}>
              m.ferreira<br />
              <a href="#" onClick={(e) => { e.preventDefault(); onLogout(); }} style={{ fontSize: "var(--text-caption)" }}>{t("Sair")}</a>
            </span>
            <span className="row" style={{ marginLeft: "auto", flexWrap: "nowrap", gap: 6 }}>
              <LangToggle />
              <ThemeToggle theme={theme} onChange={setTheme} />
            </span>
          </div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1 className="title">{t(title)}</h1>
            <div className="xs muted" style={{ marginTop: 2 }}>{t(sub)}</div>
          </div>
          <button type="button" className="iconbtn" aria-pressed={railOn} onClick={() => setRailOn((v) => !v)}
            title={railOn ? t("ocultar painel lateral") : t("mostrar painel lateral")} style={{ fontSize: 12 }}>◧</button>
        </header>
        <div className="content"><Body go={setMod} /></div>
      </div>

      <aside className="rail">
        <ProvenancePanel title={t("procedência")} rows={rail.prov} />
        {rail.acts.length > 0 && (
          <div>
            <Cap>{t("ações")}</Cap>
            <div className="stack" style={{ gap: 8, marginTop: 9 }}>
              {rail.acts.map((a, i) => <Button key={a} block variant={i ? "secondary" : "primary"}>{a}</Button>)}
            </div>
          </div>
        )}
        <div className="num faint" style={{ marginTop: "auto", fontSize: "var(--text-caption)", lineHeight: 1.6 }}>
          {t("borda tracejada âmbar = dado simulado (EST · mock)")}<br />{t("sólida = observado · pontilhada = sem coleta")}
        </div>
      </aside>
    </div>
  );
}
