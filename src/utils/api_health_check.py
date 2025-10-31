"""
API Health Check System
Validates all API credentials and connectivity before workflow execution
Prevents wasted time on failed runs due to API issues
"""
import os
import asyncio
from typing import Dict, List, Tuple
from loguru import logger
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class APIHealthChecker:
    """Validates API credentials and connectivity"""
    
    def __init__(self):
        """Initialize health checker"""
        self.results = {}
        self.critical_apis = ['anthropic', 'fmp']  # Must have these
        self.optional_apis = ['google', 'openai', 'tavily']  # Nice to have
        
    async def check_all_apis(self) -> Dict[str, any]:
        """
        Check all configured APIs
        
        Returns:
            Dictionary with health status for each API
        """
        logger.info("🔍 Starting API health checks...")
        
        checks = [
            self._check_anthropic(),
            self._check_google(),
            self._check_openai(),
            self._check_fmp(),
            self._check_tavily()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Process results
        self.results = {
            'anthropic': results[0],
            'google': results[1],
            'openai': results[2],
            'fmp': results[3],
            'tavily': results[4],
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._determine_overall_status()
        }
        
        self._display_results()
        
        return self.results
    
    async def _check_anthropic(self) -> Dict[str, any]:
        """Check Anthropic API"""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                return {'status': 'missing', 'message': 'API key not configured'}
            
            if not ANTHROPIC_AVAILABLE:
                return {'status': 'error', 'message': 'anthropic package not installed'}
            
            # Test API with minimal request
            client = anthropic.Anthropic(api_key=api_key)
            
            # Quick test with very short message
            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            return {
                'status': 'healthy',
                'message': 'Connected successfully',
                'model': 'claude-sonnet-4-5'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)[:100]}'
            }
    
    async def _check_google(self) -> Dict[str, any]:
        """Check Google AI API"""
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                return {'status': 'missing', 'message': 'API key not configured'}
            
            # Try to import and use Google AI API
            try:
                import google.generativeai as genai
                
                # Configure and test
                genai.configure(api_key=api_key)
                
                # Test with minimal request
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = model.generate_content("Hi", generation_config={'max_output_tokens': 10})
                
                return {
                    'status': 'healthy',
                    'message': 'Connected successfully',
                    'model': 'gemini-2.0-flash-exp'
                }
            except ImportError:
                return {'status': 'error', 'message': 'google-generativeai package not installed'}
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)[:100]}'
            }
    
    async def _check_openai(self) -> Dict[str, any]:
        """Check OpenAI API"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                return {'status': 'missing', 'message': 'API key not configured (optional)'}
            
            if not OPENAI_AVAILABLE:
                return {'status': 'warning', 'message': 'openai package not installed (optional)'}
            
            # Test connection
            client = openai.OpenAI(api_key=api_key)
            
            # Minimal test
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            
            return {
                'status': 'healthy',
                'message': 'Connected successfully',
                'model': 'gpt-5'
            }
            
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Optional API - {str(e)[:100]}'
            }
    
    async def _check_fmp(self) -> Dict[str, any]:
        """Check Financial Modeling Prep API"""
        try:
            api_key = os.getenv('FMP_API_KEY')
            
            if not api_key:
                return {'status': 'missing', 'message': 'API key not configured'}
            
            if not REQUESTS_AVAILABLE:
                return {'status': 'error', 'message': 'requests package not installed'}
            
            # Test with profile endpoint (lightweight)
            url = f"https://financialmodelingprep.com/api/v3/profile/AAPL?apikey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return {
                        'status': 'healthy',
                        'message': 'Connected successfully',
                        'note': 'Financial data API operational'
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': 'Unexpected response format'
                    }
            elif response.status_code == 401:
                return {
                    'status': 'error',
                    'message': 'Invalid API key'
                }
            elif response.status_code == 429:
                return {
                    'status': 'warning',
                    'message': 'Rate limit exceeded - too many requests'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP {response.status_code}'
                }
            
        except requests.Timeout:
            return {
                'status': 'error',
                'message': 'Connection timeout'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)[:100]}'
            }
    
    async def _check_tavily(self) -> Dict[str, any]:
        """Check Tavily API (optional) - REAL TEST"""
        try:
            api_key = os.getenv('TAVILY_API_KEY')
            
            if not api_key:
                return {'status': 'missing', 'message': 'API key not configured (optional)'}
            
            # Actually test Tavily with a real search
            try:
                from tavily import TavilyClient
                
                client = TavilyClient(api_key=api_key)
                
                # Perform minimal test search
                test_result = client.search(
                    query="test",
                    search_depth="basic",
                    max_results=1
                )
                
                if test_result and 'results' in test_result:
                    return {
                        'status': 'healthy',
                        'message': 'Real-time web search operational',
                        'note': 'External validation enabled'
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': 'Search returned no results (optional)'
                    }
                    
            except ImportError:
                return {'status': 'warning', 'message': 'tavily-python not installed (optional)'}
            except Exception as search_error:
                error_str = str(search_error)
                # Check for specific errors
                if '402' in error_str or 'Payment Required' in error_str:
                    return {
                        'status': 'configured',
                        'message': 'API key valid but needs credits',
                        'note': 'Add credits at https://tavily.com to enable'
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': f'Optional API - {error_str[:100]}'
                    }
            
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Optional API - {str(e)[:100]}'
            }
    
    def _determine_overall_status(self) -> str:
        """Determine overall system health"""
        # Check critical APIs
        for api in self.critical_apis:
            if api in self.results:
                status = self.results[api].get('status')
                if status in ['missing', 'error']:
                    return 'unhealthy'
        
        return 'healthy'
    
    def _display_results(self):
        """Display health check results"""
        print("\n" + "="*80)
        print("API HEALTH CHECK RESULTS".center(80))
        print("="*80 + "\n")
        
        # Critical APIs
        print("🔴 CRITICAL APIs (Required):")
        for api in self.critical_apis:
            if api in self.results:
                self._print_api_status(api, self.results[api], critical=True)
        
        print("\n🟡 OPTIONAL APIs:")
        for api in self.optional_apis:
            if api in self.results:
                self._print_api_status(api, self.results[api], critical=False)
        
        print("\n" + "="*80)
        overall = self.results.get('overall_status', 'unknown')
        if overall == 'healthy':
            print("✅ OVERALL STATUS: HEALTHY - Ready to proceed")
        else:
            print("❌ OVERALL STATUS: UNHEALTHY - Fix critical issues before proceeding")
        print("="*80 + "\n")
    
    def _print_api_status(self, api: str, result: Dict, critical: bool = False):
        """Print individual API status"""
        status = result.get('status', 'unknown')
        message = result.get('message', '')
        
        # Status icons
        if status == 'healthy':
            icon = "✅"
        elif status == 'configured':
            icon = "⚙️"
        elif status == 'warning':
            icon = "⚠️"
        elif status == 'missing':
            icon = "❌" if critical else "⏭️"
        else:
            icon = "❌"
        
        print(f"  {icon} {api.upper()}: {status.upper()}")
        if message:
            print(f"     └─ {message}")
        if 'model' in result:
            print(f"     └─ Model: {result['model']}")
        if 'note' in result:
            print(f"     └─ {result['note']}")
    
    def is_healthy(self) -> bool:
        """Check if system is healthy enough to proceed"""
        return self.results.get('overall_status') == 'healthy'
    
    def get_unhealthy_apis(self) -> List[str]:
        """Get list of unhealthy critical APIs"""
        unhealthy = []
        for api in self.critical_apis:
            if api in self.results:
                status = self.results[api].get('status')
                if status in ['missing', 'error']:
                    unhealthy.append(api)
        return unhealthy


async def run_health_check() -> Tuple[bool, Dict]:
    """
    Convenience function to run health check
    
    Returns:
        Tuple of (is_healthy, results_dict)
    """
    checker = APIHealthChecker()
    results = await checker.check_all_apis()
    is_healthy = checker.is_healthy()
    
    if not is_healthy:
        unhealthy = checker.get_unhealthy_apis()
        logger.error(f"❌ Critical APIs unhealthy: {', '.join(unhealthy)}")
        logger.error("Fix API configuration before proceeding")
    
    return is_healthy, results


# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        is_healthy, results = await run_health_check()
        print(f"\nSystem ready: {is_healthy}")
        return results
    
    asyncio.run(test())
