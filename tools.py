"""Web search, scraping, and domain-age lookup. Every function fails soft."""
import concurrent.futures
import datetime
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

SOCIAL_SITES = ("linkedin.", "glassdoor.", "facebook.", "instagram.", "twitter.", "x.com",
                "youtube.", "reddit.", "quora.", "naukri.", "indeed.", "wikipedia.")


def web_search(query: str, max_results: int = 5) -> str:
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        return "Search unavailable: TAVILY_API_KEY not set."
    try:
        from tavily import TavilyClient
        res = TavilyClient(api_key=key).search(query=query, max_results=max_results)
        out = [f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
               for r in res.get("results", [])]
        return "\n----\n".join(out) if out else "No search results found."
    except Exception as e:
        return f"Search failed: {e}"


def scrape_url(url: str, limit: int = 3000) -> str:
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer"]):
            t.decompose()
        return soup.get_text(separator=" ", strip=True)[:limit]
    except Exception as e:
        return f"Could not scrape URL: {e}"


def get_domain(url_or_email: str):
    """Return bare domain from a URL or an email, or None."""
    if not url_or_email:
        return None
    s = url_or_email.strip().lower()
    if "@" in s and "://" not in s:
        return s.split("@")[-1].strip(" .>)")
    if "://" not in s:
        s = "http://" + s
    host = urlparse(s).netloc.split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    return host or None


def extract_urls(text: str):
    return re.findall(r"URL:\s*(\S+)", text or "")


def pick_official_site(company: str, search_text: str):
    """Pick the first search-result URL whose domain contains the company name."""
    if not company:
        return None
    slug = re.sub(r"[^a-z0-9]", "", company.lower().split()[0]) if company.split() else ""
    full = re.sub(r"[^a-z0-9]", "", company.lower())
    for u in extract_urls(search_text):
        d = get_domain(u) or ""
        if any(s in d for s in SOCIAL_SITES):
            continue
        if (slug and slug in d) or (full and full in d):
            return u
    return None


def domain_age_days(domain: str, timeout: int = 8):
    """Domain age in days, or None if unknown (WHOIS often fails)."""
    if not domain:
        return None

    def _lookup():
        import whois
        w = whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list):
            created = created[0]
        if not created:
            return None
        now = datetime.datetime.now(created.tzinfo) if created.tzinfo else datetime.datetime.now()
        return (now - created).days

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(_lookup).result(timeout=timeout)
    except Exception:
        return None
