"""Offer Shield - professional Streamlit frontend. Run: streamlit run app.py
API keys are read from .env by the backend. The UI never asks for, shows, or logs any key."""
import logging
import os
import re
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env.example")

st.set_page_config(page_title="Offer Shield", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")

from ui import (CSS, STEPS, esc, flag_card, hero, step_tracker, summary_card,  # noqa: E402
                todo_card, topbar, trust_footer, verdict_card)

log = logging.getLogger("offer_shield")
SAMPLES = Path(__file__).resolve().parent / "samples"
MAX_CHARS = 6000
MAX_PDF_PAGES = 10
COOLDOWN_SECONDS = 3
CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean(text: str) -> str:
    return CTRL_RE.sub("", text or "").strip()


def load_sample(name: str):
    st.session_state["offer_text"] = (SAMPLES / name).read_text(encoding="utf-8")[:MAX_CHARS]
    st.session_state["result"] = None


def read_pdf(file) -> str:
    from pypdf import PdfReader
    pages = PdfReader(file).pages[:MAX_PDF_PAGES]
    return clean("\n".join((p.extract_text() or "") for p in pages))


st.markdown(CSS, unsafe_allow_html=True)
st.markdown(topbar() + hero(), unsafe_allow_html=True)

if "result" not in st.session_state:
    st.session_state["result"] = None

# ---------------- Input card ----------------
with st.container(border=True):
    b1, b2, _ = st.columns([1, 1, 3])
    b1.button("Load scam sample", on_click=load_sample, args=("scam_offer.txt",), use_container_width=True)
    b2.button("Load real sample", on_click=load_sample, args=("real_offer.txt",), use_container_width=True)
    offer_text = st.text_area("Offer message or email", key="offer_text", height=230, max_chars=MAX_CHARS,
                              placeholder="Paste the internship or job offer here...",
                              label_visibility="collapsed")
    st.caption(f"Up to {MAX_CHARS} characters. Offers are processed in memory and not stored.")
    pdf = st.file_uploader("Or upload the offer as a PDF (max 5 MB)", type=["pdf"])
    analyze_clicked = st.button("🔍 Analyze offer", type="primary", use_container_width=True)

pdf_text = ""
if pdf is not None:
    try:
        pdf_text = read_pdf(pdf)
        if not pdf_text:
            st.warning("No readable text found in this PDF (it may be a scanned image). Please paste the text instead.")
    except Exception:
        st.warning("This PDF could not be read. Please paste the text instead.")

# ---------------- Run analysis ----------------
tracker = st.empty()


def on_progress(msg: str):
    try:
        n = int(str(msg).split("Step ")[1].split("/")[0])
    except Exception:
        return
    tracker.markdown(step_tracker(n), unsafe_allow_html=True)


if analyze_clicked:
    text = clean(offer_text)[:MAX_CHARS] or pdf_text[:MAX_CHARS]
    now = time.time()
    if now - st.session_state.get("last_run", 0) < COOLDOWN_SECONDS:
        st.warning("Please wait a few seconds before running another analysis.")
    elif not text:
        st.warning("Please paste an offer or upload a PDF first.")
    elif not os.environ.get("GROQ_API_KEY"):
        st.error("Service is not configured. Please contact the administrator.")
    else:
        st.session_state["last_run"] = now
        st.session_state["result"] = None
        on_progress("Step 1/7")
        try:
            from pipeline import analyze_offer
            st.session_state["result"] = analyze_offer(text, progress=on_progress)
        except Exception as e:
            log.error("Analysis failed: %s", type(e).__name__)  # type only, never keys or content
            st.error("Could not complete the analysis. Please try again in a moment.")
        tracker.empty()

# ---------------- Results ----------------
res = st.session_state.get("result")
if res:
    rep = res["report"]
    try:
        from rag.retriever import retrieval_mode
        mode = retrieval_mode().split(" (")[0]
    except Exception:
        mode = "Knowledge base"

    c1, c2 = st.columns([1, 2])
    c1.markdown(verdict_card(rep), unsafe_allow_html=True)
    c2.markdown(summary_card(rep, res, mode), unsafe_allow_html=True)

    for n in res.get("notes", []):
        st.markdown(f"<div class='notice'>{esc(n)}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>🚩 Red flags</div>", unsafe_allow_html=True)
    if rep.red_flags:
        for f in rep.red_flags:
            st.markdown(flag_card(f), unsafe_allow_html=True)
    else:
        st.success("No evidence-backed red flags were found.")

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("<div class='card'><div class='label'>Reply to send the recruiter</div>"
                    "<div style='color:#8E9ABB;font-size:13px'>Copy and send this to ask for proof of legitimacy.</div></div>",
                    unsafe_allow_html=True)
        st.code(rep.reply_to_recruiter, language=None)
    with r2:
        st.markdown(todo_card(rep.next_steps), unsafe_allow_html=True)

    st.markdown("<div class='section-title'>🔎 Evidence</div>", unsafe_allow_html=True)
    st.markdown("<div class='notice'>Untrusted content (offer text, web pages) is treated as data, "
                "not instructions.</div>", unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["Rule checks", "Web results", "Website",
                                  "Knowledge base (RAG)", "Extracted details"])
    with t1:
        if res["rule_flags"]:
            for fl, sev, ev in res["rule_flags"]:
                st.markdown(f"<div class='flag {esc(sev) if sev in ('high','medium','low') else 'low'}'>"
                            f"<div class='title'>{esc(fl)}</div><div class='ev mono'>{esc(ev)}</div></div>",
                            unsafe_allow_html=True)
        else:
            st.write("No rule checks triggered.")
    with t2:
        st.text(res["search_results"] or "Unavailable")
    with t3:
        st.text(res["site_text"] or "Unavailable")
    with t4:
        for c in res["kb_chunks"]:
            st.markdown(f"<span class='badge b-info'>{esc(c['source'])}</span>", unsafe_allow_html=True)
            st.text(c["text"])
        if not res["kb_chunks"]:
            st.write("No knowledge base chunks retrieved.")
    with t5:
        st.json(res["info"].model_dump())
else:
    st.markdown("<div style='text-align:center;color:#8E9ABB;margin-top:14px'>"
                "Try a sample offer to see how it works.</div>", unsafe_allow_html=True)

st.markdown(trust_footer(), unsafe_allow_html=True)
