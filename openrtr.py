# -*- coding: utf-8 -*-
"""
Created on Sun Apr 5 14:54:48 2026

@author: chris
"""

import os
import requests

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Read the API key from environment variables.
# Example on Streamlit Cloud: add OPENROUTER_API_KEY in Secrets / environment settings.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "CLE_NON_CONFIGUREE")

# Choose the model used through OpenRouter.
# OPENROUTER_MODEL = "tngtech/deepseek-r1t-chimera:free"
OPENROUTER_MODEL = "google/gemini-2.5-pro"


class OpenRouterError(RuntimeError):
    """Custom exception raised for OpenRouter API failures."""
    pass


class OpenRouterClient:
    def __init__(self):
        # Simple in-memory cache to avoid sending the same prompt multiple times
        self.prompt_cache = {}

    def chat(self, prompt: str, response_format=None) -> str:
        """
        Sends a prompt to OpenRouter and returns the model response.

        Parameters
        ----------
        prompt : str
            Prompt sent to the model.
        response_format : optional
            Optional structured response format for compatible models.

        Returns
        -------
        str
            Model response text.
        """
        if not prompt or not prompt.strip():
            raise OpenRouterError("Prompt cannot be empty.")

        if OPENROUTER_API_KEY == "CLE_NON_CONFIGUREE":
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not configured. Please add it as an environment variable."
            )

        cached_response = self.prompt_cache.get(prompt)
        if cached_response:
            return cached_response

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
        except requests.RequestException as exc:
            raise OpenRouterError(f"Network error while calling OpenRouter: {exc}") from exc

        if not response.ok:
            raise OpenRouterError(
                f"Chat failed with status {response.status_code}: {response.text}"
            )

        try:
            response_json = response.json()
        except ValueError as exc:
            raise OpenRouterError("OpenRouter returned invalid JSON.") from exc

        try:
            ai_reply_content = response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenRouterError(
                f"Unexpected OpenRouter response format: {response_json}"
            ) from exc

        if not ai_reply_content:
            raise OpenRouterError("OpenRouter returned an empty response.")

        self.prompt_cache[prompt] = ai_reply_content
        return ai_reply_content
