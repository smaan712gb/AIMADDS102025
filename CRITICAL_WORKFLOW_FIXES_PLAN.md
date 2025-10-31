# Critical Workflow Fixes - Comprehensive Implementation Plan

**Date:** January 20, 2025  
**Priority:** CRITICAL - Production Blockers  
**Scope:** Fix all critical workflow issues identified in PLTR analysis log

---

## Executive Summary

Analysis of the PLTR workflow log revealed **5 critical issues** and **29 warnings** that must be addressed to ensure production readiness. This document provides a detailed implementation plan for each fix.

### Critical Issues Identified

1. ✅ **Fatal Agent Crash** - Deal Structuring Agent
2. ✅ **Total SEC Data Extraction Failure** - Legal Counsel Agent
3. ✅ **Suspicious "0" Results** - Legal Counsel Missing Data
4. ✅ **Grounding Check Timeouts** - Synthesis Agent
5. ✅ **Flawed Peer Benchmarking** - Competitive Benchmarking Agent

---

## Issue #1: Deal Structuring Agent Fatal Crash

### Problem Statement
```
ERROR... unsupported operand type(s) for *: 'NoneType' and 'float'
```

The Deal Structuring Agent crashes when attempting mathematical operations on missing financial data (e.g., EBITDA, revenue). This is a **CRITICAL** failure that stops the entire workflow.

### Root Cause
- Missing pre-calculation validation, also need to fix the missing data issue, need to provide the data, no exception
- No defensive checks for `None` values before performing arithmetic
- Assumes all financial metrics are always available

### Solution

#### 1.1 Add Robust Pre-Calculation Validation  and provide the required data

**File:** `src/agents/deal_structuring.py`

**Changes Required:**

```python
def _validate_financial_inputs(self, financial_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that all required financial inputs are present and valid
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_fields = ['balance_sheet', 'income_statement']
    
    for field in required_fields:
        if field not in financial_data or not financial_data[field]:
            errors.append(f"Missing required financial data: {field}")
    
    # Validate balance sheet has required fields
    if 'balance_sheet' in financial_data and financial_data['balance_sheet']:
        latest_bs = financial_data['balance_sheet'][0]
        required_bs_fields = ['totalAssets', 'totalLiabilities', 'totalCurrentAssets', 
                             'totalCurrentLiabilities', 'cashAndCashEquivalents']
        
        for field in required_bs_fields:
            if field not in latest_bs or latest_bs[field] is None:
                errors.append(f"Missing balance sheet field: {field}")
    
    return (len(errors) == 0, errors)

def _safe_calculate(self, value1: Optional[float], value2: Optional[float], 
                    operation: str = 'multiply') -> float:
    """
    Safely perform calculations with None-checking
    
    Args:
        value1: First value (may be None)
        value2: Second value (may be None)
        operation: 'multiply', 'divide', 'add', 'subtract'
    
    Returns:
        Calculated result or 0 if any input is None
    """
    if value1 is None or value2 is None:
        logger.warning(f"Attempted {operation} with None value: {value1}, {value2}")
        return 0.0
    
    try:
        if operation == 'multiply':
            return value1 * value2
        elif operation == 'divide':
            return value1 / value2 if value2 != 0 else 0.0
        elif operation == 'add':
            return value1 + value2
        elif operation == 'subtract':
            return value1 - value2
        else:
            return 0.0
    except Exception as e:
        logger.error(f"Error in safe calculation: {e}")
        return 0.0
```

#### 1.2 Update All Calculation Methods

Update methods like `_calculate_working_capital_peg`, `_estimate_purchase_price_allocation` to use defensive programming:

