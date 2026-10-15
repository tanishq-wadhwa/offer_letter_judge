"""Retriever over the scam knowledge base.
Primary: Chroma + MiniLM embeddings. Fallback: simple keyword overlap (if embeddings can't load)."""
import re
from typing import Dict, List

from rag.ingest import COLLECTION, DB_DIR, EMB_MODEL, load_and_split

_state = {"mode": None, "vs": None, "chunks": None}


def _init():
    if _state["mode"]:
        return
    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        emb = HuggingFaceEmbeddings(model_name=EMB_MODEL)
        if not (DB_DIR.exists() and any(DB_DIR.iterdir())):
            from rag.ingest import ingest
            ingest()
        _state["vs"] = Chroma(persist_directory=str(DB_DIR), embedding_function=emb,
                              collection_name=COLLECTION)
        _state["mode"] = "Chroma vector search (MiniLM embeddings)"
    except Exception:
        _state["chunks"] = load_and_split()
        _state["mode"] = "Keyword fallback (embeddings unavailable)"


def retrieval_mode() -> str:
    _init()
    return _state["mode"]


def _tokens(s: str):
    return set(re.findall(r"[a-z0-9]{3,}", s.lower()))


def retrieve(query: str, k: int = 4) -> List[Dict[str, str]]:
    _init()
    if _state["vs"] is not None:
        try:
            docs = _state["vs"].as_retriever(search_kwargs={"k": k}).invoke(query)
            return [{"source": d.metadata.get("source", "kb"), "text": d.page_content} for d in docs]
        except Exception:
            _state["chunks"] = load_and_split()
    q = _tokens(query)
    scored = sorted(_state["chunks"] or load_and_split(),
                    key=lambda d: len(q & _tokens(d.page_content)), reverse=True)[:k]
    return [{"source": d.metadata.get("source", "kb"), "text": d.page_content} for d in scored]
