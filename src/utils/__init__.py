# Utils module

from .windows_asyncio_fix import setup_windows_event_loop, get_windows_compatible_event_loop

__all__ = ['setup_windows_event_loop', 'get_windows_compatible_event_loop']