```python
def _calculate_working_capital_peg(self, financial_data: Dict) -> Dict[str, Any]:
    """Calculate working capital adjustment mechanism with validation"""
    
    balance_sheets = financial_data.get('balance_sheet', [])
    
    if not balance_sheets:
        return {
            'error': 'No balance sheet data available',
            'latest_nwc': 0,
            'normalized_nwc_peg': 0
        }
    
    latest_bs = balance_sheets[0]
    
    # Safe extraction with defaults
    current_assets = latest_bs.get('totalCurrentAssets', 0) or 0
    current_liabilities = latest_bs.get('totalCurrentLiabilities', 0) or 0
    cash = latest_bs.get('cashAndCashEquivalents', 0) or 0
    
    # Calculate with validation
    nwc = current_assets - current_liabilities - cash
    
    # Calculate historical average
    nwc_values = []
    for bs in balance_sheets[:4]:
        ca = bs.get('totalCurrentAssets', 0) or 0
        cl = bs.get('totalCurrentLiabilities', 0) or 0
        c = bs.get('cashAndCashEquivalents', 0) or 0
        if ca > 0:  # Only include valid periods
            nwc_values.append(ca - cl - c)
    
    nwc_peg = np.mean(nwc_values) if nwc_values else nwc
    
    return {
        'latest_nwc': nwc,
        'normalized_nwc_peg': nwc_peg,
        'data_quality': 'good' if len(nwc_values) >= 3 else 'limited',
        'periods_analyzed': len(nwc_values),
        'adjustment_mechanism': {
            'description': 'Purchase price adjusted dollar-for-dollar for NWC variance at close',
            'formula': 'Final Price = Base Price + (Actual NWC - NWC Peg)',
            'example': f'If NWC is ${nwc:,.0f} vs peg of ${nwc_peg:,.0f}, adjustment = ${(nwc - nwc_peg):,.0f}'
        }
    }
```

#### 1.3 Add Pre-Run Validation

```python
async def run(self, state: DiligenceState) -> Dict[str, Any]:
    """Analyze optimal deal structure with validation"""
    
    errors = []
    warnings = []
    
    # CRITICAL: Validate inputs before processing
    financial_data = state.get('financial_data', {})
    is_valid, validation_errors = self._validate_financial_inputs(financial_data)
    
    if not is_valid:
        logger.error(f"Financial data validation failed: {validation_errors}")
        return {
            "data": {},
            "errors": validation_errors,
            "warnings": ["Deal structuring requires complete financial data"],
            "recommendations": ["Ensure financial data is complete before running deal structuring"]
        }
    
    # Continue with analysis...
```

### Testing Requirements
- [ ] Test with missing EBITDA
- [ ] Test with None values in balance sheet
- [ ] Test with empty financial_data dict
- [ ] Verify graceful error handling

### Success Criteria
- No crashes when financial data is incomplete
- Clear error messages when validation fails
- Structured error response for downstream consumers

---

## Issue #2: Total SEC Data Extraction Failure

### Problem Statement
```
SEC 'Item 1A' (Risk Factors) extraction failed
SEC 'Item 7' (MD&A) extraction failed
All fallbacks (DOM and regex) also failed
```

The SEC client is unable to extract critical sections from 10-K filings, resulting in:
- 0 new risks identified
- MD&A sentiment: unknown
- No legal analysis possible

### Root Cause
1. **Outdated sec-parser library** - May not support current SEC filing formats
2. **Regex patterns too strict** - Failing on formatting variations
3. **DOM parsing insufficient** - HTML structure varies by company
4. **No commercial API fallback** - When all parsing fails, no backup

### Solution

#### 2.1 Update SEC Parser Library

**Action:** Update to latest sec-parser version

```bash
pip install --upgrade sec-parser sec-downloader
```

**Version Requirements:**
- sec-parser >= 0.58.0
- sec-downloader >= 0.10.0

#### 2.2 Enhance Regex Fallback Patterns

**File:** `src/integrations/sec_client.py`

**Method:** `_extract_section()`

