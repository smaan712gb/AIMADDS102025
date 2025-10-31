# Critical Workflow Fixes - Root Cause Solutions (NOT Band-Aids)

**Date:** January 20, 2025  
**Priority:** CRITICAL - Production Blockers  
**Philosophy:** FIX THE DATA PIPELINE, DON'T JUST VALIDATE FAILURES

---

## Executive Summary

The previous approach was flawed - it focused on validation rather than solving the root cause: **MISSING DATA**. This revised plan addresses the actual problems by ensuring data is properly sourced, extracted, and populated.

### Root Cause Analysis

All 5 critical issues stem from **DATA NOT BEING PROVIDED** to agents:

1. ❌ Deal Structuring crashes → **No EBITDA/revenue data provided**
2. ❌ SEC extraction fails → **Parser broken, data not extracted**
3. ❌ Legal Counsel "0" results → **SEC data pipeline completely broken**
4. ❌ Grounding timeouts → **No source data to verify against**
5. ❌ Peer benchmarking empty → **Wrong API endpoint used**

---

## Issue #1: Deal Structuring Agent - PROVIDE THE MISSING DATA

### Root Cause
The Deal Structuring Agent crashes because **EBITDA and revenue are not being calculated/provided** by upstream agents.

### Real Solution: ENSURE DATA IS CALCULATED AND PROVIDED

#### 1.1 Fix Financial Data Pipeline - CALCULATE EBITDA

**File:** `src/agents/financial_analyst.py`

The financial_analyst MUST calculate EBITDA and ensure it's available:

```python
def _calculate_ebitda(self, income_statements: List[Dict]) -> float:
    """
    CRITICAL: Calculate EBITDA from income statement
    This MUST succeed - it's required by downstream agents
    """
    if not income_statements:
        logger.error("CRITICAL: No income statements available to calculate EBITDA")
        return 0.0
    
    latest = income_statements[0]
    
    # Method 1: Direct EBITDA if available
    if 'ebitda' in latest and latest['ebitda']:
        return float(latest['ebitda'])
    
    # Method 2: Calculate from components
    operating_income = latest.get('operatingIncome', 0) or 0
    depreciation = latest.get('depreciationAndAmortization', 0) or 0
    
    if operating_income > 0:
        ebitda = operating_income + depreciation
        logger.info(f"Calculated EBITDA: ${ebitda:,.0f}")
        return ebitda
    
    # Method 3: Use net income as proxy (worst case)
    net_income = latest.get('netIncome', 0) or 0
    interest = latest.get('interestExpense', 0) or 0
    tax = latest.get('incomeTaxExpense', 0) or 0
    
    if net_income > 0:
        ebitda = net_income + interest + tax + depreciation
        logger.warning(f"Using estimated EBITDA from net income: ${ebitda:,.0f}")
        return ebitda
    
    # CRITICAL: Should never reach here for valid companies
    logger.error("CRITICAL: Unable to calculate EBITDA from any method")
    return 0.0

async def run(self, state: DiligenceState) -> Dict[str, Any]:
    """Execute financial analysis - MUST provide EBITDA"""
    
    # ... existing code ...
    
    # CRITICAL: Calculate and store EBITDA
    income_statements = financial_data.get('income_statement', [])
    ebitda = self._calculate_ebitda(income_statements)
    
    # ENSURE it's stored in multiple accessible places
    state['ebitda'] = ebitda
    state['financial_data']['ebitda'] = ebitda
    
    # Also store in normalized format for deal_structuring
    if 'normalized_financials' in state:
        state['normalized_financials']['ebitda'] = ebitda
    
    logger.info(f"✓ EBITDA calculated and stored: ${ebitda:,.0f}")
    
    # ... rest of analysis ...
```

#### 1.2 Ensure Deal Structuring Gets the Data

**File:** `src/agents/deal_structuring.py`

