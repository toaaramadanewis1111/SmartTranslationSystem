import asyncio
import os
import unittest
from unittest.mock import patch

import httpx

import api
from llm.schemas import TranslationResponse


class TranslationApiTests(unittest.TestCase):
    def request(self, method, path, **kwargs):
        async def send():
            transport = httpx.ASGITransport(app=api.app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver"
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    def test_translation_endpoint_returns_frontend_response_shape(self):
        result = TranslationResponse(
            translation="Bonjour.",
            source_lang="en",
            target_lang="fr",
            topic="Greetings",
            style="natural",
            ambiguity={
                "is_ambiguous": False,
                "chosen_meaning": None,
                "confidence": "high"
            },
            alternatives=["Bonne journée."]
        )

        with (
            patch.dict(os.environ, {"ENABLE_VOCABULARY_PREDICTOR": "0"}),
            patch("api.translate", return_value=result)
        ):
            response = self.request("POST", "/translate", json={
                "text": "Good morning.",
                "source_lang": "en",
                "target_lang": "fr",
                "style": "natural"
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["translation"], "Bonjour.")
        self.assertEqual(response.json()["input_type"], "text")
        self.assertEqual(response.json()["recommended_vocabulary"], [])

    def test_recommendations_use_request_language_code(self):
        result = TranslationResponse(
            translation="Bonjour.",
            source_lang="English",
            target_lang="French",
            topic="Greetings",
            style="natural",
            ambiguity={
                "is_ambiguous": False,
                "chosen_meaning": None,
                "confidence": "high"
            },
            alternatives=[]
        )
        predictor = unittest.mock.Mock()
        predictor.predict.return_value = [
            {"word": "bonjour", "score": 0.9}
        ]

        with (
            patch("api.translate", return_value=result),
            patch("api._get_vocabulary_predictor", return_value=predictor)
        ):
            response = self.request("POST", "/translate", json={
                "text": "Good morning.",
                "source_lang": "en",
                "target_lang": "fr",
                "context": "A friendly morning greeting."
            })

        predictor.predict.assert_called_once_with(
            sentence="Good morning.\nBonjour.",
            topic="Greetings",
            target_lang="fr",
            top_k=5,
            context="A friendly morning greeting."
        )
        self.assertEqual(
            response.json()["recommended_vocabulary"],
            [{"word": "bonjour", "score": 0.9}]
        )

    def test_translation_errors_are_returned_as_actionable_api_errors(self):
        with patch(
            "api.translate",
            side_effect=RuntimeError("No compatible Ollama model.")
        ):
            response = self.request("POST", "/translate", json={
                "text": "Good morning.",
                "source_lang": "en",
                "target_lang": "fr"
            })

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "No compatible Ollama model."
        )

    def test_frontend_origin_is_allowed_for_browser_requests(self):
        response = self.request(
            "OPTIONS",
            "/translate",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:3000"
        )


if __name__ == "__main__":
    unittest.main()
