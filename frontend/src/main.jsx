import React from "react";
import { createRoot } from "react-dom/client";
import "@ds/styles.css"; // tokens do design system (fonts, colors, typography, spacing, effects)
import "./app.css"; // layout e composições do app, sobre os tokens
import CitadelApp from "./CitadelApp.jsx";

createRoot(document.getElementById("root")).render(<CitadelApp />);
