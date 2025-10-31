"""
LLM Call Retry Utility - Investment Banking Quality Standard

Provides robust retry logic with exponential backoff and intelligent fallbacks.
Primary: Agent's configured LLM (3 retries) → Fallback: Claude 4.5 (3 retries)
"""
import asyncio
import traceback
from typing import Any, Optional, List
from loguru import logger


async def llm_call_with_retry(
    llm: Any,
    messages: Any,
    max_retries: int = 3,
    timeout: int = 90,
    context: str = "LLM call",
    enable_fallback: bool = True
) -> Any:
    """
    Execute LLM call with retry logic and intelligent fallback chain.
    
    Investment Banking Standard:
    - Primary: Agent's configured LLM with 3 retry attempts
    - Fallback: Claude 4.5 with 3 retry attempts if primary fails
    - Exponential backoff between retries
    - Complete error tracking
    
    Args:
        llm: Primary LLM instance to call
        messages: Messages to send to LLM
        max_retries: Number of retry attempts per model (default 3)
        timeout: Timeout per attempt in seconds (default 90)
        context: Description of what this call is for (for logging)
        enable_fallback: Whether to use Gemini fallback if primary fails (default True)
    
    Returns:
        LLM response
        
    Raises:
        RuntimeError: If all models fail after retries
    """
    # Try primary LLM (agent's configured model)
    try:
        return await _try_llm_with_retries(
            llm=llm,
            messages=messages,
            max_retries=max_retries,
            timeout=timeout,
            context=context,
            model_name="Primary"
        )
    except RuntimeError as primary_error:
        if not enable_fallback:
            raise
        
        logger.warning(f"{context}: Primary model failed, switching to Claude 4.5 fallback...")
        
        # Try Claude 4.5 fallback
        try:
            from ..core.llm_factory import get_llm
            claude = get_llm('claude')
            
            response = await _try_llm_with_retries(
                llm=claude,
                messages=messages,
                max_retries=max_retries,
                timeout=120,  # Give Claude more time
                context=context,
                model_name="Fallback (Claude 4.5)"
            )
            
            logger.info(f"{context}: Successfully completed using Claude 4.5 fallback")
            return response
            
        except Exception as fallback_error:
            # Both models failed - provide comprehensive error
            full_error = (
                f"CRITICAL FAILURE: {context} failed on both primary and fallback models\n"
                f"Primary Error: {str(primary_error)}\n"
                f"Fallback Error: {str(fallback_error)}\n"
            )
            logger.error(full_error)
            raise RuntimeError(f"Critical: {context} failed on all models - Primary: {str(primary_error)}, Fallback: {str(fallback_error)}")


async def _try_llm_with_retries(
    llm: Any,
    messages: Any,
    max_retries: int,
    timeout: int,
    context: str,
    model_name: str
) -> Any:
    """
    Try an LLM with retry logic.
    
    Args:
        llm: LLM instance
        messages: Messages to send
        max_retries: Number of retry attempts
        timeout: Timeout per attempt
        context: Call context
        model_name: Name of model for logging
    
    Returns:
        LLM response
        
    Raises:
        RuntimeError: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            logger.debug(f"{context} [{model_name}]: Attempt {attempt + 1}/{max_retries}")
            
            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=timeout
            )
            
            if attempt > 0:
                logger.info(f"{context} [{model_name}]: Succeeded on attempt {attempt + 1}")
            
            return response
            
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                error_msg = f"{model_name} timed out after {max_retries} attempts ({timeout}s each)"
                logger.error(f"{context}: {error_msg}")
                raise RuntimeError(error_msg)
            
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logger.info(f"{context} [{model_name}]: Timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else "No error message provided"
            
            if attempt == max_retries - 1:
                full_error = f"{model_name} failed - {error_type}: {error_msg}"
                logger.error(f"{context}: {full_error}\n{traceback.format_exc()}")
                raise RuntimeError(full_error)
            
            wait_time = 2 ** attempt
            logger.info(f"{context} [{model_name}]: {error_type} on attempt {attempt + 1}, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    # Should never reach here
    raise RuntimeError(f"Retry logic error in {model_name}")


async def llm_call_with_retry_str(
    llm: Any,
    prompt: str,
    max_retries: int = 3,
    timeout: int = 90,
    context: str = "LLM call",
    enable_fallback: bool = True
) -> Any:
    """
    Execute LLM call with string prompt (wrapper for llm_call_with_retry).
    
    Args:
        llm: LLM instance
        prompt: String prompt
        max_retries: Retry attempts
        timeout: Timeout per attempt
        context: Call description
        enable_fallback: Whether to use Gemini fallback
    
    Returns:
        LLM response
        
    Raises:
        RuntimeError: If all models fail
    """
    return await llm_call_with_retry(llm, prompt, max_retries, timeout, context, enable_fallback)
