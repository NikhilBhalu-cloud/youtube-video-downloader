import "primeflex/primeflex.css";
import "primereact/resources/primereact.min.css";
import "primereact/resources/themes/lara-light-indigo/theme.css";
import "primeicons/primeicons.css";
import "./index.css";
import { StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import App from "./App";

hydrateRoot(
  document.getElementById("root") as HTMLElement,
  <StrictMode>
    <App />
  </StrictMode>
);
