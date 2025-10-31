# Investment Banking Quality Fix - Immediate Action Plan

**Purpose:** Remove all fallbacks, add proper retry logic, ensure 100% real analysis

---

## 🎯 WORK REQUIRED

### Phase 1: Create Retry Utility (15 min)

**File:** `src/utils/llm_retry.py` (NEW)

```python
import asyncio
import traceback
from loguru import logger

async def llm_call_with_retry(llm, messages, max_retries=3, timeout=90):
    """Investment banking grade LLM call with retry logic"""
    for attempt in range(max_retries):
        try:
            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                logger.error(f"LLM call FAILED after {max_retries} timeout attempts")
                raise RuntimeError("Critical: LLM service timeout - analysis cannot proceed")
            logger.info(f"Timeout on attempt {attempt + 1}, retrying...")
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
        except Exception as e:
            error_msg = str(e) if str(e) else type(e).__name__
            if attempt == max_retries - 1:
                logger.error(f"LLM call FAILED: {error_msg}\n{traceback.format_exc()}")
                raise RuntimeError(f"Critical: LLM call failed - {error_msg}")
            logger.info(f"Error on attempt {attempt + 1}: {error_msg}, retrying...")
            await asyncio.sleep(2 ** attempt)
    
    raise RuntimeError("Should not reach here")
```

### Phase 2: Update All Agents (60 min)

**Replace ALL try/except fallbacks with:**

```python
from ..utils.llm_retry import llm_call_with_retry

# Instead of fallback:
response = await llm_call_with_retry(self.llm, messages, max_retries=3, timeout=90)
```

**Files to Update:**
1. Market Strategist - 4 methods
2. Integration Planner - 3 methods
3. Legal Counsel - 1 method
4. Synthesis Reporting - 2 methods
5. Financial Analyst - 1 method (Gemini fallback)

### Phase 3: Add Rate Limiting (30 min)

**File:** `src/core/llm_factory.py`

Add rate limiter to LLM factory to prevent hitting API limits

---

## ✅ EXPECTED RESULT

**After Fix:**
- All agents use REAL LLM analysis (no fallbacks)
- Proper retry with exponential backoff (3 attempts)
- Clear errors if LLM truly fails
- Rate limiting prevents API exhaustion
- 100% real analysis or clear failure

**Investment Banking Quality:** ✅ ACHIEVED

---

## 🚀 IMPLEMENTATION

**Total Time:** ~2 hours  
**Complexity:** Medium  
**Impact:** Critical for client-grade quality

**Ready to proceed?**
