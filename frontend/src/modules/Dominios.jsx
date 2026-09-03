/* DOMÍNIOS — estado por edge (DomainTile: glifo + cor + texto; pontilhado = sem coleta). */
import React from "react";
import { DomainTile, ProvenanceChip, STATUS_STATES } from "@ds";
import { useLang } from "../i18n.jsx";
import { DOMAINS } from "../mock.js";

export default function Dominios() {
  const [lang] = useLang();
  return (
    <div className="tiles">
      {DOMAINS.map((d) => (
        <div key={d.e} style={{ display: "grid", gridTemplateRows: "1fr auto", gap: 8 }}>
          <DomainTile code={d.e} state={d.st} env={STATUS_STATES[d.st][lang]} note={`${d.city} — ${d.note}`} />
          <ProvenanceChip method={d.obs ? "OBS" : "EST"} source={d.obs ? "Corvo" : "mock"} />
        </div>
      ))}
    </div>
  );
}