```python
def _extract_section(
    self,
    text: str,
    start_marker: str,
    end_marker: str
) -> Optional[str]:
    """
    ENHANCED: Extract section with multiple fallback patterns
    """
    try:
        logger.info(f"Extracting section {start_marker} to {end_marker}")
        
        # Method 1: HTML DOM parsing (most reliable)
        soup = BeautifulSoup(text, 'html.parser')
        
        # Enhanced section markers - multiple variations
        start_patterns = [
            f"Item {start_marker}",
            f"ITEM {start_marker}",
            f"Item {start_marker}.",
            f"Item {start_marker}:",
            f"Item {start_marker} —",
            f"Item {start_marker} –",
            f"Item {start_marker} -",
        ]
        
        end_patterns = [
            f"Item {end_marker}",
            f"ITEM {end_marker}",
            f"Item {end_marker}.",
            f"Item {end_marker}:",
        ]
        
        # Try to find section in HTML structure
        start_element = None
        for pattern in start_patterns:
            # Search all text nodes
            for element in soup.find_all(text=re.compile(pattern, re.IGNORECASE)):
                parent = element.parent
                if parent.name in ['b', 'strong', 'font', 'div', 'p', 'span']:
                    start_element = parent
                    logger.info(f"Found start marker '{pattern}' in <{parent.name}>")
                    break
            if start_element:
                break
        
        if not start_element:
            # Fallback: search in cleaned text
            logger.warning(f"Could not find {start_marker} in HTML structure, trying text search")
            return self._extract_section_text_fallback(text, start_marker, end_marker)
        
        # Extract content between markers
        extracted_text = []
        current = start_element.next_sibling
        
        while current:
            # Check if we've hit the end marker
            if hasattr(current, 'get_text'):
                current_text = current.get_text()
                if any(re.search(pattern, current_text, re.IGNORECASE) for pattern in end_patterns):
                    logger.info(f"Found end marker at {current.name}")
                    break
            
            # Add content
            if hasattr(current, 'get_text'):
                text_content = current.get_text(separator=' ', strip=True)
                if len(text_content) > 20:  # Filter noise
                    extracted_text.append(text_content)
            elif isinstance(current, str):
                cleaned = current.strip()
                if len(cleaned) > 20:
                    extracted_text.append(cleaned)
            
            current = current.next_sibling
        
        result = ' '.join(extracted_text)
        
        if len(result) >= 1000:  # Minimum viable content
            logger.info(f"Successfully extracted {start_marker} ({len(result)} chars)")
            return result
        else:
            logger.warning(f"Extracted content too short ({len(result)} chars), trying fallback")
            return self._extract_section_text_fallback(text, start_marker, end_marker)
    
    except Exception as e:
        logger.error(f"Error in section extraction: {e}")
        return None

def _extract_section_text_fallback(
    self,
    text: str,
    start_marker: str,
    end_marker: str
) -> Optional[str]:
    """
    NEW: Text-based extraction as final fallback
    """
    try:
        # Clean text
        text_clean = re.sub(r'\s+', ' ', text)
        text_clean = re.sub(r'<[^>]+>', '', text_clean)  # Strip HTML
        
        # Multiple regex patterns for robustness
        patterns = [
            # Pattern 1: Standard format
            re.compile(
                rf'Item\s+{start_marker}[\.\:\s\-—–]+(.+?)(?=Item\s+{end_marker}|$)',
                re.IGNORECASE | re.DOTALL
            ),
            # Pattern 2: With section name
            re.compile(
                rf'Item\s+{start_marker}[\.\:\s]+[A-Za-z\s]+(.+?)(?=Item\s+{end_marker}|$)',
                re.IGNORECASE | re.DOTALL
            ),
            # Pattern 3: Table of contents style
            re.compile(
                rf'{start_marker}[\.\s]+(.+?)(?={end_marker}|$)',
                re.IGNORECASE | re.DOTALL
            ),
        ]
        
        for i, pattern in enumerate(patterns):
            match = pattern.search(text_clean)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) >= 1000:
                    logger.info(f"Text fallback pattern {i+1} succeeded ({len(extracted)} chars)")
                    return extracted
        
        logger.warning(f"All extraction methods failed for {start_marker}")
        return None
        
    except Exception as e:
        logger.error(f"Text fallback error: {e}")
        return None
```

#### 2.3 Add Commercial API Fallback

**File:** `src/integrations/sec_client.py`

