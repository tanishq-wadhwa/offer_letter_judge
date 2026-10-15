# 🛡️ Offer Shield - Fake Internship/Job Offer Detector

Paste an offer or upload a PDF and get a **risk score (0-100)**, evidence-backed red flags,
a polite verification reply for the recruiter, and next steps.

## How it works
1. Extractor (Groq GPT-OSS 20B, Pydantic structured output)
2. Deterministic rule checks (free email, fees, urgency, channel, domain age)
3. Tavily web search + site scraping + WHOIS domain age
4. RAG: Chroma + MiniLM embeddings + RecursiveCharacterTextSplitter over `knowledge_base/`
5. Analyst (Groq GPT-OSS 120B, structured output)
6. Critic removes any red flag without evidence

## Run it
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # Windows: copy .env.example .env   then add your keys
streamlit run app.py
```
You can also paste the API keys in the app sidebar instead of using `.env`.

Get keys: Groq at console.groq.com, Tavily at tavily.com (both have free tiers).

The first run downloads the embedding model (~90 MB) and builds `chroma_db/` automatically.
To prebuild it: `python -m rag.ingest`.

## Notes
- Output is a risk assessment, not a certain verdict or legal advice.
- If embeddings cannot load, the app falls back to keyword retrieval.
- If search/scraping/WHOIS fail, the app continues with reduced evidence.
- Never commit `.env`.