```python
async def run(self, state: DiligenceState) -> Dict[str, Any]:
    """Analyze optimal deal structure"""
    
    errors = []
    warnings = []
    
    # GET the financial data from state (it SHOULD be there)
    financial_data = state.get('financial_data', {})
    
    # CRITICAL: Get EBITDA from multiple possible locations
    ebitda = None
    
    # Location 1: Direct state key
    if 'ebitda' in state:
        ebitda = state['ebitda']
    
    # Location 2: Inside financial_data
    elif 'ebitda' in financial_data:
        ebitda = financial_data['ebitda']
    
    # Location 3: Calculate from income statement if needed
    elif 'income_statement' in financial_data and financial_data['income_statement']:
        income_stmt = financial_data['income_statement'][0]
        ebitda = income_stmt.get('ebitda') or income_stmt.get('operatingIncome', 0)
    
    if ebitda is None or ebitda == 0:
        errors.append("CRITICAL: EBITDA not available - upstream financial_analyst may have failed")
        logger.error("Deal structuring cannot proceed without EBITDA")
        
        return {
            "data": {},
            "errors": errors,
            "warnings": ["Financial analyst must run successfully before deal structuring"],
            "recommendations": ["Ensure financial_analyst completes successfully and calculates EBITDA"]
        }
    
    logger.info(f"✓ EBITDA received: ${ebitda:,.0f}")
    
    # NOW proceed with calculations using the data
    # ... rest of analysis using ebitda ...
```

#### 1.3 Add Pre-Flight Validator (Orchestrator Level)

**File:** `src/api/orchestrator.py`

```python
def _validate_financial_data_completeness(self, state: DiligenceState) -> Tuple[bool, List[str]]:
    """
    CRITICAL: Validate that financial_analyst provided required data
    This runs AFTER financial_analyst but BEFORE deal_structuring
    """
    errors = []
    
    financial_data = state.get('financial_data', {})
    
    # Check required components
    required_keys = ['income_statement', 'balance_sheet', 'cash_flow']
    for key in required_keys:
        if key not in financial_data or not financial_data[key]:
            errors.append(f"Missing {key} data")
    
    # Check EBITDA is available
    ebitda = state.get('ebitda') or financial_data.get('ebitda')
    if not ebitda or ebitda == 0:
        errors.append("EBITDA not calculated - required for deal structuring")
    
    # Check revenue
    if financial_data.get('income_statement'):
        revenue = financial_data['income_statement'][0].get('revenue', 0)
        if not revenue or revenue == 0:
            errors.append("Revenue data missing or zero")
    
    return (len(errors) == 0, errors)

async def run_workflow(self, state: DiligenceState) -> DiligenceState:
    """Run the multi-agent workflow"""
    
    # ... agents run ...
    
    # After financial_analyst, BEFORE deal_structuring
    if 'deal_structuring' in self.agents_to_run:
        is_valid, validation_errors = self._validate_financial_data_completeness(state)
        
        if not is_valid:
            logger.error(f"Financial data incomplete: {validation_errors}")
            logger.error("SKIPPING deal_structuring agent due to missing data")
            
            # Add to state for user visibility
            state['workflow_warnings'] = state.get('workflow_warnings', [])
            state['workflow_warnings'].append({
                'agent': 'deal_structuring',
                'status': 'SKIPPED',
                'reason': 'Missing required financial data',
                'details': validation_errors
            })
            
            # Remove deal_structuring from execution
            self.agents_to_run.remove('deal_structuring')
    
    # ... continue workflow ...
```

### Critical Architecture Note

**YOU ARE CORRECT** - There should be a **SINGLE SOURCE OF TRUTH** for normalized financials!

The proper architecture is:

```
Raw FMP Data → financial_analyst → Normalized Financials + Forecasts → All Downstream Agents
```

**NOT:**
```
Raw FMP Data → Multiple agents each normalizing separately ❌
```

#### How It Should Work:

**File:** `src/agents/financial_analyst.py`

The financial_analyst should produce:

```python
state['normalized_financials'] = {
    'income_statement': [
        # 10 years historical + 5 years forecast
        {
            'year': 2024,
            'revenue': 1000000,
            'ebitda': 250000,  # CALCULATED HERE ONCE
            'operating_income': 200000,
            'net_income': 150000,
            # ... all normalized metrics
        },
        # ... more years
    ],
    'balance_sheet': [...],
    'cash_flow': [...],
    'forecast_assumptions': {
        'revenue_growth': 0.15,
        'ebitda_margin': 0.25,
        # ... etc
    }
}
```

**Then ALL downstream agents use this:**

```python
# Deal Structuring
async def run(self, state: DiligenceState):
    normalized = state['normalized_financials']
    ebitda = normalized['income_statement'][0]['ebitda']  # Use normalized!
    
# DCF Valuation  
async def run(self, state: DiligenceState):
    normalized = state['normalized_financials']
    forecast_income = normalized['income_statement'][-5:]  # Use forecast!
    
# Any other agent
async def run(self, state: DiligenceState):
    normalized = state['normalized_financials']
    # Use pre-calculated normalized data
```

