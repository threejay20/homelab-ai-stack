from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.chains import RetrievalQA
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import os
import tempfile
import time
import httpx as _httpx

app = FastAPI(title="Homelab RAG API", description="Local RAG pipeline", version="1.0.0")

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "homelab_docs")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
EVIDENTLY_HOST = os.getenv("EVIDENTLY_HOST", "homelab-evidently")
EVIDENTLY_PORT = os.getenv("EVIDENTLY_PORT", "8050")

API_KEY = os.getenv("API_KEY", "")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not API_KEY:
        return
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key

REQUEST_COUNT = Counter("rag_requests_total", "Total RAG requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("rag_request_duration_seconds", "RAG request latency", ["endpoint"])
CHUNKS_INGESTED = Counter("rag_chunks_ingested_total", "Total document chunks ingested")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
llm = OllamaLLM(base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}", model=OLLAMA_MODEL, temperature=0.1)

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

def ensure_collection(collection_name: str):
    existing = [c.name for c in qdrant_client.get_collections().collections]
    if collection_name not in existing:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

def ingest_documents(file_path: str, collection_name: str) -> int:
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)
    ensure_collection(collection_name)
    Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        collection_name=collection_name,
    )
    return len(chunks)

def log_to_evidently(question: str, answer: str, collection: str):
    try:
        _httpx.post(
            f"http://{EVIDENTLY_HOST}:{EVIDENTLY_PORT}/log",
            json={"question": question, "answer": answer, "collection": collection},
            timeout=2.0
        )
    except Exception:
        pass

@app.get("/")
def root():
    return {"service": "Homelab RAG API", "status": "running", "model": OLLAMA_MODEL}

@app.get("/health")
def health():
    try:
        qdrant_client.get_collections()
        qdrant_status = "ok"
    except Exception as e:
        qdrant_status = f"error: {str(e)}"
    try:
        llm.invoke("ping")
        ollama_status = "ok"
    except Exception as e:
        ollama_status = f"error: {str(e)}"
    return {"qdrant": qdrant_status, "ollama": ollama_status, "model": OLLAMA_MODEL}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/ingest", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
async def ingest(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files supported")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        chunks_stored = ingest_documents(tmp_path, COLLECTION_NAME)
        CHUNKS_INGESTED.inc(chunks_stored)
        REQUEST_COUNT.labels(endpoint="ingest", status="success").inc()
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="ingest", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)
    return IngestResponse(
        message=f"Successfully ingested {file.filename}",
        chunks_stored=chunks_stored,
        collection=COLLECTION_NAME
    )

@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
def query(request: QueryRequest):
    start_time = time.time()
    try:
        vectorstore = Qdrant(
            client=qdrant_client,
            collection_name=request.collection,
            embeddings=embeddings,
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
        )
        result = qa_chain.invoke({"query": request.question})
        answer = result.get("result", "No answer generated")
        REQUEST_COUNT.labels(endpoint="query", status="success").inc()
        REQUEST_LATENCY.labels(endpoint="query").observe(time.time() - start_time)
        log_to_evidently(request.question, answer, request.collection)
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="query", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    return QueryResponse(question=request.question, answer=answer, collection=request.collection)

@app.get("/collections", dependencies=[Depends(verify_api_key)])
def list_collections():
    collections = qdrant_client.get_collections().collections
    result = []
    for col in collections:
        info = qdrant_client.get_collection(col.name)
        result.append({"name": col.name, "vectors_count": info.vectors_count})
    return {"collections": result}
