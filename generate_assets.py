#!/usr/bin/env python3
"""
Generate portfolio documentation assets:
  docs/architecture.png           — workflow diagram
  docs/api_post_webhook_lead.png  — POST /webhook/lead showcase
  docs/api_get_leads.png          — GET /leads showcase
  docs/api_get_lead_id.png        — GET /leads/{id} showcase
  docs/api_health.png             — GET /health showcase

Run from the project root:
  python generate_assets.py
"""
import os
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
from matplotlib.font_manager import FontProperties

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
os.makedirs(DOCS_DIR, exist_ok=True)


# ── GitHub-dark palette ──────────────────────────────────────────────────────
BG     = "#0D1117"
CARD   = "#161B22"
BORDER = "#30363D"
TEXT   = "#E6EDF3"
DIM    = "#8B949E"
GREEN  = "#3FB950"
BLUE   = "#58A6FF"
PURPLE = "#BC8CFF"
YELLOW = "#E3B341"
RED    = "#F85149"
PINK   = "#FF7B72"
CYAN   = "#79C0FF"
ORANGE = "#FFA657"

MONO = FontProperties(family="monospace")

METHOD_BG = {"POST": "#1A4731", "GET": "#0D2A45", "DELETE": "#3D1218", "PUT": "#3A2E00"}
METHOD_FG = {"POST": GREEN,     "GET": BLUE,      "DELETE": RED,       "PUT": YELLOW}
STATUS_BG = {"2": "#1A4731", "4": "#3A2E00", "5": "#3D1218"}
STATUS_FG = {"2": GREEN,     "4": YELLOW,    "5": RED}
STATUS_LABEL = {
    "200": "200 OK", "201": "201 Created",
    "404": "404 Not Found", "422": "422 Unprocessable", "502": "502 Bad Gateway",
}


def _pill(ax, x, y, w, h, bg, fg, label, fs=8.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                facecolor=bg, edgecolor=fg, linewidth=0.8, zorder=5))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, fontweight="bold", color=fg, zorder=6)


# ─────────────────────────────────────────────────────────────────────────────
# ARCHITECTURE DIAGRAM
# ─────────────────────────────────────────────────────────────────────────────

def make_architecture():
    W, H = 20, 7.5
    fig, ax = plt.subplots(figsize=(W, H), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    STEPS = [
        ("POST\n/webhook/lead",  "Inbound payload",           1.6,  BLUE),
        ("Pydantic\nValidation", "Email & field check",        4.3,  GREEN),
        ("SQLite\nStorage",      "Lead persisted",             7.0,  YELLOW),
        ("OpenAI\nGPT-4o-mini", "Score · priority\nsummary",  9.7,  PURPLE),
        ("CRM\nRouting",         "Sales / SDR /\nNurture",    12.4,  PINK),
        ("Notification\nService","Console log\n(Slack sim.)", 15.1,  ORANGE),
        ("JSON\nResponse",       "201 + analysis",            17.8,  CYAN),
    ]
    BW, BH, BY = 2.2, 2.6, 1.8

    for i, (lbl, sub, cx, col) in enumerate(STEPS):
        for d, a in [(0.12, 0.10), (0.06, 0.18)]:
            ax.add_patch(FancyBboxPatch(
                (cx - BW/2 + d, BY - d), BW, BH,
                boxstyle="round,pad=0.2", facecolor=col, edgecolor="none", alpha=a, zorder=1))
        ax.add_patch(FancyBboxPatch(
            (cx - BW/2, BY), BW, BH,
            boxstyle="round,pad=0.2", facecolor=col, edgecolor=TEXT, linewidth=0.7, alpha=0.96, zorder=2))

        ax.add_patch(plt.Circle((cx - BW/2 + 0.32, BY + BH - 0.32), 0.23,
                                color=TEXT, alpha=0.18, zorder=3))
        ax.text(cx - BW/2 + 0.32, BY + BH - 0.32, str(i + 1),
                ha="center", va="center", fontsize=8, fontweight="bold", color=TEXT, zorder=4)

        ax.text(cx, BY + BH * 0.66, lbl, ha="center", va="center", zorder=4,
                fontsize=9.5, fontweight="bold", color=TEXT, multialignment="center")
        ax.text(cx, BY + BH * 0.21, sub, ha="center", va="center", zorder=4,
                fontsize=7.5, color=TEXT, alpha=0.72, multialignment="center")

        if i < len(STEPS) - 1:
            ax.annotate("", zorder=5,
                xy=(STEPS[i+1][2] - BW/2 - 0.06, BY + BH/2),
                xytext=(cx + BW/2 + 0.06, BY + BH/2),
                arrowprops=dict(arrowstyle="-|>", color=DIM, lw=2.2, mutation_scale=22))

    ax.text(W/2, 7.1, "AI Lead Qualification Agent",
            ha="center", fontsize=22, fontweight="bold", color=TEXT,
            path_effects=[pe.withStroke(linewidth=5, foreground=BG)])
    ax.text(W/2, 6.45,
            "Webhook  ›  Validation  ›  Database  ›  OpenAI Analysis  ›  CRM Routing  ›  Notification  ›  Response",
            ha="center", fontsize=10.5, color=DIM)
    ax.plot([0.5, W - 0.5], [6.1, 6.1], color=BORDER, lw=0.8)

    out = os.path.join(DOCS_DIR, "architecture.png")
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"[OK] {out}")


