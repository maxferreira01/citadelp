/* NSX T1 — OBS · nsx-collector → InfluxDB (read-model /nsx/t1/*). */
import { useEffect, useState } from "react";
import { api } from "../../api.js";

/* Premissas MAN de arquitetura (espelham backend/app/nsx/consultas.py). */
export const NSX_T1_OP_LIMIT = 2000; // 2.000 T1 por datacenter
export const T0_LIMIT = 600; // 600 por T0 (par de edges) = 200 direto + 2 × 200 em VRF
export const VRF_LIMIT = 200; // por VRF, e também para os T1 pendurados direto no T0
export const EDGE_PRODUTIVO = "TESP7";

export const stT1 = (pct) => (pct >= 100 ? "crit" : pct >= 90 ? "warn" : "ok");
export const stLabel = { crit: "no limite", warn: "atenção", ok: "folga" };
export const STATE_COLOR = { ok: "var(--state-ok)", warn: "var(--state-warn)", crit: "var(--state-crit)" };

/* Regressão linear sobre o histórico diário → projeção (CALC) em 3 passos de 30 d. */
export function projetar(hist, op) {
  const n = hist.length;
  if (n < 7) return { proj: hist.length ? [hist[n - 1]] : [], days: null, conf: "—" };
  const xs = hist.map((_, i) => i), mx = (n - 1) / 2, my = hist.reduce((a, b) => a + b, 0) / n;
  let sxy = 0, sxx = 0, sst = 0;
  xs.forEach((x, i) => { sxy += (x - mx) * (hist[i] - my); sxx += (x - mx) ** 2; sst += (hist[i] - my) ** 2; });
  const slope = sxx ? sxy / sxx : 0, last = hist[n - 1];
  const r2 = sst ? Math.max(0, Math.min(1, (slope * slope * sxx) / sst)) : 0;
  const proj = [last, ...[30, 60, 90].map((d) => Math.round(last + slope * d))];
  const days = slope > 0 && last < op ? Math.round((op - last) / slope) : null;
  return { proj, days, conf: `${Math.round(r2 * 100)}%` };
}

const q = (s) => encodeURIComponent(s);

/* Carrega o resumo de todos os sites e, para o site alvo, histórico 90 d, T0, VRF e eventos. */
export function useNsxT1(site) {
  const [sites, setSites] = useState([]);
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  useEffect(() => {
    let vivo = true;
    (async () => {
      setBusy(true); setErr("");
      try {
        const resumo = await api("/nsx/t1/resumo");
        if (!vivo) return;
        setSites(resumo);
        const alvo = resumo.find((r) => r.site === site) || resumo[0];
        if (!alvo) { setData(null); setBusy(false); return; }
        const [hist, t0, vrf, eventos] = await Promise.all([
          api(`/nsx/t1/historico?site=${q(alvo.site)}&dias=90`),
          api(`/nsx/t1/por-t0?site=${q(alvo.site)}`),
          api(`/nsx/t1/por-vrf?site=${q(alvo.site)}`),
          api(`/nsx/t1/eventos?site=${q(alvo.site)}&dias=90`),
        ]);
        if (!vivo) return;
        const pontos = hist.filter((h) => h.total != null);
        const serie = pontos.map((h) => h.total);
        const op = NSX_T1_OP_LIMIT;
        const usage = alvo.total ?? alvo.nsx_current ?? 0;
        const { proj, days, conf } = projetar(serie, op);
        const st = usage >= op ? "crit" : usage >= op * 0.85 ? "warn" : "ok";
        setData({ id: "nsxt1", name: `NSX T1 Gateways · ${alvo.site}`, site: alvo.site, usage, op, tech: null, days, conf, st, hist: serie, datas: pontos.map((h) => h.quando), eventos, proj, t0, vrf, resumo: alvo });
      } catch (e) { if (vivo) setErr(String(e.message || e)); }
      if (vivo) setBusy(false);
    })();
    return () => { vivo = false; };
  }, [site]);
  return { sites, data, busy, err };
}
