/* ARQUIVO — runbooks e fonte de verdade (EST · mock até a migração do wiki). */
import React from "react";
import { ProvenanceChip } from "@ds";
import { RUNBOOKS } from "../mock.js";
import { Cap, Card } from "../ui.jsx";

export default function Arquivo() {
  return (
    <Card mock flush>
      <div className="card-head"><Cap>runbooks e fonte de verdade</Cap><ProvenanceChip method="EST" source="mock — migração do wiki pendente" /></div>
      <div className="list" style={{ borderTop: "var(--border-hairline)" }}>
        {RUNBOOKS.map((r) => (
          <div key={r.t} className="sm" style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "11px 18px" }}>
            <a href="#" onClick={(e) => e.preventDefault()}>{r.t}</a>
            <span className="num faint" style={{ fontSize: 10.5 }}>{r.tags}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
