"""
Windows Asyncio Event Loop Fix

This module fixes the Windows-specific issue where aiodns requires SelectorEventLoop
but Windows defaults to ProactorEventLoop.

The issue manifests as:
"aiodns needs a SelectorEventLoop on Windows"

This fix should be imported and called at the start of any async application on Windows.
"""
import sys
import asyncio
from loguru import logger


def setup_windows_event_loop():
    """
    Configure asyncio event loop for Windows compatibility with aiodns/aiohttp.
    
    On Windows, the default ProactorEventLoop doesn't work with aiodns.
    This function sets up SelectorEventLoop which is required for DNS resolution.
    
    Should be called once at application startup before any async operations.
    """
    if sys.platform == 'win32':
        try:
            # Check if we're already using SelectorEventLoop
            try:
                loop = asyncio.get_event_loop()
                if isinstance(loop, asyncio.SelectorEventLoop):
                    logger.info("Already using SelectorEventLoop on Windows")
                    return
            except RuntimeError:
                pass  # No event loop exists yet
            
            # Set the event loop policy to use SelectorEventLoop
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logger.info("✅ Configured Windows to use SelectorEventLoop for aiodns compatibility")
            
        except Exception as e:
            logger.warning(f"Could not set Windows SelectorEventLoop: {e}")
            logger.warning("aiodns/aiohttp may encounter issues on this system")
    else:
        logger.debug("Not on Windows, no event loop adjustment needed")


def get_windows_compatible_event_loop():
    """
    Get or create an event loop that's compatible with aiodns on Windows.
    
    Returns:
        asyncio.AbstractEventLoop: Event loop instance
    """
    if sys.platform == 'win32':
        # Ensure Windows is using SelectorEventLoop
        setup_windows_event_loop()
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# Auto-setup on import for convenience
if __name__ != "__main__":
    setup_windows_event_loop()
