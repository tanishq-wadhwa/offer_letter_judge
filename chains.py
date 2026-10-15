"""LLM chains: extractor, analyst, critic - all with structured (Pydantic) output."""
import time

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from llm import get_llm
from schemas import OfferInfo, RiskReport

FMT = "\n\n{format_instructions}"


def run_structured(system: str, human: str, schema, inputs: dict, kind: str = "big", tries: int = 2):
    """Try native structured output (with retry); fall back to a JSON parser."""
    llm = get_llm(kind)
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human + FMT)])
    last = None
    for _ in range(tries):
        try:
            chain = prompt.partial(format_instructions="") | llm.with_structured_output(schema)
            res = chain.invoke(inputs)
            if res is not None:
                return res
        except Exception as e:
            last = e
            time.sleep(4 if "429" in str(e) or "rate" in str(e).lower() else 1)
    try:
        parser = PydanticOutputParser(pydantic_object=schema)
        chain = prompt.partial(format_instructions=parser.get_format_instructions()) | llm | parser
        return chain.invoke(inputs)
    except Exception as e:
        raise RuntimeError(f"The AI model failed to return a valid answer. ({last or e})")


EXTRACT_SYS = ("You extract structured fields from a job/internship offer. Copy values exactly as "
               "written. Use null when a field is absent. Never guess. contact_channel must be one of: "
               "email, whatsapp, telegram, other.")


def extract_offer(offer_text: str) -> OfferInfo:
    return run_structured(EXTRACT_SYS, "Offer text:\n{offer_text}", OfferInfo,
                          {"offer_text": offer_text[:3000]}, kind="small")


ANALYST_SYS = """You are a careful fraud analyst helping students judge internship/job offers.
Produce a risk assessment, never a claim of certainty.
Rules:
- Every red flag MUST have evidence: a short quote from the offer, a URL from the web results, or a knowledge base file name.
- Never invent URLs, registration numbers, or facts about the company. Do not accuse a named company of fraud without evidence.
- If web evidence is missing or failed, say so in reasoning and keep the score moderate unless the offer itself shows strong red flags.
- Score guide: any request for money = very high risk (75+). Personal email only = medium. Official-domain email, a real interview process and no fees = low risk (under 30).
- Include the rule-check flags that are supported, and add other red flags you notice in the offer text.
- reply_to_recruiter: polite, 4-6 lines, ask for official company email, offer letter on letterhead, interview schedule, and confirmation that no fee is required. Sign off as 'Candidate'.
- next_steps: 3-5 concrete actions for the student.
- verdict must be one of: Likely Genuine, Suspicious, Likely Scam."""

ANALYST_HUMAN = """OFFER TEXT:
{offer_text}

EXTRACTED FIELDS:
{info}

RULE-CHECK FLAGS:
{rule_flags}

DOMAIN AGE (days): {domain_age}

WEB SEARCH RESULTS:
{search_evidence}

OFFICIAL SITE / SCRAPED TEXT:
{site_text}

KNOWLEDGE BASE (scam patterns):
{kb_context}"""


def analyze(inputs: dict) -> RiskReport:
    return run_structured(ANALYST_SYS, ANALYST_HUMAN, RiskReport, inputs, kind="big")


CRITIC_SYS = """You are a strict verifier. You receive a draft risk report and all the evidence the analyst had.
- Remove any red flag whose evidence is not actually present in the inputs (offer text, rule flags, web results, scraped text, knowledge base file names).
- Keep supported flags. Do not add new unsupported claims. Never invent URLs.
- Adjust risk_score to match the remaining evidence (payment demand = 75+; no flags = under 30).
- Keep reply_to_recruiter and next_steps unless they contain unsupported accusations.
- Keep wording as a risk assessment, not certainty."""

CRITIC_HUMAN = """DRAFT REPORT (JSON):
{draft}

OFFER TEXT:
{offer_text}

RULE-CHECK FLAGS:
{rule_flags}

WEB SEARCH RESULTS:
{search_evidence}

SCRAPED TEXT:
{site_text}

KNOWLEDGE BASE FILE NAMES:
{kb_sources}"""


def verify(inputs: dict) -> RiskReport:
    return run_structured(CRITIC_SYS, CRITIC_HUMAN, RiskReport, inputs, kind="big")