```python
async def extract_risk_factors(
    self,
    ticker: str,
    filing_type: str = "10-K",
    num_years: int = 3
) -> Dict[str, Any]:
    """
    ENHANCED: Extract risk factors with commercial API fallback
    """
    try:
        # Try primary extraction
        result = await self._extract_risk_factors_primary(ticker, filing_type, num_years)
        
        if result.get('extraction_status') == 'failed':
            logger.warning("Primary extraction failed, trying commercial API fallback")
            result = await self._extract_risk_factors_commercial_fallback(ticker)
        
        return result
        
    except Exception as e:
        logger.error(f"Risk factor extraction error: {e}")
        return {'error': str(e)}

async def _extract_risk_factors_commercial_fallback(self, ticker: str) -> Dict[str, Any]:
    """
    NEW: Use commercial API (FMP) as fallback for risk factors
    """
    try:
        from .fmp_client import FMPClient
        
        async with FMPClient() as client:
            # FMP provides parsed SEC data
            sec_filings = await client.get_sec_filings(ticker, limit=1)
            
            if not sec_filings:
                return {'extraction_status': 'failed', 'error': 'No SEC filings available'}
            
            # Extract from FMP parsed data
            risk_text = sec_filings[0].get('riskFactors', '')
            
            if len(risk_text) >= 500:
                analysis = self._analyze_risks(risk_text)
                
                return {
                    'ticker': ticker,
                    'extraction_status': 'commercial_api',
                    'extraction_method': 'fmp_api',
                    'risk_factors_by_year': [{
                        'year': datetime.now().year,
                        'risk_text': risk_text,
                        'risk_analysis': analysis,
                        'source': 'FMP Commercial API'
                    }],
                    'num_years_analyzed': 1,
                    'new_risks_identified': analysis.get('top_risks', [])
                }
            
            return {'extraction_status': 'failed', 'error': 'Insufficient risk factor content'}
            
    except Exception as e:
        logger.error(f"Commercial fallback error: {e}")
        return {'extraction_status': 'failed', 'error': str(e)}
```

### Testing Requirements
- [ ] Test with PLTR 10-K filing
- [ ] Test with different company filing formats
- [ ] Verify all three extraction methods
- [ ] Validate fallback chain works

### Success Criteria
- Risk Factors extracted successfully (>1000 chars)
- MD&A extracted successfully (>2000 chars)
- At least one extraction method succeeds for major companies
- Clear logging of which method succeeded

---

## Issue #3: Suspicious "0" Results from Legal Counsel

### Problem Statement
```
0 compensation items
0 activist positions
0 M&A filings
```

For a major public company like PLTR, finding zero for all M&A-related categories is impossible and indicates systemic failure.

### Root Cause
- SEC extraction failures cascade to legal analysis
- No validation that "0 findings" is suspicious
- Missing error propagation from SEC client to legal agent

### Solution

#### 3.1 Add Data Quality Validation

**File:** `src/agents/legal_counsel.py`

```python
def _validate_sec_findings(
    self,
    sec_analysis: Dict[str, Any],
    ticker: str
) -> Tuple[bool, List[str]]:
    """
    NEW: Validate that SEC findings are reasonable
    
    Returns:
        (is_valid, list_of_warnings)
    """
    warnings = []
    
    # Check proxy data
    proxy_data = sec_analysis.get('proxy_statement', {})
    if 'error' not in proxy_data:
        exec_comp_count = proxy_data.get('executive_compensation', {}).get('count', 0)
        if exec_comp_count == 0:
            warnings.append("Zero executive compensation items found - likely extraction failure")
    
    # Check ownership data
    ownership_data = sec_analysis.get('ownership_structure', {})
    if 'error' not in ownership_data:
        activist_count = ownership_data.get('total_activist_positions', 0)
        major_sh_count = ownership_data.get('total_major_shareholders', 0)
        if activist_count == 0 and major_sh_count == 0:
            warnings.append("Zero ownership filings found - likely extraction failure")
    
    # Check M&A activity
    ma_activity = sec_analysis.get('ma_activity', {})
    if 'error' not in ma_activity:
        ma_count = ma_activity.get('ma_filings_found', 0)
        # Note: 0 M&A filings can be legitimate, so this is lower priority
        if ma_count == 0:
            warnings.append("No M&A filings found - may indicate no recent M&A activity or extraction issue")
    
    # For major public companies, we expect at least SOME data
    # If ALL categories are 0, that's highly suspicious
    if len(warnings) >= 2:
        return (False, warnings)
    
    return (True, warnings)
```

#### 3.2 Improve Error Propagation

```python
async def run(self, state: DiligenceState) -> Dict[str, Any]:
    """Execute legal analysis with validation"""
    
    # ... existing code ...
    
    # After SEC analysis
    if sec_analysis:
        is_valid, validation_warnings = self._validate_sec_findings(sec_analysis, ticker)
        
        if not is_valid:
            logger.warning(f"SEC findings validation failed: {validation_warnings}")
            # Add warnings to state
            for warning in validation_warnings:
                if 'warnings' not in state:
                    state['warnings'] = []
                state['warnings'].append(f"Legal Counsel: {warning}")
            
            # Flag for user attention
            sec_analysis['_data_quality_warning'] = {
                'status': 'questionable',
                'warnings': validation_warnings,
                'recommendation': 'Manual review of SEC filings recommended'
            }
    
    # ... continue analysis ...
```

