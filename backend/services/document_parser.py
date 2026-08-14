import json
import os
from backend.config import settings
from backend.pipeline_config import PipelineConfig

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def parse_document_with_llm(document_text: str, prompt: str, csv_schema: dict = None) -> dict:
    """Parse document using Anthropic Claude API via OpenRouter.

    Raises exceptions if:
    - API key is not configured
    - Anthropic API call fails
    - Response cannot be parsed as JSON
    """
    # Get API key from environment (loaded by env_loader from .env)
    api_key = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://openrouter.ai/api")

    if not api_key:
        raise ValueError(
            "❌ API Key Not Found\n"
            "Set ANTHROPIC_AUTH_TOKEN in .env file with your OpenRouter key (sk-or-...)"
        )

    if not HAS_ANTHROPIC:
        raise RuntimeError(
            "❌ Anthropic SDK Not Installed\n"
            "Install with: pip install anthropic\n"
            "Or: pip install -r requirements.txt"
        )

    try:
        client = Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        print(f"📡 Calling Anthropic Claude API via OpenRouter...")
        print(f"   Base URL: {base_url}")
        print(f"   Model: {PipelineConfig.LLM_MODEL}")

        message = client.messages.create(
            model=PipelineConfig.LLM_MODEL,
            max_tokens=PipelineConfig.LLM_MAX_TOKENS,
            temperature=PipelineConfig.LLM_TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\nDocument:\n{document_text}"
                }
            ]
        )

        response_text = message.content[0].text
        print(f"✅ LLM Response received ({len(response_text)} chars)")

        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Remove opening ```json or ```
            response_text = response_text.lstrip("`").lstrip("json").lstrip("`").strip()
        if response_text.endswith("```"):
            # Remove closing ```
            response_text = response_text.rstrip("`").rstrip()

        result = json.loads(response_text)
        print(f"✅ JSON parsed successfully")
        return result

    except json.JSONDecodeError as e:
        raise ValueError(
            f"❌ LLM Response is not valid JSON\n"
            f"Error: {str(e)}\n"
            f"Response received: {response_text[:500]}..."
        )
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        raise RuntimeError(
            f"❌ LLM API Error ({error_type})\n"
            f"Message: {error_msg}\n"
            f"Check:\n"
            f"  - API key is valid (sk-or-...)\n"
            f"  - Base URL is correct (https://openrouter.ai/api)\n"
            f"  - Model name is correct (anthropic/claude-haiku-4.5)\n"
            f"  - Network connectivity\n"
            f"  - Account has sufficient credits at openrouter.ai"
        )
