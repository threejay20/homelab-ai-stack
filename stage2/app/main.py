from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.chains import RetrievalQA
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os
import tempfile
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security
import secrets


# ─────────────────────────────────────────
# API Key Authentication
# All endpoints except /health and /
# require a valid X-API-Key header
# ─────────────────────────────────────────
API_KEY = os.getenv("API_KEY", "")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not API_KEY:
        return  # No key configured — open access (dev mode)
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key"
        )
    return api_key

app = FastAPI(
    title="Homelab RAG API",
    description="Local RAG pipeline — LangChain + Qdrant + Ollama",
    version="1.0.0"
)

# ─────────────────────────────────────────
# Configuration from environment variables
# ─────────────────────────────────────────
QDRANT_HOST     = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT     = int(os.getenv("QDRANT_PORT", 6333))
OLLAMA_HOST     = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_PORT     = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "phi3:mini")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "homelab_docs")
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP   = int(os.getenv("CHUNK_OVERLAP", 50))

# ─────────────────────────────────────────
# Embedding model
# Converts text into vectors for storage and search
# Runs locally — no API call, no cost
# ─────────────────────────────────────────
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

# ─────────────────────────────────────────
# Qdrant client
# Direct connection to your vector database
# ─────────────────────────────────────────
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# ─────────────────────────────────────────
# LLM — points to Ollama in Stage 1
# Your RAG app reuses the LLM you already have running
# ─────────────────────────────────────────
llm = OllamaLLM(
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
    model=OLLAMA_MODEL,
    temperature=0.1
)

# ─────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    collection: str = COLLECTION_NAME

class QueryResponse(BaseModel):
    question: str
    answer: str
    collection: str

class IngestResponse(BaseModel):
    message: str
    chunks_stored: int
    collection: str

# ─────────────────────────────────────────
# Helper — ensure collection exists in Qdrant
# Creates it if not, skips if already there
# ─────────────────────────────────────────
def ensure_collection(collection_name: str):
    existing = [c.name for c in qdrant_client.get_collections().collections]
    if collection_name not in existing:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,        # all-MiniLM-L6-v2 outputs 384-dimensional vectors
                distance=Distance.COSINE
            )
        )

# ─────────────────────────────────────────
# Helper — split and embed documents
# This is the core of the ingestion pipeline
# ─────────────────────────────────────────
def ingest_documents(file_path: str, collection_name: str) -> int:
    # Load document based on file type
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    documents = loader.load()

    # Split into chunks
    # RecursiveCharacterTextSplitter tries to split on paragraphs,
    # then sentences, then words — preserving semantic meaning
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)

    # Ensure collection exists
    ensure_collection(collection_name)

    # Embed and store in Qdrant
    Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        collection_name=collection_name,
    )

    return len(chunks)

# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Homelab RAG API",
        "status": "running",
        "model": OLLAMA_MODEL,
        "vector_db": f"{QDRANT_HOST}:{QDRANT_PORT}"
    }

@app.get("/health")
def health():
    # Check Qdrant connectivity
    try:
        qdrant_client.get_collections()
        qdrant_status = "ok"
    except Exception as e:
        qdrant_status = f"error: {str(e)}"

    # Check Ollama connectivity
    try:
        llm.invoke("ping")
        ollama_status = "ok"
    except Exception as e:
        ollama_status = f"error: {str(e)}"

    return {
        "qdrant": qdrant_status,
        "ollama": ollama_status,
        "model": OLLAMA_MODEL
    }

@app.post("/ingest", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
async def ingest(file: UploadFile = File(...)):
    """
    Upload a document (PDF or TXT) and ingest it into the vector database.
    The document is chunked, embedded, and stored in Qdrant.
    """
    # Validate file type
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files supported"
        )

    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=os.path.splitext(file.filename)[1]
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        chunks_stored = ingest_documents(tmp_path, COLLECTION_NAME)
    finally:
        os.unlink(tmp_path)  # Clean up temp file

    return IngestResponse(
        message=f"Successfully ingested {file.filename}",
        chunks_stored=chunks_stored,
        collection=COLLECTION_NAME
    )

@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
def query(request: QueryRequest):
    """
    Ask a question. The RAG pipeline retrieves relevant document chunks
    from Qdrant and passes them as context to the LLM for grounded answers.
    """
    # Connect to existing Qdrant collection
    vectorstore = Qdrant(
        client=qdrant_client,
        collection_name=request.collection,
        embeddings=embeddings,
    )

    # Build retrieval chain
    # k=3 means retrieve the 3 most relevant chunks
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
    )

    try:
        result = qa_chain.invoke({"query": request.question})
        answer = result.get("result", "No answer generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(
        question=request.question,
        answer=answer,
        collection=request.collection
    )

@app.get("/collections", dependencies=[Depends(verify_api_key)])
def list_collections():
    """List all collections in Qdrant with document counts."""
    collections = qdrant_client.get_collections().collections
    result = []
    for col in collections:
        info = qdrant_client.get_collection(col.name)
        result.append({
            "name": col.name,
            "vectors_count": info.vectors_count
        })
    return {"collections": result}