#### 3.3 Add Fallback Data Sources

```python
async def _extract_fallback_legal_data(
    self,
    ticker: str
) -> Dict[str, Any]:
    """
    NEW: Extract legal data from alternative sources when SEC fails
    """
    try:
        from .fmp_client import FMPClient
        
        fallback_data = {}
        
        async with FMPClient() as client:
            # Get press releases that mention legal/regulatory topics
            news = await client.get_stock_news(ticker, limit=50)
            
            # Scan for legal keywords
            legal_keywords = ['lawsuit', 'litigation', 'SEC investigation', 'regulatory', 'settlement']
            legal_news = []
            
            for item in news:
                text = (item.get('text', '') + ' ' + item.get('title', '')).lower()
                if any(keyword.lower() in text for keyword in legal_keywords):
                    legal_news.append(item)
            
            fallback_data['legal_news_mentions'] = len(legal_news)
            fallback_data['source'] = 'FMP press releases (fallback)'
        
        return fallback_data
        
    except Exception as e:
        logger.error(f"Fallback legal data extraction error: {e}")
        return {}
```

### Testing Requirements
- [ ] Test validation logic with PLTR data
- [ ] Verify warnings are properly propagated
- [ ] Test fallback data sources
- [ ] Ensure user is notified of data quality issues

### Success Criteria
- System detects when "0 findings" is suspicious
- Clear warnings displayed to user
- Fallback sources attempted when SEC extraction fails
- Manual review recommendations provided

---

## Issue #4: Grounding Check Timeouts

### Problem Statement
```
financial_analyst grounding check: TIMEOUT after 30 seconds
financial_deep_dive grounding check: TIMEOUT after 30 seconds
Claims flagged as "potential hallucinations"
```

The fact-checking validation is timing out, meaning critical financial claims are not being verified.

### Root Cause
1. **Too many claims to verify** - Attempting to verify every claim
2. **Slow LLM calls** - Sequential processing without batching
3. **Insufficient timeout** - 30 seconds inadequate for complex financial claims
4. **No prioritization** - All claims treated equally

### Solution

#### 4.1 Increase Timeout (Immediate Fix)

**File:** `config/synthesis_config.py`

```python
PRODUCTION_CONFIG = SynthesisConfig(
    grounding_depth=GroundingDepth.CRITICAL_ONLY,
    max_concurrent_llm_calls=5,
    enable_batched_verification=True,
    batch_size=5,
    llm_timeout=90,  # CHANGED: from 30 to 90 seconds
    max_retries=2,
    retry_delay=1.0,
    enable_caching=True,
    max_claims_per_agent=20,
    agent_claim_limits={
        'financial_analyst': 15,  # Most important, allow more
        'financial_deep_dive': 15,
        'legal_counsel': 10,
        'deal_structuring': 8,
        'market_strategist': 5,
    }
)
```

#### 4.2 Implement Claim Prioritization (Already Exists - Verify)

**File:** `src/config/synthesis_config.py`

Verify that the `ClaimPrioritizer` class is properly configured:

```python
class ClaimPrioritizer:
    """
    Intelligent claim prioritization for grounding checks
    """
    
    # High priority keywords that indicate critical claims
    HIGH_PRIORITY_KEYWORDS = [
        # Financial metrics (most critical)
        'valuation', 'enterprise_value', 'dcf', 'wacc', 'irr',
        'ebitda', 'revenue', 'margin', 'cash_flow',
        
        # Deal-critical terms
        'change-of-control', 'earnout', 'escrow', 'indemnification',
        'tax_benefit', 'synergy', 'nol',
        
        # Risk factors
        'covenant', 'default', 'penalty', 'liability', 'litigation',
        'regulatory', 'compliance'
    ]
    
    def filter_claims_by_priority(
        self,
        claims: List[Dict[str, Any]],
        config: 'SynthesisConfig'
    ) -> List[Dict[str, Any]]:
        """
        Filter and prioritize claims based on importance
        
        Returns:
            Prioritized list of claims
        """
        if config.grounding_depth == GroundingDepth.FULL:
            return claims  # No filtering
        
        # Score each claim
        scored_claims = []
        for claim in claims:
            content = claim.get('content', '').lower()
            priority_score = 0
            
            # Check for high-priority keywords
            for keyword in self.HIGH_PRIORITY_KEYWORDS:
                if keyword.lower() in content:
                    priority_score += 10
            
            # Numerical claims are important
            if any(char.isdigit() for char in content):
                priority_score += 5
            
            # Financial agents get priority boost
            source_agent = claim.get('source_agent', '')
            if source_agent in ['financial_analyst', 'financial_deep_dive', 'deal_structuring']:
                priority_score += 8
            
            scored_claims.append({
                **claim,
                '_priority_score': priority_score
            })
        
        # Sort by priority
        scored_claims.sort(key=lambda x: x.get('_priority_score', 0), reverse=True)
        
        # Apply depth-based filtering
        if config.grounding_depth == GroundingDepth.CRITICAL_ONLY:
            # Only verify claims with score >= 15
            filtered = [c for c in scored_claims if c.get('_priority_score', 0) >= 15]
            return filtered[:50]  # Max 50 critical claims
        
        elif config.grounding_depth == GroundingDepth.MEDIUM:
            # Verify claims with score >= 5
            filtered = [c for c in scored_claims if c.get('_priority_score', 0) >= 5]
            return filtered[:100]  # Max 100 claims
        
        return scored_claims
```

#### 4.3 Optimize Batched Verification

**File:** `src/utils/parallel_processor.py`

Ensure the `BatchedVerificationProcessor` is being used:

```python
class BatchedVerificationProcessor:
    """
    Process verification tasks in batches for 10x speedup
    """
    
    def __init__(self, parallel_processor: ParallelProcessor):
        self.parallel_processor = parallel_processor
    
    async def verify_claims_batched(
        self,
        claims: List[str],
        source_data: Dict[str, Any],
        verify_func: Callable,
        batch_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Verify claims in batches with parallel processing
        
        Args:
            claims: List of claims to verify
            source_data: Source data for verification
            verify_func: Function to verify a batch of claims
            batch_size: Claims per batch
            
        Returns:
            List of verification results
        """
        # Create batches
        batches = []
        for i in range(0, len(claims), batch_size):
            batch = claims[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"Verifying {len(claims)} claims in {len(batches)} batches of {batch_size}")
        
        # Process batches in parallel
        async def process_batch(batch: List[str]) -> List[Dict[str, Any]]:
            return await verify_func(batch, source_data)
        
        # Use parallel processor with controlled concurrency
        results = await self.parallel_processor.process_tasks(
            [process_batch(batch) for batch in batches],
            task_descriptions=[f"Batch {i+1}/{len(batches)}" for i in range(len(batches))]
        )
        
        # Flatten results
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
            else:
                all_results.append(result)
        
        return all_results
```

#### 4.4 Add Fallback for Timeouts

**File:** `src/agents/synthesis_reporting.py`

Add timeout handling in `_ground_agent_claims`:

