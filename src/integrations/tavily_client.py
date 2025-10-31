"""
Tavily Search Client - Real-time web search for AI agents

Provides production-grade web search capabilities for external validation:
- Real-time access to Wall Street analyst reports
- Recent SEC filings and financial news
- Earnings transcripts and market data
- AI-optimized search results

Used by: External Validator Agent
"""
import os
from typing import Dict, List, Any, Optional
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("Tavily library not installed. Run: pip install tavily-python")


class TavilySearchClient:
    """
    Client for Tavily web search API
    
    Tavily is optimized for AI agents conducting research, providing:
    - Structured, relevant results
    - Automatic content extraction
    - Source attribution
    - Real-time web data
    """
    
    def __init__(self):
        """Initialize Tavily client with API key from environment"""
        if not TAVILY_AVAILABLE:
            raise ImportError("Tavily library not available. Install with: pip install tavily-python")
        
        self.api_key = os.getenv('TAVILY_API_KEY')
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        
        self.client = TavilyClient(api_key=self.api_key)
        logger.info("✓ Tavily web search client initialized")
    
    async def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform web search using Tavily
        
        Args:
            query: Search query string
            search_depth: "basic" (faster) or "advanced" (more comprehensive)
            max_results: Number of results to return (1-20)
            include_domains: List of domains to prioritize (e.g., ["bloomberg.com"])
            exclude_domains: List of domains to exclude
        
        Returns:
            Dictionary with search results and AI-generated answer
        """
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,  # Don't need full HTML
                "include_images": False
            }
            
            # Add domain filters if specified
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            
            logger.info(f"Tavily search: '{query}' (depth={search_depth}, max={max_results})")
            
            # Execute search
            results = self.client.search(**search_params)
            
            # Extract and structure results
            search_results = {
                'success': True,
                'query': query,
                'answer': results.get('answer', ''),
                'results': results.get('results', []),
                'result_count': len(results.get('results', [])),
                'search_depth': search_depth
            }
            
            logger.info(f"✓ Tavily returned {search_results['result_count']} results")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Tavily search error for '{query}': {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'results': [],
                'result_count': 0
            }
    
    async def search_financial_data(
        self,
        company: str,
        topic: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Specialized search for financial/analyst data
        
        Prioritizes financial news sources and analyst firms
        
        Args:
            company: Company name or ticker
            topic: What to search for (e.g., "revenue forecast", "valuation")
            max_results: Number of results
        
        Returns:
            Search results prioritizing financial sources
        """
        # Build financial-focused query
        query = f"{company} {topic} analyst consensus 2025"
        
        # Prioritize financial sources
        financial_domains = [
            "bloomberg.com",
            "reuters.com",
            "wsj.com",
            "ft.com",
            "seekingalpha.com",
            "yahoo.com/finance",
            "cnbc.com",
            "marketwatch.com"
        ]
        
        return await self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=financial_domains
        )
    
    def parse_search_results(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and extract structured information from search results
        
        Args:
            search_results: Raw results from search()
        
        Returns:
            Structured data with confidence scoring
        """
        if not search_results.get('success'):
            return {
                'confidence': 'none',
                'sources': [],
                'summary': 'Search failed'
            }
        
        results = search_results.get('results', [])
        
        # Extract source information
        sources = []
        financial_sources = 0
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            content = result.get('content', '')
            
            # Check if it's a financial source
            is_financial = any(domain in url.lower() for domain in [
                'bloomberg', 'reuters', 'wsj', 'ft.com', 'seeking', 
                'yahoo.com/finance', 'cnbc', 'marketwatch'
            ])
            
            if is_financial:
                financial_sources += 1
            
            sources.append({
                'title': title,
                'url': url,
                'snippet': content[:200] + '...' if len(content) > 200 else content,
                'is_financial_source': is_financial
            })
        
        # Determine confidence based on source quality
        if financial_sources >= 3:
            confidence = 'high'
        elif financial_sources >= 1:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'confidence': confidence,
            'sources': sources,
            'financial_source_count': financial_sources,
            'total_sources': len(sources),
            'summary': search_results.get('answer', 'No summary available')
        }


# Global client instance
_tavily_client: Optional[TavilySearchClient] = None


def get_tavily_client() -> Optional[TavilySearchClient]:
    """
    Get global Tavily client instance
    
    Returns:
        TavilySearchClient instance or None if not available
    """
    global _tavily_client
    
    if _tavily_client is None:
        try:
            _tavily_client = TavilySearchClient()
        except (ImportError, ValueError) as e:
            logger.warning(f"Tavily client not available: {e}")
            return None
    
    return _tavily_client
