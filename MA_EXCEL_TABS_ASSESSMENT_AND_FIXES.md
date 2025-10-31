# M&A Excel Tabs Assessment & Zero Values Fix

**Date**: October 30, 2025  
**Issue**: EPS Accretion/Dilution tab shows $0.00 values, missing 3 M&A agent tabs

## Excel Tab Coverage Assessment

### ✅ Current Tab: EPS Accretion/Dilution
**Status**: CRITICAL for M&A - Correctly included ✅  
**Purpose**: Shows if deal is accretive or dilutive to acquirer's earnings

**However**: Shows $0.00 for all acquirer metrics (DATA ISSUE - see Fix #2 below)

### 🆕 Missing M&A Tabs (Investment Banking Standard)

#### 1. Sources & Uses Tab (CRITICAL - MISSING)
**Why Essential**:
- **THE** standard tab in every investment banking M&A model
- Shows exactly how deal will be financed
- Required by lenders, boards, rating agencies

**What It Shows**:
- **Uses**: Purchase price, refinance target debt, transaction fees, financing fees
- **Sources**: Acquirer cash, new debt, new equity, rollover equity
- **Pro Forma Cap Table**: Combined debt/equity structure

**Investment Banking View**: "No sources & uses = incomplete M&A model"

#### 2. Deal Structure Tab (IMPORTANT - MISSING)
**Why Essential**:
- Compares structural alternatives (asset vs. stock, cash vs. stock mix)
- Tax implications analysis (338(h)(10) elections)
- Earnout provisions modeling
- Working capital peg calculations

**What It Shows**:
- Stock vs. cash consideration analysis
- Purchase price allocation
- Tax structure comparison
- Earnout scenarios

**Investment Banking View**: "Shows we've thought through all structural options"

#### 3. Contribution Analysis Tab (IMPORTANT FOR MERGERS - MISSING)
**Why Essential**:
- Critical for merger-of-equals transactions
- Required for fairness opinions
- Shows relative value contribution of each party

**What It Shows**:
- Revenue/EBITDA/NI contribution percentages
- Ownership split vs. contribution split
- Fairness delta analysis
- Relative valuation multiples

**Investment Banking View**: "Essential for negotiating fair exchange ratios"

#### 4. Exchange Ratio Tab (CRITICAL FOR STOCK DEALS - MISSING)
**Why Essential**:
- Required for any stock-for-stock deal
- Shows premium analysis
- Multiple valuation-based ratios

**What It Shows**:
- Proposed exchange ratio (acquirer shares per target share)
- DCF/P/E/P/B-based exchange ratios
- Premium to current/30-day/52-week prices
- Fairness assessment

**Investment Banking View**: "Can't do a stock deal without this analysis"

## Verdict on Current Coverage

### For Acquisition (All-Cash or Mostly Cash)
**Minimum Required**:
- ✅ EPS Accretion/Dilution (have it)
- ❌ Sources & Uses (MISSING - CRITICAL)
- ❌ Deal Structure (MISSING - IMPORTANT)

**Grade**: C+ (60%) - Missing critical financing tab

### For Merger or Stock-Heavy Deal
**Minimum Required**:
- ✅ EPS Accretion/Dilution (have it)
- ❌ Sources & Uses (MISSING - CRITICAL)
- ❌ Deal Structure (MISSING - IMPORTANT)
- ❌ Contribution Analysis (MISSING - CRITICAL)
- ❌ Exchange Ratio (MISSING - CRITICAL)

**Grade**: D (40%) - Missing most M&A-specific tabs

## Zero Values Fix

### Problem Diagnosis
```
Acquirer Standalone EPS: $0.00  ← Should be ~$5-15 typically
Target Contribution to EPS: $0.00  ← Should show incremental contribution
Pro Forma Combined EPS: $10.63  ← This works! So calculation logic is OK
```

### Root Cause
The accretion_dilution agent is receiving:
- ✅ Target data (works - contributes to pro forma)
- ❌ Acquirer data (missing - causes $0.00 values)

### Where to Fix

**File**: `src/api/orchestrator.py` (already has code but may not be working)

**Check**:
```python
# Around line 240 in orchestrator.py
acquirer_ticker = state.get('acquirer_ticker')
if acquirer_ticker:
    # Fetch acquirer data
    acquirer_analyst = FinancialAnalystAgent()
    acquirer_result = await acquirer_analyst.analyze(acquirer_ticker)
    state['acquirer_data']
