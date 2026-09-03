/* LOGIN — tela 4b (aprovada 27/07/2026)
   Painel escuro: métrica herói AGREGADA (sem nome de recurso nem R$) + trajetória.
   Painel claro: nota do dia (citação, sem comentário), SSO TOTVS, Google, formulário. */
import React, { useEffect, useRef, useState } from "react";
import { Button, TextField, TrajectoryChart } from "@ds";
import { api } from "../api.js";
import { useT, useLang, quoteOfDay } from "../i18n.jsx";
import { CAPACITY } from "../mock.js";
import { saturation } from "../capacity.js";
import { Cap, Wordmark, TotvsLogo, LangToggle, ThemeToggle, Metric } from "../ui.jsx";

/* ====================== LOGIN GOOGLE (GIS + backend) ====================== */
function GoogleSignIn({ onUser }) {
  const t = useT();
  const ref = useRef(null);
  const [state, setState] = useState("carregando");
  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const cfg = await api("/auth/config");
        if (dead) return;
        if (!cfg.google) { setState("ausente"); return; }
        const s = document.createElement("script");
        s.src = "https://accounts.google.com/gsi/client";
        s.async = true;
        s.onload = () => {
          if (dead || !window.google) return;
          window.google.accounts.id.initialize({
            client_id: cfg.google_client_id,
            callback: async (resp) => {
              try {
                const out = await api("/auth/google", { method: "POST", body: JSON.stringify({ credential: resp.credential }) });
                sessionStorage.setItem("citadel_token", out.token);
                onUser(out.user);
              } catch { setState("erro"); }
            },
          });
          window.google.accounts.id.renderButton(ref.current, { theme: "outline", size: "large", width: 380 });
          setState("pronto");
        };
        s.onerror = () => !dead && setState("erro");
        document.head.appendChild(s);
      } catch { !dead && setState("ausente"); }
    })();
    return () => { dead = true; };
  }, []);
  return (
    <div style={{ marginTop: 14 }}>
      <div ref={ref} style={{ display: state === "pronto" ? "flex" : "none", justifyContent: "center" }} />
      {state === "ausente" && (
        <div className="xs muted" style={{ textAlign: "center", border: "1px dashed var(--hairline)", borderRadius: "var(--radius-md)", padding: "9px 10px" }}>
          {t("Login Google indisponível — defina")} <span className="num">GOOGLE_CLIENT_ID</span> {t("no .env do backend.")}
        </div>
      )}
      {state === "erro" && (
        <div className="xs" role="alert" style={{ color: "var(--state-crit)", textAlign: "center", padding: "6px 0" }}>▲ {t("Falha no login Google. Tente novamente.")}</div>
      )}
    </div>
  );
}

const STATS = [
  [3, "var(--p-ink)", "recursos saturam em menos de 90 dias"],
  [2, "var(--p-gold)", "coletores sem coleta há mais de 24 h"],
  [55, "var(--p-cyan)", "sinais de float IP analisados no trimestre"],
];

