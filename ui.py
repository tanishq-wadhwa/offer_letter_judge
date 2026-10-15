"""Offer Shield UI helpers: CSS + small HTML components.
SECURITY: every dynamic value is passed through esc() before being placed in HTML."""
import html

STEPS = [
    "Extracting offer details",
    "Searching the web",
    "Reading company website",
    "Checking domain age",
    "Running rule checks",
    "Retrieving scam knowledge (RAG)",
    "AI analysis and verification",
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--bg:#0A0F1F;--bg2:#0E1530;--surface:#111A38;--surface2:#16224A;--border:#233062;
--text:#E8ECF8;--muted:#8E9ABB;--accent:#4F8CFF;--accent2:#22D3EE;
--safe:#22C55E;--warn:#F59E0B;--danger:#F43F5E;}
html,body,[data-testid='stAppViewContainer'],.stMarkdown,p,label,li{font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;}
[data-testid='stAppViewContainer']{color:var(--text);
background:radial-gradient(600px circle at 85% -10%,rgba(79,140,255,.18),transparent 60%),linear-gradient(180deg,#0A0F1F 0%,#0E1530 100%);}
[data-testid='stHeader'],[data-testid='stToolbar'],#MainMenu,footer,[data-testid='stSidebar'],[data-testid='collapsedControl'],[data-testid='stDecoration']{display:none !important;}
.block-container{max-width:1100px;padding-top:1.2rem;padding-bottom:4rem;}

.topbar{display:flex;justify-content:space-between;align-items:center;padding:6px 0 18px;}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:18px;color:var(--text);}
.brand .logo{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:linear-gradient(135deg,#4F8CFF,#22D3EE);font-size:18px;}
.pill{border:1px solid var(--border);background:rgba(17,26,56,.7);color:var(--muted);padding:6px 12px;border-radius:999px;font-size:12px;}

.hero{text-align:center;padding:30px 0 10px;}
.hero h1{font-size:50px;font-weight:800;letter-spacing:-.02em;line-height:1.1;margin:0 0 14px;padding:0;
background:linear-gradient(135deg,#FFFFFF 30%,#9CC2FF 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hero p{color:var(--muted);font-size:17px;max-width:680px;margin:0 auto 18px;}
.chips{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:18px;}
.chip{border:1px solid var(--border);background:var(--surface);color:var(--text);padding:6px 12px;border-radius:999px;font-size:12.5px;}
.chip b{color:var(--accent2);}

.card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:22px;box-shadow:0 10px 30px rgba(0,0,0,.35);margin-bottom:14px;}
.card.center{text-align:center;}
.label{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;font-weight:600;}
.mono{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:13px;}
.verdict{font-size:24px;font-weight:800;margin-top:6px;}
.reason{color:var(--text);line-height:1.65;font-size:15px;margin:6px 0 14px;}
.section-title{font-size:20px;font-weight:700;margin:26px 0 12px;color:var(--text);}

[data-testid='stVerticalBlockBorderWrapper']:has(textarea){background:var(--surface);border:1px solid var(--border) !important;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.35);}
[data-testid='stTextArea'] textarea{background:var(--surface2) !important;color:var(--text) !important;border:1px solid var(--border) !important;border-radius:12px !important;font-family:'JetBrains Mono',monospace !important;font-size:13px !important;}
[data-testid='stTextArea'] textarea:focus{border-color:var(--accent) !important;box-shadow:0 0 0 3px rgba(79,140,255,.25) !important;}
[data-testid='stFileUploader'] section{background:var(--surface2);border:1px dashed var(--border);border-radius:12px;}

.stButton>button{border-radius:12px;border:1px solid var(--border);background:var(--surface2);color:var(--text);font-weight:600;transition:all .15s ease;}
.stButton>button:hover{border-color:var(--accent);transform:translateY(-1px);color:#fff;}
.stButton>button[kind='primary']{background:linear-gradient(135deg,#4F8CFF,#22D3EE);color:#06101F;border:none;font-weight:700;padding:.7rem 1rem;box-shadow:0 8px 24px rgba(79,140,255,.35);}
.stButton>button[kind='primary']:hover{color:#06101F;box-shadow:0 10px 30px rgba(34,211,238,.4);}

.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;margin:0 6px 6px 0;}
.b-high{background:rgba(244,63,94,.15);color:#FF7A93;border:1px solid rgba(244,63,94,.4);}
.b-medium{background:rgba(245,158,11,.15);color:#FBBF55;border:1px solid rgba(245,158,11,.4);}
.b-low{background:rgba(34,197,94,.12);color:#5EE08A;border:1px solid rgba(34,197,94,.35);}
.b-info{background:rgba(79,140,255,.14);color:#8DB4FF;border:1px solid rgba(79,140,255,.4);}

.flag{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--muted);border-radius:12px;padding:14px 16px;margin-bottom:10px;}
.flag.high{border-left-color:var(--danger);} .flag.medium{border-left-color:var(--warn);} .flag.low{border-left-color:var(--safe);}
.flag .title{font-weight:600;margin-bottom:6px;}
.flag .ev{color:var(--muted);font-size:13px;word-break:break-word;}

.todo{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid rgba(35,48,98,.6);font-size:14.5px;}
.todo:last-child{border-bottom:none;}
.todo .box{min-width:18px;height:18px;border:2px solid var(--accent);border-radius:5px;margin-top:2px;}

.step{display:flex;align-items:center;gap:12px;padding:8px 0;color:var(--muted);font-size:14.5px;}
.step .dot{width:10px;height:10px;border-radius:50%;background:var(--border);flex:none;}
.step.done{color:var(--text);} .step.done .dot{background:var(--safe);}
.step.active{color:#fff;font-weight:600;} .step.active .dot{background:var(--accent2);box-shadow:0 0 0 6px rgba(34,211,238,.18);animation:pulse 1.2s infinite;}
@keyframes pulse{50%{box-shadow:0 0 0 10px rgba(34,211,238,0);}}

.notice{border:1px solid rgba(79,140,255,.35);background:rgba(79,140,255,.08);color:#B8CEFF;border-radius:12px;padding:10px 14px;font-size:13px;margin:8px 0;}
.fadein{animation:fade .5s ease both;} @keyframes fade{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}
.footer{text-align:center;color:var(--muted);font-size:12.5px;margin-top:40px;border-top:1px solid var(--border);padding-top:18px;line-height:1.8;}
@media (max-width:640px){.hero h1{font-size:34px;} .hero p{font-size:15px;}}
</style>
"""


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""), quote=True)


def risk_color(score: int) -> str:
    return "#22C55E" if score <= 30 else ("#F59E0B" if score <= 65 else "#F43F5E")


def _sev(s) -> str:
    s = str(s).lower().strip()
    return s if s in ("high", "medium", "low") else "low"


def topbar() -> str:
    return ("<div class='topbar'><div class='brand'><div class='logo'>🛡️</div>Offer Shield</div>"
            "<div class='pill'>AI-powered offer verification</div></div>")


def hero() -> str:
    return ("<div class='hero'><h1>Verify any job offer before it costs you.</h1>"
            "<p>AI agents, live web evidence and a scam-pattern knowledge base, combined into one "
            "risk assessment in seconds.</p>"
            "<div class='chips'><span class='chip'><b>●</b> Rule engine</span>"
            "<span class='chip'><b>●</b> Live web evidence</span>"
            "<span class='chip'><b>●</b> RAG knowledge base</span></div></div>")


def gauge(score: int) -> str:
    score = max(0, min(100, int(score)))
    C = 339.29
    off = C * (1 - score / 100)
    col = risk_color(score)
    return (f"<svg width='170' height='170' viewBox='0 0 120 120'>"
            f"<circle cx='60' cy='60' r='54' fill='none' stroke='#233062' stroke-width='9'/>"
            f"<circle cx='60' cy='60' r='54' fill='none' stroke='{col}' stroke-width='9' "
            f"stroke-linecap='round' stroke-dasharray='{C}' stroke-dashoffset='{off:.2f}' "
            f"transform='rotate(-90 60 60)'/>"
            f"<text x='60' y='62' text-anchor='middle' fill='#E8ECF8' font-size='30' font-weight='800'>{score}</text>"
            f"<text x='60' y='80' text-anchor='middle' fill='#8E9ABB' font-size='8'>RISK SCORE / 100</text></svg>")


def verdict_card(report) -> str:
    col = risk_color(report.risk_score)
    return (f"<div class='card center fadein'><div class='label'>Risk assessment</div>"
            f"{gauge(report.risk_score)}"
            f"<div class='verdict' style='color:{col}'>{esc(report.verdict)}</div></div>")


def summary_card(report, res, mode: str) -> str:
    age = res.get("domain_age")
    age_txt = f"Domain age: {int(age)} days" if age is not None else "Domain age: unknown"
    n = len(report.red_flags)
    badges = (f"<span class='badge b-info'>{esc(age_txt)}</span>"
              f"<span class='badge b-info'>{n} red flag{'s' if n != 1 else ''}</span>"
              f"<span class='badge b-info'>{esc(mode)}</span>")
    return (f"<div class='card fadein'><div class='label'>Assessment</div>"
            f"<div class='reason'>{esc(report.reasoning)}</div>{badges}</div>")


def flag_card(flag) -> str:
    sev = _sev(flag.severity)
    return (f"<div class='flag {sev} fadein'><div class='title'>"
            f"<span class='badge b-{sev}'>{esc(sev.upper())}</span>{esc(flag.flag)}</div>"
            f"<div class='ev mono'>{esc(flag.evidence)}</div></div>")


def todo_card(steps) -> str:
    rows = "".join(f"<div class='todo'><div class='box'></div><div>{esc(s)}</div></div>" for s in steps)
    return f"<div class='card fadein'><div class='label'>Next steps</div>{rows}</div>"


def step_tracker(current: int) -> str:
    rows = []
    for i, name in enumerate(STEPS, start=1):
        state = "done" if i < current else ("active" if i == current else "")
        rows.append(f"<div class='step {state}'><div class='dot'></div>{esc(name)}</div>")
    return f"<div class='card'><div class='label'>Analysis in progress</div>{''.join(rows)}</div>"


def trust_footer() -> str:
    return ("<div class='footer'>"
            "<span class='badge b-info'>Untrusted input sanitized</span>"
            "<span class='badge b-info'>No keys exposed to the browser</span>"
            "<span class='badge b-info'>Offers processed in memory, not stored</span>"
            "<span class='badge b-info'>Evidence-backed findings</span><br>"
            "Risk assessment only, not legal advice. Report scams: cybercrime.gov.in, helpline 1930.<br>"
            "Built for PromptWars x HackWiE</div>")
