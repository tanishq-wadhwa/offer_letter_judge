"""Deterministic rule checks (no LLM). Returns a list of (flag, severity, evidence)."""
import re
from typing import List, Optional, Tuple

from schemas import OfferInfo
from tools import get_domain

FREE_EMAIL = {"gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com",
              "rediffmail.com", "proton.me", "protonmail.com", "icloud.com", "live.com"}

FEE_RE = re.compile(
    r"registration\s*(fee|fees|charge|charges|amount)|security\s*deposit|refundable|"
    r"training\s*(fee|fees|charge|charges)|processing\s*(fee|fees|charge|charges)|"
    r"(kit|onboarding|verification|id\s*card)\s*(fee|fees|charge|charges)|"
    r"laptop\s*(courier|charge|charges|fee)|\bupi\b|"
    r"pay\s+(rs\.?|inr|\u20b9)\s*\d|(rs\.?|inr|\u20b9)\s?\d[\d,]*\s*(as|for|towards)\s",
    re.I)
NEGATION_RE = re.compile(r"\b(no|never|not|without|don't|do not|doesn't|zero|free of)\b", re.I)
URGENCY_RE = re.compile(
    r"no interview|without (any )?interview|within 24 hours|within 48 hours|limited seats|"
    r"last chance|act now|urgent(ly)?|immediately confirm|confirm immediately|offer expires", re.I)
JOBY_RE = re.compile(r"data entry|typing job|copy[- ]paste|earn (up to )?\u20b9?\s?rs?\.?\s?\d|"
                     r"like and subscribe|task[- ]based", re.I)


def _is_negated(text: str, start: int) -> bool:
    return bool(NEGATION_RE.search(text[max(0, start - 40):start]))


def run_checks(offer_text: str, info: OfferInfo,
               domain_age: Optional[int] = None) -> List[Tuple[str, str, str]]:
    flags: List[Tuple[str, str, str]] = []
    text = offer_text or ""
    low = text.lower()

    # recruiter email
    email = (info.recruiter_email or "").strip()
    if not email:
        m = re.search(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", text)
        email = m.group(0) if m else ""
    email_dom = get_domain(email) if email else None
    site_dom = get_domain(info.company_website) if info.company_website else None

    if email_dom and email_dom in FREE_EMAIL:
        flags.append(("Recruiter uses a free personal email domain", "high",
                      f"Recruiter email: {email}"))
    elif email_dom and site_dom and not (email_dom == site_dom or email_dom.endswith("." + site_dom)):
        flags.append(("Recruiter email domain does not match company website", "high",
                      f"Email domain {email_dom} vs website {site_dom}"))

    # fee / payment demand (ignore negated mentions like "we never charge a registration fee")
    for m in FEE_RE.finditer(text):
        if not _is_negated(text, m.start()):
            ctx = text[max(0, m.start() - 30): m.end() + 40].replace("\n", " ").strip()
            flags.append(("Asks for money / payment from the candidate", "high", f'"{ctx}"'))
            break

    # contact channel
    chan = (info.contact_channel or "").lower()
    if chan in ("whatsapp", "telegram") or re.search(
            r"(whatsapp|telegram)[^.\n]{0,60}(only|interview|contact|message)", low):
        flags.append(("Communication happens over WhatsApp/Telegram", "medium",
                      "Offer directs the candidate to WhatsApp/Telegram"))

    # urgency / no interview
    m = URGENCY_RE.search(text)
    if m and not _is_negated(text, m.start()):
        flags.append(("Urgency or no-interview language", "medium", f'"{m.group(0)}"'))

    # too-good-to-be-true / gig style work
    m = JOBY_RE.search(text)
    if m:
        flags.append(("Typical scam-style task (data entry / easy earning)", "medium", f'"{m.group(0)}"'))

    # domain age
    if domain_age is not None and domain_age < 180:
        flags.append(("Company domain is very new", "high", f"Domain registered ~{domain_age} days ago"))

    return flags
