# M&A Tabs & Acquirer Data - Complete Implementation Plan

**Date**: October 30, 2025  
**Scope**: Add 3 M&A tabs + fix acquirer data flow

## Tasks Overview

### Task 1: Fix Acquirer Data Flow (CRITICAL - Do First)
**Priority**: P0 - Blocks accretion/dilution calculations  
**Files**: 1 file
**Estimated Time**: 15 minutes

### Task 2: Add Sources & Uses Tab
**Priority**: P0 - Investment banking standard  
**Files**: 4 files (Excel, PDF, PPT, Dashboard)
**Estimated Time**: 45 minutes

### Task 3: Add Deal Structure Tab
**Priority**: P1 - Important for M&A  
**Files**: 4 files
**Estimated Time**: 30 minutes

### Task 4: Add Contribution Analysis Tab
**Priority**: P1 - Important for mergers  
**Files**: 4 files
**Estimated Time**: 30 minutes

### Task 5: Add Exchange Ratio Tab
**Priority**: P1 - Important for stock deals  
**Files**: 4 files
**Estimated Time**: 30 minutes

**Total Estimated Time**: ~2.5 hours for complete implementation

---

## TASK 1: Fix Acquirer Data Flow ⚡ DO FIRST

### Problem
```
Acquirer Standalone EPS: $0.00  ← Missing acquirer data
Target Contribution: $0.00      ← Can't calculate without acquirer baseline
Pro Forma Combined EPS: $10.63  ← This works (uses target data only)
```

### Root Cause
The orchestrator fetches acquirer data but may not be storing it correctly in the format the accretion_dilution agent expects.

### Fix Location
**File**: `src/api/orchestrator.py`

**Current Code** (around line 240):
```python
if acquirer_ticker:
    acquirer_analyst = FinancialAnalystAgent()
    acquirer_result = await acquirer_analyst.analyze(acquirer_ticker)
    
    # ISSUE: Storing in wrong location
    state['acquirer_financial_data'] = acquirer_result.get('historical_data', {})
    state['acquirer_metrics'] = acquirer_result.get('financial_health', {})
```

**What accretion_dilution agent expects**:
```python
# From accretion_dilution.py line 53:
acquirer_data = state.get('acquirer_data', {})  # ← Looks for 'acquirer_data'
```

**Fix Required**:
```python
if acquirer_ticker:
    acquirer_analyst = FinancialAnalystAgent()
    acquirer_result = await acquirer_analyst.analyze(acquirer_ticker)
    
    # CRITICAL FIX: Store in correct location
    state['acquirer_data'] = {
        'income_statement': acquirer_result.get('historical_data', {}).get('income_statement', []),
        'balance_sheet': acquirer_result.get('historical_data', {}).get('balance_sheet', []),
        'cash_flow': acquirer_result.get('historical_data', {}).get('cash_flow', []),
        'current_stock_price': acquirer_result.get('price_data', {}).get('current_price', 100)
    }
    
    # Also store in original locations for backward compatibility
    state['acquirer_financial_data'] = acquirer_result.get('historical_data', {})
    state['acquirer_metrics'] = acquirer_result.get('financial_health', {})
```

---

## TASK 2: Add Sources & Uses Tab

### Files to Modify

#### 1. src/outputs/revolutionary_excel_generator.py
**Add Method**:
```python
def _create_sources_uses_tab(self, workbook, state):
    """Create Sources & Uses of Funds tab"""
    # Extract sources_uses agent data
    # Create formatted tables for Uses and Sources
    # Add pro forma capitalization section
```

**Add to Workflow** (in `generate_revolutionary_workbook`):
```python
self._create_sources_uses_tab(workbook, state)
```

#### 2. src/outputs/revolutionary_pdf_generator.py
**Add Section**: "Section 5C: Sources & Uses Analysis"
```python
def _create_sources_uses_section(self, state):
    """Create sources & uses PDF section"""
```

#### 3. src/outputs/revolutionary_ppt_generator.py
**Add Slide**: Sources & Uses slide

#### 4. Frontend Dashboard
**Add Widget**: Sources & Uses summary card

---

## TASK 3-5: Add Other M&A Tabs

Similar pattern for:
- Deal Structure
- Contribution Analysis
- Exchange Ratio

Each requires updates to Excel, PDF, PPT, Dashboard

---

## Implementation Order

1. ✅ Fix acquirer data flow (15 min) - **DO THIS FIRST**
2. ✅ Add Sources & Uses to Excel (20 min)
3. ✅ Add Sources & Uses to PDF (15 min)
4. Add Sources & Uses to PPT (10 min)
5. Add Sources & Uses to Dashboard (10 min)
6. Repeat for Deal Structure, Contribution, Exchange Ratio

---

## Testing Plan

After each tab addition:
1. Run full M&A workflow
2. Check Excel has new tab with real data
3. Verify PDF has new section
4. Confirm PPT has new slide
5. Validate Dashboard shows widget

---

## Success Criteria

✅ All $0.00 values fixed (acquirer data flows)  
✅ Sources & Uses tab in Excel/PDF/PPT  
✅ Deal Structure tab in Excel/PDF/PPT  
✅ Contribution Analysis tab in Excel/PDF/PPT  
✅ Exchange Ratio tab in Excel/PDF/PPT  
✅ Dashboard shows all M&A metrics

**Result**: Investment banking-grade M&A analysis suite

---

**Ready to Proceed**: Let me know when to start implementation!
