# Cloud Deployment Issues - Root Cause Analysis & Fix

**Date**: November 4, 2025  
**Status**: CRITICAL PRODUCTION ISSUE  
**Impact**: System slowness, agent failures (sources_uses, accretion_dilution, exchange_ratio), synthesis hanging

## Root Cause Analysis

### 1. **SEC API Timeout Issues in Cloud** ⚠️
**Location**: `src/agents/financial_deep_dive.py` lines 114-151

**Problem**:
- The deep dive agent fetches SEC documents (10-K, DEF 14A) which can take 5-10+ minutes per document
- In cloud environment with limited timeout windows, these API calls are failing silently
- The agent has SEC caching code BUT it's not working efficiently in cloud

**Evidence**:
```python
# Pre-fetching SEC documents (10-K, DEF 14A) to avoid redundant API calls
logger.info(f"[DEEP DIVE] Pre-fetching SEC documents...")
filing_10k = await sec_client.get_filing_full_text(target_ticker, '10-K')
```

**Impact**: 
- Deep dive agent hangs or times out
- Downstream agents that depend on this data fail
- Synthesis agent waits forever for incomplete data

### 2. **M&A Agents Missing Required Data** ⚠️
**Location**: `src/api/orchestrator.py` - Agent execution order

**Problem**:
- M&A agents (sources_uses, accretion_dilution, exchange_ratio) require specific data fields
- If financial_deep_dive or other upstream agents fail to complete, these agents show "pending"
- No proper error handling for missing prerequisites

**Current Agent Order**:
```python
("financial_analyst", FinancialAnalystAgent()),        # Completes
("financial_deep_dive", FinancialDeepDiveAgent()),    # HANGS in cloud
("deal_structuring", DealStructuringAgent()),         # May complete
("sources_uses", SourcesUsesGenerator()),            # PENDING - needs data
("accretion_dilution", AccretionDilutionAgent()),     # PENDING - needs data  
("exchange_ratio_analysis", ExchangeRatioAnalyzer()), # PENDING - needs data
```

### 3. **Cloud Environment Timeout Constraints** ⚠️
**Location**: Cloud Run / Container orchestration

**Problem**:
- Google Cloud Run has default request timeout of 5 minutes (can be extended to 60 min max)
- SEC API calls can take 10-15 minutes for large 10-K filings
- WebSocket connections may timeout during long-running operations
- No retry logic for failed API calls

### 4. **Post-Deployment Code Changes** ⚠️
**User reported**: "Changed deep agent after deploying to cloud which is a mistake"

**Problem**:
- Modifications made to financial_deep_dive.py after deployment
- Working local code was replaced with cloud-specific changes
- Need to restore original working version

## Immediate Fix Plan

### Phase 1: Restore Working Local Version (PRIORITY 1)

1. **Revert financial_deep_dive.py changes**
   ```bash
   git log --all -- src/agents/financial_deep_dive.py
   git diff HEAD~1 src/agents/financial_deep_dive.py
   # Review changes and revert if needed
   ```

2. **Disable SEC document fetching in cloud temporarily**
   - Set environment variable: `DISABLE_SEC_FILINGS=true`
   - Agent will skip 10-K/DEF 14A parsing
   - Use only FMP API data (much faster)

### Phase 2: Fix Agent Timeout Issues (PRIORITY 1)

1. **Add timeout controls to SEC API calls**
   ```python
   # In financial_deep_dive.py
   try:
       filing_10k = await asyncio.wait_for(
           sec_client.get_filing_full_text(target_ticker, '10-K'),
           timeout=120  # 2 minute timeout
       )
   except asyncio.TimeoutError:
       logger.warning("10-K fetch timed out - using FMP data only")
       sec_cache['10k_text'] = ''
   ```

2. **Make SEC document fetching optional**
   ```python
   ENABLE_SEC_FILINGS = os.getenv('ENABLE_SEC_FILINGS', 'false').lower() == 'true'
   
   if ENABLE_SEC_FILINGS:
       # Fetch SEC documents
   else:
       # Skip and use FMP data only
       logger.info("SEC filings disabled - using FMP data only")
   ```

### Phase 3: Fix M&A Agent Dependencies (PRIORITY 1)

