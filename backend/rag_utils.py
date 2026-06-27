import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pickle

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DIM = 384

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model

def chunk_text(text: str, chunk_size=500, overlap=100):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def build_faiss_index(chunks: list[str]):
    model = get_embedding_model()
    embeddings = model.encode(chunks, show_progress_bar=False)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(VECTOR_DIM)
    index.add(embeddings)

    return index, embeddings

def save_index(index, chunks, path: Path):
    with open(path / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)
    faiss.write_index(index, str(path / "index.faiss"))

def load_index(path: Path):
    index = faiss.read_index(str(path / "index.faiss"))
    with open(path / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

def retrieve(query: str, index, chunks, top_k=5):
    model = get_embedding_model()
    q_emb = model.encode([query]).astype("float32")
    distances, indices = index.search(q_emb, top_k)
    return [chunks[i] for i in indices[0]]
