import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.core.config import get_settings
from app.db.session import create_db_and_tables
from app.telemetry.metrics import API_ERROR_TOTAL, observe_request, setup_metrics

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Incident tracking API for a DevSecOps and GitOps portfolio platform.",
    lifespan=lifespan,
)


UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DevSecOps Incident Platform</title>
  <style>
    :root {
      --bg: #07111a;
      --panel: rgba(10, 28, 41, 0.88);
      --panel-strong: rgba(13, 34, 49, 0.96);
      --panel-soft: rgba(255, 255, 255, 0.035);
      --line: rgba(143, 214, 186, 0.16);
      --line-strong: rgba(143, 214, 186, 0.3);
      --text: #eef7f2;
      --muted: #9cb8af;
      --accent: #95e5c7;
      --accent-strong: #50cf9f;
      --accent-deep: #10382d;
      --warn: #ffbf69;
      --danger: #ff7c7c;
      --critical: #ff627d;
      --shadow: 0 24px 90px rgba(0, 0, 0, 0.35);
      --radius: 26px;
    }

    * {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Bahnschrift, "Aptos", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(80, 207, 159, 0.2), transparent 28%),
        radial-gradient(circle at top right, rgba(255, 191, 105, 0.14), transparent 25%),
        linear-gradient(140deg, #04090e 0%, #081723 46%, #102334 100%);
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(143, 227, 197, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(143, 227, 197, 0.04) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.65), transparent 85%);
    }

    .shell {
      width: min(1240px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 54px;
    }

    .hero,
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .hero {
      position: relative;
      overflow: hidden;
      padding: 30px;
      margin-bottom: 24px;
    }

    .hero::after {
      content: "";
      position: absolute;
      inset: auto -6% -34% auto;
      width: 420px;
      height: 420px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(149, 229, 199, 0.18), transparent 62%);
    }

    .hero::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(120deg, rgba(255, 255, 255, 0.03), transparent 30%),
        linear-gradient(0deg, rgba(255, 255, 255, 0.02), transparent 45%);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 9px 13px;
      border-radius: 999px;
      background: rgba(149, 229, 199, 0.08);
      color: var(--accent);
      font-size: 0.84rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--accent-strong);
      box-shadow: 0 0 16px rgba(72, 207, 162, 0.8);
    }

    h1,
    h2,
    h3,
    p {
      margin: 0;
    }

    .hero-grid {
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 24px;
      margin-top: 18px;
      position: relative;
      z-index: 1;
    }

    .hero-copy h1 {
      font-size: clamp(2.5rem, 5.6vw, 4.8rem);
      line-height: 0.92;
      letter-spacing: -0.04em;
      max-width: 10ch;
      margin-bottom: 16px;
    }

    .hero-copy p {
      max-width: 62ch;
      color: var(--muted);
      font-size: 1.02rem;
      line-height: 1.65;
    }

    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 24px;
    }

    .hero-signal-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-top: 26px;
    }

    .signal-card {
      padding: 16px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .signal-card span {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }

    .signal-card strong {
      display: block;
      font-size: 1.5rem;
      line-height: 1.1;
      letter-spacing: -0.04em;
    }

    .signal-card small {
      display: block;
      color: var(--muted);
      margin-top: 8px;
      line-height: 1.45;
    }

    .button,
    button,
    select,
    input,
    textarea {
      font: inherit;
    }

    .button,
    button {
      border: 0;
      cursor: pointer;
      border-radius: 16px;
      transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
    }

    .button:hover,
    button:hover {
      transform: translateY(-1px);
    }

    .button.primary,
    button.primary {
      background: linear-gradient(135deg, var(--accent-strong), #79e3c4);
      color: #052a21;
      box-shadow: 0 18px 36px rgba(72, 207, 162, 0.22);
    }

    .button.secondary,
    button.secondary {
      background: rgba(233, 243, 239, 0.08);
      color: var(--text);
      border: 1px solid rgba(233, 243, 239, 0.12);
    }

    .button.ghost,
    button.ghost {
      background: transparent;
      color: var(--accent);
      border: 1px solid rgba(149, 229, 199, 0.18);
    }

    .button {
      text-decoration: none;
      padding: 14px 18px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .status-panel {
      padding: 22px;
      background: var(--panel-strong);
      border-radius: 22px;
      border: 1px solid rgba(149, 229, 199, 0.12);
    }

    .status-panel h2 {
      font-size: 1rem;
      margin-bottom: 16px;
    }

    .status-list {
      display: grid;
      gap: 12px;
    }

    .status-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .status-item small {
      display: block;
      color: var(--muted);
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.7rem;
    }

    .state-pill {
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 0.82rem;
      background: rgba(255, 255, 255, 0.07);
      color: var(--text);
    }

    .state-pill.ok {
      background: rgba(72, 207, 162, 0.16);
      color: #a7f5db;
    }

    .state-pill.fail {
      background: rgba(255, 123, 123, 0.15);
      color: #ffc0c0;
    }

    .status-note {
      margin-top: 14px;
      color: var(--muted);
      line-height: 1.55;
      font-size: 0.88rem;
    }

    .dashboard {
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.88fr);
      gap: 24px;
    }

    .stack {
      display: grid;
      gap: 24px;
    }

    .panel {
      padding: 24px;
    }

    .panel-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    .panel-head p {
      color: var(--muted);
      margin-top: 6px;
      line-height: 1.55;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
    }

    .metric-card {
      padding: 16px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03));
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .metric-card span {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }

    .metric-card strong {
      font-size: clamp(1.8rem, 3vw, 2.6rem);
      letter-spacing: -0.04em;
    }

    .metric-card small {
      display: block;
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.4;
    }

    .insight-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }

    .subpanel {
      padding: 18px;
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.025));
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .subpanel h3 {
      font-size: 1rem;
      margin-bottom: 8px;
    }

    .subpanel p {
      color: var(--muted);
      line-height: 1.55;
    }

    .distribution {
      display: grid;
      gap: 12px;
      margin-top: 18px;
    }

    .distribution-row {
      display: grid;
      grid-template-columns: 74px minmax(0, 1fr) 44px;
      align-items: center;
      gap: 12px;
    }

    .distribution-row span {
      color: var(--muted);
      font-size: 0.86rem;
      text-transform: capitalize;
    }

    .distribution-track {
      height: 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      overflow: hidden;
    }

    .distribution-fill {
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, rgba(80, 207, 159, 0.45), rgba(149, 229, 199, 0.95));
      width: 0;
      transition: width 240ms ease;
    }

    .distribution-fill.medium {
      background: linear-gradient(90deg, rgba(255, 191, 105, 0.45), rgba(255, 191, 105, 0.95));
    }

    .distribution-fill.high {
      background: linear-gradient(90deg, rgba(255, 151, 89, 0.45), rgba(255, 151, 89, 0.95));
    }

    .distribution-fill.critical {
      background: linear-gradient(90deg, rgba(255, 98, 125, 0.45), rgba(255, 98, 125, 0.95));
    }

    .service-list,
    .route-list,
    .checklist {
      display: grid;
      gap: 10px;
      margin-top: 16px;
    }

    .service-item,
    .route-item,
    .check-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .service-item strong,
    .route-item strong,
    .check-item strong {
      font-size: 0.96rem;
    }

    .route-item a {
      color: var(--text);
      text-decoration: none;
    }

    .route-item a:hover {
      color: var(--accent);
    }

    .service-item span,
    .check-item span,
    .route-item span {
      color: var(--muted);
      font-size: 0.86rem;
      line-height: 1.45;
    }

    .brief-card {
      margin-top: 16px;
      padding: 16px;
      border-radius: 18px;
      background: rgba(149, 229, 199, 0.06);
      border: 1px solid rgba(149, 229, 199, 0.14);
    }

    .brief-card strong {
      display: block;
      font-size: 1rem;
      margin-bottom: 6px;
    }

    .brief-card p {
      color: var(--text);
      line-height: 1.6;
    }

    .empty-state {
      padding: 28px;
      border-radius: 20px;
      text-align: center;
      background: rgba(255, 255, 255, 0.035);
      border: 1px dashed rgba(255, 255, 255, 0.12);
      color: var(--muted);
    }

    .incident-list {
      display: grid;
      gap: 14px;
    }

    .incident-card {
      padding: 18px;
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.025));
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .incident-top,
    .incident-meta,
    .incident-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .incident-top {
      margin-bottom: 10px;
    }

    .incident-card h3 {
      font-size: 1.08rem;
    }

    .incident-card p {
      color: var(--muted);
      line-height: 1.6;
      margin-bottom: 14px;
    }

    .meta-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 88px;
      padding: 8px 12px;
      border-radius: 999px;
      text-transform: capitalize;
      font-size: 0.82rem;
      letter-spacing: 0.02em;
      border: 1px solid transparent;
    }

    .badge.low {
      color: #c8f2e2;
      background: rgba(72, 207, 162, 0.12);
      border-color: rgba(72, 207, 162, 0.22);
    }

    .badge.medium {
      color: #ffe4b4;
      background: rgba(255, 180, 84, 0.14);
      border-color: rgba(255, 180, 84, 0.25);
    }

    .badge.high {
      color: #ffd0a0;
      background: rgba(255, 143, 59, 0.14);
      border-color: rgba(255, 143, 59, 0.24);
    }

    .badge.critical {
      color: #ffc1ca;
      background: rgba(255, 93, 115, 0.14);
      border-color: rgba(255, 93, 115, 0.24);
    }

    .badge.status {
      color: #dce9e4;
      background: rgba(255, 255, 255, 0.06);
      border-color: rgba(255, 255, 255, 0.08);
    }

    .toolbar {
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) repeat(2, minmax(140px, 0.6fr)) auto;
      gap: 12px;
      margin-bottom: 18px;
    }

    .toolbar button {
      min-height: 50px;
    }

    .muted-label {
      display: block;
      color: var(--muted);
      font-size: 0.76rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }

    form {
      display: grid;
      gap: 14px;
    }

    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    label {
      display: grid;
      gap: 8px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    input,
    select,
    textarea {
      width: 100%;
      padding: 14px 15px;
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(3, 12, 19, 0.6);
      color: var(--text);
      outline: none;
      transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
    }

    input:focus,
    select:focus,
    textarea:focus {
      border-color: rgba(143, 227, 197, 0.6);
      box-shadow: 0 0 0 4px rgba(143, 227, 197, 0.12);
      background: rgba(3, 12, 19, 0.82);
    }

    textarea {
      min-height: 130px;
      resize: vertical;
    }

    .form-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: space-between;
      align-items: center;
      margin-top: 4px;
    }

    .helper {
      color: var(--muted);
      font-size: 0.86rem;
      line-height: 1.5;
    }

    .message {
      min-height: 24px;
      font-size: 0.92rem;
    }

    .message.success {
      color: #a7f5db;
    }

    .message.error {
      color: #ffc0c0;
    }

    .tiny-button {
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .tiny-button.danger {
      color: #ffc0c0;
      background: rgba(255, 123, 123, 0.08);
      border-color: rgba(255, 123, 123, 0.16);
    }

    .footer-note {
      margin-top: 16px;
      color: var(--muted);
      font-size: 0.86rem;
    }

    .sidebar-stack {
      display: grid;
      gap: 24px;
    }

    .urgent-card {
      padding: 18px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(255, 98, 125, 0.12), rgba(255, 98, 125, 0.04));
      border: 1px solid rgba(255, 98, 125, 0.16);
      margin-top: 16px;
    }

    .urgent-card h3 {
      margin-bottom: 8px;
    }

    .urgent-card p {
      color: #ffd2d9;
      line-height: 1.6;
    }

    .micro-copy {
      margin-top: 12px;
      color: var(--muted);
      font-size: 0.86rem;
      line-height: 1.5;
    }

    @media (max-width: 1024px) {
      .hero-grid,
      .dashboard {
        grid-template-columns: 1fr;
      }

      .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .insight-grid {
        grid-template-columns: 1fr;
      }

      .toolbar {
        grid-template-columns: 1fr 1fr;
      }

      .hero-signal-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 640px) {
      .shell {
        width: min(100% - 20px, 1180px);
        padding-top: 12px;
      }

      .hero,
      .panel {
        padding: 18px;
        border-radius: 20px;
      }

      .metric-grid,
      .field-grid,
      .toolbar {
        grid-template-columns: 1fr;
      }

      .hero-copy h1 {
        max-width: none;
      }

      .distribution-row {
        grid-template-columns: 60px minmax(0, 1fr) 36px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">
        <span class="dot"></span>
        Live response console
      </div>
      <div class="hero-grid">
        <div class="hero-copy">
          <h1>See what is burning, who owns it, and what happens next.</h1>
          <p>
            This dashboard turns the incident API into an operations cockpit. It highlights live platform health,
            current workload, severity pressure, impacted services, and a clear path to log the next incident without
            dropping into raw JSON unless you want to.
          </p>
          <div class="hero-actions">
            <a class="button primary" href="#create-incident">Create incident</a>
            <a class="button secondary" href="/docs">Open API docs</a>
            <a class="button ghost" href="/metrics">View metrics</a>
          </div>
          <div class="hero-signal-grid" aria-label="Top level signals">
            <article class="signal-card">
              <span>Operations focus</span>
              <strong id="signal-focus">Watching incident load</strong>
              <small id="signal-focus-copy">The dashboard will surface the most urgent posture once incident data loads.</small>
            </article>
            <article class="signal-card">
              <span>Services impacted</span>
              <strong id="signal-services">0 services</strong>
              <small id="signal-services-copy">Unique services with incident records in the current feed.</small>
            </article>
            <article class="signal-card">
              <span>Last refresh</span>
              <strong id="signal-refresh">Pending</strong>
              <small id="signal-refresh-copy">Pulling fresh API and readiness signals.</small>
            </article>
          </div>
        </div>
        <aside class="status-panel" aria-label="Service status">
          <h2>Runtime status</h2>
          <div class="status-list">
            <div class="status-item">
              <div>
                <small>Platform</small>
                <strong>API health</strong>
              </div>
              <span id="health-pill" class="state-pill">Checking...</span>
            </div>
            <div class="status-item">
              <div>
                <small>Database</small>
                <strong>Readiness</strong>
              </div>
              <span id="ready-pill" class="state-pill">Checking...</span>
            </div>
            <div class="status-item">
              <div>
                <small>Endpoints</small>
                <strong>Control routes</strong>
              </div>
              <span class="state-pill ok">/ /docs /api/incidents</span>
            </div>
          </div>
          <p class="status-note">
            Use this page for a fast operational read. Use Swagger when you need full request and response detail.
          </p>
        </aside>
      </div>
    </section>

    <section class="dashboard">
      <div class="stack">
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Operations summary</h2>
              <p>Live metrics computed from current incidents so you can scan load, urgency, ownership, and progress in one pass.</p>
            </div>
          </div>
          <div class="metric-grid" aria-label="Incident metrics">
            <article class="metric-card">
              <span>Total incidents</span>
              <strong id="metric-total">0</strong>
              <small>Records currently in the incident feed.</small>
            </article>
            <article class="metric-card">
              <span>Active incidents</span>
              <strong id="metric-active">0</strong>
              <small>Open or investigating incidents needing attention.</small>
            </article>
            <article class="metric-card">
              <span>High risk</span>
              <strong id="metric-risk">0</strong>
              <small>High and critical incidents in the queue.</small>
            </article>
            <article class="metric-card">
              <span>Resolved incidents</span>
              <strong id="metric-resolved">0</strong>
              <small>Items already closed out and recovered.</small>
            </article>
            <article class="metric-card">
              <span>Services impacted</span>
              <strong id="metric-services">0</strong>
              <small>Unique service owners represented in the feed.</small>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Command insight</h2>
              <p>Use the mix of severity, service ownership, and response guidance to decide what to tackle first.</p>
            </div>
          </div>
          <div class="insight-grid">
            <section class="subpanel">
              <h3>Severity mix</h3>
              <p>Distribution across low, medium, high, and critical incidents.</p>
              <div id="severity-breakdown" class="distribution">
                <div class="empty-state">Waiting for incident data.</div>
              </div>
            </section>

            <section class="subpanel">
              <h3>Service ownership</h3>
              <p>Services with the heaviest incident load right now.</p>
              <div id="service-breakdown" class="service-list">
                <div class="empty-state">Service ownership will appear once incidents are loaded.</div>
              </div>
            </section>

            <section class="subpanel">
              <h3>Response brief</h3>
              <p>A short, dynamic note based on the current incident posture.</p>
              <div id="response-brief" class="brief-card">
                <strong>Waiting for data</strong>
                <p>The dashboard will suggest a focus once the incident feed is available.</p>
              </div>
            </section>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Live incident queue</h2>
              <p>Search and filter the queue to focus on the service, severity, or state you care about right now.</p>
            </div>
          </div>
          <div class="toolbar" aria-label="Incident filters">
            <label>
              <span class="muted-label">Search title or service</span>
              <input id="search-input" type="search" placeholder="Search incidents, services, or keywords" />
            </label>
            <label>
              <span class="muted-label">Severity</span>
              <select id="severity-filter">
                <option value="all">All severities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label>
              <span class="muted-label">Status</span>
              <select id="status-filter">
                <option value="all">All statuses</option>
                <option value="open">Open</option>
                <option value="investigating">Investigating</option>
                <option value="mitigated">Mitigated</option>
                <option value="resolved">Resolved</option>
              </select>
            </label>
            <button id="refresh-button" class="secondary" type="button">Refresh data</button>
          </div>
          <div id="incident-list" class="incident-list" aria-live="polite">
            <div class="empty-state">Loading incident feed...</div>
          </div>
          <p class="footer-note">
            Tip: the API remains fully available at <code>/api/incidents</code> if you want to automate against the same data shown here.
          </p>
        </section>
      </div>

      <aside class="sidebar-stack">
        <section class="panel" id="create-incident">
          <div class="panel-head">
            <div>
              <h2>Create a new incident</h2>
              <p>Capture title, impact, severity, and service ownership directly from the browser.</p>
            </div>
          </div>

          <form id="incident-form">
            <label>
              Title
              <input id="title" name="title" minlength="3" maxlength="120" placeholder="Database latency spike" required />
            </label>

            <label>
              Description
              <textarea
                id="description"
                name="description"
                minlength="5"
                maxlength="2000"
                placeholder="Describe the incident impact, signals, and the affected path."
                required
              ></textarea>
            </label>

            <div class="field-grid">
              <label>
                Severity
                <select id="severity" name="severity">
                  <option value="low">Low</option>
                  <option value="medium" selected>Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </label>

              <label>
                Status
                <select id="status" name="status">
                  <option value="open" selected>Open</option>
                  <option value="investigating">Investigating</option>
                  <option value="mitigated">Mitigated</option>
                  <option value="resolved">Resolved</option>
                </select>
              </label>
            </div>

            <label>
              Service name
              <input id="service_name" name="service_name" minlength="2" maxlength="120" placeholder="payments-api" required />
            </label>

            <div class="form-actions">
              <div class="helper">The form submits to the same FastAPI backend used by the dashboard, docs, and automation endpoints.</div>
              <button class="primary" type="submit">Create incident</button>
            </div>
            <div id="form-message" class="message" aria-live="polite"></div>
          </form>

          <div id="urgent-spotlight" class="urgent-card">
            <h3>Urgent spotlight</h3>
            <p>No critical incident is active right now. The dashboard will pin the most urgent item here when one appears.</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Runbook starter</h2>
              <p>A quick human checklist for the first few minutes of response.</p>
            </div>
          </div>
          <div class="checklist">
            <div class="check-item">
              <strong>Confirm impact</strong>
              <span>Validate which customer path, service, or dependency is actually degraded.</span>
            </div>
            <div class="check-item">
              <strong>Assign ownership</strong>
              <span>Make one service team clearly accountable for updates and mitigation.</span>
            </div>
            <div class="check-item">
              <strong>Communicate early</strong>
              <span>Share scope, current status, and next checkpoint before speculation spreads.</span>
            </div>
            <div class="check-item">
              <strong>Track recovery</strong>
              <span>Move incidents toward mitigated and resolved so the queue reflects reality.</span>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Quick routes</h2>
              <p>Jump to the most useful backend surfaces from the same page.</p>
            </div>
          </div>
          <div class="route-list">
            <div class="route-item">
              <div>
                <strong><a href="/docs">Swagger UI</a></strong>
                <span>Inspect schemas and test requests interactively.</span>
              </div>
            </div>
            <div class="route-item">
              <div>
                <strong><a href="/metrics">Prometheus metrics</a></strong>
                <span>Review counters and latency measurements exported by the API.</span>
              </div>
            </div>
            <div class="route-item">
              <div>
                <strong><a href="/health">Health endpoint</a></strong>
                <span>Fast liveness check for local and platform probes.</span>
              </div>
            </div>
            <div class="route-item">
              <div>
                <strong><a href="/ready">Readiness endpoint</a></strong>
                <span>Verify database reachability before routing production traffic.</span>
              </div>
            </div>
          </div>
          <p class="micro-copy">This page is optimized for operator clarity, while the linked routes remain useful for automation and diagnostics.</p>
        </section>
      </aside>
    </section>
  </main>

  <script>
    const incidentList = document.getElementById("incident-list");
    const form = document.getElementById("incident-form");
    const formMessage = document.getElementById("form-message");
    const refreshButton = document.getElementById("refresh-button");
    const severityBreakdown = document.getElementById("severity-breakdown");
    const serviceBreakdown = document.getElementById("service-breakdown");
    const responseBrief = document.getElementById("response-brief");
    const urgentSpotlight = document.getElementById("urgent-spotlight");
    const searchInput = document.getElementById("search-input");
    const severityFilter = document.getElementById("severity-filter");
    const statusFilter = document.getElementById("status-filter");
    let allIncidents = [];

    function setPill(id, ok, label) {
      const pill = document.getElementById(id);
      pill.textContent = label;
      pill.className = ok ? "state-pill ok" : "state-pill fail";
    }

    function formatDate(value) {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return "Unknown time";
      }
      return date.toLocaleString();
    }

    function escapeHtml(value) {
      return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function formatCountLabel(count, singular, plural) {
      return count === 1 ? `1 ${singular}` : `${count} ${plural}`;
    }

    function updateRefreshSignal() {
      const now = new Date();
      document.getElementById("signal-refresh").textContent = now.toLocaleTimeString();
      document.getElementById("signal-refresh-copy").textContent = `Data synced on ${now.toLocaleDateString()} at ${now.toLocaleTimeString()}.`;
    }

    function updateMetrics(incidents) {
      const total = incidents.length;
      const active = incidents.filter((incident) => ["open", "investigating"].includes(incident.status)).length;
      const highRisk = incidents.filter((incident) => ["high", "critical"].includes(incident.severity)).length;
      const resolved = incidents.filter((incident) => incident.status === "resolved").length;
      const services = new Set(incidents.map((incident) => incident.service_name)).size;

      document.getElementById("metric-total").textContent = String(total);
      document.getElementById("metric-active").textContent = String(active);
      document.getElementById("metric-risk").textContent = String(highRisk);
      document.getElementById("metric-resolved").textContent = String(resolved);
      document.getElementById("metric-services").textContent = String(services);
      document.getElementById("signal-services").textContent = formatCountLabel(services, "service", "services");
      document.getElementById("signal-services-copy").textContent = services
        ? "Distinct services currently represented in the incident queue."
        : "No services are impacted yet because the queue is empty.";
    }

    function renderSeverityBreakdown(incidents) {
      const levels = ["low", "medium", "high", "critical"];
      if (!incidents.length) {
        severityBreakdown.innerHTML = '<div class="empty-state">No incidents yet. The severity mix will update once records exist.</div>';
        return;
      }

      severityBreakdown.innerHTML = levels
        .map((level) => {
          const count = incidents.filter((incident) => incident.severity === level).length;
          const percent = incidents.length ? Math.round((count / incidents.length) * 100) : 0;
          return `
            <div class="distribution-row">
              <span>${level}</span>
              <div class="distribution-track">
                <div class="distribution-fill ${level}" style="width: ${percent}%"></div>
              </div>
              <strong>${count}</strong>
            </div>
          `;
        })
        .join("");
    }

    function renderServiceBreakdown(incidents) {
      if (!incidents.length) {
        serviceBreakdown.innerHTML = '<div class="empty-state">No service pressure to show yet.</div>';
        return;
      }

      const counts = incidents.reduce((services, incident) => {
        services[incident.service_name] = (services[incident.service_name] || 0) + 1;
        return services;
      }, {});

      const topServices = Object.entries(counts)
        .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
        .slice(0, 5);

      serviceBreakdown.innerHTML = topServices
        .map(([service, count]) => `
          <div class="service-item">
            <div>
              <strong>${escapeHtml(service)}</strong>
              <span>${formatCountLabel(count, "incident", "incidents")}</span>
            </div>
            <span>${count}</span>
          </div>
        `)
        .join("");
    }

    function renderResponseBrief(incidents) {
      const critical = incidents.filter((incident) => incident.severity === "critical" && incident.status !== "resolved");
      const investigating = incidents.filter((incident) => incident.status === "investigating");
      const open = incidents.filter((incident) => incident.status === "open");
      const resolved = incidents.filter((incident) => incident.status === "resolved");

      if (!incidents.length) {
        responseBrief.innerHTML = `
          <strong>Quiet queue</strong>
          <p>No incidents are currently logged. This is a good time to validate alerts, ownership, and readiness paths.</p>
        `;
        document.getElementById("signal-focus").textContent = "Queue is clear";
        document.getElementById("signal-focus-copy").textContent = "No active incident pressure detected in the current dataset.";
        urgentSpotlight.innerHTML = `
          <h3>Urgent spotlight</h3>
          <p>No critical incident is active right now. The dashboard will pin the most urgent item here when one appears.</p>
        `;
        return;
      }

      if (critical.length) {
        const mostUrgent = critical[0];
        responseBrief.innerHTML = `
          <strong>Escalate critical work</strong>
          <p>${formatCountLabel(critical.length, "critical incident remains", "critical incidents remain")} active. Keep the owner and stakeholder updates tight until customer impact is contained.</p>
        `;
        document.getElementById("signal-focus").textContent = "Critical escalation";
        document.getElementById("signal-focus-copy").textContent = "At least one critical incident is unresolved and should anchor response priority.";
        urgentSpotlight.innerHTML = `
          <h3>Urgent spotlight</h3>
          <p><strong>${escapeHtml(mostUrgent.title)}</strong> is the highest-risk item right now for <strong>${escapeHtml(mostUrgent.service_name)}</strong>. Keep status updates frequent until it moves past open or investigating.</p>
        `;
        return;
      }

      if (investigating.length) {
        responseBrief.innerHTML = `
          <strong>Drive mitigation</strong>
          <p>${formatCountLabel(investigating.length, "incident is under investigation", "incidents are under investigation")}. Focus on narrowing blast radius and recording recovery steps clearly.</p>
        `;
        document.getElementById("signal-focus").textContent = "Mitigation in progress";
        document.getElementById("signal-focus-copy").textContent = "The current queue has active investigation work that should move toward mitigation.";
      } else if (open.length) {
        responseBrief.innerHTML = `
          <strong>Clarify ownership</strong>
          <p>${formatCountLabel(open.length, "open incident needs a clear next action", "open incidents need clear next actions")}. Make sure each one has a named service owner and first checkpoint.</p>
        `;
        document.getElementById("signal-focus").textContent = "Triage ownership";
        document.getElementById("signal-focus-copy").textContent = "Open incidents exist without being pushed deeper into the response workflow.";
      } else {
        responseBrief.innerHTML = `
          <strong>Close the loop</strong>
          <p>${formatCountLabel(resolved.length, "incident is resolved", "incidents are resolved")}. Capture follow-ups and post-incident actions while context is still fresh.</p>
        `;
        document.getElementById("signal-focus").textContent = "Recovery complete";
        document.getElementById("signal-focus-copy").textContent = "The queue is resolved, so this is a good time to log follow-up improvements.";
      }

      urgentSpotlight.innerHTML = `
        <h3>Urgent spotlight</h3>
        <p>No critical incident is active right now. The dashboard suggests focusing on ownership, mitigation progress, and closure quality.</p>
      `;
    }

    function getFilteredIncidents() {
      const searchTerm = searchInput.value.trim().toLowerCase();
      const severityValue = severityFilter.value;
      const statusValue = statusFilter.value;

      return allIncidents.filter((incident) => {
        const matchesSearch = !searchTerm
          || incident.title.toLowerCase().includes(searchTerm)
          || incident.service_name.toLowerCase().includes(searchTerm)
          || incident.description.toLowerCase().includes(searchTerm);
        const matchesSeverity = severityValue === "all" || incident.severity === severityValue;
        const matchesStatus = statusValue === "all" || incident.status === statusValue;
        return matchesSearch && matchesSeverity && matchesStatus;
      });
    }

    function renderIncidents(incidents) {
      if (!incidents.length) {
        incidentList.innerHTML = allIncidents.length
          ? '<div class="empty-state">No incidents match the current filters. Clear or relax the filters to broaden the queue.</div>'
          : '<div class="empty-state">No incidents yet. Use the form to create the first one and start the operational view.</div>';
        return;
      }

      incidentList.innerHTML = incidents
        .sort((left, right) => new Date(right.created_at) - new Date(left.created_at))
        .map((incident) => `
          <article class="incident-card">
            <div class="incident-top">
              <h3>${escapeHtml(incident.title)}</h3>
              <div class="meta-wrap">
                <span class="badge ${escapeHtml(incident.severity)}">${escapeHtml(incident.severity)}</span>
                <span class="badge status">${escapeHtml(incident.status)}</span>
              </div>
            </div>
            <p>${escapeHtml(incident.description)}</p>
            <div class="incident-meta">
              <div class="meta-wrap">
                <span><strong>Service:</strong> ${escapeHtml(incident.service_name)}</span>
                <span><strong>ID:</strong> ${incident.id}</span>
                <span><strong>Created:</strong> ${formatDate(incident.created_at)}</span>
                <span><strong>Updated:</strong> ${formatDate(incident.updated_at)}</span>
              </div>
              <div class="incident-actions">
                <button class="tiny-button danger" type="button" data-delete-id="${incident.id}">Delete</button>
              </div>
            </div>
          </article>
        `)
        .join("");

      document.querySelectorAll("[data-delete-id]").forEach((button) => {
        button.addEventListener("click", async () => {
          const incidentId = button.getAttribute("data-delete-id");
          button.disabled = true;
          button.textContent = "Deleting...";

          const response = await fetch(`/api/incidents/${incidentId}`, { method: "DELETE" });
          if (!response.ok) {
            button.disabled = false;
            button.textContent = "Delete";
            formMessage.textContent = "Unable to delete the incident right now.";
            formMessage.className = "message error";
            return;
          }

          formMessage.textContent = `Incident #${incidentId} deleted.`;
          formMessage.className = "message success";
          await loadIncidents();
          await loadHealth();
        });
      });
    }

    function renderDashboard() {
      const filteredIncidents = getFilteredIncidents();
      updateMetrics(allIncidents);
      renderSeverityBreakdown(allIncidents);
      renderServiceBreakdown(allIncidents);
      renderResponseBrief(allIncidents);
      renderIncidents(filteredIncidents);
    }

    async function loadHealth() {
      try {
        const [healthResponse, readyResponse] = await Promise.all([
          fetch("/health"),
          fetch("/ready"),
        ]);

        const healthPayload = await healthResponse.json();
        const readyPayload = await readyResponse.json();

        setPill("health-pill", healthResponse.ok && healthPayload.status === "ok", healthPayload.status);
        setPill("ready-pill", readyResponse.ok && readyPayload.status === "ready", readyPayload.status);
      } catch (_) {
        setPill("health-pill", false, "unreachable");
        setPill("ready-pill", false, "unreachable");
      }
    }

    async function loadIncidents() {
      incidentList.innerHTML = '<div class="empty-state">Loading incident feed...</div>';

      try {
        const response = await fetch("/api/incidents");
        if (!response.ok) {
          throw new Error("incident request failed");
        }

        allIncidents = await response.json();
        renderDashboard();
        updateRefreshSignal();
      } catch (_) {
        allIncidents = [];
        renderDashboard();
        document.getElementById("signal-refresh").textContent = "Failed";
        document.getElementById("signal-refresh-copy").textContent = "The dashboard could not refresh incident data from the API.";
        incidentList.innerHTML = '<div class="empty-state">Unable to load incidents. Make sure the API is running and the database is reachable.</div>';
        severityBreakdown.innerHTML = '<div class="empty-state">Severity insight is unavailable until the incident feed recovers.</div>';
        serviceBreakdown.innerHTML = '<div class="empty-state">Service ownership insight is unavailable until the incident feed recovers.</div>';
        responseBrief.innerHTML = `
          <strong>Feed unavailable</strong>
          <p>The dashboard could not fetch incidents. Restore API access or database reachability and refresh.</p>
        `;
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      formMessage.textContent = "Creating incident...";
      formMessage.className = "message";

      const payload = {
        title: form.title.value.trim(),
        description: form.description.value.trim(),
        severity: form.severity.value,
        status: form.status.value,
        service_name: form.service_name.value.trim(),
      };

      const response = await fetch("/api/incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: "Request failed" }));
        const detail = Array.isArray(payload.detail) ? "Please review the form fields and try again." : payload.detail;
        formMessage.textContent = detail || "Unable to create incident.";
        formMessage.className = "message error";
        return;
      }

      form.reset();
      form.severity.value = "medium";
      form.status.value = "open";
      formMessage.textContent = "Incident created successfully.";
      formMessage.className = "message success";
      await loadIncidents();
      await loadHealth();
    });

    [searchInput, severityFilter, statusFilter].forEach((control) => {
      control.addEventListener("input", renderDashboard);
      control.addEventListener("change", renderDashboard);
    });

    refreshButton.addEventListener("click", async () => {
      refreshButton.disabled = true;
      refreshButton.textContent = "Refreshing...";
      await Promise.all([loadHealth(), loadIncidents()]);
      refreshButton.disabled = false;
      refreshButton.textContent = "Refresh data";
    });

    loadHealth();
    loadIncidents();
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse, tags=["ui"])
def root_dashboard() -> str:
    return UI_HTML


@app.middleware("http")
async def record_api_errors(request: Request, call_next):
    request_started = time.perf_counter()
    handler = request.url.path

    try:
        response = await call_next(request)
    except Exception:
        API_ERROR_TOTAL.labels(
            path=handler,
            method=request.method,
            status_code="500",
        ).inc()
        observe_request(
            handler=handler,
            method=request.method,
            status_code=500,
            duration=time.perf_counter() - request_started,
        )
        raise

    if response.status_code >= 400:
        API_ERROR_TOTAL.labels(
            path=handler,
            method=request.method,
            status_code=str(response.status_code),
        ).inc()

    observe_request(
        handler=handler,
        method=request.method,
        status_code=response.status_code,
        duration=time.perf_counter() - request_started,
    )

    return response


app.include_router(health_router)
app.include_router(incidents_router)
setup_metrics(app)
