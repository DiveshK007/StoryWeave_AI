import re
import os
import json
import pickle
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import numpy as np
import faiss
from pypdf import PdfReader
import tiktoken
from sentence_transformers import SentenceTransformer
from joblib import Memory
from .settings import settings
from .logger import logger

# Initialize Sentence Transformer model
_model: Optional[SentenceTransformer] = None

def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the Sentence Transformer model."""
    global _model
    if _model is None:
        logger.info("Loading Sentence Transformer model: all-MiniLM-L6-v2")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully")
    return _model

# Token counter for chunk sizing
_encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(_encoding.encode(text))


class EnhancedRetrieval:
    """Enhanced retrieval system with Sentence Transformers embeddings and semantic chunking."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: Optional[str] = None):
        """
        Initialize enhanced retrieval system.
        
        Args:
            model_name: Name of the Sentence Transformer model
            cache_dir: Directory for caching embeddings (None = no caching)
        """
        self.model_name = model_name
        self.model = get_embedding_model()
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # FAISS index (using L2 distance)
        self.index: Optional[faiss.IndexFlatL2] = None
        
        # Store chunks and metadata
        self.chunks: List[str] = []
        self.chunk_metadata: List[Dict[str, Any]] = []
        
        # Cache for embeddings
        self.cache_dir = cache_dir
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            self.memory = Memory(cache_dir, verbose=0)
            self._get_cached_embedding = self.memory.cache(self._compute_embedding)
        else:
            self._get_cached_embedding = self._compute_embedding
        
        # Paths for persistence
        self.index_path = Path(settings.INDEX_DIR) / "faiss.index"
        self.chunks_path = Path(settings.INDEX_DIR) / "chunks.json"
        self.metadata_path = Path(settings.INDEX_DIR) / "metadata.json"
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for a single text (for caching)."""
        return self.model.encode(text, convert_to_numpy=True)
    
    def _split_by_markdown_headers(self, text: str) -> List[Tuple[str, str]]:
        """
        Split text by markdown headers, preserving header context.
        
        Returns:
            List of (heading, content) tuples
        """
        sections = []
        
        # Pattern to match markdown headers (# Header)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        
        lines = text.split('\n')
        current_heading = ""
        current_content = []
        
        for line in lines:
            match = re.match(header_pattern, line)
            if match:
                # Save previous section
                if current_content:
                    sections.append((current_heading, '\n'.join(current_content)))
                
                # Start new section
                current_heading = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_content:
            sections.append((current_heading, '\n'.join(current_content)))
        
        # If no headers found, return entire text with empty heading
        if not sections:
            sections.append(("", text))
        
        return sections
    
    def _split_semantic(
        self,
        text: str,
        min_tokens: int = 100,
        max_tokens: int = 500,
        overlap_tokens: int = 50
    ) -> List[Tuple[str, str]]:
        """
        Split text with semantic awareness, respecting markdown headers and paragraphs.
        
        Args:
            text: Text to split
            min_tokens: Minimum tokens per chunk
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap tokens between chunks
            
        Returns:
            List of (heading, chunk_text) tuples
        """
        chunks = []
        
        # First, split by markdown headers
        sections = self._split_by_markdown_headers(text)
        
        for heading, section_text in sections:
            section_tokens = count_tokens(section_text)
            
            # If section fits within max_tokens, keep it as-is
            if section_tokens <= max_tokens:
                if section_tokens >= min_tokens or not chunks:  # Allow smaller first chunk
                    chunks.append((heading, section_text))
                elif chunks:  # Merge with previous chunk if too small
                    prev_heading, prev_text = chunks[-1]
                    chunks[-1] = (prev_heading, f"{prev_text}\n\n{section_text}")
                continue
            
            # Otherwise, split by paragraphs
            paragraphs = section_text.split('\n\n')
            current_chunk = []
            current_tokens = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                para_tokens = count_tokens(para)
                
                # If paragraph itself exceeds max, split by sentences
                if para_tokens > max_tokens:
                    # Save current chunk if any
                    if current_chunk and current_tokens >= min_tokens:
                        chunks.append((heading, '\n\n'.join(current_chunk)))
                        current_chunk = []
                        current_tokens = 0
                    
                    # Split paragraph by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        
                        sent_tokens = count_tokens(sentence)
                        
                        # If adding sentence exceeds max, save current chunk
                        if current_chunk and current_tokens + sent_tokens > max_tokens:
                            chunks.append((heading, '\n\n'.join(current_chunk)))
                            # Start new chunk with overlap
                            if current_chunk:
                                overlap_text = '\n\n'.join(current_chunk[-2:])  # Last 2 sentences
                                overlap_toks = count_tokens(overlap_text)
                                if overlap_toks <= overlap_tokens:
                                    current_chunk = [overlap_text, sentence]
                                    current_tokens = overlap_toks + sent_tokens
                                else:
                                    current_chunk = [sentence]
                                    current_tokens = sent_tokens
                            else:
                                current_chunk = [sentence]
                                current_tokens = sent_tokens
                        else:
                            current_chunk.append(sentence)
                            current_tokens += sent_tokens
                else:
                    # Check if adding paragraph would exceed max
                    if current_chunk and current_tokens + para_tokens > max_tokens:
                        chunks.append((heading, '\n\n'.join(current_chunk)))
                        # Start new chunk with overlap
                        if current_chunk:
                            overlap_text = '\n\n'.join(current_chunk[-1:])  # Last paragraph
                            overlap_toks = count_tokens(overlap_text)
                            if overlap_toks <= overlap_tokens:
                                current_chunk = [overlap_text, para]
                                current_tokens = overlap_toks + para_tokens
                            else:
                                current_chunk = [para]
                                current_tokens = para_tokens
                        else:
                            current_chunk = [para]
                            current_tokens = para_tokens
                    else:
                        current_chunk.append(para)
                        current_tokens += para_tokens
                
                # Save chunk if it meets minimum size
                if current_chunk and current_tokens >= min_tokens and current_tokens <= max_tokens:
                    chunks.append((heading, '\n\n'.join(current_chunk)))
                    current_chunk = []
                    current_tokens = 0
            
            # Add remaining content
            if current_chunk:
                chunks.append((heading, '\n\n'.join(current_chunk)))
        
        # Ensure we have at least one chunk
        if not chunks:
            chunks.append(("", text[:max_tokens * 4]))  # Fallback: first max_tokens*4 chars
        
        return chunks
    
    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]]) -> None:
        """
        Add documents to the retrieval system.
        
        Args:
            documents: List of document texts
            metadata: List of metadata dicts (one per document)
        """
        if len(documents) != len(metadata):
            raise ValueError(f"Documents ({len(documents)}) and metadata ({len(metadata)}) must have same length")
        
        all_chunks = []
        all_metadata = []
        
        for doc_text, doc_meta in zip(documents, metadata):
            # Extract metadata fields
            source_file = doc_meta.get('source_file', doc_meta.get('source', 'unknown'))
            
            # Split into chunks
            chunk_data = self._split_semantic(
                doc_text,
                min_tokens=100,
                max_tokens=500,
                overlap_tokens=50
            )
            
            for chunk_idx, (heading, chunk_text) in enumerate(chunk_data):
                all_chunks.append(chunk_text)
                
                # Create metadata for this chunk
                chunk_meta = {
                    'source_file': source_file,
                    'heading': heading,
                    'chunk_index': chunk_idx,
                    'char_count': len(chunk_text),
                    'token_count': count_tokens(chunk_text),
                    **{k: v for k, v in doc_meta.items() if k != 'source_file'}
                }
                all_metadata.append(chunk_meta)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
        embeddings = []
        for i, chunk in enumerate(all_chunks):
            if (i + 1) % 100 == 0:
                logger.debug(f"Embedded {i + 1}/{len(all_chunks)} chunks")
            emb = self._get_cached_embedding(chunk)
            embeddings.append(emb)
        
        embeddings_array = np.array(embeddings, dtype='float32')
        
        # Initialize or update FAISS index
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.chunks = []
            self.chunk_metadata = []
        
        # Normalize embeddings for cosine similarity (L2 normalization)
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Store chunks and metadata
        self.chunks.extend(all_chunks)
        self.chunk_metadata.extend(all_metadata)
        
        logger.info(f"Added {len(all_chunks)} chunks to index (total: {len(self.chunks)})")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of dicts with keys: text, metadata, score
        """
        if self.index is None or len(self.chunks) == 0:
            logger.warning("No index available for search")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        query_vector = np.array([query_embedding], dtype='float32')
        faiss.normalize_L2(query_vector)
        
        # Search
        k = min(top_k, len(self.chunks))
        distances, indices = self.index.search(query_vector, k)
        
        # Convert distances to similarity scores (L2 distance -> cosine similarity)
        # Since vectors are normalized, similarity = 1 - distance^2 / 2
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                # Convert L2 distance to similarity score (0-1, higher is better)
                similarity = max(0.0, 1.0 - (dist ** 2) / 2.0)
                
                results.append({
                    'text': self.chunks[idx],
                    'metadata': self.chunk_metadata[idx],
                    'score': float(similarity),
                    'distance': float(dist)
                })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.debug(f"Search returned {len(results)} results")
        return results
    
    def save_index(self, path: Optional[str] = None) -> None:
        """Save FAISS index, chunks, and metadata to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        index_path = Path(path) if path else self.index_path
        chunks_path = index_path.parent / "chunks.json"
        metadata_path = index_path.parent / "metadata.json"
        
        # Create directory if needed
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(index_path))
            
            # Save chunks as JSON
            with open(chunks_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
            
            # Save metadata as JSON
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved index to {index_path}, {len(self.chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}", exc_info=True)
            raise
    
    def load_index(self, path: Optional[str] = None) -> bool:
        """Load FAISS index, chunks, and metadata from disk."""
        index_path = Path(path) if path else self.index_path
        chunks_path = index_path.parent / "chunks.json"
        metadata_path = index_path.parent / "metadata.json"
        
        if not index_path.exists() or not chunks_path.exists() or not metadata_path.exists():
            logger.info("No saved index found")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load chunks
            with open(chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.chunk_metadata = json.load(f)
            
            logger.info(f"Loaded index from {index_path}, {len(self.chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {e}", exc_info=True)
            return False
    
    def _pdf_to_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(str(pdf_path))
            return '\n'.join([(p.extract_text() or '') for p in reader.pages])
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise ValueError(f"Failed to read PDF: {e}") from e
    
    def ingest_docs(self, paths: List[str], source_names: Optional[List[str]] = None) -> None:
        """
        Ingest documents from file paths.
        
        Args:
            paths: List of file paths to ingest
            source_names: Optional list of source names for each file
        """
        if not paths:
            raise ValueError("No files provided for ingestion")
        
        logger.info(f"Ingesting {len(paths)} file(s)")
        
        documents = []
        metadata_list = []
        
        for idx, p in enumerate(paths):
            pth = Path(p)
            if not pth.exists():
                logger.warning(f"File not found: {p}")
                continue
            
            source_name = source_names[idx] if source_names and idx < len(source_names) else pth.name
            
            try:
                if pth.suffix.lower() == '.pdf':
                    text = self._pdf_to_text(pth)
                else:
                    text = pth.read_text(encoding='utf-8', errors='ignore')
                
                if not text.strip():
                    logger.warning(f"Empty file: {p}")
                    continue
                
                documents.append(text)
                metadata_list.append({
                    'source_file': source_name,
                    'file_path': str(p)
                })
                
                logger.info(f"Loaded document: {pth.name} ({len(text)} chars)")
                
            except Exception as e:
                logger.error(f"Error processing file {p}: {e}", exc_info=True)
                continue
        
        if not documents:
            raise ValueError("No valid documents extracted from files")
        
        # Add documents to retrieval system
        self.add_documents(documents, metadata_list)
        
        # Save index
        self.save_index()


class VectorStore:
    """Legacy vector store wrapper for backward compatibility."""
    
    def __init__(self):
        self.enhanced = EnhancedRetrieval(cache_dir=str(Path(settings.INDEX_DIR) / "cache"))
        self.index = None  # Will be set when index is loaded
        self.chunks: List[str] = []
        self.chunk_metadata: List[Dict[str, Any]] = []
        self.index_path = Path(settings.INDEX_DIR) / "faiss.index"
        self.chunks_path = Path(settings.INDEX_DIR) / "chunks.json"
        
    def _split_semantic(self, text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
        """Legacy method - delegates to enhanced retrieval."""
        # Convert to (heading, text) format and extract just text
        chunks = self.enhanced._split_semantic(text, min_tokens=100, max_tokens=500, overlap_tokens=50)
        return [text for _, text in chunks]
    
    def _split_simple(self, text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
        """Simple character-based splitting as fallback."""
        out, i = [], 0
        while i < len(text):
            out.append(text[i:i+chunk_size])
            i += max(1, chunk_size - overlap)
        return out

    def _pdf_to_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        return self.enhanced._pdf_to_text(pdf_path)

    def ingest_docs(self, paths: List[str], embed_url: str = None, source_names: List[str] = None):
        """
        Ingest documents (legacy interface).
        
        Args:
            paths: List of file paths to ingest
            embed_url: Deprecated - kept for backward compatibility
            source_names: Optional list of source names
        """
        if embed_url:
            logger.warning("embed_url parameter is deprecated, using Sentence Transformers")
        
        self.enhanced.ingest_docs(paths, source_names)
        
        # Update legacy attributes
        self.index = self.enhanced.index
        self.chunks = self.enhanced.chunks
        self.chunk_metadata = self.enhanced.chunk_metadata

    def search(self, query: str, embed_url: str = None, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Search the vector store (legacy interface).
        
        Args:
            query: Search query
            embed_url: Deprecated - kept for backward compatibility
            top_k: Number of results to return
            
        Returns:
            List of (chunk_index, similarity_score) tuples
        """
        if embed_url:
            logger.warning("embed_url parameter is deprecated, using Sentence Transformers")
        
        results = self.enhanced.search(query, top_k)
        
        # Convert to legacy format: List[Tuple[int, float]]
        # Find the actual index in self.chunks by matching text
        legacy_results = []
        for result in results:
            # Find the index of this chunk in self.chunks
            chunk_text = result['text']
            try:
                chunk_idx = self.chunks.index(chunk_text)
            except ValueError:
                # If not found, use the chunk_index from metadata as fallback
                chunk_idx = result['metadata'].get('chunk_index', len(legacy_results))
            
            # Use score as similarity (0-1 range)
            legacy_results.append((chunk_idx, result['score']))
        
        return legacy_results

    def save_index(self):
        """Save index (legacy interface)."""
        self.enhanced.save_index()
        self.index = self.enhanced.index

    def load_index(self) -> bool:
        """Load index (legacy interface)."""
        loaded = self.enhanced.load_index()
        if loaded:
            self.index = self.enhanced.index
            self.chunks = self.enhanced.chunks
            self.chunk_metadata = self.enhanced.chunk_metadata
        return loaded


# Global instance for backward compatibility
store = VectorStore()

# Also export enhanced retrieval for new code
enhanced_store = EnhancedRetrieval(cache_dir=str(Path(settings.INDEX_DIR) / "cache"))
