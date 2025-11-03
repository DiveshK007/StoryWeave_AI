from typing import List, Tuple
from pathlib import Path
import numpy as np
import faiss
from pypdf import PdfReader
from .nim_client import embed_text

class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks: List[str] = []

    def _split(self, text: str, chunk=600, overlap=80):
        out, i = [], 0
        while i < len(text):
            out.append(text[i:i+chunk])
            i += max(1, chunk - overlap)
        return out

    def _pdf_to_text(self, pdf_path: Path) -> str:
        reader = PdfReader(str(pdf_path))
        return '\n'.join([(p.extract_text() or '') for p in reader.pages])

    def ingest_docs(self, paths: List[str], embed_url: str):
        all_chunks = []
        for p in paths:
            pth = Path(p)
            if pth.suffix.lower() == '.pdf':
                t = self._pdf_to_text(pth)
            else:
                t = pth.read_text(encoding='utf-8', errors='ignore')
            all_chunks += self._split(t)
        self.chunks = all_chunks
        embs = embed_text(all_chunks, embed_url)
        import numpy as _np
        X = _np.array([e['embedding'] for e in embs], dtype='float32')
        self.index = faiss.IndexFlatIP(X.shape[1])
        faiss.normalize_L2(X)
        self.index.add(X)

    def search(self, query: str, embed_url: str, top_k=5) -> List[Tuple[int, float]]:
        q = embed_text([query], embed_url)[0]['embedding']
        q = np.asarray([q], dtype='float32')
        faiss.normalize_L2(q)
        D, I = self.index.search(q, top_k)
        return list(zip(I[0].tolist(), D[0].tolist()))

store = VectorStore()
