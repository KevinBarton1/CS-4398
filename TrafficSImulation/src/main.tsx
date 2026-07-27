import { Component, StrictMode } from "react";
import type { ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

class AppErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return <div className="startup-message">
        <strong>TrafficScope could not finish loading.</strong>
        <span>Refresh the page. If the issue continues, restart with start_demo.bat.</span>
      </div>;
    }
    return this.props.children;
  }
}

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode><AppErrorBoundary><App /></AppErrorBoundary></StrictMode>
  );
}
