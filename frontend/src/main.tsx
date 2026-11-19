import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { applyEmbedOptions } from "./embed";
import "./styles.css";

applyEmbedOptions();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