#### Updated Solution:

**1.1 Financial Analyst Produces Complete Normalized Data**

**File:** `src/agents/financial_analyst.py`

```python
async def run(self, state: DiligenceState) -> Dict[str, Any]:
    """
    CRITICAL: This agent is the SINGLE SOURCE OF TRUTH for all financial data
    All downstream agents MUST use the normalized_financials produced here
    """
    
    # Fetch raw data
    financial_data = await self._fetch_financial_data(state)
    
    # NORMALIZE (adjust for non-recurring items, standardize formats)
    normalized_income = self._normalize_income_statements(financial_data['income_statement'])
    normalized_balance = self._normalize_balance_sheets(financial_data['balance_sheet'])
    normalized_cashflow = self._normalize_cash_flows(financial_data['cash_flow'])
    
    # CALCULATE ALL KEY METRICS ONCE
    for statement in normalized_income:
        # Calculate EBITDA if not present
        if 'ebitda' not in statement or not statement['ebitda']:
            statement['ebitda'] = self._calculate_ebitda_from_statement(statement)
        
        # Calculate margins
        statement['ebitda_margin'] = statement['ebitda'] / statement['revenue'] if statement['revenue'] else 0
        statement['operating_margin'] = statement['operating_income'] / statement['revenue'] if statement['revenue'] else 0
        # ... etc
    
    # FORECAST (project 5 years forward)
    forecast_income, forecast_balance, forecast_cashflow = self._generate_forecasts(
        normalized_income,
        normalized_balance,
        normalized_cashflow
    )
    
    # STORE AS SINGLE SOURCE OF TRUTH
    state['normalized_financials'] = {
        'historical': {
            'income_statement': normalized_income,
            'balance_sheet': normalized_balance,
            'cash_flow': normalized_cashflow,
            'years_of_history': len(normalized_income)
        },
        'forecast': {
            'income_statement': forecast_income,
            'balance_sheet': forecast_balance,
            'cash_flow': forecast_cashflow,
            'years_forecast': len(forecast_income),
            'assumptions': self._document_forecast_assumptions()
        },
        'metadata': {
            'normalized_by': 'financial_analyst',
            'normalization_date': datetime.now().isoformat(),
            'data_quality_score': self._calculate_data_quality_score(normalized_income)
        }
    }
    
    # ALSO store quick-access keys for convenience
    state['ebitda'] = normalized_income[0]['ebitda']  # Latest year
    state['revenue'] = normalized_income[0]['revenue']
    
    logger.info(f"✓ Normalized financials created and stored as SINGLE SOURCE OF TRUTH")
    logger.info(f"  - {len(normalized_income)} historical years")
    logger.info(f"  - {len(forecast_income)} forecast years")
    logger.info(f"  - EBITDA: ${state['ebitda']:,.0f}")
    
    return {
        "data": {
            "normalized_financials": state['normalized_financials'],
            # ... other analysis
        }
    }
```

**1.2 Deal Structuring Uses Normalized Data**

**File:** `src/agents/deal_structuring.py`

```python
async def run(self, state: DiligenceState) -> Dict[str, Any]:
    """
    Use pre-normalized financials from financial_analyst
    DO NOT re-normalize or re-calculate - use the single source of truth
    """
    
    # GET NORMALIZED DATA (should already exist)
    if 'normalized_financials' not in state:
        return {
            "data": {},
            "errors": ["normalized_financials not found - financial_analyst must run first"],
            "recommendations": ["Ensure financial_analyst completes before deal_structuring"]
        }
    
    normalized = state['normalized_financials']
    historical = normalized['historical']
    forecast = normalized['forecast']
    
    # EBITDA is already calculated in normalized data
    latest_income = historical['income_statement'][0]
    ebitda = latest_income['ebitda']
    revenue = latest_income['revenue']
    
    logger.info(f"✓ Using normalized EBITDA: ${ebitda:,.0f}")
    logger.info(f"✓ Using normalized Revenue: ${revenue:,.0f}")
    
    # NOW use this data for deal structuring calculations
    # No need to recalculate or re-normalize anything
    
    # Calculate earnout based on forecast
    forecast_revenue_growth = self._calculate_cagr(
        [stmt['revenue'] for stmt in forecast['income_statement']]
    )
    
    earnout_metrics = [
        {
            'metric': 'Revenue Growth',
            'threshold': f'{forecast_revenue_growth * 100:.1f}% CAGR',
            'payout': deal_value * 0.06
        },
        {
            'metric': 'EBITDA Margin',
            'threshold': f"{latest_income['ebitda_margin'] * 100:.1f}% margin",
            'payout': deal_value * 0.05
        }
    ]
    
    # ... rest of analysis using normalized data
```

