"""
LLM-based parser fallback.

Invoked when the regex/TexSoup parser fails to extract modules.
Uses the user's configured LLM provider to identify structural components
in the raw template text.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.schemas.mapping import TemplateMapping, ModuleMapping

logger = logging.getLogger(__name__)


async def llm_parse_template(
    filepath: str, fmt: str, llm_config: dict | None = None
) -> TemplateMapping | None:
    """Use an LLM to identify template modules.

    Reads the raw .tex/.docx text, sends a short prompt to the LLM
    asking it to output a JSON list of modules.

    Only tokenizes ~2KB of the template file (not user content).
    """
    path = Path(filepath)
    if not path.exists():
        return None

    raw = path.read_text(encoding="utf-8", errors="replace")
    # Only send the first 3000 chars — enough to capture the structure
    snippet = raw[:3000]
    if len(raw) > 3000:
        snippet += "\n% ... (truncated)"

    prompt = f"""You are a LaTeX template analyzer. Given this template snippet, identify the MODULE STRUCTURE.

For each section/heading/environment found, output a JSON object:

{{
  "modules": [
    {{
      "type": "title|author|abstract|section|bibliography|figure|table|acknowledgments",
      "label": "Human-readable name",
      "level": null or 1/2/3 for sections,
      "anchor_type": "regex",
      "anchor_pattern": "LaTeX command regex to locate this module (e.g. \\\\\\\\title\\\\{{\\\\}})"
    }}
  ]
}}

Template snippet:
```
{snippet}
```

Output ONLY valid JSON, no explanation."""

    # Try to get an LLM
    try:
        response_text = await _call_llm(prompt, llm_config)
        # Extract JSON from response
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text)
        raw_modules = data.get("modules", [])

        modules = []
        for i, m in enumerate(raw_modules):
            modules.append(
                ModuleMapping(
                    id=f"llm-{i+1:03d}",
                    type=m.get("type", "section"),
                    label=m.get("label", f"Module {i+1}"),
                    anchor_line=m.get("anchor_line"),
                    anchor_type=m.get("anchor_type", "regex"),
                    anchor_pattern=m.get("anchor_pattern", ""),
                    content=m.get("content", ""),
                    level=m.get("level"),
                )
            )

        return TemplateMapping(
            template_path=str(path.resolve()),
            format=fmt,
            modules=modules,
        )
    except Exception as exc:
        logger.warning("LLM fallback parser failed: %s", exc)
        return None


async def _call_llm(prompt: str, config: dict | None = None) -> str:
    """Call an LLM via langchain with the user's stored config.

    Supports OpenAI, Anthropic, Gemini, and Ollama backends.
    Falls back gracefully if no config or key is available.
    """
    provider = (config or {}).get("provider", "openai")
    api_key = (config or {}).get("api_key", "")
    base_url = (config or {}).get("base_url", "")
    model = (config or {}).get("model_name", "")

    # Decrypt key if needed
    if api_key and not api_key.startswith("sk-") and not api_key.startswith("ant-"):
        try:
            from app.core.security import decrypt
            api_key = decrypt(api_key)
        except Exception:
            pass

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=model or "gpt-4o",
            api_key=api_key or "sk-placeholder",
            base_url=base_url or None,
            temperature=0,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=model or "claude-sonnet-4-6",
            api_key=api_key or "sk-ant-placeholder",
            base_url=base_url or None,
            temperature=0,
        )
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=model or "gemini-2.0-flash",
            google_api_key=api_key or "placeholder",
            temperature=0,
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=model or "llama3",
            base_url=base_url or "http://localhost:11434",
            temperature=0,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    response = await llm.ainvoke(prompt)
    return response.content if hasattr(response, "content") else str(response)
