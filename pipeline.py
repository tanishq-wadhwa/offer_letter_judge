"""Orchestrates the Offer Shield pipeline."""
from typing import Callable, Optional

from chains import analyze, extract_offer, verify
from checks import FREE_EMAIL, run_checks
from rag.retriever import retrieve
from schemas import OfferInfo, RiskReport, verdict_for
from tools import (domain_age_days, extract_urls, get_domain, pick_official_site,
                   scrape_url, web_search)


def _noop(msg: str):
    print(msg)


def _finalize(report: RiskReport, rule_flags) -> RiskReport:
    """Enforce consistency: evidence on every flag, score floors from hard rules, verdict mapping."""
    report.red_flags = [f for f in report.red_flags if f.evidence and f.evidence.strip()]
    score = max(0, min(100, int(report.risk_score)))
    sev = {s for _, s, _ in rule_flags}
    if any("money" in f.lower() for f, _, _ in rule_flags):
        score = max(score, 75)
    elif "high" in sev:
        score = max(score, 50)
    report.risk_score = score
    report.verdict = verdict_for(score)
    return report


def analyze_offer(offer_text: str, progress: Optional[Callable[[str], None]] = None) -> dict:
    log = progress or _noop
    offer_text = (offer_text or "").strip()
    notes = []

    log("Step 1/7: Extracting offer details...")
    try:
        info = extract_offer(offer_text)
    except Exception as e:
        info = OfferInfo()
        notes.append(f"Extraction failed ({e}); relied on rules and text.")

    company = (info.company_name or "").strip()
    email_dom = get_domain(info.recruiter_email) if info.recruiter_email else None
    site_url = info.company_website
    site_dom = get_domain(site_url) if site_url else None

    search_text, site_text = "", ""
    domain_age = None

    if company:
        log("Step 2/7: Searching the web for the company...")
        try:
            scam_q = web_search(f"{company} internship job offer scam reviews", 4)
            off_q = web_search(f"{company} official website careers", 4)
            search_text = f"[Scam/review search]\n{scam_q}\n\n[Official site search]\n{off_q}"
        except Exception as e:
            notes.append(f"Web search failed: {e}")
        if not site_url:
            site_url = pick_official_site(company, off_q if search_text else "")
            site_dom = get_domain(site_url) if site_url else None

        log("Step 3/7: Reading the company's website...")
        if site_url:
            site_text = f"[{site_url}]\n{scrape_url(site_url if '://' in site_url else 'http://' + site_url)}"
        else:
            notes.append("Could not identify an official website for this company.")
            urls = extract_urls(search_text)
            if urls:
                site_text = f"[{urls[0]}]\n{scrape_url(urls[0], 1500)}"
    else:
        log("Step 2/7: No company name found - skipping web search.")
        log("Step 3/7: Skipped website reading.")
        notes.append("No company name detected, so web evidence was unavailable.")

    log("Step 4/7: Checking domain age...")
    dom = site_dom or (email_dom if email_dom and email_dom not in FREE_EMAIL else None)
    if dom:
        domain_age = domain_age_days(dom)

    log("Step 5/7: Running rule checks...")
    rule_flags = run_checks(offer_text, info, domain_age)

    log("Step 6/7: Retrieving scam patterns from the knowledge base (RAG)...")
    query = " ".join(f for f, _, _ in rule_flags) + " " + offer_text[:500]
    try:
        kb_chunks = retrieve(query, k=4)
    except Exception as e:
        kb_chunks = []
        notes.append(f"Knowledge base retrieval failed: {e}")
    kb_context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in kb_chunks) or "None"

    rule_text = "\n".join(f"- [{s}] {f} | evidence: {e}" for f, s, e in rule_flags) or "None"
    inputs = {
        "offer_text": offer_text[:3000],
        "info": info.model_dump_json(),
        "rule_flags": rule_text,
        "domain_age": domain_age if domain_age is not None else "unknown",
        "search_evidence": (search_text or "Unavailable")[:3500],
        "site_text": (site_text or "Unavailable")[:3000],
        "kb_context": kb_context[:3000],
    }

    log("Step 7/7: Analyzing and verifying with AI...")
    draft = analyze(inputs)
    try:
        final = verify({**inputs, "draft": draft.model_dump_json(),
                        "kb_sources": ", ".join(sorted({c["source"] for c in kb_chunks})) or "None"})
    except Exception as e:
        final = draft
        notes.append(f"Verifier step failed ({e}); showing the draft report.")
    final = _finalize(final, rule_flags)

    return {
        "info": info, "rule_flags": rule_flags, "search_results": search_text,
        "site_text": site_text, "domain_age": domain_age, "kb_chunks": kb_chunks,
        "draft": draft, "report": final, "notes": notes,
    }