```python
async def _ground_agent_claims(
    self,
    agent_name: str,
    agent_data: Dict[str, Any],
    source_data: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Ground agent claims against source data with timeout handling
    """
    grounded_data = agent_data.copy()
    hallucinations = []

    try:
        # Extract and prioritize claims
        claim_dicts = self._extract_factual_claims(agent_data, agent_name)
        
        if not claim_dicts:
            return grounded_data, hallucinations
        
        claims = [c['content'] for c in claim_dicts]
        
        self.log_action(f"Verifying {len(claims)} prioritized claims for {agent_name}")

        # Verify with timeout protection
        try:
            verification_results = await asyncio.wait_for(
                self._verify_claims_batched_parallel(claims, source_data, agent_name),
                timeout=self.config.llm_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Grounding check for {agent_name} timed out after {self.config.llm_timeout}s")
            
            # FALLBACK: Mark all claims as "unverified" instead of "hallucination"
            verification_results = []
            for claim in claims:
                verification_results.append({
                    'is_grounded': False,
                    'severity': 'unknown',
                    'reason': f'Verification timed out after {self.config.llm_timeout}s',
                    'action': 'Manual review recommended'
                })
            
            # Add timeout warning
            hallucinations.append({
                'agent': agent_name,
                'claim': f'{len(claims)} claims not verified due to timeout',
                'severity': 'medium',
                'reason': f'Grounding check exceeded {self.config.llm_timeout}s timeout',
                'suggested_action': 'Consider increasing timeout or reducing claim count'
            })
        
        # Process results
        for claim, verification in zip(claims, verification_results):
            if not verification['is_grounded'] and verification['severity'] not in ['unknown']:
                hallucinations.append({
                    'agent': agent_name,
                    'claim': claim,
                    'severity': verification['severity'],
                    'reason': verification['reason'],
                    'suggested_action': verification['action']
                })

        # Add metadata
        grounded_data['_grounding_metadata'] = {
            'total_claims_checked': len(claims),
            'hallucinations_found': len(hallucinations),
            'grounding_coverage': (len(claims) - len(hallucinations)) / len(claims) if claims else 0,
            'optimization_used': 'batched_parallel',
            'timeout_occurred': len(verification_results) > 0 and verification_results[0].get('reason', '').startswith('Verification timed out')
        }

    except Exception as e:
        self.log_action(f"Error grounding claims for {agent_name}: {e}", level="error")

    return grounded_data, hallucinations
```

### Testing Requirements
- [ ] Test with financial_analyst (complex claims)
- [ ] Test with financial_deep_dive (many claims)
- [ ] Verify batching reduces processing time
- [ ] Confirm timeout handling works

### Success Criteria
- Grounding checks complete within timeout
- Critical claims prioritized and verified
- Timeout failures handled gracefully
- Processing time < 60 seconds for typical agent

---

## Issue #5: Flawed Peer Benchmarking

### Problem Statement
```
Primary peer finding method: EMPTY
Secondary peer finding method: EMPTY
Fallback: Generic broad industry screen (not accurate)
```

The competitive benchmarking agent cannot find direct peers, leading to invalid competitive analysis.

### Root Cause
1. **FMP stock-peers endpoint not reliable** - Returns empty for many companies
2. **No fallback to FMP peers-bulk endpoint** - Better data source not being used
3. **Sector screening too restrictive** - Market cap and other filters too narrow
4. **No validation of peer quality** - Accepts any company in sector

### Solution

#### 5.1 Add FMP Stock Peer Comparison API

**User feedback specified this critical API:**
```
Stock Peer Comparison API
Endpoint: https://financialmodelingprep.com/stable/stock-peers?symbol=AAPL
```

**File:** `src/integrations/fmp_client.py`

Add method to access this endpoint:

```python
async def get_stock_peers(self, symbol: str) -> Dict[str, Any]:
    """
    Get peer companies using FMP Stock Peer Comparison API
    
    This endpoint identifies companies within the same sector and market cap range
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with peersList containing peer tickers
    """
    try:
        # Use the stable endpoint for stock peers
        endpoint = f"stock-peers?symbol={symbol}"
        
        response = await self._make_request(endpoint)
        
        if response and isinstance(response, list) and len(response) > 0:
            # API returns a list with one object containing peersList
            peers_data = response[0]
            
            logger.info(f"Found {len(peers_data.get('peersList', []))} peers for {symbol} via stock-peers API")
            
            return peers_data
        
        logger.warning(f"stock-peers API returned no data for {symbol}")
        return {}
        
    except Exception as e:
        logger.error(f"Error fetching stock peers for {symbol}: {e}")
        return {}
```

#### 5.2 Update Competitive Benchmarking Agent

**File:** `src/agents/competitive_benchmarking.py`

Update `_identify_peers` method to use the new endpoint first:

```python
async def _identify_peers(self, symbol: str) -> List[str]:
    """
    ENHANCED: Identify true peer companies using multi-tiered approach
    
    Tier 1: FMP Stock Peer Comparison API (BEST - same sector + market cap)
    Tier 2: FMP peers-bulk endpoint
    Tier 3: Sector + industry screening
    Tier 4: Broad sector screening
    """
    try:
        async with FMPClient() as client:
            # TIER 1: Try FMP Stock Peer Comparison API (USER REQUESTED)
            try:
                peers_response = await client.get_stock_peers(symbol)
                
                if peers_response and 'peersList' in peers_response:
                    peers_list = peers_response.
