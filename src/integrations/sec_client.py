"""
SEC EDGAR Client - Fetches SEC filings (10-K, 10-Q, 8-K, etc.)

Phase 2 Enhancements:
- Full text extraction from 10-K/10-Q filings
- Risk Factors (Item 1A) extraction and year-over-year tracking
- MD&A section analysis using sec-parser library
- Footnote mining for debt covenants, pension liabilities, off-balance-sheet items
- Related party transaction detection
- Management tone sentiment analysis

Uses sec-parser library for robust semantic parsing of SEC filings.
"""
import os
import time
import re
from typing import Dict, List, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from loguru import logger
import asyncio
import aiohttp
from datetime import datetime

try:
    import sec_parser
    from sec_downloader import Downloader
    # Check if the needed components are available
    available_components = []
    try:
        from sec_parser import Edgar10QParser
        available_components.append('Edgar10QParser')
    except ImportError:
        pass
    try:
        from sec_parser.semantic_elements import TitleElement, TextElement
        available_components.append('semantic_elements')
    except ImportError:
        pass

    SEC_PARSER_AVAILABLE = len(available_components) > 0
    logger.info(f"sec-parser available with components: {available_components}")
except ImportError as e:
    SEC_PARSER_AVAILABLE = False
    logger.warning(f"sec-parser library not available: {e}. Install with: pip install sec-parser")


