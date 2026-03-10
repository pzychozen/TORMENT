"""Embedding backends.

v1.10 focus:
  - Keep deterministic hash embeddings for tests/replay.
  - Add real embedding providers (SentenceTransformers / Ollama) as opt-in.

Design:
  - `embed(text) -> np.ndarray[float32]` always returns a 1D vector.
  - `dim` is an explicit, stable property.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass
from typing import Protocol

import numpy as np


def embedding_checksum(summary: str, provider: str, model: str) -> str:
    """Stable checksum tying an embedding to its summary + embedder identity."""
    s = (summary or "").strip()
    p = (provider or "").strip()
    m = (model or "").strip()
    h = hashlib.sha256()
    h.update((p + "\n" + m + "\n" + s).encode("utf-8"))
    return h.hexdigest()


class Embedder(Protocol):
    dim: int
    provider: str
    model: str

    def embed(self, text: str) -> np.ndarray:  # pragma: no cover
        ...


@dataclass
class EmbedderInfo:
    provider: str
    model: str
    dim: int


class CachedEmbedder:
    """LRU cache wrapper for any embedder.

    Useful for tight query loops, UI chat, and simulation.
    Cache key is (text) only; provider/model are implied by the wrapped embedder instance.
    """

    def __init__(self, inner: Embedder, max_size: int = 2048) -> None:
        self.inner = inner
        self.max_size = int(max_size)
        self.dim = int(getattr(inner, "dim", 0) or 0)
        self.provider = str(getattr(inner, "provider", ""))
        self.model = str(getattr(inner, "model", ""))
        self._cache: "OrderedDict[str, np.ndarray]" = OrderedDict()

    def embed(self, text: str) -> np.ndarray:
        text = (text or "").strip()
        if not text:
            return np.zeros(self.dim, dtype=np.float32)

        hit = self._cache.get(text)
        if hit is not None:
            # Refresh LRU position
            self._cache.move_to_end(text, last=True)
            return hit

        v = self.inner.embed(text)
        v = np.asarray(v, dtype=np.float32).reshape(-1)
        if self.dim and int(v.shape[0]) != int(self.dim):
            raise RuntimeError("Embedding dimension changed unexpectedly (cache wrapper)")
        if not self.dim:
            self.dim = int(v.shape[0])

        # Store copy to prevent accidental mutation
        self._cache[text] = v.copy()
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
        return v




class HashEmbedding:
    """Deterministic, dependency-free embedding.

    Not SOTA, but stable for local prototyping, simulation, and replay determinism.
    """

    provider = "hash"

    def __init__(self, dim: int = 384, salt: str = "torment") -> None:
        self.dim = int(dim)
        self.salt = salt
        self.model = f"hash:{self.dim}:{self.salt}"

    def embed(self, text: str) -> np.ndarray:
        text = (text or "").strip()
        if not text:
            return np.zeros(self.dim, dtype=np.float32)

        v = np.zeros(self.dim, dtype=np.float32)
        toks = text.lower().split()
        for t in toks[:2048]:
            h = hashlib.blake2b((self.salt + ":" + t).encode("utf-8"), digest_size=16).digest()
            a = int.from_bytes(h[:8], "little", signed=False)
            b = int.from_bytes(h[8:], "little", signed=False)
            idx = a % self.dim
            sign = 1.0 if (b & 1) == 0 else -1.0
            v[idx] += sign
        n = float(np.linalg.norm(v))
        if n > 0:
            v /= n
        return v


class STEmbedding:
    """SentenceTransformers embedding backend.

    Requires: `pip install sentence-transformers`
    """

    provider = "st"

    def __init__(self, model: str, device: str = "cpu", batch_size: int = 32) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "SentenceTransformers provider selected but dependency is missing. "
                "Install with: pip install sentence-transformers"
            ) from e

        self.model = model
        self.device = device
        self.batch_size = int(batch_size)
        self._st = SentenceTransformer(model, device=device)

        test = self._st.encode(["dim_probe"], normalize_embeddings=True)
        self.dim = int(np.asarray(test).shape[-1])

    def embed(self, text: str) -> np.ndarray:
        text = (text or "").strip()
        if not text:
            return np.zeros(self.dim, dtype=np.float32)
        v = self._st.encode([text], normalize_embeddings=True)
        v = np.asarray(v, dtype=np.float32).reshape(-1)
        if v.shape[0] != self.dim:
            raise RuntimeError("Embedding dimension changed unexpectedly")
        return v


class OllamaEmbedding:
    """Ollama embedding backend via HTTP.

    Uses stdlib `urllib` to avoid adding hard dependencies.
    """

    provider = "ollama"

    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434", timeout_s: float = 30.0) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_s = float(timeout_s)

        v = self._embed_raw("dim_probe")
        self.dim = int(v.shape[0])

    def _embed_raw(self, text: str) -> np.ndarray:
        payload = {"model": self.model, "prompt": text}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"{self.base_url}/api/embeddings",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            obj = json.loads(resp.read().decode("utf-8"))
        emb = obj.get("embedding")
        if not isinstance(emb, list):
            raise RuntimeError("Ollama embeddings response missing 'embedding' list")
        return np.asarray(emb, dtype=np.float32).reshape(-1)

    def embed(self, text: str) -> np.ndarray:
        text = (text or "").strip()
        if not text:
            return np.zeros(self.dim, dtype=np.float32)
        v = self._embed_raw(text)
        if int(v.shape[0]) != int(self.dim):
            raise RuntimeError("Embedding dimension changed unexpectedly")
        n = float(np.linalg.norm(v))
        if n > 0:
            v = v / n
        return v.astype(np.float32)


def build_embedder_from_env() -> Embedder:
    """Factory used by the service at startup."""

    provider = (os.environ.get("TORMENT_EMBED_PROVIDER") or "hash").strip().lower()
    model = (os.environ.get("TORMENT_EMBED_MODEL") or "").strip()
    batch = int(os.environ.get("TORMENT_EMBED_BATCH") or 32)
    cache_size = int(os.environ.get("TORMENT_EMBED_CACHE_SIZE") or 0)

    def _maybe_cache(e: Embedder) -> Embedder:
        if cache_size and int(cache_size) > 0:
            return CachedEmbedder(e, max_size=int(cache_size))
        return e

    if provider in ("hash", "det", "deterministic"):
        dim = int(os.environ.get("TORMENT_HASH_DIM") or 384)
        salt = os.environ.get("TORMENT_HASH_SALT") or "torment"
        return _maybe_cache(HashEmbedding(dim=dim, salt=salt))

    if provider in ("st", "sentence_transformers", "sentence-transformers"):
        if not model:
            model = "BAAI/bge-small-en-v1.5"
        device = (os.environ.get("TORMENT_EMBED_DEVICE") or "cpu").strip()
        return _maybe_cache(STEmbedding(model=model, device=device, batch_size=batch))

    if provider in ("ollama",):
        if not model:
            model = os.environ.get("TORMENT_OLLAMA_MODEL") or "nomic-embed-text"
        base_url = os.environ.get("TORMENT_OLLAMA_URL") or "http://127.0.0.1:11434"
        timeout_s = float(os.environ.get("TORMENT_OLLAMA_TIMEOUT_S") or 30.0)
        return _maybe_cache(OllamaEmbedding(model=model, base_url=base_url, timeout_s=timeout_s))

    raise RuntimeError(f"Unknown TORMENT_EMBED_PROVIDER: {provider}")