1. **Add prerequisite data checks**
   ```python
   # In orchestrator.py before running M&A agents
   required_data = {
       'sources_uses': ['deal_value', 'financial_data'],
       'accretion_dilution': ['acquirer_data', 'deal_terms', 'deal_value'],
       'exchange_ratio_analysis': ['acquirer_data', 'target_data', 'valuation_models']
   }
   
   for agent_key, required_fields in required_data.items():
       missing = [f for f in required_fields if not state.get(f)]
       if missing:
           logger.error(f"Cannot run {agent_key} - missing: {missing}")
           state = update_agent_status(state, agent_key, AgentStatus.SKIPPED)
           continue
   ```

2. **Add graceful fallbacks for M&A agents**
   - If acquirer_data missing, use target-only analysis
   - If deal_terms missing, use auto-generated defaults from DCF
   - Log warnings but don't block entire workflow

### Phase 4: Increase Cloud Timeout Limits (PRIORITY 2)

1. **Update Cloud Run service timeout**
   ```bash
   gcloud run services update aimadds-backend \
       --timeout=3600 \
       --region=us-central1
   ```

2. **Update Dockerfile health checks**
   ```dockerfile
   # Increase startup/liveness probe timeouts
   HEALTHCHECK --interval=60s --timeout=30s --start-period=120s \
       CMD python -c "import requests; requests.get('http://localhost:8000/health')"
   ```

3. **Configure async worker pool**
   ```python
   # In server.py
   MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
   WORKER_TIMEOUT = int(os.getenv('WORKER_TIMEOUT', '3600'))
   ```

## Quick Fix Implementation

### Step 1: Add Environment Variable Control
```python
# Add to src/agents/financial_deep_dive.py (top of file)
import os

# Feature flag for SEC document fetching
ENABLE_SEC_DOCUMENTS = os.getenv('ENABLE_SEC_DOCUMENTS', 'false').lower() == 'true'
SEC_FETCH_TIMEOUT = int(os.getenv('SEC_FETCH_TIMEOUT', '180'))  # 3 minutes default
```

### Step 2: Wrap SEC Calls with Timeout
```python
# In financial_deep_dive.py _analyze_customer_concentration method
if ENABLE_SEC_DOCUMENTS and sec_cache:
    try:
        text = await asyncio.wait_for(
            self._fetch_sec_text_safely(sec_cache, ticker),
            timeout=SEC_FETCH_TIMEOUT
        )
    except asyncio.TimeoutError:
        logger.warning(f"SEC document fetch timed out after {SEC_FETCH_TIMEOUT}s")
        text = ''
else:
    text = ''
    logger.info("SEC documents disabled - using FMP data only")
```

### Step 3: Add Agent Prerequisite Validation
```python
# In orchestrator.py before M&A agents
def validate_agent_prerequisites(state, agent_key):
    """Check if agent has required data to run"""
    prerequisites = {
        'sources_uses': {
            'required': ['deal_value'],
            'optional': ['deal_terms', 'financial_data']
        },
        'accretion_dilution': {
            'required': ['acquirer_data', 'deal_value'],
            'optional': ['deal_terms']
        },
        'exchange_ratio_analysis': {
            'required': ['acquirer_data', 'valuation_models'],
            'optional': ['deal_terms']
        }
    }
    
    if agent_key not in prerequisites:
        return True, []
    
    reqs = prerequisites[agent_key]['required']
    missing = [field for field in reqs if not state.get(field)]
    
    if missing:
        logger.error(f"❌ {agent_key} missing required data: {missing}")
        return False, missing
    
    return True, []

# Use before running agents
can_run, missing = validate_agent_prerequisites(state, agent_key)
if not can_run:
    logger.warning(f"Skipping {agent_key} - missing: {missing}")
    state = update_agent_status(state, agent_key, AgentStatus.SKIPPED)
    state['warnings'].append(f"{agent_key} skipped - missing data: {', '.join(missing)}")
    continue
```

## Deployment Steps

### 1. Local Testing First
```bash
# Test with SEC documents disabled
$env:ENABLE_SEC_DOCUMENTS="false"
python -m src.api.server

# Run analysis - should complete quickly
# Verify M&A agents complete successfully
```

