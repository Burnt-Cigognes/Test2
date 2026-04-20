# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 14:54:48 2026

@author: chris
"""

import os
import requests

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Read the API key from environment variables first. If not set, fall back to the hardcoded key.
# This allows overriding the key without modifying the code (e.g. for security or using a personal key).
# os.environ.get() works cross-platform on Windows, Mac, and Linux.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "CLE_NON_CONFIGUREE")

# The AI model to use via OpenRouter. Free models are available — switch by uncommenting another line.
# OPENROUTER_MODEL = "tngtech/deepseek-r1t-chimera:free"
OPENROUTER_MODEL = "google/gemini-2.0-flash-lite-preview-02-05:free"


# Custom error class for OpenRouter API failures, inherits from Python's built-in RuntimeError.
class OpenRouterError(RuntimeError):
    pass


# Blueprint for a tool that sends prompts to an AI model and remembers past responses.
class OpenRouterClient:
    def __init__(self):
        # In-memory cache (dictionary) to store past prompts and their AI responses.
        # Avoids sending the same prompt twice, saving time and API costs.
        self.prompt_cache = {}

    def chat(self, prompt, response_format=None):
        # Step 1 — Check the cache first.
        # If this exact prompt was already sent before, return the saved answer immediately.
        ai_reply_content = self.prompt_cache.get(prompt)

        if ai_reply_content:
            return ai_reply_content

        # Step 2 — Build the request payload to send to the AI.
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            # Temperature controls creativity: 0 = very consistent, 1 = very random.
            # Low temperature is appropriate here for reliable financial analysis output.
            "temperature": 0.2
        }

        # Optionally enforce a specific response format (e.g. JSON) if provided.
        if response_format is not None:
            payload["response_format"] = response_format

        # Step 3 — Send the prompt to OpenRouter via an HTTP POST request.
        # The API key is passed in the Authorization header to authenticate the request.
        r = requests.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )

        # Step 4 — Handle errors.
        # If the API returns a failure (e.g. invalid key, network issue), raise a descriptive error.
        if not r.ok:
            raise OpenRouterError(f"Chat failed: {r.status_code} {r.text}")

        response = r.json()

        print(response)

        # Step 5 — Extract the AI's reply from the response.
        # The API returns a JSON object; the text reply is nested at choices[0].message.content.
        # This is a standard structure shared by most LLM APIs (OpenAI, OpenRouter, etc.).
        ai_reply_content = response["choices"][0]["message"]["content"]

        # Save the response to cache so the same prompt is not sent again.
        self.prompt_cache[prompt] = ai_reply_content

        return ai_reply_content