export default function Login({ onEnter, theme, setTheme }) {
  const t = useT();
  const [lang] = useLang();
  const [user, setUser] = useState("m.ferreira");
  const [pass, setPass] = useState("");
  const quote = quoteOfDay(lang);
  const risk = CAPACITY[0]; // EST · mock — risco mais próximo (agregado no painel)
  return (
    <div className="login">
      <div className="login-panel">
        <div>
          <div className="row" style={{ gap: 10 }}>
            <TotvsLogo white height={15} style={{ opacity: .9 }} />
            <span className="num" style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: ".2em", color: "var(--p-cap)" }}>CLOUD</span>
          </div>
          <Wordmark size={40} style={{ display: "block", marginTop: 24 }} />
          <div style={{ color: "var(--p-sub)", marginTop: 9 }}>{t("Veja o limite antes de alcançá-lo.")}</div>
        </div>
        <div>
          <Cap>{t("risco mais próximo")} · 27 jul 2026</Cap>
          <div className="metric-row" style={{ gap: 16 }}>
            <Metric size={84} color="var(--p-amber)">{risk.days}</Metric>
            <div>
              <div style={{ font: "700 21px var(--font-ui)", fontStretch: "112%", color: "var(--p-amber)" }}>{t("dias")}</div>
              <div style={{ marginTop: 4, lineHeight: 1.5, whiteSpace: "pre-line" }}>{t("até o limite operacional mais próximo\nem um domínio de produção")}</div>
            </div>
          </div>
          <div style={{ marginTop: 14, maxWidth: 780 }}>
            <TrajectoryChart dark width={780} height={150} history={risk.hist} projection={risk.proj} opLimit={risk.op} techLimit={risk.tech}
              {...saturation(risk)} satLabel={`+${risk.days} d · ${risk.conf}`} todayLabel={t("hoje")}
              ariaText={`${t("risco mais próximo")}: ${risk.days} ${t("dias")} · ${risk.conf}`} />
          </div>
        </div>
        <div className="login-stats">
          {STATS.map(([n, c, txt]) => (
            <div key={txt}>
              <div className="hero num" style={{ fontSize: 21, fontStretch: "114%", color: c }}>{n}</div>
              <div className="xs" style={{ color: "var(--p-sub)", lineHeight: 1.4, marginTop: 3 }}>{t(txt)}</div>
            </div>
          ))}
        </div>
        <div className="num" style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 10.5, color: "var(--p-mut)" }}>
          <span>{t("coleta contínua · 46 de 48 coletores respondendo")}</span>
          <span>{t("projeção 12 m · cone P10–P90")}</span>
        </div>
      </div>

      <div className="login-form">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span style={{ font: "650 15px var(--font-ui)", fontStretch: "110%" }}>{t("Bem-vindo de volta")}</span>
          <span className="row">
            <span className="num muted" style={{ fontSize: 10.5 }}>{t("plataforma interna · TOTVS Cloud")}</span>
            <LangToggle />
            <ThemeToggle theme={theme} onChange={setTheme} />
          </span>
        </div>
        <div style={{ borderTop: "var(--border-hairline)", borderBottom: "var(--border-hairline)", padding: "15px 0" }}>
          <Cap>{t("nota do dia")}</Cap>
          <p style={{ font: "400 16px/1.5 var(--font-ui)", color: "var(--brand)", marginTop: 9 }}>“{quote.text}”</p>
          <div className="num muted" style={{ fontSize: 10.5, marginTop: 8 }}>{quote.who}</div>
        </div>
        <div>
          <h1 className="title" style={{ fontSize: 23 }}>{t("Entrar")}</h1>
          <p className="sm muted" style={{ marginTop: 5 }}>{t("Acesso restrito às equipes de infraestrutura, operações e gestão.")}</p>
          <Button block size="lg" style={{ marginTop: 18 }} onClick={onEnter}>{t("Continuar com SSO TOTVS")}</Button>
          <GoogleSignIn onUser={() => onEnter()} />
          <div className="hr" style={{ margin: "16px 0" }}>{t("ou")}</div>
          <TextField label={t("Usuário corporativo")} value={user} mono onChange={setUser} />
          <TextField label={t("Senha")} value={pass} type="password" mono onChange={setPass} style={{ marginTop: 13 }} />
          <Button variant="secondary" block size="lg" style={{ marginTop: 16 }} onClick={onEnter}>{t("Entrar")}</Button>
        </div>
        <div>
          <Cap>{t("status da plataforma")}</Cap>
          <div className="kv" style={{ marginTop: 9 }}>
            <span>{t("coletores respondendo")}</span><span>46 / 48</span>
            <span>{t("varredura Corvo (Slack)")}</span><span>27 jul 20:40</span>
            <span>{t("sincronização CMDB")}</span><span>{t("há 9 min")}</span>
          </div>
        </div>
        <div className="row" style={{ justifyContent: "space-between", borderTop: "var(--border-hairline)", paddingTop: 13 }}>
          <span className="xs muted">{t("Uso interno · dados classificados")}</span>
          <span className="num muted" style={{ fontSize: 10.5 }}>CITADEL v0.1 · protótipo</span>
        </div>
      </div>
    </div>
  );
}
