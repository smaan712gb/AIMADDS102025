"""
LLM Factory for creating and managing AI model instances
"""
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from openai import AsyncOpenAI
from loguru import logger

from .config import get_config, AIModelConfig


class LLMFactory:
    """Factory for creating LLM instances"""
    
    def __init__(self):
        """Initialize LLM factory"""
        self.config = get_config()
        self._llm_cache = {}
    
    def get_llm(self, model_name: str) -> BaseChatModel:
        """
        Get or create an LLM instance
        
        Args:
            model_name: Name of the model (gemini, claude, grok)
        
        Returns:
            LLM instance
        """
        if model_name in self._llm_cache:
            return self._llm_cache[model_name]
        
        llm = self._create_llm(model_name)
        self._llm_cache[model_name] = llm
        return llm
    
    def _create_llm(self, model_name: str) -> BaseChatModel:
        """
        Create a new LLM instance
        
        Args:
            model_name: Name of the model (gemini, claude, grok)
        
        Returns:
            LLM instance
        """
        model_config = self.config.get_model_config(model_name)
        
        if model_name == "claude":
            return self._create_claude(model_config)
        elif model_name == "gemini":
            return self._create_gemini(model_config)
        elif model_name == "grok":
            return self._create_grok(model_config)
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    def _create_claude(self, config: AIModelConfig) -> ChatAnthropic:
        """Create Claude model instance"""
        api_key = self.config.get_api_key("anthropic")
        
        logger.info(f"Creating Claude model: {config.model_name}")
        
        return ChatAnthropic(
            model=config.model_name,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=120.0,
            max_retries=3
        )
    
    def _create_gemini(self, config: AIModelConfig) -> ChatGoogleGenerativeAI:
        """Create Gemini model instance"""
        api_key = self.config.get_api_key("google")
        
        logger.info(f"Creating Gemini model: {config.model_name}")
        
        return ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=api_key,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
            timeout=120.0,
            max_retries=3
        )
    
    def _create_grok(self, config: AIModelConfig) -> BaseChatModel:
        """
        Create Grok model instance
        Note: Using OpenAI SDK with custom base URL for X.AI Grok
        """
        from langchain_openai import ChatOpenAI
        
        # CRITICAL FIX: Use XAI_API_KEY, not OPENAI_API_KEY
        api_key = self.config.get_api_key("xai")
        
        logger.info(f"Creating Grok model: {config.model_name} (via X.AI API)")
        
        return ChatOpenAI(
            model=config.model_name,
            api_key=api_key,
            base_url="https://api.x.ai/v1",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=120.0,
            max_retries=3
        )
    
    async def get_async_openai_client(self) -> AsyncOpenAI:
        """
        Get async X.AI client for direct API calls (Grok)
        Used for streaming and advanced features
        
        Returns:
            AsyncOpenAI client configured for X.AI
        """
        # CRITICAL FIX: Use XAI_API_KEY for Grok, not OPENAI_API_KEY
        api_key = self.config.get_api_key("xai")
        return AsyncOpenAI(api_key=api_key, base_url="https://api.x.ai/v1")


# Global factory instance
_factory: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    """
    Get global LLM factory instance
    
    Returns:
        LLMFactory instance
    """
    global _factory
    if _factory is None:
        _factory = LLMFactory()
    return _factory


def get_llm(model_name: str) -> BaseChatModel:
    """
    Convenience function to get LLM instance
    
    Args:
        model_name: Name of the model (gemini, claude, grok)
    
    Returns:
        LLM instance
    """
    factory = get_llm_factory()
    return factory.get_llm(model_name)
