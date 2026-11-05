"""Tests for Ollama's local HTTP adapter."""

import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from skywalker.core.config import Settings
from skywalker.domain.ai import ChatMessage
from skywalker.infrastructure.ollama import OllamaError, OllamaProvider


class OllamaProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = OllamaProvider(Settings(data_directory=Path("."), system_prompt="Be brief"))

    def test_list_models_reads_local_tags(self) -> None:
        response = io.BytesIO(json.dumps({"models": [{"name": "qwen3.5:4b"}]}).encode())
        with patch("skywalker.infrastructure.ollama.urlopen", return_value=response):
            self.assertEqual(self.provider.list_models(), ["qwen3.5:4b"])

    def test_stream_chat_sends_context_and_yields_chunks(self) -> None:
        lines = [
            json.dumps({"message": {"content": "Hello"}, "done": False}).encode() + b"\n",
            json.dumps({"message": {"content": " there"}, "done": True}).encode() + b"\n",
        ]
        response = io.BytesIO(b"".join(lines))
        with patch("skywalker.infrastructure.ollama.urlopen", return_value=response) as request:
            result = list(self.provider.stream_chat("qwen3.5:4b", [ChatMessage("user", "Hi")]))
        self.assertEqual(result, ["Hello", " there"])
        sent = json.loads(request.call_args.args[0].data)
        self.assertEqual(sent["messages"][0], {"role": "system", "content": "Be brief"})
        self.assertEqual(sent["messages"][1], {"role": "user", "content": "Hi"})

    def test_stream_chat_surfaces_model_errors(self) -> None:
        response = io.BytesIO(b'{"error":"model not found"}\n')
        with patch("skywalker.infrastructure.ollama.urlopen", return_value=response):
            with self.assertRaisesRegex(OllamaError, "model not found"):
                list(self.provider.stream_chat("missing", []))


if __name__ == "__main__":
    unittest.main()
