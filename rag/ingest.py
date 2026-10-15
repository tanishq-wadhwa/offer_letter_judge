"""Load knowledge_base/*.md -> split -> embed -> store in Chroma. Run: python -m rag.ingest"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "knowledge_base"
DB_DIR = ROOT / "chroma_db"
COLLECTION = "scam_kb"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_and_split():
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    docs = []
    for p in sorted(KB_DIR.glob("*.md")):
        docs.append(Document(page_content=p.read_text(encoding="utf-8"),
                             metadata={"source": p.name}))
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
    return splitter.split_documents(docs)


def ingest():
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    chunks = load_and_split()
    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)
    emb = HuggingFaceEmbeddings(model_name=EMB_MODEL)
    Chroma.from_documents(chunks, emb, persist_directory=str(DB_DIR), collection_name=COLLECTION)
    print(f"Ingested {len(chunks)} chunks into {DB_DIR}")


if __name__ == "__main__":
    ingest()