**1.3 DCF Valuation Uses Forecasts**

**File:** `src/utils/advanced_valuation.py`

```python
def calculate_dcf(self, state: DiligenceState, scenario: str = 'base') -> Dict[str, Any]:
    """
    DCF MUST use the forecasts from financial_analyst
    DO NOT create separate forecasts
    """
    
    # GET FORECASTS (already created by financial_analyst)
    if 'normalized_financials' not in state:
        raise ValueError("normalized_financials required for DCF - run financial_analyst first")
    
    normalized = state['normalized_financials']
    forecast_income = normalized['forecast']['income_statement']
    forecast_cashflow = normalized['forecast']['cash_flow']
    
    logger.info(f"✓ Using pre-built forecast: {len(forecast_income)} years")
    
    # Extract free cash flows from forecast
    fcf_projections = []
    for year_data in forecast_income:
        # FCF already calculated in normalized data
        fcf = year_data.get('free_cash_flow') or self._calculate_fcf_from_forecast(
            year_data,
            forecast_cashflow[forecast_income.index(year_data)]
        )
        fcf_projections.append(fcf)
    
    # Calculate terminal value using last forecast year
    last_year_fcf = fcf_projections[-1]
    terminal_value = last_year_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    
    # ... rest of DCF calculation
```

### Success Criteria (UPDATED)
- ✅ Financial_analyst is SINGLE SOURCE OF TRUTH for all financial data
- ✅ Normalized financials include 10 years history + 5 years forecast
- ✅ All metrics calculated ONCE in financial_analyst
- ✅ Downstream agents ONLY read from normalized_financials
- ✅ NO agent re-normalizes or re-calculates base metrics
- ✅ Deal structuring receives valid normalized data

---

## Issue #2 & #3: SEC Data Extraction - FIX THE PARSER

### Root Cause
The SEC parser **DOES NOT WORK** for current filing formats. It returns empty strings, providing NO data to legal_counsel.

### Real Solution: USE A WORKING DATA SOURCE

#### 2.1 PRIMARY FIX: Use FMP SEC RSS Feed (Pre-Parsed Data)

FMP provides **pre-parsed** SEC data through their RSS feed endpoints. This is MORE RELIABLE than trying to parse HTML ourselves.

**File:** `src/integrations/fmp_client.py`

Add methods to get pre-parsed SEC data:

```python
async def get_sec_rss_feed(self, ticker: str, filing_type: str = '10-K', limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get SEC filings from FMP RSS feed - PRE-PARSED and RELIABLE
    
    This is MORE RELIABLE than parsing HTML ourselves
    
    Args:
        ticker: Stock ticker
        filing_type: Filing type (10-K, 10-Q, 8-K, DEF 14A, etc.)
        limit: Number of filings
        
    Returns:
        List of filing data with pre-parsed sections
    """
    try:
        endpoint = f"rss_feed?symbol={ticker}&type={filing_type}&limit={limit}"
        
        response = await self._make_request(endpoint)
        
        if response:
            logger.info(f"✓ Retrieved {len(response)} {filing_type} filings for {ticker} from FMP RSS")
            return response
        
        return []
        
    except Exception as e:
        logger.error(f"Error fetching SEC RSS feed: {e}")
        return []

async def get_risk_factors_from_fmp(self, ticker: str) -> Dict[str, Any]:
    """
    Get risk factors using FMP's pre-parsed data (RELIABLE)
    
    Returns:
        Risk factors extracted by FMP
    """
    try:
        # FMP provides risk factors as structured data
        endpoint = f"risk-factors/{ticker}"
        
        response = await self._make_request(endpoint)
        
        if response and isinstance(response, list) and len(response) > 0:
            risk_data = response[0]
            logger.info(f"✓ Retrieved risk factors for {ticker} from FMP")
            return risk_data
        
        return {}
        
    except Exception as e:
        logger.error(f"Error fetching risk factors from FMP: {e}")
        return {}
```

