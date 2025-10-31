"""
Caching Layer for LLM Responses and Financial Calculations

Reduces redundant API calls and speeds up synthesis process.
"""

import json
import hashlib
import time
from typing import Any, Optional, Dict
from dataclasses import dataclass, asdict
from loguru import logger
import pickle
from pathlib import Path


@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    value: Any
    timestamp: float
    ttl_seconds: int
    hit_count: int = 0


class CacheManager:
    """
    Simple in-memory cache with TTL support
    
    Features:
    - TTL-based expiration
    - Hit counting for analytics
    - Serialization support
    - Cache statistics
    """
    
    def __init__(
        self,
        default_ttl: int = 3600,
        max_size: int = 1000,
        enable_persistence: bool = False,
        cache_dir: str = "data/cache"
    ):
        """
        Initialize cache manager
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum cache entries
            enable_persistence: Whether to persist cache to disk
            cache_dir: Directory for persistent cache
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enable_persistence = enable_persistence
        self.cache_dir = Path(cache_dir)
        
        self._cache: Dict[str, CacheEntry] = {}
        self._statistics = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
        if enable_persistence:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_persistent_cache()
        
        logger.info(f"Cache Manager initialized: ttl={default_ttl}s, max_size={max_size}")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create deterministic string representation
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        
        # Hash for shorter keys
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._statistics["misses"] += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if time.time() - entry.timestamp > entry.ttl_seconds:
            del self._cache[key]
            self._statistics["misses"] += 1
            return None
        
        # Update hit count
        entry.hit_count += 1
        self._statistics["hits"] += 1
        
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        # Evict oldest entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl_seconds=ttl or self.default_ttl
        )
        
        self._cache[key] = entry
        
        if self.enable_persistence:
            self._persist_entry(entry)
    
    def _evict_oldest(self) -> None:
        """Evict oldest cache entry"""
        if not self._cache:
            return
        
        # Find entry with oldest timestamp
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].timestamp
        )
        
        del self._cache[oldest_key]
        self._statistics["evictions"] += 1
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Statistics dictionary
        """
        total_requests = self._statistics["hits"] + self._statistics["misses"]
        hit_rate = (
            self._statistics["hits"] / total_requests * 100
            if total_requests > 0 else 0
        )
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._statistics["hits"],
            "misses": self._statistics["misses"],
            "evictions": self._statistics["evictions"],
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    def _persist_entry(self, entry: CacheEntry) -> None:
        """Persist cache entry to disk"""
        try:
            cache_file = self.cache_dir / f"{entry.key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.warning(f"Failed to persist cache entry: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Load persistent cache from disk"""
        try:
            if not self.cache_dir.exists():
                return
            
            loaded = 0
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                        
                    # Check if expired
                    if time.time() - entry.timestamp <= entry.ttl_seconds:
                        self._cache[entry.key] = entry
                        loaded += 1
                    else:
                        # Remove expired file
                        cache_file.unlink()
                        
                except Exception as e:
                    logger.warning(f"Failed to load cache entry {cache_file}: {e}")
            
            if loaded > 0:
                logger.info(f"Loaded {loaded} entries from persistent cache")
                
        except Exception as e:
            logger.warning(f"Failed to load persistent cache: {e}")


class LLMResponseCache:
    """
    Specialized cache for LLM responses
    
    Caches LLM responses based on prompt + model parameters.
    """
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize LLM response cache
        
        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager
        logger.info("LLM Response Cache initialized")
    
    def get_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        Get cached LLM response
        
        Args:
            prompt: Prompt text
            model: Model name
            temperature: Temperature setting
            max_tokens: Max tokens
            
        Returns:
            Cached response or None
        """
        key = self.cache._generate_key(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return self.cache.get(key)
    
    def cache_response(
        self,
        prompt: str,
        model: str,
        response: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache LLM response
        
        Args:
            prompt: Prompt text
            model: Model name
            response: LLM response
            temperature: Temperature setting
            max_tokens: Max tokens
            ttl: Cache TTL
        """
        key = self.cache._generate_key(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        self.cache.set(key, response, ttl)


class FinancialCalculationCache:
    """
    Specialized cache for financial calculations
    
    Caches DCF, LBO, and other calculations.
    """
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize financial calculation cache
        
        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager
        logger.info("Financial Calculation Cache initialized")
    
    def get_calculation(
        self,
        calculation_type: str,
        **params
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached calculation result
        
        Args:
            calculation_type: Type of calculation (e.g., 'dcf_standard')
            **params: Calculation parameters
            
        Returns:
            Cached result or None
        """
        key = self.cache._generate_key(
            type=calculation_type,
            **params
        )
        
        return self.cache.get(key)
    
    def cache_calculation(
        self,
        calculation_type: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None,
        **params
    ) -> None:
        """
        Cache calculation result
        
        Args:
            calculation_type: Type of calculation
            result: Calculation result
            ttl: Cache TTL
            **params: Calculation parameters
        """
        key = self.cache._generate_key(
            type=calculation_type,
            **params
        )
        
        # Financial calculations can be cached longer (they're deterministic)
        if ttl is None:
            ttl = 7200  # 2 hours
        
        self.cache.set(key, result, ttl)


# Global cache instances
_global_cache_manager: Optional[CacheManager] = None
_llm_cache: Optional[LLMResponseCache] = None
_calc_cache: Optional[FinancialCalculationCache] = None


def get_cache_manager(
    enable_caching: bool = True,
    **kwargs
) -> Optional[CacheManager]:
    """
    Get or create global cache manager
    
    Args:
        enable_caching: Whether caching is enabled
        **kwargs: Additional cache manager arguments
        
    Returns:
        Cache manager instance or None if disabled
    """
    global _global_cache_manager
    
    if not enable_caching:
        return None
    
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager(**kwargs)
    
    return _global_cache_manager


def get_llm_cache(enable_caching: bool = True) -> Optional[LLMResponseCache]:
    """
    Get or create global LLM cache
    
    Args:
        enable_caching: Whether caching is enabled
        
    Returns:
        LLM cache instance or None if disabled
    """
    global _llm_cache
    
    if not enable_caching:
        return None
    
    if _llm_cache is None:
        cache_manager = get_cache_manager(enable_caching=True)
        if cache_manager:
            _llm_cache = LLMResponseCache(cache_manager)
    
    return _llm_cache


def get_calculation_cache(enable_caching: bool = True) -> Optional[FinancialCalculationCache]:
    """
    Get or create global calculation cache
    
    Args:
        enable_caching: Whether caching is enabled
        
    Returns:
        Calculation cache instance or None if disabled
    """
    global _calc_cache
    
    if not enable_caching:
        return None
    
    if _calc_cache is None:
        cache_manager = get_cache_manager(enable_caching=True)
        if cache_manager:
            _calc_cache = FinancialCalculationCache(cache_manager)
    
    return _calc_cache
