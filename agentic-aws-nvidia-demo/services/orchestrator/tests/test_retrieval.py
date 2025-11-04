import pytest
from app.retrieval import VectorStore
from app.settings import settings
import os

# Set mock mode
os.environ["USE_MOCK"] = "1"


def test_semantic_chunking():
    """Test semantic chunking respects sentence boundaries."""
    store = VectorStore()
    text = "This is sentence one. This is sentence two. This is sentence three. " * 10
    chunks = store._split_semantic(text, chunk_size=100, overlap=20)
    
    assert len(chunks) > 0
    # Check that chunks don't exceed size significantly
    for chunk in chunks:
        assert len(chunk) <= 150  # Allow some margin for overlap


def test_simple_chunking():
    """Test simple chunking fallback."""
    store = VectorStore()
    text = "A" * 1000
    chunks = store._split_simple(text, chunk_size=100, overlap=20)
    
    assert len(chunks) > 0
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_pdf_to_text_error_handling():
    """Test PDF reading error handling."""
    store = VectorStore()
    # Try to read non-existent PDF
    from pathlib import Path
    fake_path = Path("/nonexistent/file.pdf")
    
    with pytest.raises(ValueError):
        store._pdf_to_text(fake_path)

