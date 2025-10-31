# M&A Agents Data Requirements - CRITICAL FINDING

**Date:** October 30, 2025
**Status:** ✅ Agents Running, ❌ Missing Critical Input Data

## Summary

**Good News:** All 5 M&A agents ARE running successfully and appearing in logs
**Problem:** They're producing default/placeholder values because `deal_terms` is MISSING from the analysis state

## Diagnostic Results

### Agent Execution Status: ✅ ALL RUNNING

```
M&A agents that ran: 5/5
  ✅ accretion_dilution
  ✅ sources_uses
  ✅ contribution_analysis
  ✅ exchange_ratio_analysis
  ✅ deal_structuring
```

### Data Structure: ✅ CORRECT

All agents return proper dictionary structures (not lists):
- `accretion_dilution`: Has 12 keys including deal_recommendation, board_summary
- `sources_uses`: Has 7 keys including uses_of_funds, sources_of_funds  
- `contribution_analysis`: Has 6 keys including fairness_analysis
- `exchange_ratio_analysis`: Has 7 keys including fairness_assessment, proposed_ratio
- `deal_structuring`: Has 7 keys including recommended_structure

### Critical Input Data: ❌ MISSING `deal_terms`

**Problem Found:**
```
Required inputs: ['acquirer_data', 'deal_terms']
  ✅ acquirer_data: dict - Present
  ❌ deal_terms: MISSING!  <-- THIS IS THE ISSUE
```

## Why Default Values Appear

When M&A agents run WITHOUT `deal_terms`, they:

1. **Accretion/Dilution Agent:**
   - `deal_recommendation`: "Under review" (no financing terms to calculate with)
   - `eps_impact`: 0 (can't calculate without cash/stock mix)

2. **Sources & Uses Agent:**
   - Returns structure but with placeholder amounts
   - Can't calculate financing without deal terms

3. **Contribution Analysis:**
   - `fairness_assessment`: "Under review" (no deal structure to assess)

4. **Exchange Ratio:**
   - `base_exchange_ratio`: 0 (no proposed ratio without deal terms)

5. **Deal Structuring:**
   - `recommended_structure`: "Mixed cash and stock" (generic recommendation)

## What is `deal_terms`?

The `deal_terms` object should contain:

```python
deal_terms = {
    'purchase_price': 30000000000,  # Total deal value
    'cash_percentage': 0.5,  # 50% cash, 50% stock
    'debt_interest_rate': 0.05,  # 5% interest on debt financing
    'tax_rate': 0.21,  # 21% tax rate
    'acquirer_stock_price': 150,  # Current acquirer stock price
    'synergies_year1': 1000000000,  # $1B Year 1 synergies
    'acquirer_cash_available': 5000000000,  # $5B available cash
    'proposed_exchange_ratio': 0.50  # 0.50 acquirer shares per target share
}
```

## How to Fix

### Option 1: User Provides deal_terms (Preferred)

Update the frontend `AnalysisForm.jsx` to collect deal terms:
- Cash vs stock percentage
- Proposed exchange ratio (if stock deal)
- Estimated synergies
- Financing assumptions

### Option 2: Auto-Generate deal_terms from Valuation

If user doesn't provide deal_terms, system should auto-generate from Financial Analyst output:

```python
# After financial_analyst completes in orchestrator.py
if not state.get('deal_terms'):
    dcf_value = state.get('valuation_models', {}).get('dcf_advanced', {})
    base_ev = dcf_value.get('dcf_analysis', {}).get('base', {}).get('enterprise_value', 0)
    acquirer_price = state.get('acquirer_data', {}).get('current_stock_price', 100)
    
    # Auto-generate reasonable defaults
    state['deal_terms'] = {
        'purchase_price': base_ev,
        'cash_percentage': 0.5,  # 50/50 mix
        'debt_interest_rate': 0.05,
        'tax_rate': 0.21,
        'acquirer_stock_price': acquirer_price,
        'synergies_year1': base_ev * 0.05,  # 5% synergies assumption
        'acquirer_cash_available': 0
    }
    logger.info("Auto-generated deal_terms from valuation")
```

### Option 3: Make M&A Agents More Defensive

Update each M&A agent to work with minimal data:

```python
# In accretion_dilution.py analyze() method
if not deal_terms or not deal_terms.get('purchase_price'):
    # Use DCF valuation as fallback
    purchase_price = valuation_data.get('dcf_advanced', {}).get('dcf_analysis', {}).get('base', {}).get('enterprise_value', 0)
    
    deal_terms = {
        'purchase_price': purchase_price,
        'cash_percentage': 0.5,
        'debt_interest_rate': 0.05,
        'tax_rate': 0.21,
        'acquirer_stock_price': acquirer_data.get('current_stock_price', 100),
        'synergies_year1': purchase_price * 0.05
    }
    logger.warning("Using auto-generated deal_terms - results are ILLUSTRATIVE ONLY")
```

## Current State

✅ **Frontend:** All M&A agents now visible in progress tracker
✅ **Backend:** All M&A agents executing successfully  
✅ **PDF Generator:** Type-safe data access (no more list errors)
❌ **Data Flow:** `deal_terms` not being passed to M&A agents

## Recommended Immediate Fix

Add `deal_terms` auto-generation in `src/api/orchestrator.py` right after financial_analyst completes:

```python
# After financial_analyst agent (around line 650)
if agent_key == "financial_analyst":
    # Auto-generate deal_terms if not provided
    if not state.get('deal_terms'):
        logger.info("deal_terms not provided - auto-generating from valuation...")
        
        dcf_value = state.get('valuation_models', {}).get('dcf_advanced', {})
        base_ev = dcf_value.get('dcf_analysis', {}).get('base', {}).get('enterprise_value', 0)
        acquirer_price = state.get('acquirer_data', {}).get('current_stock_price', 100)
        
        state['deal_terms'] = {
            'purchase_price': base_ev,
            'cash_percentage': 0.5,
            'debt_interest_rate': 0.05,
            'tax_rate': 0.21,
            'acquirer_stock_price': acquirer_price,
            'synergies_year1': base_ev * 0.05,
            'acquirer_cash_available': 0,
            'auto_generated': True,
            'note': 'Auto-generated from DCF valuation - user should provide actual deal terms for accurate analysis'
        }
        
        logger.info(f"✓ Auto-generated deal_terms with ${base_ev/1e9:.1f}B purchase price")
```

This way M&A agents will have at least illustrative data to work with, even if user doesn't provide specific deal terms.

## Impact

**Before Fix:**
- M&A agents run but produce: "Under review", 0, "N/A"
- Reports show placeholders instead of analysis

**After Fix:**
- M&A agents calculate with realistic assumptions
- Reports show actual accretion/dilution, sources & uses, exchange ratios
- User experience dramatically improved

## Action Required

**Immediate:** Add deal_terms auto-generation to orchestrator.py
**Long-term:** Update frontend to collect deal_terms from user