#### 2.2 UPDATE SEC Client to Use FMP First

**File:** `src/integrations/sec_client.py`

```python
async def extract_risk_factors(
    self,
    ticker: str,
    filing_type: str = "10-K",
    num_years: int = 3
) -> Dict[str, Any]:
    """
    Extract risk factors - USE FMP FIRST (it works!)
    
    Priority:
    1. FMP pre-parsed data (MOST RELIABLE)
    2. FMP RSS feed with sections
    3. Our HTML parsing (fallback only)
    """
    try:
        from .fmp_client import FMPClient
        
        # METHOD 1: Try FMP's risk factors endpoint (PRE-PARSED)
        async with FMPClient() as client:
            fmp_risks = await client.get_risk_factors_from_fmp(ticker)
            
            if fmp_risks and 'riskFactors' in fmp_risks:
                risk_text = fmp_risks['riskFactors']
                
                if len(risk_text) >= 500:  # Has substantial content
                    logger.info(f"✓ Using FMP pre-parsed risk factors ({len(risk_text)} chars)")
                    
                    analysis = self._analyze_risks(risk_text)
                    
                    return {
                        'ticker': ticker,
                        'extraction_method': 'fmp_preparsed',
                        'extraction_status': 'success',
                        'risk_factors_by_year': [{
                            'year': datetime.now().year,
                            'risk_text': risk_text,
                            'risk_analysis': analysis,
                            'source': 'FMP Pre-Parsed Data'
                        }],
                        'num_years_analyzed': 1,
                        'new_risks_identified': analysis.get('top_risks', [])[:10]
                    }
            
            # METHOD 2: Try FMP RSS feed
            rss_filings = await client.get_sec_rss_feed(ticker, '10-K', limit=num_years)
            
            if rss_filings:
                risk_factors_by_year = []
                
                for filing in rss_filings:
                    # FMP RSS often includes parsed sections
                    risk_section = filing.get('riskFactors') or filing.get('item1A')
                    
                    if risk_section and len(risk_section) >= 500:
                        analysis = self._analyze_risks(risk_section)
                        
                        risk_factors_by_year.append({
                            'year': filing.get('filingDate', '')[:4],
                            'risk_text': risk_section,
                            'risk_analysis': analysis,
                            'source': 'FMP RSS Feed'
                        })
                
                if risk_factors_by_year:
                    logger.info(f"✓ Extracted risks from {len(risk_factors_by_year)} years via FMP RSS")
                    
                    yoy_comparison = self._compare_risk_factors(risk_factors_by_year)
                    
                    return {
                        'ticker': ticker,
                        'extraction_method': 'fmp_rss',
                        'extraction_status': 'success',
                        'num_years_analyzed': len(risk_factors_by_year),
                        'risk_factors_by_year': risk_factors_by_year,
                        'year_over_year_comparison': yoy_comparison,
                        'new_risks_identified': yoy_comparison.get('new_risks', [])
                    }
        
        # METHOD 3: Our HTML parsing (LAST RESORT)
        logger.warning("FMP methods failed, falling back to HTML parsing")
        return await self._extract_risk_factors_html_fallback(ticker, filing_type, num_years)
        
    except Exception as e:
        logger.error(f"All risk factor extraction methods failed: {e}")
        return {
            'ticker': ticker,
            'extraction_status': 'failed',
            'error': str(e),
            'recommendation': 'Manual review of SEC filings required'
        }
```

#### 2.3 Same Approach for MD&A

```python
async def extract_mda_section(
    self,
    ticker: str,
    filing_type: str = "10-K"
) -> Dict[str, Any]:
    """
    Extract MD&A - USE FMP FIRST
    """
    try:
        from .fmp_client import FMPClient
        
        async with FMPClient() as client:
            # Try FMP RSS feed for MD&A
            rss_filings = await client.get_sec_rss_feed(ticker, filing_type, limit=1)
            
            if rss_filings and len(rss_filings) > 0:
                filing = rss_filings[0]
                
                # FMP often includes MD&A as item7
                mda_text = filing.get('mda') or filing.get('item7')
                
                if mda_text and len(mda_text) >= 1000:
                    logger.info(f"✓ Retrieved MD&A from FMP RSS ({len(mda_text)} chars)")
                    
                    analysis = self._analyze_mda(mda_text)
                    
                    return {
                        'ticker': ticker,
                        'filing_type': filing_type,
                        'mda_text': mda_text,
                        'mda_length': len(mda_text),
                        'analysis': analysis,
                        'extraction_method': 'fmp_rss',
                        'source': 'FMP RSS Feed'
                    }
        
        # Fallback to HTML parsing
        logger.warning("FMP RSS did not provide MD&A, trying HTML parsing")
        return await self._extract_mda_html_fallback(ticker, filing_type)
        
    except Exception as e:
        logger.error(f"MD&A extraction failed: {e}")
        return {'error': str(e), 'extraction_status': 'failed'}
```

