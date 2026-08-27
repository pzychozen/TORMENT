"""Focused regression tests for auth logging and Ollama URL validation."""

import os
import tempfile
import unittest
from unittest.mock import patch

from torment_service.auth import APIKeyStore
from torment_service.embeddings import OllamaEmbedding


class _EmbeddingResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b'{"embedding": [0.25, 0.75]}'


class TestCredentialFileErrorRedaction(unittest.TestCase):
    def test_credential_file_exception_text_is_not_logged(self):
        secret = "api-key-material-must-not-appear-in-logs"
        with tempfile.NamedTemporaryFile() as credential_file:
            with patch.dict(
                os.environ,
                {"TORMENT_API_KEYS": "", "TORMENT_API_KEYS_FILE": credential_file.name},
                clear=False,
            ):
                with patch("builtins.open", side_effect=RuntimeError(secret)):
                    with self.assertLogs("torment.auth", level="ERROR") as captured:
                        APIKeyStore()

        output = "\n".join(captured.output)
        self.assertIn("Failed to load configured API key file", output)
        self.assertNotIn(secret, output)
        self.assertNotIn(credential_file.name, output)


class TestOllamaBaseUrlValidation(unittest.TestCase):
    def _construct(self, base_url):
        calls = []

        def fake_urlopen(request, timeout):
            calls.append((request.full_url, timeout))
            return _EmbeddingResponse()

        with patch("torment_service.embeddings.urllib.request.urlopen", side_effect=fake_urlopen):
            embedder = OllamaEmbedding(model="nomic-embed-text", base_url=base_url)
        return embedder, calls

    def test_accepts_localhost_http_before_probe(self):
        embedder, calls = self._construct("http://localhost:11434")

        self.assertEqual(embedder.base_url, "http://localhost:11434")
        self.assertEqual(embedder.dim, 2)
        self.assertEqual(calls, [("http://localhost:11434/api/embeddings", 30.0)])

    def test_accepts_remote_https_before_probe(self):
        embedder, calls = self._construct("https://ollama.example.test")

        self.assertEqual(embedder.base_url, "https://ollama.example.test")
        self.assertEqual(embedder.dim, 2)
        self.assertEqual(calls, [("https://ollama.example.test/api/embeddings", 30.0)])

    def test_rejects_non_http_urls_before_network_contact(self):
        invalid_urls = (
            "file:///tmp/ollama",
            "ftp://ollama.example.test",
            "data:text/plain,embedding",
            "custom://ollama.example.test",
            "localhost:11434",
            "http:///api/embeddings",
            "https://",
            "https://[::1",
        )

        for base_url in invalid_urls:
            with self.subTest(base_url=base_url):
                with patch("torment_service.embeddings.urllib.request.urlopen") as urlopen:
                    with self.assertRaisesRegex(ValueError, "HTTP\\(S\\) URL with a hostname"):
                        OllamaEmbedding(model="nomic-embed-text", base_url=base_url)
                urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
