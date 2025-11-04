import os
import math
import random
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
)
from .settings import settings
from .logger import logger


def _mock_vec(text: str, dim: int = 384) -> List[float]:
    """Generate a mock embedding vector for testing."""
    random.seed(hash(text) & 0xffffffff)
    v = [random.random() for _ in range(dim)]
    norm = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x / norm for x in v]


class BaseNIMClient(ABC):
    """Base class for NIM clients."""
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generated text from a prompt."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the client can connect to the service."""
        pass


class NIMClient(BaseNIMClient):
    """Real NVIDIA NIM API client with async support, retry logic, and rate limiting."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model_id: str = "meta/llama-3.1-nemotron-70b-instruct",
        timeout: float = 60.0
    ):
        """
        Initialize NIM client.
        
        Args:
            api_key: NVIDIA API key
            base_url: Base URL for NIM API
            model_id: Model identifier
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model_id = model_id
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._client
    
    async def _close_client(self):
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    def _is_rate_limit_error(self, exc: Exception) -> bool:
        """Check if exception is a rate limit error."""
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code == 429
        return False
    
    def _should_retry(self, exc: Exception) -> bool:
        """Determine if we should retry on this exception."""
        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            # Retry on 429 (rate limit) and 5xx errors
            return exc.response.status_code in (429, 500, 502, 503, 504)
        return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        stream: bool = False
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"NIM API request to {url}: {json.dumps(payload, indent=2)}")
        
        try:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            logger.debug(f"NIM API response status: {response.status_code}")
            
            # Handle rate limiting - raise error so retry logic can handle it
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limited. Retry-After: {wait_time} seconds")
                else:
                    logger.warning("Rate limited. Will retry with exponential backoff")
            
            response.raise_for_status()
            
            return response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"NIM API error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"NIM API timeout after {self.timeout}s: {e}")
            raise
        except httpx.NetworkError as e:
            logger.error(f"NIM API network error: {e}")
            raise
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.
    
    Args:
            prompt: The prompt text
            temperature: Sampling temperature (0.0 to 2.0)
        max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        try:
            # Convert prompt to messages format
            messages = [{"role": "user", "content": prompt}]
            
            payload = {
                "model": self.model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            response = await self._make_request("/chat/completions", payload)
            data = response.json()
            
            # Extract text from response
            choices = data.get("choices", [])
            if not choices:
                logger.warning("NIM API returned no choices")
                raise ValueError("NIM API returned no choices")
            
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                logger.warning("NIM API returned empty content")
                raise ValueError("NIM API returned empty content")
            
            logger.debug(f"Generated text length: {len(content)} characters")
            return content.strip()
            
        except Exception as e:
            logger.error(f"Error in generate_text: {e}", exc_info=True)
            raise
    
    async def stream_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream generated text from a prompt.
        
        Args:
            prompt: The prompt text
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Yields:
            Text chunks as they are generated
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            payload = {
                "model": self.model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs
            }
            
            client = await self._get_client()
            url = f"{self.base_url}/chat/completions"
            
            logger.debug(f"NIM API streaming request to {url}")
            
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # SSE format: data: {...}
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE data: {data_str}")
                            continue
                        
        except Exception as e:
            logger.error(f"Error in stream_generate: {e}", exc_info=True)
            raise
    
    async def health_check(self) -> bool:
        """
        Check if the client can connect to the NIM API.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check with minimal prompt
            messages = [{"role": "user", "content": "ping"}]
            payload = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": 5,
                "temperature": 0.1
            }
            
            response = await self._make_request("/chat/completions", payload)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_client()


class MockClient(BaseNIMClient):
    """Mock NIM client for testing without API calls."""
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Generate mock text from a prompt."""
        logger.debug("Using mock LLM response")
        pl = prompt.lower()
    
        # Outline planner → return proper JSON with 6–7 beats including Inciting Incident
        if "return json with keys logline and beats" in pl or "story planner" in pl:
            data = {
                "logline": "A shy barista can pause time for 10 seconds, but each pause steals hours from tomorrow.",
                "beats": [
                    {"title":"Hook","goal":"Keep the café calm","conflict":"Time jitters spill orders","outcome":"Rin discovers the pause"},
                    {"title":"Inciting Incident","goal":"Save a child from a crash","conflict":"Ten-second limit nearly fails","outcome":"Child saved; Rin blacks out"},
                    {"title":"First Threshold","goal":"Use pauses to help quietly","conflict":"Ringing ears, blurred vision","outcome":"Rin commits to a secret rulebook"},
                    {"title":"Midpoint","goal":"Stop a closing-time robbery","conflict":"Multiple attackers exceed 10s","outcome":"Wins but loses half a day tomorrow"},
                    {"title":"Crisis","goal":"Protect a friend from a stalker","conflict":"Pauses cause memory gaps","outcome":"Work and friendships strain"},
                    {"title":"Climax","goal":"Catch stalker without pausing","conflict":"Must rely on wit not power","outcome":"Rin succeeds; sets new limits"},
                    {"title":"Resolution","goal":"Live with balance","conflict":"Temptation to overuse","outcome":"Rin keeps the gift for emergencies"}
                ]
            }
            return json.dumps(data)
    
        # Scene expansion → readable mock text
        return ("[MOCK LLM]\n"
                "Scene based on: " + prompt[:600] + "\n"
                "…cups rattle, air crystallizes, and time thins to a silver thread…\n"
                "— End of mock output —")
        
    async def stream_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream mock generated text."""
        text = await self.generate_text(prompt, temperature, max_tokens, **kwargs)
        # Simulate streaming by yielding chunks
        chunk_size = 50
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]
            await asyncio.sleep(0.01)  # Small delay to simulate streaming
    
    async def health_check(self) -> bool:
        """Mock health check always returns True."""
        return True


def create_nim_client() -> BaseNIMClient:
    """
    Factory function to create appropriate NIM client based on configuration.
    
    Returns:
        NIMClient or MockClient instance
    """
    if settings.USE_MOCK:
        logger.info("Creating MockClient (USE_MOCK=True)")
        return MockClient()
    
    api_key = settings.NIM_API_KEY
    if not api_key:
        logger.warning("NIM_API_KEY not set, falling back to MockClient")
        return MockClient()
    
    logger.info(f"Creating NIMClient with base_url={settings.NVCF_BASE}, model={settings.NIM_TEXT_FUNC_ID}")
    return NIMClient(
        api_key=api_key,
        base_url=settings.NVCF_BASE,
        model_id=settings.NIM_TEXT_FUNC_ID,
        timeout=settings.API_TIMEOUT
    )


# Global client instance
_client_instance: Optional[BaseNIMClient] = None


def get_nim_client() -> BaseNIMClient:
    """Get or create the global NIM client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = create_nim_client()
    return _client_instance


# Backward compatibility: async version of call_llm
async def call_llm(
    prompt: str,
    llm_url: str = None,  # Kept for backward compatibility, but not used
    max_tokens: int = 512,
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Call the LLM API with proper error handling and logging.
    
    Args:
        prompt: The prompt to send to the LLM
        llm_url: Deprecated - kept for backward compatibility
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional parameters
        
    Returns:
        Generated text from the LLM
        
    Raises:
        ValueError: If the API call fails or returns invalid data
    """
    try:
        client = get_nim_client()
        return await client.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error in call_llm: {e}", exc_info=True)
        raise ValueError(f"LLM call failed: {e}") from e


def embed_text(chunks: List[str], embed_url: str) -> List[Dict[str, Any]]:
    """
    Generate embeddings for text chunks with proper error handling.
    
    Args:
        chunks: List of text chunks to embed
        embed_url: The URL of the embedding service
        
    Returns:
        List of dictionaries with 'embedding' key
        
    Raises:
        ValueError: If the API call fails or returns invalid data
        Timeout: If the request times out
    """
    try:
        if settings.USE_MOCK:
            logger.debug(f"Using mock embeddings for {len(chunks)} chunks")
            return [{"embedding": _mock_vec(ch)} for ch in chunks]
        
        logger.debug(f"Calling embedding API at {embed_url} for {len(chunks)} chunks")
        payload = {"input": chunks}
        
        import requests
        from requests.exceptions import RequestException, Timeout
        
        response = requests.post(
            f"{embed_url}/v1/embeddings",
            json=payload,
            timeout=settings.API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
        embeddings = data.get("data", [])
        if len(embeddings) != len(chunks):
            logger.warning(f"Embedding count mismatch: expected {len(chunks)}, got {len(embeddings)}")
            raise ValueError(f"Embedding count mismatch: expected {len(chunks)}, got {len(embeddings)}")
        
        logger.debug(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
        
    except Timeout as e:
        logger.error(f"Embedding request timed out after {settings.API_TIMEOUT}s: {e}")
        raise ValueError(f"Embedding request timed out: {e}") from e
    except RequestException as e:
        logger.error(f"Embedding request failed: {e}")
        raise ValueError(f"Embedding request failed: {e}") from e
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Invalid response from embedding API: {e}")
        raise ValueError(f"Invalid response from embedding API: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error in embed_text: {e}", exc_info=True)
        raise