# ─────────────────────────────────────────────────────────────────────────────
# API SHOWCASE CARDS
# ─────────────────────────────────────────────────────────────────────────────

def make_api_card(fname, method, endpoint, status, title, req=None, resp=None):
    req_lines  = json.dumps(req,  indent=2).split("\n") if req  is not None else []
    resp_lines = json.dumps(resp, indent=2).split("\n") if resp is not None else []

    LINE_H = 0.295
    FW = 16.0
    split = bool(req_lines and resp_lines)
    n_max = max(len(req_lines), len(resp_lines), 5)
    FH = 2.15 + n_max * LINE_H + 0.9

    fig, ax = plt.subplots(figsize=(FW, FH), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, FW)
    ax.set_ylim(0, FH)
    ax.axis("off")

    cy = FH - 0.5

    # ── title
    ax.text(0.5, cy, title, ha="left", va="center",
            fontsize=12.5, fontweight="bold", color=TEXT)
    cy -= 0.68

    # ── method pill + URL + status pill
    sc = str(status)
    _pill(ax, 0.5, cy - 0.22, 0.9, 0.44,
          METHOD_BG.get(method, "#1A1A2E"), METHOD_FG.get(method, BLUE), method, fs=8.5)
    ax.text(1.56, cy, endpoint, ha="left", va="center",
            fontsize=10.5, color=TEXT, fontproperties=MONO)
    _pill(ax, FW - 2.45, cy - 0.22, 1.95, 0.44,
          STATUS_BG.get(sc[0], "#1A1A2E"), STATUS_FG.get(sc[0], DIM),
          STATUS_LABEL.get(sc, sc), fs=7.5)
    cy -= 0.58

    # ── divider
    ax.plot([0.3, FW - 0.3], [cy, cy], color=BORDER, lw=0.8)
    cy -= 0.42

    # ── JSON panels
    def render_panel(px, pw, label, lines):
        ax.text(px, cy, label, ha="left", va="center",
                fontsize=7.5, fontweight="bold", color=DIM, zorder=4)
        bh = len(lines) * LINE_H + 0.38
        ax.add_patch(FancyBboxPatch(
            (px - 0.12, cy - 0.3 - bh), pw + 0.12, bh,
            boxstyle="round,pad=0.1", facecolor=CARD, edgecolor=BORDER,
            linewidth=0.6, zorder=2))
        for idx, line in enumerate(lines):
            ax.text(px + 0.1, cy - 0.52 - idx * LINE_H, line,
                    ha="left", va="center", fontsize=8.0, color=TEXT,
                    fontproperties=MONO, zorder=3)

    if split:
        half = FW / 2 - 0.55
        render_panel(0.5,       half, "REQUEST BODY", req_lines)
        ax.plot([FW/2, FW/2], [0.25, cy + 0.1], color=BORDER, lw=0.7)
        render_panel(FW/2 + 0.4, half, "RESPONSE",   resp_lines)
    elif resp_lines:
        render_panel(0.5, FW - 0.8, "RESPONSE", resp_lines)
    elif req_lines:
        render_panel(0.5, FW - 0.8, "REQUEST BODY", req_lines)

    out = os.path.join(DOCS_DIR, fname)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"[OK] {out}")


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────────────────────────────────────

LEAD_REQUEST = {
    "name": "John Smith",
    "email": "john@acmeinc.com",
    "company": "Acme Inc",
    "message": "We want AI automation for customer support.",
}

WEBHOOK_RESPONSE = {
    "status": "qualified",
    "lead_id": 1,
    "analysis": {
        "id": 1,
        "lead_id": 1,
        "lead_score": 85,
        "priority": "Hot",
        "summary": "Acme Inc seeks AI-powered customer support automation.",
        "recommended_action": "Schedule a demo call within 24 hours.",
        "crm_route": "Sales Team",
        "created_at": "2024-11-15T09:42:31",
    },
}

SINGLE_LEAD = {
    "id": 1,
    "name": "John Smith",
    "email": "john@acmeinc.com",
    "company": "Acme Inc",
    "message": "We want AI automation for customer support.",
    "created_at": "2024-11-15T09:42:31",
    "analysis": {
        "id": 1,
        "lead_id": 1,
        "lead_score": 85,
        "priority": "Hot",
        "summary": "Acme Inc seeks AI-powered customer support automation.",
        "recommended_action": "Schedule a demo call within 24 hours.",
        "crm_route": "Sales Team",
        "created_at": "2024-11-15T09:42:31",
    },
}

LEADS_LIST = [SINGLE_LEAD]
HEALTH_RESPONSE = {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    make_architecture()

    make_api_card(
        "api_post_webhook_lead.png",
        "POST", "/webhook/lead", 201,
        "POST /webhook/lead  —  Submit a new lead for AI qualification",
        req=LEAD_REQUEST,
        resp=WEBHOOK_RESPONSE,
    )
    make_api_card(
        "api_get_leads.png",
        "GET", "/leads", 200,
        "GET /leads  —  Retrieve all qualified leads",
        resp=LEADS_LIST,
    )
    make_api_card(
        "api_get_lead_id.png",
        "GET", "/leads/1", 200,
        "GET /leads/{id}  —  Retrieve a single lead by ID",
        resp=SINGLE_LEAD,
    )
    make_api_card(
        "api_health.png",
        "GET", "/health", 200,
        "GET /health  —  Health check",
        resp=HEALTH_RESPONSE,
    )

    print("\n[DONE] All assets saved to docs/")
