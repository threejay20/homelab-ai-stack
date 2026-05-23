import os
import sys
from pathlib import Path
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
QDRANT_HOST     = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT     = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "homelab_docs")
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP   = int(os.getenv("CHUNK_OVERLAP", 50))
DOCS_PATH       = os.getenv("DOCS_PATH", "./docs")

# ─────────────────────────────────────────
# Initialize components
# ─────────────────────────────────────────
print("Loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# ─────────────────────────────────────────
# Ensure collection exists
# ─────────────────────────────────────────
def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        print(f"Creating collection: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")

# ─────────────────────────────────────────
# Ingest a single file
# ─────────────────────────────────────────
def ingest_file(file_path: str) -> int:
    print(f"  Loading: {file_path}")

    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        print(f"  Skipping unsupported file type: {file_path}")
        return 0

    documents = loader.load()
    print(f"  Pages/sections loaded: {len(documents)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)
    print(f"  Chunks created: {len(chunks)}")

    Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        collection_name=COLLECTION_NAME,
    )

    print(f"  Stored {len(chunks)} vectors in Qdrant")
    return len(chunks)

# ─────────────────────────────────────────
# Main — scan docs folder and ingest all files
# ─────────────────────────────────────────
def main():
    docs_path = Path(DOCS_PATH)

    if not docs_path.exists():
        print(f"Docs folder not found: {DOCS_PATH}")
        sys.exit(1)

    files = list(docs_path.glob("*.pdf")) + list(docs_path.glob("*.txt"))

    if not files:
        print(f"No PDF or TXT files found in {DOCS_PATH}")
        sys.exit(0)

    print(f"\nFound {len(files)} file(s) to ingest")
    ensure_collection()

    total_chunks = 0
    for f in files:
        print(f"\nIngesting: {f.name}")
        chunks = ingest_file(str(f))
        total_chunks += chunks

    print(f"\nDone. Total vectors stored: {total_chunks}")
    print(f"Collection: {COLLECTION_NAME}")

if __name__ == "__main__":
    main()
