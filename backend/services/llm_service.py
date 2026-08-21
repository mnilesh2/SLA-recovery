"""
LLM Service Layer - Abstraction for LLM API calls
Supports OpenRouter (with ChatGPT) and Anthropic Claude API with caching and fallbacks
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
import logging

from ..config import settings

# Try to import OpenAI (for OpenRouter support)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Try to import Anthropic
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

logger = logging.getLogger(__name__)


class LLMService:
    """Service for making LLM API calls with Claude"""

    def __init__(self):
        self.client = None
        self.provider = settings.llm_provider
        self.cache_enabled = settings.cache_llm_responses
        self.cache_dir = Path(settings.cache_dir)
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.thinking_enabled = settings.llm_thinking_enabled
        self.thinking_budget = settings.llm_thinking_budget
        self.use_mock = settings.use_mock_llm

        # Create cache directory if needed
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize client based on provider
        if self.use_mock:
            logger.info("Using mock LLM responses")
            return

        if self.provider == "openrouter":
            self._init_openrouter()
        elif self.provider == "anthropic":
            self._init_anthropic()
        else:
            logger.error(f"Unknown LLM provider: {self.provider}")

    def _init_openrouter(self):
        """Initialize OpenRouter client"""
        if not HAS_OPENAI:
            logger.error("OpenAI SDK not installed. Install with: pip install openai>=1.3.0")
            return

        if not settings.openrouter_api_key:
            logger.error("OPENROUTER_API_KEY not configured in .env")
            return

        try:
            logger.info("Initializing OpenRouter client...")
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info(f"✅ OpenRouter client initialized successfully with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenRouter client: {type(e).__name__}: {e}")
            self.client = None

    def _init_anthropic(self):
        """Initialize Anthropic Claude client"""
        if not HAS_ANTHROPIC:
            logger.error("Anthropic SDK not installed. Install with: pip install anthropic>=0.32.0")
            return

        if not settings.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY not configured in .env")
            return

        try:
            logger.info("Initializing Anthropic client...")
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            logger.info(f"✅ Anthropic client initialized successfully with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {type(e).__name__}: {e}")
            self.client = None

    def _get_cache_key(self, prompt: str, system: str = "") -> str:
        """Generate cache key for a prompt"""
        content = f"{system}||{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load response from cache if available"""
        if not self.cache_enabled:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading cache: {e}")
        return None

    def _save_to_cache(self, cache_key: str, response: Dict):
        """Save response to cache"""
        if not self.cache_enabled:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(response, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")

    def call_claude(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        use_thinking: bool = True
    ) -> Dict[str, Any]:
        """
        Call LLM API (OpenRouter or Anthropic) with caching

        Args:
            prompt: User prompt/message
            system: System prompt
            model: Model to use (defaults to settings.llm_model)
            max_tokens: Max output tokens
            temperature: Temperature for sampling
            use_thinking: Whether to enable adaptive thinking (Claude only)

        Returns:
            Dict with 'content', 'usage', and 'cached' keys
        """
        model = model or self.model
        max_tokens = max_tokens or self.max_tokens

        # Check cache
        cache_key = self._get_cache_key(prompt, system)
        cached_response = self._load_from_cache(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for prompt")
            return {**cached_response, "cached": True}

        # Use mock if enabled
        if self.use_mock:
            logger.info("Using mock response")
            return self._get_mock_response(use_error=False)

        # Check if client is initialized
        if not self.client:
            error_msg = f"LLM client not initialized. Provider: {self.provider}, API Key configured: {bool(getattr(settings, f'{self.provider}_api_key', None))}"
            logger.error(error_msg)
            return self._get_mock_response(use_error=True, error_message=error_msg)

        try:
            if self.provider == "openrouter":
                result = self._call_openrouter(prompt, system, model, max_tokens, temperature)
            elif self.provider == "anthropic":
                result = self._call_anthropic(prompt, system, model, max_tokens, temperature, use_thinking)
            else:
                error_msg = f"Unknown LLM provider: {self.provider}. Supported: openrouter, anthropic"
                logger.error(error_msg)
                return self._get_mock_response(use_error=True, error_message=error_msg)

            # Save to cache
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            error_msg = f"LLM API Error ({self.provider} - {model}): {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            return self._get_mock_response(use_error=True, error_message=error_msg)

    def _call_openrouter(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call OpenRouter API (ChatGPT compatible)"""
        try:
            messages = [{"role": "user", "content": prompt}]
            if system:
                messages.insert(0, {"role": "system", "content": system})

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content if response.choices else ""
            if not content:
                raise ValueError("Empty response from OpenRouter API")

            result = {
                "content": content,
                "thinking": "",
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                },
                "model": model,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"OpenRouter API call successful. Model: {model}, Tokens - In: {result['usage']['input_tokens']}, Out: {result['usage']['output_tokens']}")
            return result

        except Exception as e:
            error_msg = f"OpenRouter API error (model: {model}): {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def _call_anthropic(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
        use_thinking: bool
    ) -> Dict[str, Any]:
        """Call Anthropic Claude API"""
        try:
            request_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            if system:
                request_params["system"] = system

            if use_thinking and "opus-4-6" in model:
                request_params["thinking"] = {"type": "adaptive"}

            response = self.client.messages.create(**request_params)

            content = ""
            thinking = ""
            for block in response.content:
                if block.type == "text":
                    content = block.text
                elif block.type == "thinking":
                    thinking = block.thinking

            if not content:
                raise ValueError("Empty response from Anthropic API")

            result = {
                "content": content,
                "thinking": thinking,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "model": model,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Anthropic API call successful. Model: {model}, Tokens - In: {result['usage']['input_tokens']}, Out: {result['usage']['output_tokens']}")
            return result

        except Exception as e:
            error_msg = f"Anthropic API error (model: {model}): {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def extract_json_from_response(self, response: str) -> Dict:
        """
        Extract JSON from LLM response

        Args:
            response: Response string from LLM

        Returns:
            Parsed JSON dict or error dict if extraction fails
        """
        if not response:
            logger.error("Empty response received from LLM")
            return {
                "status": "error",
                "error": "Empty response from LLM",
                "type": "extraction_error"
            }

        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try finding JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        logger.error(f"Could not extract JSON from response. Response preview: {response[:200]}...")
        return {
            "status": "error",
            "error": "Failed to parse LLM response as JSON",
            "type": "json_extraction_error",
            "response_preview": response[:200]
        }

    def _get_mock_response(self, use_error: bool = False, error_message: str = "") -> Dict:
        """
        Return error response when LLM is unavailable
        NO static/mock data is returned - only errors

        Args:
            use_error: If True, returns error response (always True in production)
            error_message: Specific error message to include
        """
        content_dict = {
            "status": "error",
            "error": error_message or "LLM API unavailable",
            "type": "llm_error",
            "fallback": True,
            "message": "Unable to process document with LLM. Please verify API configuration."
        }

        return {
            "content": json.dumps(content_dict),
            "thinking": "",
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
            },
            "model": "error",
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_document(
        self,
        document_text: str,
        document_type: str = "custom",
        custom_instructions: str = "",
        system_prompt: str = "",
        csv_schema_info: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze a document using LLM with CSV schema context

        Args:
            document_text: The document content to analyze
            document_type: Type of document (sla, insurance, contract, etc.)
            custom_instructions: Additional instructions for analysis
            system_prompt: Custom system prompt
            csv_schema_info: CSV schema information (headers, sample data, types)

        Returns:
            Dict with analysis results including extraction status
        """
        from ..document_types import get_document_type

        try:
            # Get document type configuration
            doc_type_config = get_document_type(document_type)

            # Build prompt with CSV schema if available
            prompt = doc_type_config.get_full_prompt(document_text, custom_instructions)
            if csv_schema_info:
                prompt = f"{prompt}\n{csv_schema_info}"

            # Use document-type-specific or custom system prompt
            if system_prompt:
                system = system_prompt
            elif document_type.lower() == "sla":
                from ..prompts import get_system_prompt
                system = get_system_prompt("sla_recovery_agent")
            else:
                system = f"You are an expert document analyzer specializing in {doc_type_config.description}. Provide analysis in valid JSON format only."

            # Call LLM API
            response = self.call_claude(
                prompt=prompt,
                system=system,
                use_thinking=self.thinking_enabled and "opus-4-6" in self.model
            )

            # Extract JSON from response
            extracted_json = self.extract_json_from_response(response["content"])

            # Check if extraction resulted in an error
            has_error = extracted_json.get("status") == "error" or extracted_json.get("type") in ["llm_error", "extraction_error", "json_extraction_error"]

            return {
                "extraction": extracted_json,
                "document_type": document_type,
                "model_used": response["model"],
                "cached": response["cached"],
                "usage": response["usage"],
                "thinking": response.get("thinking", ""),
                "raw_response": response["content"],
                "timestamp": response["timestamp"],
                "extraction_error": has_error,
                "extraction_error_type": extracted_json.get("type", None) if has_error else None,
            }

        except Exception as e:
            error_msg = f"Document analysis failed: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            return {
                "extraction": {
                    "status": "error",
                    "error": error_msg,
                    "type": "analysis_exception",
                    "fallback": True
                },
                "document_type": document_type,
                "model_used": "error",
                "cached": False,
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "thinking": "",
                "raw_response": error_msg,
                "timestamp": datetime.now().isoformat(),
                "extraction_error": True,
                "extraction_error_type": "analysis_exception",
            }


# Global LLM service instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def call_claude(
    prompt: str,
    system: str = "",
    **kwargs
) -> str:
    """Convenience function to call Claude"""
    service = get_llm_service()
    response = service.call_claude(prompt, system, **kwargs)
    return response["content"]
