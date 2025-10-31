"""
Financial Modeling Prep (FMP) API Client with async support
Handles parallel data fetching for financial analysis
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from loguru import logger

from ..core.config import get_config


class FMPClient:
    """Async client for Financial Modeling Prep API"""
    
    def __init__(self):
        """Initialize FMP client"""
        self.config = get_config()
        self.api_key = self.config.get_api_key("fmp")
        # Base URL without version (we'll add version per endpoint)
        self.base_domain = "https://financialmodelingprep.com/api"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Endpoint-to-version mapping for correct API routing
        self.endpoint_versions = {
            # v3 endpoints (most financial data)
            'profile/': 'v3',
            'income-statement/': 'v3',
            'balance-sheet-statement/': 'v3',
            'cash-flow-statement/': 'v3',
            'ratios/': 'v3',
            'key-metrics/': 'v3',
            'discounted-cash-flow/': 'v3',
            'enterprise-values/': 'v3',
            'financial-growth/': 'v3',
            'income-statement-growth/': 'v3',
            'balance-sheet-statement-growth/': 'v3',
            'cash-flow-statement-growth/': 'v3',
            'market-capitalization/': 'v3',
            
            # v4 endpoints (newer features)
            'stock-peers': 'v4',
            'levered-discounted-cash-flow': 'v4',
            'company-outlook': 'v4',
            'analyst-estimates/': 'v4',
            'price-target/': 'v4',
            'insider-trading': 'v4',
            'economic_calendar': 'v4',
            'stock-screener': 'v3',
            'sector-performance': 'v3',
            
            # v3 but special format
            'income-statement-as-reported/': 'v3',
            'balance-sheet-statement-as-reported/': 'v3',
            'cash-flow-statement-as-reported/': 'v3',
            'key-metrics-ttm/': 'v3',
            'ratios-ttm/': 'v3',
            'sec_filings/': 'v3',
            'treasury': 'v4',
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_api_version(self, endpoint: str) -> str:
        """Determine the correct API version for an endpoint"""
        # Check if endpoint matches any known pattern
        for pattern, version in self.endpoint_versions.items():
            if endpoint.startswith(pattern) or pattern in endpoint:
                return version
        # Default to v3 for unknown endpoints
        return 'v3'
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make async API request with dynamic version routing
        
        Args:
            endpoint: API endpoint
            params: Query parameters
        
        Returns:
            API response data
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        if params is None:
            params = {}
        
        params["apikey"] = self.api_key
        
        # Dynamically determine correct API version
        api_version = self._get_api_version(endpoint)
        url = f"{self.base_domain}/{api_version}/{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug(f"FMP API request successful: {endpoint} (using {api_version})")
                return data
        except aiohttp.ClientError as e:
            logger.error(f"FMP API request failed: {endpoint} (v{api_version}) - {e}")
            raise
    
    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Get company profile information
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Company profile data
        """
        data = await self._make_request(f"profile/{symbol}")
        return data[0] if data else {}
    
    async def get_income_statement(self, symbol: str, period: str = "annual", limit: int = 5, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get income statements with enhanced date filtering

        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            from_date: Start date (YYYY-MM-DD) - NEW
            to_date: End date (YYYY-MM-DD) - NEW

        Returns:
            List of income statements
        """
        params = {"period": period, "limit": limit}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self._make_request(f"income-statement/{symbol}", params)
    
    async def get_balance_sheet(self, symbol: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get balance sheets
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of balance sheets
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"balance-sheet-statement/{symbol}", params)
    
    async def get_cash_flow_statement(self, symbol: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get cash flow statements
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of cash flow statements
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"cash-flow-statement/{symbol}", params)
    
    async def get_key_metrics(self, symbol: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get key financial metrics
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of key metrics
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"key-metrics/{symbol}", params)
    
    async def get_financial_ratios(self, symbol: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get financial ratios
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of financial ratios
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"ratios/{symbol}", params)
    
    async def get_company_outlook(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive company outlook
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Company outlook data
        """
        return await self._make_request(f"company-outlook", {"symbol": symbol})
    
    async def get_dcf(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get discounted cash flow valuation
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            DCF valuation data
        """
        return await self._make_request(f"discounted-cash-flow/{symbol}")
    
    async def get_historical_price(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data
        
        Args:
            symbol: Stock ticker symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        
        Returns:
            Historical price data
        """
        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        return await self._make_request(f"historical-price-full/{symbol}", params)
    
    async def get_cash_flow_growth(self, symbol: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get cash flow statement growth metrics
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of cash flow growth metrics
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"cash-flow-statement-growth/{symbol}", params)
    
    async def get_income_statement_as_reported(self, symbol: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get income statement as reported (GAAP vs non-GAAP)
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of as-reported income statements
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"income-statement-as-reported/{symbol}", params)
    
    async def get_balance_sheet_as_reported(self, symbol: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get balance sheet as reported
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of as-reported balance sheets
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"balance-sheet-statement-as-reported/{symbol}", params)
    
    async def get_cash_flow_as_reported(self, symbol: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get cash flow statement as reported
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of as-reported cash flow statements
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"cash-flow-statement-as-reported/{symbol}", params)
    
    async def get_earning_call_transcript(self, symbol: str, year: int, quarter: int) -> Dict[str, Any]:
        """
        Get earnings call transcript
        
        Args:
            symbol: Stock ticker symbol
            year: Year of the earnings call
            quarter: Quarter (1-4)
        
        Returns:
            Earnings call transcript data
        """
        return await self._make_request(f"earning_call_transcript/{symbol}", {"year": year, "quarter": quarter})
    
    async def get_earning_call_transcripts_list(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get list of available earnings call transcripts
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            List of available transcripts
        """
        return await self._make_request(f"earning_call_transcript", {"symbol": symbol})
    
    async def get_sec_filings(self, symbol: str, filing_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get SEC filings for a company
        
        Args:
            symbol: Stock ticker symbol
            filing_type: Type of filing (e.g., '10-K', '10-Q', '8-K')
            limit: Number of filings to retrieve
        
        Returns:
            List of SEC filings
        """
        params = {"limit": limit}
        if filing_type:
            params["type"] = filing_type
        return await self._make_request(f"sec_filings/{symbol}", params)
    
    async def get_sec_rss_feeds(self, symbol: str, filing_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get SEC RSS feed for latest filings
        
        Args:
            symbol: Stock ticker symbol
            filing_type: Type of filing (e.g., '10-K', '10-Q', '8-K')
            limit: Number of filings to retrieve
        
        Returns:
            List of recent SEC filings from RSS
        """
        params = {"limit": limit}
        if filing_type:
            params["type"] = filing_type
        return await self._make_request(f"rss_feed", {"symbol": symbol, **params})
    
    async def get_financial_growth(self, symbol: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get financial statement growth metrics
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of growth metrics
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"financial-growth/{symbol}", params)
    
    async def get_income_growth(self, symbol: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get income statement growth metrics
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of income growth metrics
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"income-statement-growth/{symbol}", params)
    
    async def get_balance_sheet_growth(self, symbol: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get balance sheet growth metrics
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of balance sheet growth metrics
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"balance-sheet-statement-growth/{symbol}", params)
    
    async def get_market_cap(self, symbol: str) -> Dict[str, Any]:
        """
        Get current market capitalization
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Market cap data
        """
        data = await self._make_request(f"market-capitalization/{symbol}")
        return data[0] if data else {}
    
    async def get_enterprise_value(self, symbol: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get enterprise value calculations
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of enterprise value data
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"enterprise-values/{symbol}", params)
    
    async def get_key_metrics_ttm(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get trailing twelve months (TTM) key metrics
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            TTM metrics
        """
        return await self._make_request(f"key-metrics-ttm/{symbol}")
    
    async def get_ratios_ttm(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get trailing twelve months (TTM) financial ratios
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            TTM ratios
        """
        return await self._make_request(f"ratios-ttm/{symbol}")
    
    async def get_analyst_estimates(self, symbol: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get analyst estimates
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
        
        Returns:
            List of analyst estimates
        """
        params = {"period": period, "limit": limit}
        return await self._make_request(f"analyst-estimates/{symbol}", params)
    
    async def get_price_target(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get analyst price targets
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Price target data
        """
        return await self._make_request(f"price-target/{symbol}")
    
    async def get_insider_trading(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get insider trading activity
        
        Args:
            symbol: Stock ticker symbol
            limit: Number of transactions to retrieve
        
        Returns:
            List of insider trades
        """
        params = {"limit": limit}
        return await self._make_request(f"insider-trading", {"symbol": symbol, **params})
    
    async def get_stock_peers(self, symbol: str) -> Dict[str, Any]:
        """
        Get peer companies for competitive analysis
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Dictionary with peer list
        """
        data = await self._make_request(f"stock-peers", {"symbol": symbol})
        # Returns format: [{"symbol": "NVDA", "peersList": ["AMD", "INTC", ...]}]
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return {"symbol": symbol, "peersList": []}
    
    async def get_levered_dcf(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get levered discounted cash flow valuation from FMP
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Levered DCF valuation data
        """
        return await self._make_request(f"levered-discounted-cash-flow", {"symbol": symbol})
    
    async def get_treasury_rates(self, maturity: str = "10year") -> List[Dict[str, Any]]:
        """
        Get current treasury rates
        
        Args:
            maturity: Treasury maturity ('1month', '3month', '6month', '1year', '2year', '3year', '5year', '7year', '10year', '20year', '30year')
        
        Returns:
            List with treasury rate data
        """
        # FMP endpoint: treasury
        data = await self._make_request("treasury")
        # Filter by maturity if available
        if isinstance(data, list) and data:
            for item in data:
                if maturity in item.get('maturity', '').lower():
                    return [item]
            # Return first item if specific maturity not found
            return [data[0]]
        return [{"maturity": maturity, "value": 4.5}]  # Default fallback
    
    async def get_economic_calendar(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get economic calendar events
        
        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        
        Returns:
            List of economic events
        """
        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        return await self._make_request("economic_calendar", params)
    
    async def get_sector_performance(self) -> List[Dict[str, Any]]:
        """
        Get current sector performance metrics
        
        Returns:
            List of sector performance data
        """
        return await self._make_request("sector-performance")
    
    async def get_stock_screener(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Screen stocks based on criteria
        
        Args:
            **kwargs: Screening criteria (marketCapMoreThan, marketCapLowerThan, 
                     priceMoreThan, priceLowerThan, betaMoreThan, betaLowerThan,
                     volumeMoreThan, volumeLowerThan, dividendMoreThan, dividendLowerThan,
                     isEtf, isActivelyTrading, sector, industry, country, exchange, limit)
        
        Returns:
            List of stocks matching criteria
        """
        return await self._make_request("stock-screener", kwargs)
    
    async def get_custom_dcf_levered(self, symbol: str) -> Dict[str, Any]:
        """
        Get FMP's custom levered DCF valuation for external validation
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            FMP's DCF analysis with their assumptions
        """
        data = await self._make_request(f"levered-discounted-cash-flow", {"symbol": symbol})
        return data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else {}
    
    async def get_stock_news(self, tickers: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent stock news for sentiment analysis
        
        Args:
            tickers: Stock ticker symbol(s) - can be comma-separated
            limit: Number of news articles to retrieve
        
        Returns:
            List of news articles with dates, sources, sentiment
        """
        params = {"tickers": tickers, "limit": limit}
        return await self._make_request("stock_news", params)
    
    async def get_institutional_ownership(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get institutional ownership data (smart money positioning)
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            List of institutional holders with positions
        """
        return await self._make_request(f"institutional-holder/{symbol}")
    
    async def get_earnings_surprises(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get earnings surprise history (beat/miss analysis)
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            List of earnings surprises showing actual vs. estimated
        """
        return await self._make_request(f"earnings-surprises/{symbol}")
    
    async def fetch_all_financial_data(self, symbol: str, extended: bool = True) -> Dict[str, Any]:
        """
        Fetch all financial data in parallel for comprehensive analysis
        
        FISCAL YEAR INTELLIGENCE:
        - Detects company's fiscal year end (handles non-calendar year filers)
        - Fetches latest 10-K + all 10-Qs since last 10-K
        - Ensures most recent data for normalization and forecasting
        - Critical for companies like Walmart (Jan 31), Oracle (May 31), etc.
        
        Args:
            symbol: Stock ticker symbol
            extended: If True, fetch extended dataset (10 years + quarterly data)
        
        Returns:
            Dictionary with all financial data including fiscal year metadata
        """
        logger.info(f"Fetching comprehensive financial data for {symbol} (extended={extended})")
        logger.info("🗓️ FISCAL YEAR INTELLIGENCE: Detecting fiscal year end and latest filings...")
        
        # Step 1: Get company profile to determine fiscal year end
        profile = await self.get_company_profile(symbol)
        fiscal_year_end = self._detect_fiscal_year_end(profile, symbol)
        
        logger.info(f"✓ Detected fiscal year end: {fiscal_year_end}")
        
        # Step 2: Calculate intelligent date ranges for data fetching
        date_ranges = self._calculate_fiscal_intelligent_ranges(fiscal_year_end, extended)
        
        logger.info(f"✓ Fetching data from {date_ranges['from_date']} to {date_ranges['to_date']}")
        logger.info(f"✓ Target: Last 10-K + {date_ranges['expected_quarters']} quarters of 10-Qs")
        
        # Base tasks (always fetch) - NOW WITH FISCAL INTELLIGENCE
        tasks = {
            "profile": self.get_company_profile(symbol),
            "income_statement": self.get_income_statement(
                symbol, 
                limit=10 if extended else 5,
                from_date=date_ranges['from_date'],
                to_date=date_ranges['to_date']
            ),
            "balance_sheet": self.get_balance_sheet(symbol, limit=10 if extended else 5),
            "cash_flow": self.get_cash_flow_statement(symbol, limit=10 if extended else 5),
            "key_metrics": self.get_key_metrics(symbol, limit=10 if extended else 5),
            "ratios": self.get_financial_ratios(symbol, limit=10 if extended else 5),
            "outlook": self.get_company_outlook(symbol),
            "dcf": self.get_dcf(symbol),
            "market_cap": self.get_market_cap(symbol),
            "enterprise_value": self.get_enterprise_value(symbol),
        }
        
        # Extended tasks for Phase 2 professional analysis
        if extended:
            extended_tasks = {
                # Quarterly data for trend analysis (20 quarters = 5 years)
                "income_statement_quarterly": self.get_income_statement(symbol, period="quarter", limit=20),
                "balance_sheet_quarterly": self.get_balance_sheet(symbol, period="quarter", limit=20),
                "cash_flow_quarterly": self.get_cash_flow_statement(symbol, period="quarter", limit=20),
                
                # Growth metrics
                "financial_growth": self.get_financial_growth(symbol, limit=10),
                "income_growth": self.get_income_growth(symbol, limit=10),
                "balance_sheet_growth": self.get_balance_sheet_growth(symbol, limit=10),
                "cash_flow_growth": self.get_cash_flow_growth(symbol, limit=10),
                
                # As-reported data (GAAP vs non-GAAP detection)
                "income_as_reported": self.get_income_statement_as_reported(symbol, limit=10),
                "balance_as_reported": self.get_balance_sheet_as_reported(symbol, limit=10),
                "cash_flow_as_reported": self.get_cash_flow_as_reported(symbol, limit=10),
                
                # TTM data for most recent analysis
                "key_metrics_ttm": self.get_key_metrics_ttm(symbol),
                "ratios_ttm": self.get_ratios_ttm(symbol),
                
                # Analyst data
                "analyst_estimates": self.get_analyst_estimates(symbol),
                "price_target": self.get_price_target(symbol),
                
                # Insider activity
                "insider_trading": self.get_insider_trading(symbol, limit=100),
                
                # SEC filings metadata
                "sec_filings": self.get_sec_filings(symbol, limit=100),
                
                # NEW: Enhanced validation and market intelligence
                "custom_dcf_levered": self.get_custom_dcf_levered(symbol),
                "stock_news": self.get_stock_news(symbol, limit=50),
                "institutional_ownership": self.get_institutional_ownership(symbol),
                "earnings_surprises": self.get_earnings_surprises(symbol),
            }
            tasks.update(extended_tasks)
        
        # Execute all requests in parallel
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )
        
        # Map results back to keys
        financial_data = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {key} for {symbol}: {result}")
                financial_data[key] = None
            else:
                financial_data[key] = result
        
        logger.info(f"Completed fetching financial data for {symbol}")
        return financial_data
    
    def _detect_fiscal_year_end(self, profile: Dict[str, Any], symbol: str) -> str:
        """
        UNIVERSAL: Dynamically detects ANY company's fiscal year end
        
        ⚠️ NO HARDCODING - This is a DYNAMIC function that:
        1. Reads 'fiscalYearEnd' from the company profile DATA
        2. Works for ANY company with ANY fiscal year end
        3. Not limited to specific tickers or companies
        
        Examples below are ILLUSTRATIVE ONLY (showing the variety handled):
        - Calendar year companies (12-31): Most tech, most finance
        - January fiscal (01-31): Walmart, Target, Best Buy, etc.
        - May fiscal (05-31): Oracle, etc.
        - September fiscal (09-30): Apple, etc.
        - ANY month (01-31 through 12-31): Handled dynamically
        
        The function reads from DATA, not from hardcoded logic.
        
        Args:
            profile: Company profile (from ANY data source with fiscalYearEnd field)
            symbol: Ticker symbol for logging only
        
        Returns:
            Fiscal year end as "MM-DD" (dynamically read from profile data)
        """
        # DYNAMIC: Reads from profile data (works for ALL companies)
        if profile and 'fiscalYearEnd' in profile:
            fiscal_end = profile['fiscalYearEnd']
            logger.info(f"✓ {symbol}: Fiscal year end DYNAMICALLY DETECTED: {fiscal_end}")
            return fiscal_end
        
        # Fallback: Try alternate field names (data source agnostic)
        alternate_fields = ['fiscal_period_end', 'fyEnd', 'fiscal_year_end_date']
        for field in alternate_fields:
            if profile and field in profile:
                fiscal_end = profile[field]
                logger.info(f"✓ {symbol}: Fiscal year end from {field}: {fiscal_end}")
                return fiscal_end
        
        # Last resort: Default to calendar year
        logger.warning(f"⚠️ {symbol}: Fiscal year end not in profile, defaulting to calendar year (12-31)")
        logger.warning(f"   → For accuracy, ensure data source provides fiscalYearEnd field")
        return "12-31"
    
    def _calculate_fiscal_intelligent_ranges(
        self, 
        fiscal_year_end: str,
        extended: bool
    ) -> Dict[str, Any]:
        """
        Calculate intelligent date ranges based on fiscal year
        
        Ensures we get:
        - Last 10 fiscal years of 10-Ks
        - Plus all 10-Qs filed since last 10-K
        
        Args:
            fiscal_year_end: Fiscal year end as "MM-DD"
            extended: If True, get 10 years; else 5 years
        
        Returns:
            Dict with from_date, to_date, and expected quarters
        """
        try:
            # Parse fiscal year end
            month, day = map(int, fiscal_year_end.split('-'))
            
            # Current date
            today = datetime.now()
            current_year = today.year
            current_month = today.month
            current_day = today.day
            
            # Determine most recent fiscal year end
            fiscal_end_this_year = datetime(current_year, month, day)
            
            if today < fiscal_end_this_year:
                # Haven't reached this year's fiscal end yet
                most_recent_fy_end = datetime(current_year - 1, month, day)
                current_fiscal_year = current_year - 1
            else:
                # Past this year's fiscal end
                most_recent_fy_end = fiscal_end_this_year
                current_fiscal_year = current_year
            
            # Calculate how many quarters since last 10-K
            days_since_fy_end = (today - most_recent_fy_end).days
            expected_quarters = min(3, days_since_fy_end // 90)  # Roughly 90 days per quarter
            
            # Calculate from_date (10 years back for extended, 5 for basic)
            years_back = 10 if extended else 5
            from_year = current_fiscal_year - years_back
            from_date = f"{from_year}-{month:02d}-{day:02d}"
            
            # to_date is today
            to_date = today.strftime('%Y-%m-%d')
            
            logger.info(f"✓ Fiscal intelligence: FY ends {fiscal_year_end}, most recent: {most_recent_fy_end.strftime('%Y-%m-%d')}")
            logger.info(f"✓ Current fiscal year: FY{current_fiscal_year}, {expected_quarters} quarters elapsed")
            
            return {
                'from_date': from_date,
                'to_date': to_date,
                'fiscal_year_end': fiscal_year_end,
                'most_recent_fy_end': most_recent_fy_end.strftime('%Y-%m-%d'),
                'current_fiscal_year': current_fiscal_year,
                'expected_quarters': expected_quarters,
                'days_since_fy_end': days_since_fy_end
            }
            
        except Exception as e:
            logger.error(f"Error calculating fiscal ranges: {e}")
            # Fallback to simple date range
            years_back = 10 if extended else 5
            from_date = (datetime.now() - timedelta(days=365 * years_back)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            return {
                'from_date': from_date,
                'to_date': to_date,
                'fiscal_year_end': '12-31',
                'expected_quarters': 0,
                'fallback': True
            }
    
    async def fetch_multiple_companies(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch financial data for multiple companies in parallel
        
        Args:
            symbols: List of stock ticker symbols
        
        Returns:
            Dictionary mapping symbols to their financial data
        """
        logger.info(f"Fetching data for {len(symbols)} companies in parallel")
        
        tasks = [self.fetch_all_financial_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        company_data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch data for {symbol}: {result}")
                company_data[symbol] = None
            else:
                company_data[symbol] = result
        
        return company_data


async def get_financial_data(symbol: str) -> Dict[str, Any]:
    """
    Convenience function to fetch financial data for a single company
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Financial data dictionary
    """
    async with FMPClient() as client:
        return await client.fetch_all_financial_data(symbol)


async def get_multiple_companies_data(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to fetch financial data for multiple companies
    
    Args:
        symbols: List of stock ticker symbols
    
    Returns:
        Dictionary mapping symbols to their financial data
    """
    async with FMPClient() as client:
        return await client.fetch_multiple_companies(symbols)
