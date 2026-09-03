/* CAMPANHAS — planos de ação: todo sinal leva a uma ação (cards OBS do canal, EST mock). */
import React from "react";
import { ProvenanceChip } from "@ds";
import { CAMPAIGNS } from "../mock.js";
import { Cap, Card } from "../ui.jsx";

const COLS = [["aberto", "Aberto"], ["andamento", "Em andamento"], ["concluido", "Concluído"]];

export default function Campanhas() {
  return (
    <div className="cols-3">
      {COLS.map(([id, label]) => {
        const items = CAMPAIGNS.filter((c) => c.col === id);
        return (
          <div key={id}>
            <Cap style={{ marginBottom: 8 }}>{label} · {items.length}</Cap>
            <div className="stack" style={{ gap: 10 }}>
              {items.map((c) => (
                <Card key={c.t} mock={c.src === "EST"} style={{ padding: 14 }}>
                  <div className="sm" style={{ lineHeight: 1.45 }}>{c.t}</div>
                  <div className="row" style={{ justifyContent: "space-between", marginTop: 10 }}>
                    <ProvenanceChip method={c.src} source={c.src === "OBS" ? "canal Slack" : "mock"} />
                    <span className="xs muted">{c.owner}</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