class SECClient:
    """
    Enhanced Client for fetching and analyzing SEC EDGAR filings
    
    Provides access to:
    - 10-K (Annual Reports) - Full text extraction
    - 10-Q (Quarterly Reports) - Full text extraction
    - 8-K (Current Reports)
    - Risk Factors (Item 1A) extraction and tracking
    - MD&A section analysis
    - Footnote mining
    - Related party transaction detection
    """
    
    def __init__(self):
        """Initialize SEC EDGAR client with LLM-powered extraction"""
        self.base_url = "https://www.sec.gov"
        self.headers = {
            "User-Agent": "AIMADDS102025 smaan2011@gmail.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        self.rate_limit_delay = 0.1  # SEC requires 10 requests per second max
        
        # Initialize LLM for intelligent section extraction
        self.llm = None
        try:
            from anthropic import Anthropic
            import os
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.llm = Anthropic(api_key=api_key)
                logger.info("✓ LLM-powered SEC extraction ENABLED")
            else:
                logger.warning("⚠️ ANTHROPIC_API_KEY not found - LLM extraction unavailable")
        except ImportError:
            logger.warning("⚠️ Anthropic library not available - LLM extraction unavailable")
        
        # Phase 2: Keywords for deep analysis
        self.risk_keywords = [
            'risk', 'uncertain', 'volatility', 'litigation', 'competition',
            'regulatory', 'compliance', 'cybersecurity', 'economic conditions'
        ]
        
        self.debt_keywords = [
            'covenant', 'debt agreement', 'credit facility', 'loan agreement',
            'indebtedness', 'default', 'principal amount', 'interest rate'
        ]
        
        self.related_party_keywords = [
            'related party', 'affiliated', 'director', 'officer', 'executive',
            'shareholder', 'family member', 'controlled entity'
        ]
        
        self.off_balance_sheet_keywords = [
            'off-balance-sheet', 'operating lease', 'purchase obligation',
            'guarantee', 'indemnification', 'contingent liability'
        ]
    
    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK (Central Index Key) for a company ticker
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            CIK string (10 digits, zero-padded)
        """
        try:
            # Use SEC's company tickers JSON
            url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            ticker_upper = ticker.upper()
            
            for item in data.values():
                if item.get('ticker') == ticker_upper:
                    cik = str(item['cik_str']).zfill(10)
                    logger.info(f"Found CIK for {ticker}: {cik}")
                    return cik
            
            logger.warning(f"CIK not found for ticker: {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get CIK for {ticker}: {e}")
            return None
    
    def get_latest_filings(
        self,
        ticker: str,
        filing_types: List[str] = None,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get latest SEC filings for a company - VIEW ALL by default
        
        UNIVERSAL DESIGN:
        - Default (filing_types=None): Fetches ALL filing types (comprehensive M&A view)
        - Specific types: Pass list of filing types to filter
        
        Critical M&A filing types that will be included:
        - 10-K, 10-Q: Financial statements
        - 8-K: Material events
        - DEF 14A: Proxy statements (compensation, governance)
        - S-4: Business combinations
        - SC 13D/13G: Beneficial ownership (>5% shareholders)
        - SC TO: Tender offers
        - 13F: Institutional holdings
        - And ALL other filing types

        Args:
            ticker: Stock ticker
            filing_types: List of specific filing types, or None for ALL (view all)
            count: Number of filings to retrieve (default 100 for comprehensive view)

        Returns:
            List of filing information with date validation
        """
        # VIEW ALL by default - do NOT limit filing types
        if filing_types is None:
            # Fetch ALL filings - no type filter
            filing_types = ['']  # Empty string = all types in SEC API
            logger.info(f"Fetching ALL filing types for {ticker} (comprehensive M&A view)")
        else:
            logger.info(f"Fetching specific filing types for {ticker}: {filing_types}")

        try:
            cik = self.get_company_cik(ticker)
            if not cik:
                return []

            time.sleep(self.rate_limit_delay)

            # Get filing submissions
            url = f"{self.base_url}/cgi-bin/browse-edgar"
            params = {
                "action": "getcompany",
                "CIK": cik,
                "type": "",
                "dateb": "",
                "owner": "exclude",
                "count": count,
                "output": "atom"
            }

            filings = []
            for filing_type in filing_types:
                params["type"] = filing_type
                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code == 200:
                    # Parse filing information with date extraction
                    filing_info = self._parse_filing_with_dates(response.text, ticker, cik, filing_type)
                    if filing_info:
                        filings.extend(filing_info)
                        logger.info(f"Retrieved {len(filing_info)} {filing_type} filing(s) for {ticker}")

                time.sleep(self.rate_limit_delay)

            # Sort by date (newest first) and validate freshness
            filings.sort(key=lambda x: x.get('filing_date', ''), reverse=True)

            # Validate and log freshness
            for filing in filings[:3]:  # Check top 3
                filing_date = filing.get('filing_date')
                if filing_date:
                    try:
                        f_date = datetime.strptime(filing_date, '%Y-%m-%d')
                        days_old = (datetime.now() - f_date).days

                        if days_old > 365:
                            logger.warning(f"⚠️ {filing.get('type')} filing for {ticker} is {days_old} days old ({filing_date})")
                        else:
                            logger.info(f"✓ {filing.get('type')} filing for {ticker} is fresh ({days_old} days old, {filing_date})")
                    except ValueError:
                        logger.warning(f"⚠️ Could not parse filing date: {filing_date}")

            return filings

        except Exception as e:
            logger.error(f"Failed to get filings for {ticker}: {e}")
            return []

    def _parse_filing_with_dates(self, xml_content: str, ticker: str, cik: str, filing_type: str) -> List[Dict[str, Any]]:
        """
        Parse SEC filing XML and extract filing dates

        Args:
            xml_content: Raw XML response from SEC
            ticker: Company ticker
            cik: Company CIK
            filing_type: Type of filing

        Returns:
            List of filing information with dates
        """
        try:
            # Try lxml parser first, fallback to html.parser
            try:
                soup = BeautifulSoup(xml_content, 'lxml-xml')
            except:
                try:
                    soup = BeautifulSoup(xml_content, 'lxml')
                except:
                    soup = BeautifulSoup(xml_content, 'html.parser')

            entries = soup.find_all('entry')
            filings = []

            for entry in entries:
                # Extract filing date
                filing_date_element = entry.find('filing-date') or entry.find('accepted-date')
                filing_date = filing_date_element.text if filing_date_element else None

                # Extract accession number
                accession_element = entry.find('accession-number')
                accession_number = accession_element.text.replace('-', '') if accession_element else None

                # Extract primary document
                primary_doc_element = entry.find('primary-document')
                primary_document = primary_doc_element.text if primary_doc_element else None

                # Construct filing URL
                if accession_number and primary_document:
                    filing_url = f"{self.base_url}/Archives/edgar/data/{cik}/{accession_number}/{primary_document}"
                else:
                    filing_url = f"{self.base_url}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}"

                filing_info = {
                    "ticker": ticker,
                    "cik": cik,
                    "type": filing_type,
                    "filing_date": filing_date,
                    "accession_number": accession_number,
                    "primary_document": primary_document,
                    "filing_url": filing_url,
                    "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Validate date
                if filing_date:
                    try:
                        datetime.strptime(filing_date, '%Y-%m-%d')
                        filings.append(filing_info)
                    except ValueError:
                        logger.warning(f"Invalid filing date format: {filing_date}")
                else:
                    # Include even without date for completeness
                    filings.append(filing_info)

            return filings

        except Exception as e:
            logger.error(f"Error parsing filing XML: {e}")
            return []
    
    def get_filing_summary(
        self,
        ticker: str,
        filing_type: str = "10-K"
    ) -> Dict[str, Any]:
        """
        Get summary information about latest filing
        
        Args:
            ticker: Stock ticker
            filing_type: Type of filing
        
        Returns:
            Filing summary
        """
        try:
            cik = self.get_company_cik(ticker)
            if not cik:
                return {}
            
            return {
                "ticker": ticker,
                "cik": cik,
                "filing_type": filing_type,
                "sec_url": f"{self.base_url}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}",
                "note": "Full text extraction requires additional parsing"
            }
            
        except Exception as e:
            logger.error(f"Failed to get filing summary: {e}")
            return {}
    
    def get_all_filings_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive filing information
        
        Args:
            ticker: Stock ticker
        
        Returns:
            Comprehensive filing information
        """
        logger.info(f"Fetching SEC filings information for {ticker}")
        
        filings = self.get_latest_filings(ticker, ['10-K', '10-Q', '8-K'], count=5)
        
        return {
            "ticker": ticker,
            "cik": filings[0]['cik'] if filings else None,
            "available_filings": filings,
            "filing_count": len(filings),
            "sec_edgar_url": f"{self.base_url}/cgi-bin/browse-edgar?action=getcompany&CIK={filings[0]['cik']}" if filings else None
        }
    
    async def get_filing_full_text(
        self,
        ticker: str,
        filing_type: str = "10-K",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Phase 2: Get full text of SEC filing
        
        Args:
            ticker: Stock ticker
            filing_type: Type of filing ('10-K', '10-Q', '8-K')
            year: Specific year to retrieve (None for latest)
        
        Returns:
            Dictionary containing full text and metadata
        """
        try:
            logger.info(f"Fetching full text for {ticker} {filing_type} filing")
            
            cik = self.get_company_cik(ticker)
            if not cik:
                return {'error': 'CIK not found'}
            
            # Get filing URL and accession number
            filing_url, accession_number = await self._get_filing_url(cik, filing_type, year)
            
            if not filing_url:
                return {'error': 'Filing URL not found'}
            
            # Fetch and parse the filing
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(self.rate_limit_delay)
                async with session.get(filing_url, headers=self.headers) as response:
                    if response.status != 200:
                        return {'error': f'Failed to fetch filing: {response.status}'}
                    
                    html_content = await response.text()
            
            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get text
            full_text = soup.get_text(separator='\n', strip=True)
            
            return {
                'ticker': ticker,
                'filing_type': filing_type,
                'accession_number': accession_number,
                'filing_url': filing_url,
                'text_length': len(full_text),
                'full_text': full_text,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching full text: {e}")
            return {'error': str(e)}
    
    async def _get_filing_url(
        self,
        cik: str,
        filing_type: str,
        year: Optional[int]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the direct URL to a filing document (NOT the index page)

        Returns:
            Tuple of (filing_url, accession_number)
        """
        try:
            # Get submissions for the company
            submissions_url = f"{self.base_url}/cgi-bin/browse-edgar"
            params = {
                "action": "getcompany",
                "CIK": cik,
                "type": filing_type,
                "dateb": "",
                "owner": "exclude",
                "count": "10",
                "output": "atom"
            }

            response = requests.get(submissions_url, headers=self.headers, params=params)

            if response.status_code == 200:
                # Try lxml parser first, fallback to html.parser
                try:
                    soup = BeautifulSoup(response.text, 'lxml-xml')
                except:
                    try:
                        soup = BeautifulSoup(response.text, 'lxml')
                    except:
                        soup = BeautifulSoup(response.text, 'html.parser')
                entries = soup.find_all('entry')

                if entries:
                    # Get the first (most recent) entry
                    entry = entries[0]
                    accession_number = entry.find('accession-number')
                    
                    if accession_number:
                        accession_text = accession_number.text
                        accession_clean = accession_text.replace('-', '')
                        
                        # Get filing-href to find the index page first
                        filing_href = entry.find('filing-href')
                        if filing_href:
                            index_url = filing_href.text
                            
                            # Fetch the index page to find the actual document
                            await asyncio.sleep(self.rate_limit_delay)
                            index_response = requests.get(index_url, headers=self.headers)
                            
                            if index_response.status_code == 200:
                                index_soup = BeautifulSoup(index_response.text, 'html.parser')
                                
                                # Look for the actual 10-K/10-Q document (not -index.htm)
                                # Pattern: Look for .htm files that are NOT index files
                                document_table = index_soup.find('table', {'class': 'tableFile'})
                                
                                if document_table:
                                    rows = document_table.find_all('tr')[1:]  # Skip header
                                    
                                    for row in rows:
                                        cols = row.find_all('td')
                                        if len(cols) >= 4:
                                            doc_type = cols[3].text.strip()
                                            doc_link = cols[2].find('a')
                                            
                                            # Look for the main document (10-K or 10-Q)
                                            if doc_link and filing_type in doc_type.upper():
                                                doc_href = doc_link.get('href')
                                                if doc_href and not doc_href.endswith('-index.htm'):
                                                    # Extract the actual filename from the href
                                                    # Handle /ix?doc= format by extracting the document path
                                                    if '/ix?doc=' in doc_href:
                                                        # Extract the path after /ix?doc=
                                                        actual_path = doc_href.split('/ix?doc=')[1]
                                                        full_url = f"{self.base_url}{actual_path}"
                                                    elif doc_href.startswith('/'):
                                                        full_url = f"{self.base_url}{doc_href}"
                                                    else:
                                                        full_url = f"{self.base_url}/Archives/edgar/data/{cik}/{accession_clean}/{doc_href}"
                                                    
                                                    logger.info(f"Found actual filing document: {full_url}")
                                                    return full_url, accession_text
                        
                        # FALLBACK: Try common patterns for the actual document
                        # Pattern 1: Company ticker-based filename (e.g., crwd-20250131.htm)
                        ticker_lower = filing_href.text.split('/')[-1].split('-')[0] if filing_href else ''
                        
                        fallback_patterns = [
                            f"{ticker_lower}.htm",
                            f"{ticker_lower}-10k.htm",
                            f"{ticker_lower}-10q.htm",
                            f"d{accession_clean}.htm",
                        ]
                        
                        for pattern in fallback_patterns:
                            fallback_url = f"{self.base_url}/Archives/edgar/data/{cik}/{accession_clean}/{pattern}"
                            # Test if this URL exists
                            await asyncio.sleep(self.rate_limit_delay)
                            test_response = requests.head(fallback_url, headers=self.headers)
                            if test_response.status_code == 200:
                                logger.info(f"Using fallback filing URL: {fallback_url}")
                                return fallback_url, accession_text
                        
                        logger.warning(f"Could not find actual filing document, using index: {index_url}")
                        return index_url, accession_text

            return None, None

        except Exception as e:
            logger.error(f"Error getting filing URL: {e}")
            return None, None
    
    def _extract_section_with_sec_parser(
        self,
        html_content: str,
        section_name: str,
        filing_type: str = "10-K"
    ) -> Optional[str]:
        """
        Extract section using sec-parser library for semantic understanding
        
        Updated for sec-parser v0.58+ API using Edgar10QParser
        
        Args:
            html_content: Raw HTML content from SEC filing
            section_name: Name of section to extract (e.g., "RISK_FACTORS", "MANAGEMENT_DISCUSSION")
            filing_type: Type of filing
        
        Returns:
            Extracted section text or None
        """
        try:
            from sec_parser import Edgar10QParser
            from sec_parser.semantic_elements import TitleElement, TextElement
            
            # Parse the HTML using Edgar10QParser (works for 10-K too)
            parser = Edgar10QParser()
            elements = parser.parse(html_content)
            
            # Map section names to keywords in titles
            section_keywords = {
                "RISK_FACTORS": ["risk factors", "item 1a"],
                "MANAGEMENT_DISCUSSION": ["management's discussion", "item 7"],
                "BUSINESS": ["business", "item 1"],
                "PROPERTIES": ["properties", "item 2"],
                "LEGAL_PROCEEDINGS": ["legal proceedings", "item 3"],
                "MARKET_RISK": ["market risk", "item 7a"],
                "FINANCIAL_STATEMENTS": ["financial statements", "item 8"]
            }
            
            keywords = section_keywords.get(section_name.upper(), [])
            if not keywords:
                logger.warning(f"Unknown section name: {section_name}")
                return None
            
            # Find the section by looking for title elements containing keywords
            section_start = None
            section_text = []
            
            for i, element in enumerate(elements):
                if isinstance(element, TitleElement):
                    title_text = element.get_text().lower()
                    if any(keyword in title_text for keyword in keywords):
                        section_start = i
                        logger.info(f"Found section start for {section_name} at element {i}")
                        break
            
            if section_start is not None:
                # Collect text until next major section or end
                for element in elements[section_start + 1:]:
                    if isinstance(element, TitleElement):
                        title_text = element.get_text().lower()
                        # Stop if we hit another major section
                        if any(word in title_text for word in ["item", "part", "note"]):
                            break
                    if isinstance(element, (TextElement, TitleElement)):
                        text = element.get_text()
                        if text.strip():
                            section_text.append(text)
            
            extracted_text = ' '.join(section_text).strip()
            
            if extracted_text and len(extracted_text) > 500:
                logger.info(f"Successfully extracted {section_name} using sec-parser ({len(extracted_text)} chars)")
                return extracted_text
            else:
                logger.debug(f"sec-parser: {section_name} section too short or empty")
                return None
            
        except Exception as e:
            logger.error(f"Error using sec-parser for {section_name}: {e}")
            return None
    
    async def extract_risk_factors_reliable(
        self,
        ticker: str,
        num_years: int = 3
    ) -> Dict[str, Any]:
        """
        PRODUCTION-SAFE: Extract risk factors using sec-edgar-downloader
        
        This method uses the proven sec-edgar-downloader library.
        Falls back to existing methods if download fails.
        
        Priority:
        1. sec-edgar-downloader + sec-parser (MOST RELIABLE)
        2. FMP pre-parsed data (COMMERCIAL BACKUP)
        3. Existing extraction methods (FALLBACK)
        
        Returns:
            Risk factors with extraction status
        """
        try:
            from .sec_downloader_client import SECDownloaderClient
            from .fmp_client import FMPClient
            
            # METHOD 1: Use sec-edgar-downloader (BEST)
            try:
                downloader = SECDownloaderClient(
                    company_name="AIMADDS",
                    email="analysis@aimadds.com"
                )
                
                # Download recent 10-K filings
                filing_paths = downloader.download_10k(ticker, num_filings=num_years)
                
                if filing_paths:
                    logger.info(f"✓ Downloaded {len(filing_paths)} filings via sec-edgar-downloader")
                    
                    risk_factors_by_year = []
                    
                    for filing_path in filing_paths:
                        filing_text = downloader.read_filing_text(filing_path)
                        
                        if len(filing_text) < 1000:
                            continue
                        
                        # Use sec-parser to extract Item 1A
                        risk_text = await self._extract_section(filing_text, "Item 1A", "Item 1B")
                        
                        if risk_text and len(risk_text) >= 500:
                            analysis = self._analyze_risks(risk_text)
                            
                            risk_factors_by_year.append({
                                'year': filing_path.parent.name[:4] if len(filing_path.parent.name) >= 4 else 'unknown',
                                'risk_text': risk_text,
                                'risk_analysis': analysis,
                                'source': 'sec-edgar-downloader',
                                'file_path': str(filing_path)
                            })
                    
                    if risk_factors_by_year:
                        logger.info(f"✓ Extracted risks from {len(risk_factors_by_year)} filings")
                        
                        yoy_comparison = self._compare_risk_factors(risk_factors_by_year)
                        
                        return {
                            'ticker': ticker,
                            'extraction_method': 'sec-edgar-downloader',
                            'extraction_status': 'success',
                            'num_years_analyzed': len(risk_factors_by_year),
                            'risk_factors_by_year': risk_factors_by_year,
                            'year_over_year_comparison': yoy_comparison,
                            'new_risks_identified': yoy_comparison.get('new_risks', [])
                        }
            
            except Exception as e:
                logger.warning(f"sec-edgar-downloader failed: {e}, trying FMP")
            
            # METHOD 2: FMP pre-parsed data (COMMERCIAL BACKUP)
            try:
                async with FMPClient() as client:
                    # Check if FMP has risk factors method
                    if hasattr(client, 'get_risk_factors_from_fmp'):
                        fmp_risks = await client.get_risk_factors_from_fmp(ticker)
                        
                        if fmp_risks and 'riskFactors' in fmp_risks:
                            risk_text = fmp_risks['riskFactors']
                            
                            if len(risk_text) >= 500:
                                logger.info(f"✓ Using FMP pre-parsed risk factors")
                                
                                analysis = self._analyze_risks(risk_text)
                                
                                return {
                                    'ticker': ticker,
                                    'extraction_method': 'fmp_commercial',
                                    'extraction_status': 'success',
                                    'risk_factors_by_year': [{
                                        'year': datetime.now().year,
                                        'risk_text': risk_text,
                                        'risk_analysis': analysis,
                                        'source': 'FMP Commercial API'
                                    }],
                                    'num_years_analyzed': 1,
                                    'new_risks_identified': analysis.get('top_risks', [])[:10]
                                }
            except Exception as e:
                logger.warning(f"FMP extraction failed: {e}, trying existing methods")
            
            # METHOD 3: Use existing extraction methods (FALLBACK)
            logger.warning("All primary methods failed, using existing extraction")
            return await self.extract_risk_factors(ticker, "10-K", num_years)
            
        except Exception as e:
            logger.error(f"All extraction methods failed: {e}")
            return {
                'ticker': ticker,
                'extraction_status': 'failed',
                'error': str(e),
                'recommendation': 'Manual SEC filing review required'
            }
    
    async def extract_risk_factors(
        self,
        ticker: str,
        filing_type: str = "10-K",
        num_years: int = 3
    ) -> Dict[str, Any]:
        """
        Phase 2: Extract and analyze Risk Factors (Item 1A) from multiple years
        Uses sec-parser for robust semantic extraction
        
        Args:
            ticker: Stock ticker
            filing_type: Type of filing
            num_years: Number of years to analyze for comparison
        
        Returns:
            Risk factors analysis with year-over-year comparison
        """
        try:
            logger.info(f"Extracting risk factors for {ticker} over {num_years} years using sec-parser")
            
            risk_factors_by_year = []
            
            for year_offset in range(num_years):
                # Get filing for each year
                filing_data = await self.get_filing_full_text(ticker, filing_type)
                
                if 'full_text' in filing_data:
                    html_content = filing_data.get('full_text', '')
                    
                    # Try sec-parser first for semantic extraction
                    risk_section = None
                    if SEC_PARSER_AVAILABLE:
                        risk_section = self._extract_section_with_sec_parser(
                            html_content, 
                            "RISK_FACTORS", 
                            filing_type
                        )
                    
                    # Fallback to regex method if sec-parser fails
                    if not risk_section:
                        risk_section = await self._extract_section(html_content, "Item 1A", "Item 1B")
                    
                    if risk_section:
                        # Analyze risk factors
                        analysis = self._analyze_risks(risk_section)
                        risk_factors_by_year.append({
                            'year': datetime.now().year - year_offset,
                            'risk_text': risk_section,
                            'risk_analysis': analysis,
                            'accession_number': filing_data.get('accession_number'),
                            'extraction_method': 'sec-parser' if SEC_PARSER_AVAILABLE else 'regex'
                        })
                    else:
                        logger.warning(f"Could not extract risk factors for year offset {year_offset}")
                
                await asyncio.sleep(self.rate_limit_delay)
            
            # Compare year-over-year changes
            yoy_comparison = self._compare_risk_factors(risk_factors_by_year)
            
            return {
                'ticker': ticker,
                'num_years_analyzed': len(risk_factors_by_year),
                'risk_factors_by_year': risk_factors_by_year,
                'year_over_year_comparison': yoy_comparison,
                'new_risks_identified': yoy_comparison.get('new_risks', []),
                'removed_risks': yoy_comparison.get('removed_risks', [])
            }
            
        except Exception as e:
            logger.error(f"Error extracting risk factors: {e}")
            return {'error': str(e)}
    
    async def _extract_section(
        self,
        text: str,
        start_marker: str,
        end_marker: str
    ) -> Optional[str]:
        """
        Extract a specific section from filing text using INTELLIGENT MULTI-METHOD approach:
        
        Priority:
        1. LLM-powered extraction (MOST RELIABLE - understands document structure)
        2. HTML DOM parsing with BeautifulSoup
        3. Regex-based pattern matching
        
        This ensures "SEC provides full text" is actually used effectively,
        since LLM can understand and extract sections even when HTML parsing fails.
        
        Args:
            text: Full filing text (HTML)
            start_marker: Section start identifier (e.g., "Item 1A", "Item 7")
            end_marker: Section end identifier (e.g., "Item 1B", "Item 7A")
        
        Returns:
            Extracted section text
        """
        try:
            logger.info(f"Extracting section {start_marker} to {end_marker} using intelligent multi-method approach")
            
            # METHOD 1: LLM-Powered Extraction (BEST - handles ANY format)
            llm_extracted = await self._llm_extract_section(text, start_marker, end_marker)
            if llm_extracted and len(llm_extracted) >= 500:
                logger.info(f"✓ LLM successfully extracted {start_marker} ({len(llm_extracted)} chars)")
                return llm_extracted
            
            # METHOD 2: HTML DOM parsing (GOOD - structured documents)
            logger.info(f"LLM extraction unavailable, trying HTML DOM parsing...")
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')
            
            # Find all text nodes that might contain section markers
            # Common patterns in SEC filings:
            # - <b>Item 7.</b> or <b>ITEM 7.</b>
            # - <font>Item 7</font>
            # - <div>Item 7 - Management's Discussion</div>
            
            # Strategy: Find all elements, extract text, look for markers
            start_element = None
            end_element = None
            
            # Search through all elements
            all_elements = soup.find_all()
            
            for i, element in enumerate(all_elements):
                element_text = element.get_text(strip=True)
                
                # Check if this element contains start marker
                if not start_element:
                    # Flexible matching for start marker
                    if re.search(
                        rf'\bItem\s*{start_marker.split()[-1]}[\.\:\s]',
                        element_text,
                        re.IGNORECASE
                    ):
                        start_element = element
                        logger.info(f"Found start marker in element {i}: {element.name}")
                        continue
                
                # If we have start, look for end marker
                if start_element and not end_element:
                    if re.search(
                        rf'\bItem\s*{end_marker.split()[-1]}[\.\:\s]',
                        element_text,
                        re.IGNORECASE
                    ):
                        end_element = element
                        logger.info(f"Found end marker in element {i}: {element.name}")
                        break
            
            # Extract content between markers
            if start_element:
                extracted_text = []
                
                # Get all siblings between start and end
                current = start_element.next_sibling
                while current and current != end_element:
                    if hasattr(current, 'get_text'):
                        text_content = current.get_text(separator=' ', strip=True)
                        if text_content:
                            extracted_text.append(text_content)
                    elif isinstance(current, str):
                        text_content = current.strip()
                        if text_content:
                            extracted_text.append(text_content)
                    current = current.next_sibling
                
                result = ' '.join(extracted_text)
                
                # If we got meaningful content, return it
                if len(result) >= 500:
                    logger.info(f"Successfully extracted {start_marker} section ({len(result)} chars) using DOM parsing")
                    return result
                else:
                    logger.warning(f"DOM extraction found content but too short ({len(result)} chars)")
            
            # METHOD 3: Enhanced regex-based extraction on cleaned text
            logger.info("Falling back to enhanced regex-based extraction")
            
            # Clean text: remove excessive whitespace but preserve structure
            text_normalized = re.sub(r'\s+', ' ', text)
            
            # Extract item numbers for flexible matching
            start_item_num = start_marker.split()[-1].replace('.', '')
            end_item_num = end_marker.split()[-1].replace('.', '')
            
            # PRODUCTION-GRADE patterns with multiple variations
            patterns = [
                # Pattern 1: Standard "Item X." format with optional descriptive text
                re.compile(
                    rf'Item\s+{start_item_num}[\.\:]\s*[^\n]*?(.+?)(?=Item\s+{end_item_num}[\.\:]|$)',
                    re.IGNORECASE | re.DOTALL
                ),
                # Pattern 2: All caps "ITEM X" format
                re.compile(
                    rf'ITEM\s+{start_item_num}[\.\:]?\s*[^\n]*?(.+?)(?=ITEM\s+{end_item_num}[\.\:]?|$)',
                    re.DOTALL
                ),
                # Pattern 3: Bold marker format "<b>Item X</b>"
                re.compile(
                    rf'<b>Item\s+{start_item_num}[<\.\:].*?</b>(.+?)(?=<b>Item\s+{end_item_num}|$)',
                    re.IGNORECASE | re.DOTALL
                ),
                # Pattern 4: With full section name (e.g., "Item 7. Management's Discussion")
                re.compile(
                    rf'Item\s+{start_item_num}\s*[\.\:]?\s*Management[^\.]*?\.(.+?)(?=Item\s+{end_item_num}|$)',
                    re.IGNORECASE | re.DOTALL
                ),
                # Pattern 5: Flexible with any punctuation
                re.compile(
                    rf'Item\s+{start_item_num}[\.:\-\s]{{1,3}}(.+?)(?=Item\s+{end_item_num}[\.:\-\s]|$)',
                    re.IGNORECASE | re.DOTALL
                ),
                # Pattern 6: Look for table of contents anchor format
                re.compile(
                    rf'name="Item_{start_item_num}".*?>(.+?)(?=name="Item_{end_item_num}"|$)',
                    re.IGNORECASE | re.DOTALL
                ),
            ]
            
            best_match = None
            best_length = 0
            
            for i, pattern in enumerate(patterns):
                try:
                    match = pattern.search(text_normalized)
                    if match:
                        extracted = match.group(1).strip()
                        # Keep track of longest valid match
                        if len(extracted) >= 500 and len(extracted) > best_length:
                            best_match = extracted
                            best_length = len(extracted)
                            logger.info(f"Pattern {i+1} found match: {len(extracted)} chars")
                except Exception as e:
                    logger.debug(f"Pattern {i+1} failed: {e}")
                    continue
            
            if best_match:
                logger.info(f"✓ Regex extraction successful: {len(best_match):,} chars")
                return best_match
            
            logger.warning(f"Could not extract {start_marker} section using DOM or regex methods")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting section {start_marker}: {e}")
            return None
    
    async def _llm_extract_section(
        self,
        full_text: str,
        start_marker: str,
        end_marker: str
    ) -> Optional[str]:
        """
        LLM-POWERED: Intelligently extract SEC filing sections using Claude
        
        PRODUCTION-GRADE with smart chunking strategy for large sections
        
        Args:
            full_text: Complete SEC filing text (HTML or plain text)
            start_marker: Section start (e.g., "Item 1A", "Item 7")
            end_marker: Section end (e.g., "Item 1B", "Item 7A")
        
        Returns:
            Extracted section text or None
        """
        if not self.llm:
            logger.debug("LLM not available for section extraction")
            return None
        
        try:
            # SMART DETECTION: Check if this is a large section that needs chunking
            # Item 1A (Risk Factors) is typically very large (50K+ chars)
            start_item_num = start_marker.split()[-1].replace('.', '')
            is_large_section = start_item_num in ['1A', '7', '8']  # Risk Factors, MD&A, Financials
            
            # Quick size check - if we can find the section, check its size
            quick_regex_check = re.search(
                rf'(?i)item\s*{start_item_num}[\.:\s]',
                full_text
            )
            
            if quick_regex_check and is_large_section:
                # Estimate section size
                start_pos = quick_regex_check.start()
                estimated_section_size = len(full_text[start_pos:start_pos + 100000])
                
                # If large (>50K chars), use parallel chunked extraction
                if estimated_section_size > 50000:
                    logger.info(f"{start_marker} detected as large section, using parallel chunked extraction")
                    
                    from .sec_client_chunked import get_chunked_extractor
                    chunked_extractor = get_chunked_extractor()
                    
                    result = await chunked_extractor.extract_large_section_parallel(
                        full_text, start_marker, end_marker
                    )
                    
                    if result:
                        logger.info(f"✓ Chunked extraction successful for {start_marker}")
                        return result
                    else:
                        logger.warning(f"Chunked extraction failed for {start_marker}, falling back to standard method")
            
            # Standard extraction for smaller sections
            # Clean text for LLM (remove excess whitespace, but preserve structure)
            clean_text = re.sub(r'\n\s*\n', '\n\n', full_text)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            
            # SMART CHUNKING: Try to find the section in the text first
            # Look for the start marker in the full text to determine best chunk
            start_item_num = start_marker.split()[-1].replace('.', '')
            
            # Create multiple search patterns for flexibility
            search_patterns = [
                rf'(?i)item\s*{start_item_num}[\.:\s]',
                rf'(?i)ITEM\s*{start_item_num}[\.:\s]',
                rf'(?i)Item\s*{start_item_num}\.',
            ]
            
            start_pos = None
            for pattern in search_patterns:
                match = re.search(pattern, clean_text)
                if match:
                    start_pos = match.start()
                    logger.info(f"Found {start_marker} at position {start_pos}")
                    break
            
            # Extract relevant chunk (30K before, 120K after the section start)
            # Reduced from 50K/150K to stay within context limits for standard extraction
            if start_pos:
                chunk_start = max(0, start_pos - 30000)
                chunk_end = min(len(clean_text), start_pos + 120000)
                extraction_chunk = clean_text[chunk_start:chunk_end]
                logger.info(f"Using smart chunk: {len(extraction_chunk)} chars around {start_marker}")
            else:
                # Fallback: Use first 150K chars (most sections are in first half)
                extraction_chunk = clean_text[:150000]
                logger.info(f"Section position unknown, using first 150K chars")
            
            # Create improved extraction prompt with more flexibility
            prompt = f"""You are an expert SEC filing analyst. Extract the COMPLETE text of the section starting with "{start_marker}".

SEC FILING EXCERPT:
{extraction_chunk}

TASK:
1. Locate the section header that matches "{start_marker}" - this could appear as:
   - "Item {start_item_num}"
   - "ITEM {start_item_num}."
   - "Item {start_item_num}:"
   - Or similar variations

2. Extract ALL text from that section header until you reach:
   - "{end_marker}" section, OR
   - The next major Item section, OR
   - The end of the provided text

3. Return the COMPLETE extracted section text with NO summarization

4. If you cannot find the section clearly, return exactly: SECTION_NOT_FOUND

IMPORTANT: Return the full section text as it appears, preserving all details, tables, and formatting."""

            # Call Claude with streaming enabled for long operations
            extracted_text = ""
            
            with self.llm.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=32000,  # Doubled for longer sections
                temperature=0,  # Deterministic extraction
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            ) as stream:
                for text in stream.text_stream:
                    extracted_text += text
            
            extracted_text = extracted_text.strip()
            
            # Validate extraction with more flexible threshold
            if extracted_text == "SECTION_NOT_FOUND" or len(extracted_text) < 200:
                logger.warning(f"LLM could not extract {start_marker} (result: {len(extracted_text)} chars)")
                return None
            
            # Success - log details
            logger.info(f"✓ LLM successfully extracted {start_marker}: {len(extracted_text):,} chars")
            return extracted_text
            
        except Exception as e:
            logger.error(f"LLM extraction failed for {start_marker}: {e}")
            return None
    
    def _analyze_risks(self, risk_text: str) -> Dict[str, Any]:
        """
        Analyze risk factors text for key themes and sentiment
        
        Args:
            risk_text: Risk factors section text
        
        Returns:
            Risk analysis
        """
        risk_counts = {}
        
        # Count occurrences of risk keywords
        text_lower = risk_text.lower()
        for keyword in self.risk_keywords:
            count = text_lower.count(keyword)
            if count > 0:
                risk_counts[keyword] = count
        
        # Calculate risk score (based on frequency and severity keywords)
        total_risk_mentions = sum(risk_counts.values())
        risk_density = total_risk_mentions / max(len(risk_text), 1) * 10000  # Per 10K chars
        
        return {
            'risk_keyword_counts': risk_counts,
            'total_risk_mentions': total_risk_mentions,
            'risk_density': risk_density,
            'text_length': len(risk_text),
            'top_risks': sorted(risk_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _compare_risk_factors(
        self,
        risk_factors_by_year: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare risk factors year-over-year
        
        Args:
            risk_factors_by_year: List of risk factors by year
        
        Returns:
            Year-over-year comparison
        """
        if len(risk_factors_by_year) < 2:
            return {'note': 'Insufficient data for comparison'}
        
        # Compare most recent year with previous
        current = risk_factors_by_year[0]['risk_analysis']['risk_keyword_counts']
        prior = risk_factors_by_year[1]['risk_analysis']['risk_keyword_counts']
        
        # Identify new and removed risks
        current_keywords = set(current.keys())
        prior_keywords = set(prior.keys())
        
        new_risks = list(current_keywords - prior_keywords)
        removed_risks = list(prior_keywords - current_keywords)
        
        # Calculate changes in risk emphasis
        risk_changes = {}
        for keyword in current_keywords & prior_keywords:
            change = current[keyword] - prior[keyword]
            if abs(change) >= 2:  # Significant change threshold
                risk_changes[keyword] = {
                    'current_count': current[keyword],
                    'prior_count': prior[keyword],
                    'change': change,
                    'percent_change': (change / prior[keyword]) * 100 if prior[keyword] > 0 else 0
                }
        
        return {
            'new_risks': new_risks,
            'removed_risks': removed_risks,
            'risk_changes': risk_changes,
            'overall_trend': 'increasing' if len(new_risks) > len(removed_risks) else 'decreasing'
        }
    
    async def extract_mda_section(
        self,
        ticker: str,
        filing_type: str = "10-K"
    ) -> Dict[str, Any]:
        """
        Phase 2: Extract Management Discussion & Analysis section using sec-parser
        
        Args:
            ticker: Stock ticker
            filing_type: Type of filing
        
        Returns:
            MD&A section with analysis
        """
        try:
            logger.info(f"Extracting MD&A for {ticker} using sec-parser")
            
            filing_data = await self.get_filing_full_text(ticker, filing_type)
            
            if 'full_text' not in filing_data:
                return {'error': 'Filing text not available'}
            
            html_content = filing_data['full_text']
            
            # Try sec-parser first for semantic extraction
            mda_section = None
            extraction_method = 'none'
            
            if SEC_PARSER_AVAILABLE:
                mda_section = self._extract_section_with_sec_parser(
                    html_content,
                    "MANAGEMENT_DISCUSSION",
                    filing_type
                )
                if mda_section:
                    extraction_method = 'sec-parser'
            
            # Fallback to regex-based extraction
            if not mda_section:
                mda_section = await self._extract_section(html_content, "Item 7", "Item 7A")
                if mda_section:
                    extraction_method = 'regex_item7'
            
            if not mda_section:
                # Try alternative pattern
                mda_section = await self._extract_section(html_content, "Management's Discussion", "Quantitative and Qualitative")
                if mda_section:
                    extraction_method = 'regex_management'
            
            if mda_section:
                # Analyze management tone and key topics
                analysis = self._analyze_mda(mda_section)
                
                return {
                    'ticker': ticker,
                    'filing_type': filing_type,
                    'mda_text': mda_section,
                    'mda_length': len(mda_section),
                    'analysis': analysis,
                    'accession_number': filing_data.get('accession_number'),
                    'extraction_method': extraction_method
                }
            
            return {'error': 'MD&A section not found'}
            
        except Exception as e:
            logger.error(f"Error extracting MD&A: {e}")
            return {'error': str(e)}
    
    def _analyze_mda(self, mda_text: str) -> Dict[str, Any]:
        """
        Analyze MD&A section for tone and key topics
        
        Args:
            mda_text: MD&A section text
        
        Returns:
            MD&A analysis
        """
        # Positive and negative sentiment words
        positive_words = ['growth', 'increase', 'improve', 'strong', 'favorable', 'success', 'opportunity']
        negative_words = ['decline', 'decrease', 'weakness', 'challenging', 'adverse', 'risk', 'concern']
        
        text_lower = mda_text.lower()
        
        positive_count = sum(text_lower.count(word) for word in positive_words)
        negative_count = sum(text_lower.count(word) for word in negative_words)
        
        # Calculate sentiment score (-1 to 1)
        total_sentiment_words = positive_count + negative_count
        sentiment_score = (positive_count - negative_count) / max(total_sentiment_words, 1)
        
        return {
            'positive_tone_count': positive_count,
            'negative_tone_count': negative_count,
            'sentiment_score': sentiment_score,
            'overall_tone': 'positive' if sentiment_score > 0.2 else 'negative' if sentiment_score < -0.2 else 'neutral',
            'text_length': len(mda_text)
        }
    
    async def mine_footnotes(
        self,
        ticker: str,
        filing_type: str = "10-K"
    ) -> Dict[str, Any]:
        """
        Phase 2: Mine footnotes for debt covenants, pension liabilities, off-balance-sheet items
        
        Args:
            ticker: Stock ticker
            filing_type: Type of filing
        
        Returns:
            Footnote analysis
        """
        try:
            logger.info(f"Mining footnotes for {ticker}")
            
            filing_data = await self.get_filing_full_text(ticker, filing_type)
            
            if 'full_text' not in filing_data:
                return {'error': 'Filing text not available'}
            
            text = filing_data['full_text']
            
            # Search for key items in footnotes
            debt_findings = self._search_text_for_keywords(text, self.debt_keywords, context_chars=500)
            related_party_findings = self._search_text_for_keywords(text, self.related_party_keywords, context_chars=500)
            off_balance_findings = self._search_text_for_keywords(text, self.off_balance_sheet_keywords, context_chars=500)
            
            return {
                'ticker': ticker,
                'filing_type': filing_type,
                'debt_covenants': {
                    'found': len(debt_findings) > 0,
                    'count': len(debt_findings),
                    'excerpts': debt_findings[:5]  # Top 5
                },
                'related_party_transactions': {
                    'found': len(related_party_findings) > 0,
                    'count': len(related_party_findings),
                    'excerpts': related_party_findings[:5]
                },
                'off_balance_sheet_items': {
                    'found': len(off_balance_findings) > 0,
                    'count': len(off_balance_findings),
                    'excerpts': off_balance_findings[:5]
                },
                'accession_number': filing_data.get('accession_number')
            }
            
        except Exception as e:
            logger.error(f"Error mining footnotes: {e}")
            return {'error': str(e)}
    
    def _search_text_for_keywords(
        self,
        text: str,
        keywords: List[str],
        context_chars: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Search text for keywords and extract context
        
        Args:
            text: Text to search
            keywords: List of keywords to search for
            context_chars: Number of characters of context to extract
        
        Returns:
            List of findings with context
        """
        findings = []
        text_lower = text.lower()
        
        for keyword in keywords:
            # Find all occurrences
            start_pos = 0
            while True:
                pos = text_lower.find(keyword.lower(), start_pos)
                if pos == -1:
                    break
                
                # Extract context
                context_start = max(0, pos - context_chars // 2)
                context_end = min(len(text), pos + len(keyword) + context_chars // 2)
                context = text[context_start:context_end]
                
                findings.append({
                    'keyword': keyword,
                    'position': pos,
                    'context': context.strip()
                })
                
                start_pos = pos + 1
        
        return findings
    
    async def extract_proxy_data(
        self,
        ticker: str
    ) -> Dict[str, Any]:
        """
        Extract critical M&A data from DEF 14A proxy statements
        
        Extracts:
        - Executive compensation and employment agreements
        - Related party transactions
        - Board composition and governance
        - Change of control provisions
        
        Args:
            ticker: Stock ticker
        
        Returns:
            Proxy statement analysis
        """
        try:
            logger.info(f"Extracting proxy statement data for {ticker}")
            
            filing_data = await self.get_filing_full_text(ticker, 'DEF 14A')
            
            if 'error' in filing_data or 'full_text' not in filing_data:
                return {'error': 'Proxy statement not available'}
            
            text = filing_data['full_text']
            
            # Search for executive compensation
            compensation_keywords = [
                'executive compensation', 'summary compensation table',
                'employment agreement', 'severance', 'golden parachute',
                'change in control', 'equity compensation'
            ]
            compensation_findings = self._search_text_for_keywords(
                text, compensation_keywords, context_chars=500
            )
            
            # Search for related party transactions
            related_party_findings = self._search_text_for_keywords(
                text, self.related_party_keywords, context_chars=500
            )
            
            # Search for governance info
            governance_keywords = [
                'board of directors', 'board composition', 'independent director',
                'audit committee', 'compensation committee', 'nominating committee'
            ]
            governance_findings = self._search_text_for_keywords(
                text, governance_keywords, context_chars=500
            )
            
            return {
                'ticker': ticker,
                'filing_type': 'DEF 14A',
                'executive_compensation': {
                    'found': len(compensation_findings) > 0,
                    'count': len(compensation_findings),
                    'excerpts': compensation_findings[:5]
                },
                'related_party_transactions': {
                    'found': len(related_party_findings) > 0,
                    'count': len(related_party_findings),
                    'excerpts': related_party_findings[:5]
                },
                'governance_structure': {
                    'found': len(governance_findings) > 0,
                    'count': len(governance_findings),
                    'excerpts': governance_findings[:3]
                },
                'accession_number': filing_data.get('accession_number')
            }
            
        except Exception as e:
            logger.error(f"Error extracting proxy data: {e}")
            return {'error': str(e)}
    
    async def extract_ownership_data(
        self,
        ticker: str
    ) -> Dict[str, Any]:
        """
        Extract beneficial ownership data from SC 13D/13G filings
        
        Identifies:
        - Major shareholders (>5% ownership)
        - Activist investors
        - Ownership concentration
        - Recent changes in control
        
        Args:
            ticker: Stock ticker
        
        Returns:
            Ownership analysis
        """
        try:
            logger.info(f"Extracting ownership data for {ticker}")
            
            ownership_data = {'major_shareholders': [], 'activist_positions': []}
            
            # Check SC 13D (activist) filings
            filing_13d = await self.get_filing_full_text(ticker, 'SC 13D')
            if 'full_text' in filing_13d:
                text = filing_13d['full_text']
                
                # Search for ownership percentage
                ownership_pattern = r'(\d+\.?\d*)%?\s+(?:percent|%)\s+(?:of|ownership)'
                matches = re.findall(ownership_pattern, text, re.IGNORECASE)
                
                if matches:
                    ownership_data['activist_positions'].append({
                        'filing_type': 'SC 13D',
                        'ownership_percentage': matches[0] if matches else 'Unknown',
                        'filing_url': filing_13d.get('filing_url'),
                        'accession_number': filing_13d.get('accession_number'),
                        'note': 'Activist investor position'
                    })
            
            # Check SC 13G (passive) filings
            filing_13g = await self.get_filing_full_text(ticker, 'SC 13G')
            if 'full_text' in filing_13g:
                text = filing_13g['full_text']
                
                ownership_pattern = r'(\d+\.?\d*)%?\s+(?:percent|%)\s+(?:of|ownership)'
                matches = re.findall(ownership_pattern, text, re.IGNORECASE)
                
                if matches:
                    ownership_data['major_shareholders'].append({
                        'filing_type': 'SC 13G',
                        'ownership_percentage': matches[0] if matches else 'Unknown',
                        'filing_url': filing_13g.get('filing_url'),
                        'accession_number': filing_13g.get('accession_number'),
                        'note': 'Passive institutional investor'
                    })
            
            return {
                'ticker': ticker,
                'total_major_shareholders': len(ownership_data['major_shareholders']),
                'total_activist_positions': len(ownership_data['activist_positions']),
                'ownership_data': ownership_data,
                'ownership_concentration': 'high' if len(ownership_data['activist_positions']) > 0 else 'moderate'
            }
            
        except Exception as e:
            logger.error(f"Error extracting ownership data: {e}")
            return {'error': str(e)}
    
    async def extract_ma_activity(
        self,
        ticker: str
    ) -> Dict[str, Any]:
        """
        Extract M&A activity from S-4 and tender offer filings
        
        Identifies:
        - Prior merger/acquisition attempts
        - Business combination filings
        - Tender offers
        - Target responses
        
        Args:
            ticker: Stock ticker
        
        Returns:
            M&A activity analysis
        """
        try:
            logger.info(f"Extracting M&A activity for {ticker}")
            
            ma_activity = []
            
            # Check S-4 (business combination) filings
            filing_s4 = await self.get_filing_full_text(ticker, 'S-4')
            if 'full_text' in filing_s4:
                ma_activity.append({
                    'filing_type': 'S-4',
                    'description': 'Business combination registration statement filed',
                    'filing_url': filing_s4.get('filing_url'),
                    'accession_number': filing_s4.get('accession_number'),
                    'significance': 'high'
                })
            
            # Check SC TO (tender offer) filings
            filing_scto = await self.get_filing_full_text(ticker, 'SC TO')
            if 'full_text' in filing_scto:
                ma_activity.append({
                    'filing_type': 'SC TO',
                    'description': 'Tender offer statement',
                    'filing_url': filing_scto.get('filing_url'),
                    'accession_number': filing_scto.get('accession_number'),
                    'significance': 'high'
                })
            
            return {
                'ticker': ticker,
                'ma_filings_found': len(ma_activity),
                'ma_activity': ma_activity,
                'has_recent_ma_activity': len(ma_activity) > 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting M&A activity: {e}")
            return {'error': str(e)}


# Global client instance
_sec_client: Optional[SECClient] = None


def get_sec_client() -> SECClient:
    """
    Get global SEC client instance
    
    Returns:
        SECClient instance
    """
    global _sec_client
    if _sec_client is None:
        _sec_client = SECClient()
    return _sec_client
