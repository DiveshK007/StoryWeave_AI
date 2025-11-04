import pytest
import os
from app.nim_client import call_llm, embed_text

# Set mock mode
os.environ["USE_MOCK"] = "1"


def test_call_llm_mock():
    """Test LLM call with mock mode."""
    result = call_llm("test prompt", "http://fake-url", 100)
    assert isinstance(result, str)
    assert len(result) > 0


def test_embed_text_mock():
    """Test embedding generation with mock mode."""
    chunks = ["test chunk 1", "test chunk 2"]
    result = embed_text(chunks, "http://fake-url")
    
    assert len(result) == len(chunks)
    assert all("embedding" in r for r in result)
    assert all(len(r["embedding"]) > 0 for r in result)


def test_embed_text_empty():
    """Test embedding with empty chunks."""
    result = embed_text([], "http://fake-url")
    assert result == []

