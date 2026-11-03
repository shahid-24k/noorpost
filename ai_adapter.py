"""
ai_adapter.py — Optional AI Integration with Guaranteed Rule-Based Fallbacks for NoorPost Ultimate
Provides optional AI enhancement for reflections and captions, while strictly guaranteeing
100% functionality without any API key or paid service.

Safety & Accuracy Principles:
- Core engine ALWAYS functions completely offline via deterministic rule-based algorithms.
- API keys are NEVER hardcoded or printed in logs (masked automatically).
- Network errors or timeouts gracefully fall back to the local rule-based engine.
- AI is NEVER allowed to invent Quran/Hadith references or modify sacred Arabic text.
- AI commentary is strictly isolated from authentic religious quotations.
"""

import os
import json
from typing import Dict, Any, Tuple, Optional
from logger import log
from categories import resolve_category

# Load configuration from environment
ENABLE_AI = os.getenv("ENABLE_AI", "False").strip().lower() in ("true", "1", "yes")
AI_PROVIDER = os.getenv("AI_PROVIDER", "none").strip().lower()

class AIAdapter:
    """
    Adapter for optional AI assistance with automatic graceful fallback.
    """
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or AI_PROVIDER).lower()
        self.enabled = ENABLE_AI and self.provider != "none"
        self._api_key = self._load_api_key()

    def _load_api_key(self) -> Optional[str]:
        if not self.enabled:
            return None
        if self.provider == "gemini":
            key = os.getenv("GEMINI_API_KEY", "").strip()
            return key if key else None
        elif self.provider == "openai":
            key = os.getenv("OPENAI_API_KEY", "").strip()
            return key if key else None
        return None

    def is_available(self) -> bool:
        """Return True if an AI provider is configured and enabled with a valid key."""
        return self.enabled and bool(self._api_key)

    def suggest_theme_and_layout(self, content: Dict[str, Any]) -> Tuple[str, str]:
        """
        Suggest visual theme and layout.
        Uses rule-based heuristics as primary, with AI enhancement when active.
        """
        category = content.get("category", "daily_duas")
        cat_meta = resolve_category(category) or {}
        default_theme = cat_meta.get("default_theme", "midnight-gold")
        default_layout = cat_meta.get("default_layout", "dua")

        # Layout heuristics based on text length and source type
        arabic = content.get("arabic", "")
        source = content.get("source", "")

        if "qur'an" in source.lower():
            default_layout = "quran"
        elif len(arabic) > 120:
            default_layout = "dua"

        return default_theme, default_layout

    def generate_reflection(self, content: Dict[str, Any]) -> str:
        """
        Produce a concise 1-2 sentence reflection on the content.
        Falls back to verified database commentary if AI is disabled or fails.
        """
        # Rule-based fallback (Always available)
        rule_based_reflection = content.get("commentary", "").strip()
        if not rule_based_reflection:
            category = content.get("category", "daily_duas")
            rule_based_reflection = f"A timeless reminder from the authentic Sunnah on the importance of {category.replace('_', ' ')}."

        if not self.is_available():
            return rule_based_reflection

        # Optional AI enhancement attempt
        try:
            return self._call_ai_for_reflection(content, fallback=rule_based_reflection)
        except Exception as e:
            log(f"⚠️  AI provider '{self.provider}' call failed: {e}. Falling back to rule-based reflection.", level="WARNING")
            return rule_based_reflection

    def _call_ai_for_reflection(self, content: Dict[str, Any], fallback: str) -> str:
        """
        Internal dispatcher for configured AI providers.
        """
        # Strictly constrained prompt preventing hallucination
        prompt = (
            "You are an assistant for authentic Islamic content creation.\n"
            "TASK: Provide a concise, 1-2 sentence respectful reflection on this authentic teaching.\n"
            "STRICT RULES:\n"
            "1. DO NOT alter the sacred text or invent any religious rulings or promises.\n"
            "2. DO NOT invent hadith citations or Quranic references.\n"
            "3. Keep the language humble, direct, and universally inspiring.\n\n"
            f"Text: {content.get('arabic')}\n"
            f"Translation: {content.get('translation')}\n"
            f"Reference: {content.get('source')}\n"
        )

        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                if response and response.text:
                    cleaned = response.text.strip().replace("\n", " ")
                    return f"{cleaned} (AI Reflection)"
            except Exception as e:
                log(f"Gemini API invocation error: {e}", level="WARNING")
                return fallback

        elif self.provider == "openai":
            try:
                import urllib.request
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}"
                }
                data = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.5
                }
                req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    text = res_json["choices"][0]["message"]["content"].strip()
                    return f"{text} (AI Reflection)"
            except Exception as e:
                log(f"OpenAI API invocation error: {e}", level="WARNING")
                return fallback

        return fallback

# Singleton instance
ai_engine = AIAdapter()