### 2. Update .env Files
```bash
# Add to .env and production secrets
ENABLE_SEC_DOCUMENTS=false
SEC_FETCH_TIMEOUT=180
MAX_WORKERS=4
WORKER_TIMEOUT=3600
```

### 3. Deploy to Cloud
```bash
# Update secrets
gcloud secrets versions add ENABLE_SEC_DOCUMENTS --data-file=- <<< "false"

# Increase timeout
gcloud run services update aimadds-backend \
    --timeout=3600 \
    --max-instances=4 \
    --region=us-central1

# Deploy updated code
./scripts/deploy_to_gcloud.ps1
```

### 4. Monitor Cloud Run Logs
```bash
# Watch logs for errors
gcloud run services logs read aimadds-backend --limit=100 --region=us-central1

# Check for timeout errors
gcloud run services logs read aimadds-backend --limit=100 --region=us-central1 | grep -i "timeout"
```

## Performance Improvements

### Expected Results After Fix:
- **Financial Analyst**: 30-60 seconds (was working)
- **Deep Dive Agent**: 60-90 seconds (vs 10+ minutes with SEC docs)
- **M&A Agents**: 30-45 seconds each (vs pending/hanging)
- **Synthesis**: 2-3 minutes (vs hanging)
- **Total Runtime**: 8-12 minutes (vs 20+ minutes or timeout)

### If SEC Documents Needed:
1. Make them async background tasks
2. Store in database for future use
3. Don't block main workflow
4. Display progress separately

```python
# Background SEC fetching (future enhancement)
async def fetch_sec_documents_background(job_id, ticker):
    """Fetch SEC documents asynchronously without blocking workflow"""
    try:
        docs = await sec_client.get_all_filings(ticker)
        # Store in database
        await store_sec_documents(job_id, docs)
        # Notify frontend
        await broadcast_update(job_id, {"type": "sec_docs_ready"})
    except Exception as e:
        logger.error(f"Background SEC fetch failed: {e}")
```

## Monitoring & Validation

### Health Checks
```python
# Add to api_health_check.py
def check_agent_timeouts():
    """Check if any agents are timing out"""
    recent_jobs = get_recent_jobs(limit=10)
    
    timeout_agents = []
    for job in recent_jobs:
        for agent_status in job['agent_statuses']:
            if agent_status['status'] == 'running':
                runtime = datetime.now() - agent_status['started_at']
                if runtime > timedelta(minutes=10):
                    timeout_agents.append({
                        'job_id': job['id'],
                        'agent': agent_status['name'],
                        'runtime': runtime
                    })
    
    return timeout_agents
```

### Alert Thresholds
- Agent running > 10 minutes: WARNING
- Agent running > 20 minutes: CRITICAL (kill and skip)
- Total job time > 30 minutes: CRITICAL (investigate)

## Rollback Plan

If fixes don't work:
1. Revert to last known working commit
2. Disable all M&A agents temporarily
3. Run with only core agents (financial_analyst, market_strategist, synthesis)
4. Investigate cloud environment constraints separately

```bash
# Emergency rollback
git revert HEAD~3..HEAD
./scripts/deploy_to_gcloud.ps1 --force
```

## Testing Checklist

- [ ] Local run completes in < 10 minutes
- [ ] All M&A agents complete successfully
- [ ] No pending/hanging agents
- [ ] Synthesis completes and generates reports
- [ ] Cloud deployment with test ticker (AAPL)
- [ ] Monitor cloud logs for timeouts
- [ ] Verify all reports generated
- [ ] Check WebSocket connections stable

## Next Steps

1. **Immediate**: Implement Phase 1-2 fixes (timeout control, disable SEC temporarily)
2. **Short-term**: Add agent prerequisite validation
3. **Medium-term**: Optimize SEC document fetching (caching, async)
4. **Long-term**: Implement background job queue for long-running tasks

## Conclusion

The root cause is **SEC API calls timing out in cloud environment** combined with **missing error handling for agent dependencies**. The fix is to:

1. Temporarily disable SEC document fetching
2. Add timeout controls to all external API calls
3. Add prerequisite validation for M&A agents
4. Increase cloud timeout limits

This will restore the system to working order and allow all agents to complete successfully.