### Success Criteria
- ✅ Risk factors extracted with >1000 chars
- ✅ MD&A extracted with >2000 chars
- ✅ Legal counsel receives ACTUAL data (not empty)
- ✅ Extraction succeeds for PLTR and other major companies

---

## Issue #4: Grounding Check Timeouts - PROVIDE SOURCE DATA

### Root Cause
Grounding checks timeout because there's **NO SOURCE DATA** to verify against (due to SEC extraction failures).

### Real Solution: ENSURE SOURCE DATA EXISTS

Once SEC extraction is fixed (Issue #2), grounding will have data to verify against. But we also need to:

#### 4.1 Store Source Data Properly

**File:** `src/api/orchestrator.py`

```python
async def run_workflow(self, state: DiligenceState) -> DiligenceState:
    """Run workflow and ENSURE source data is stored"""
    
    # ... agents run ...
    
    # After legal_counsel, STORE SEC data for grounding
    if 'legal_counsel' in completed_agents:
        legal_data = state.get('legal_counsel', {})
        sec_analysis = legal_data.get('data', {}).get('sec_analysis', {})
        
        # CRITICAL: Store SEC source data for synthesis agent
        if 'source_documents' not in state:
            state['source_documents'] = {}
        
        state['source_documents']['sec_filings'] = {
            'risk_factors': sec_analysis.get('sec_risk_factors', {}),
            'mda': sec_analysis.get('mda_sentiment', {}),
            'proxy_data': sec_analysis.get('proxy_statement', {}),
            'source': 'legal_counsel_agent'
        }
        
        logger.info("✓ SEC source data stored for grounding checks")
    
    # ... continue workflow ...
```

#### 4.2 Synthesis Agent Uses Stored Source Data

**File:** `src/agents/synthesis_reporting.py`

```python
def _extract_source_data(self, state: DiligenceState) -> Dict[str, Any]:
    """
    Extract source data for grounding - MUST HAVE DATA
    """
    source_data = {
        'sec_filings': {},
        'financial_statements': {},
        'market_data': {}
    }
    
    # Get SEC source data (SHOULD be populated by legal_counsel)
    if 'source_documents' in state and 'sec_filings' in state['source_documents']:
        source_data['sec_filings'] = state['source_documents']['sec_filings']
        logger.info("✓ SEC source data available for grounding")
    else:
        logger.warning("No SEC source data available - grounding will be limited")
    
    # Get financial statements (SHOULD be populated by financial_analyst)
    if 'financial_data' in state:
        source_data['financial_statements'] = state['financial_data']
        logger.info("✓ Financial statements available for grounding")
    
    return source_data
```

### Success Criteria
- ✅ SEC data extracted and stored by legal_counsel
- ✅ Source data accessible to synthesis agent
- ✅ Grounding checks have data to verify against
- ✅ No timeouts due to missing data

---

## Issue #5: Peer Benchmarking - USE THE RIGHT ENDPOINT

### Root Cause
The competitive benchmarking agent uses endpoints that return EMPTY results. The correct FMP endpoint exists but isn't being used.

### Real Solution: USE THE FMP STOCK-PEERS ENDPOINT

#### 5.1 Add the Correct FMP Method

**File:** `src/integrations/fmp_client.py`

```python
async def get_stock_peers(self, symbol: str) -> Dict[str, Any]:
    """
    Get peer companies using FMP Stock Peer Comparison API
    
    This is the CORRECT endpoint that actually returns peers
    Endpoint: stock-peers?symbol=AAPL
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with peersList containing peer tickers
    """
    try:
        # Use the CORRECT stable endpoint
        endpoint = f"stock-peers?symbol={symbol}"
        
        response = await self._make_request(endpoint)
        
        if response and isinstance(response, list) and len(response) > 0:
            # API returns list with one object containing peersList
            peers_data = response[0]
            peers_list = peers_data.get('peersList', [])
            
            if peers_list:
                logger.info(f"✓ Found {len(peers_list)} peers for {symbol} via FMP stock-peers API")
                return {
                    'symbol': symbol,
                    'peersList': peers_list,
                    'source': 'fmp_stock_peers_api'
                }
        
        logger.warning(f"FMP stock-peers returned no data for {symbol}")
        return {}
        
    except Exception as e:
        logger.error(f"Error fetching stock peers for {symbol}: {e}")
        return {}
```

#### 5.2 Update Competitive Benchmarking to Use Correct Endpoint

**File:** `src/agents/competitive_benchmarking.py`

```python
async def _identify_peers(self, symbol: str) -> List[str]:
    """
    FIXED: Identify peers using the CORRECT FMP endpoint
    
    Priority order:
    1. FMP stock-peers endpoint (USER SPECIFIED - WORKS!)
    2. Sector/industry screening (fallback)
    """
    try:
        async with FMPClient() as client:
            # TIER 1: Use the CORRECT FMP endpoint (as specified by user)
            logger.info(f"Fetching peers for {symbol} using FMP stock-peers API")
            
            peers_response = await client.get_stock_peers(symbol)
            
            if peers_response and 'peersList' in peers_response:
                peers_list = peers_response['peersList']
                
                if isinstance(peers_list, list) and len(peers_list) > 0:
                    # Filter out the symbol itself if present
                    peers = [p for p in peers_list if p != symbol]
                    
                    logger.info(f"✓ SUCCESS: Found {len(peers)} peers for {symbol}")
                    logger.info(f"Peers: {', '.join(peers[:5])}{'...' if len(peers) > 5 else ''}")
                    
                    self.peers_cache[symbol] = peers
                    return peers[:10]  # Top 10 peers
            
            # TIER 2: Fallback to sector screening only if API fails
            logger.warning(f"FMP stock-peers returned empty for {symbol}, trying sector screening")
            
            profile = await client.get_company_profile(symbol)
            
            if not profile:
                logger.error(f"Could not get company profile for {symbol}")
                return []
            
            sector = profile.get('sector', '')
            industry = profile.get('industry', '')
            market_cap = profile.get('mktCap', 0)
            
            if not sector:
                logger.error(f"No sector information available for {symbol}")
                return []
            
            logger.info(f"Screening by sector: {sector}, industry: {industry}")
            
            # Use BROAD screening to find ANY peers
            screening_criteria = {
                'sector': sector,
                'marketCapMoreThan': max(market_cap * 0.1, 100_000_000) if market_cap > 0 else 100_000_000,
                'marketCapLowerThan': market_cap * 20 if market_cap > 0 else 1_000_000_000_000,
                'limit': 20,
                'isActivelyTrading': 'true'
            }
            
            screened_companies = await client.get_stock_screener(**screening_criteria)
            
            if screened_companies and isinstance(screened_companies, list):
                peers = [
                    comp.get('symbol')
                    for comp in screened_companies
                    if comp.get('symbol') and comp.get('symbol') != symbol
                ][:10]
                
                if peers:
                    logger.info(f"✓ Found {len(peers)} peers via sector screening: {', '.join(peers[:5])}")
                    self.peers_cache[symbol] = peers
                    return peers
            
            logger.error(f"Unable to find any peers for {symbol}")
            return []
            
    except Exception as e:
        logger.error(f"Error identifying peers: {e}")
        return []
```

### Success Criteria
- ✅ Peers found for PLTR and other major companies
- ✅ Uses correct FMP stock-peers endpoint FIRST
- ✅ Fallback only if API fails
- ✅ Competitive analysis has valid peer data

---

## Summary: DATA PIPELINE FIXES

### What We're ACTUALLY Fixing

| Issue | Root Cause | Real Solution |
|-------|------------|---------------|
| Deal Structuring Crash | EBITDA not calculated | Financial_analyst CALCULATES and STORES EBITDA |
| SEC Extraction Failure | HTML parser broken | Use FMP pre-parsed SEC data (RSS feed, risk factors endpoint) |
| Legal "0" Results | No SEC data extracted | Fix SEC extraction → legal_counsel gets data |
| Grounding Timeouts | No source data | Store SEC/financial data properly for synthesis |
| Peer Benchmarking Empty | Wrong API endpoint | Use correct FMP stock-peers endpoint |

### Implementation Priority

1. **HIGHEST PRIORITY: Fix SEC Data Extraction**
   - Add `get_sec_rss_feed()` to FMP client
   - Add `get_risk_factors_from_fmp()` to FMP client
   - Update `extract_risk_factors()` to use FMP first
   - Update `extract_mda_section()` to use FMP first
   - **Impact:** Fixes Issues #2, #3, and #4

2. **HIGH PRIORITY: Fix EBITDA Calculation**
   - Add `_calculate_ebitda()` to financial_analyst
   - Store EBITDA in state properly
   - Update deal_structuring to get EBITDA from state
   - **Impact:** Fixes Issue #1

3. **HIGH PRIORITY: Fix Peer Benchmarking**
   - Add `get_stock_peers()` to FMP client
   - Update `_identify_peers()` to use correct endpoint
   - **Impact:** Fixes Issue #5

4. **MEDIUM PRIORITY: Orchestrator Validation**
   - Add data completeness checks between agents
   - Skip downstream agents if upstream data missing
   - Provide clear error messages to users

### Testing Plan

#### Test Case 1: EBITDA Calculation
```python
# Test with PLTR
state = {'target_ticker': 'PLTR'}
result = await financial_analyst.run(state)

assert 'ebitda' in state
assert state['ebitda'] > 0
print(f"✓ EBITDA: ${state['ebitda']:,.0f}")
```

#### Test Case 2: SEC Data Extraction
```python
# Test with PLTR
sec_client = SECClient()
risks = await sec_client.extract_risk_factors('PLTR')

assert risks['extraction_status'] == 'success'
assert len(risks.get('risk_factors_by_year', [])) > 0
assert risks['risk_factors_by_year'][0]['risk_text']
print(f"✓ Extracted {len(risks['new_risks_identified'])} risk factors")
```

#### Test Case 3: Peer Benchmarking
```python
# Test with PLTR
fmp_client = FMPClient()
peers = await fmp_client.get_stock_peers('PLTR')

assert 'peersList' in peers
assert len(peers['peersList']) > 0
print(f"✓ Found peers: {peers['peersList']}")
```

### Acceptance Criteria

The workflow is considered FIXED when:

- ✅ Financial_analyst calculates and stores EBITDA
- ✅ Deal_structuring receives EBITDA and completes without crashes
- ✅ SEC extraction returns >1000 chars of risk factors
- ✅ SEC extraction returns >2000 chars of MD&A
- ✅ Legal_counsel finds >0 compensation items
- ✅ Legal_counsel finds >0 ownership positions
- ✅ Synthesis agent has source data for grounding
- ✅ Grounding checks complete within 90s
- ✅ Competitive benchmarking finds >5 peers
- ✅ All agents complete successfully for PLTR ticker

### Migration Path

**Phase 1: FMP Client Updates (30 minutes)**
- Add `get_sec_rss_feed()` method
- Add `get_risk_factors_from_fmp()` method
- Add `get_stock_peers()` method
- Test each method independently

**Phase 2: SEC Client Updates (45 minutes)**
- Update `extract_risk_factors()` to use FMP first
- Update `extract_mda_section()` to use FMP first
- Test with PLTR ticker

**Phase 3: Financial Analyst Updates (30 minutes)**
- Add `_calculate_ebitda()` method
- Store EBITDA in state properly
- Test calculation with multiple tickers

**Phase 4: Deal Structuring Updates (20 minutes)**
- Update to get EBITDA from state
- Test with PLTR data

**Phase 5: Competitive Benchmarking Updates (20 minutes)**
- Update `_identify_peers()` to use correct endpoint
- Test with multiple tickers

**Phase 6: Integration Testing (1 hour)**
- Run full workflow for PLTR
- Verify all agents complete successfully
- Verify no crashes or empty results

**Total Estimated Time: 3.5 hours**

---

## Conclusion

This plan provides **REAL SOLUTIONS** that fix the **ROOT CAUSE** - missing data - rather than just validating failures.

The key insight: **Don't validate that data is missing. PROVIDE the data.**

**Next Steps:**
1. Implement FMP client updates
2. Test each endpoint independently
3. Update dependent agents
4. Run full integration test
5. Deploy to production
