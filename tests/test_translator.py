import json
import unittest
from unittest.mock import patch

import requests
from llm import translator


class TranslatorTests(unittest.TestCase):
    def make_response(self, status_code, body):
        response = requests.Response()
        response.status_code = status_code
        response.url = "http://ollama:11435/api/chat"
        response._content = body.encode()
        return response

    @patch("llm.translator.requests.post")
    @patch("llm.translator.requests.get")
    def test_uses_the_configured_model_and_custom_ollama_host(
        self,
        get,
        post
    ):
        get.return_value.json.return_value = {
            "models": [
                {"name": "qwen3:4b-instruct"},
                {"name": "qwen3:0.6b"}
            ]
        }
        post.return_value.json.return_value = {
            "message": {
                "content": json.dumps({
                    "translation": "Bonjour.",
                    "source_lang": "en",
                    "target_lang": "fr",
                    "topic": "General",
                    "style": "natural",
                    "ambiguity": {
                        "is_ambiguous": False,
                        "chosen_meaning": None,
                        "confidence": "high"
                    },
                    "alternatives": ["Salut.", "Bonjour."]
                })
            }
        }

        with (
            patch.object(translator, "OLLAMA_URL", "http://ollama:11435/api/chat"),
            patch.object(translator, "DEFAULT_MODEL", "qwen3:4b-instruct")
        ):
            result = translator.translate("Hello.", "en", "fr")

        get.assert_called_once_with(
            "http://ollama:11435/api/tags",
            timeout=10
        )
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], "http://ollama:11435/api/chat")
        self.assertEqual(
            post.call_args.kwargs["json"]["model"],
            "qwen3:4b-instruct"
        )
        request_payload = post.call_args.kwargs["json"]
        self.assertEqual(request_payload["options"]["num_ctx"], 2048)
        self.assertEqual(request_payload["options"]["num_gpu"], 0)
        self.assertFalse(request_payload["think"])
        self.assertIn(
            "Never replace a place",
            request_payload["messages"][0]["content"]
        )
        self.assertEqual(result.translation, "Bonjour.")
        self.assertEqual(result.alternatives, ["Salut."])
        self.assertEqual(result.source_lang, "en")
        self.assertEqual(result.target_lang, "fr")

    @patch("llm.translator._pull_model")
    def test_pulls_configured_model_instead_of_using_another_installed_model(
        self,
        pull_model
    ):
        with patch.object(translator, "DEFAULT_MODEL", "qwen3:4b-instruct"):
            selected = translator._select_models([
                "qwen3:0.6b",
                "tinyllama:latest"
            ])

        pull_model.assert_called_once_with("qwen3:4b-instruct")
        self.assertEqual(selected, ["qwen3:4b-instruct"])

    @patch("llm.translator.requests.get")
    def test_connection_errors_are_not_hidden(self, get):
        get.side_effect = requests.ConnectionError("Ollama is offline")

        with self.assertRaises(requests.ConnectionError):
            translator.translate("Hello.", "en", "fr")

    @patch("llm.translator.requests.post")
    @patch("llm.translator.requests.get")
    def test_out_of_memory_does_not_silently_use_a_less_accurate_model(
        self,
        get,
        post
    ):
        get.return_value.json.return_value = {
            "models": [{"name": "qwen3:4b-instruct"}]
        }
        post.return_value = self.make_response(
            500,
            '{"error":"failed to allocate model memory"}'
        )

        with (
            patch.object(translator, "OLLAMA_URL", "http://ollama:11435/api/chat"),
            patch.object(translator, "DEFAULT_MODEL", "qwen3:4b-instruct")
        ):
            with self.assertRaises(RuntimeError) as raised:
                translator.translate("Hello.", "en", "fr")

        post.assert_called_once()
        self.assertIn("failed to allocate model memory", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
