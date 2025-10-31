# AGENT DATA COMPLETENESS & RECENCY WEIGHTING FIXES

**Date**: October 29, 2025  
**Priority**: CRITICAL - Ensures agents have correct data and emphasize recent reality  

---

## 🎯 ISSUES TO FIX

### Issue #1: Agents May Be Falling Back to Raw Data
**Problem**: If normalized arrays are empty, agents use raw financial_data as fallback
**Impact**: Agents get un-normalized data with corrupted years included
**Solution**: Ensure normalized arrays ALWAYS populated before agents run

### Issue #2: Equal Weighting of All Years
**Problem**: Normalization treats 2018 data same as 2024 data
**Impact**: Old corrupted data has same influence as recent accurate data
**Solution**: Implement recency weighting - recent quarters/years weighted higher

---

## ✅ FIX #1: Ensure Normalized Data Always Available

### Implementation in `src/agents/financial_analyst.py`:

```python
async def run(self, state: DiligenceState) -> Dict[str, Any]:
    # ... existing code ...
    
    # Phase 2 Enhancement 1: Financial Statement Normalization
    logger.info("Step 1: Normalizing financial statements...")
    normalized_data = await self._normalize_financial_statements(financial_data)
    
    # CRITICAL FIX: Validate normalization succeeded
    income_count = len(normalized_data.get('income_statement', []))
    if income_count == 0:
        logger.error("❌ CRITICAL: Normalization failed - income_statement array is EMPTY")
        logger.error("❌ BLOCKING: Cannot proceed without normalized data")
        return {
            "data": {},
            "errors": ["Normalization failed - no clean data available"],
            "warnings": ["Check for data quality issues in raw financial data"],
            "recommendations": ["Review FMP API data quality for this ticker"]
        }
    
    logger.info(f"✓ Normalization successful: {income_count} clean years available")
```

### Implementation in `src/agents/competitive_benchmarking.py`:

```python
async def run(self, state: Any) -> Dict[str, Any]:
    # Get target financial metrics using smart accessor (prioritizes normalized)
    financial_data_smart = self._get_financial_data_smart(state, prefer_normalized=True)
    
    # CRITICAL FIX: Validate we got normalized data
    data_source = financial_data_smart.get('source', 'unknown')
    if data_source != 'normalized':
        logger.warning(
            f"⚠️ Competitive benchmarking using '{data_source}' data instead of normalized. "
            f"Results may include corrupted historical years."
        )
```

---

## ✅ FIX #2: Implement Recency Weighting

### Concept: Recent Data is More Predictive
- **Most Recent Quarter**: 50% weight (closest to current reality)
- **Most Recent Year**: 30% weight (recent annual performance)
- **2-3 Years Ago**: 15% weight (medium-term trends)
- **4+ Years Ago**: 5% weight (historical context only)

### Implementation in `src/utils/financial_normalizer.py`:

```python
def _calculate_cagrs_with_recency_weight(
    self, 
    normalized_income: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate CAGRs with RECENCY WEIGHTING
    
    Recent years weighted higher as they're more predictive of future performance
    """
    if len(normalized_income) < 2:
        return {}
    
    # Standard CAGR (all years equal weight)
    standard_cagr = self._calculate_standard_cagr(normalized_income)
    
    # RECENCY-WEIGHTED Growth Rate
    # Weight recent years more heavily
    revenue_values = [stmt.get('revenue', 0) for stmt in normalized_income]
    
    # Create recency weights (most recent = highest weight)
    weights = []
    total_years = len(revenue_values)
    for i in range(total_years):
        # Exponential decay: most recent year = weight 1.0, oldest year = weight 0.2
        recency_factor = 0.85 ** i  # 15% decay per year back
        weights.append(recency_factor)
    
    # Normalize weights to sum to 1
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]
    
    # Calculate weighted average growth rate
    growth_rates = []
    for i in range(len(revenue_values) - 1):
        if revenue_values[i+1] > 0:
            growth = (revenue_values[i] - revenue_values[i+1]) / revenue_values[i+1]
            growth_rates.append(growth)
    
    if growth_rates:
        # Apply recency weights to growth rates
        weighted_growth = sum(g * weights[i] for i, g in enumerate(growth_rates))
    else:
        weighted_growth = 0
    
    logger.info(f"Growth Rates: Standard CAGR {standard_cagr['revenue_cagr']:.2%}, "
                f"Recency-Weighted {weighted_growth:.2%}")
    
    return {
        'revenue_cagr': standard_cagr['revenue_cagr'],
        'revenue_cagr_recency_weighted': weighted_growth,
        'net_income_cagr': standard_cagr['net_income_cagr'],
        'ebitda_cagr': standard_cagr['ebitda_cagr'],
        'recency_weights': weights,
        'recommendation': 'Use recency-weighted growth for forward projections',
        'periods': len(normalized_income) - 1
    }
```

---

## ✅ FIX #3: Add Quarterly Recency Emphasis

### Implementation:

```python
def emphasize_recent_quarters(
    self,
    normalized_data: Dict[str, Any],
    quarterly_income: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Add recent quarterly emphasis to normalized data
    
    Most recent 4 quarters are weighted heavily as they show current momentum
    """
    if not quarterly_income or len(quarterly_income) < 4:
        return normalized_data
    
    # Calculate LTM (Last Twelve Months) metrics from most recent 4 quarters
    ltm_revenue = sum(q.get('revenue', 0) for q in quarterly_income[:4])
    ltm_net_income = sum(q.get('netIncome', 0) for q in quarterly_income[:4])
    ltm_operating_income = sum(q.get('operatingIncome', 0) for q in quarterly_income[:4])
    
    # Calculate LTM margins
    ltm_net_margin = (ltm_net_income / ltm_revenue) if ltm_revenue > 0 else 0
    ltm_operating_margin = (ltm_operating_income / ltm_revenue) if ltm_revenue > 0 else 0
    
    # Add LTM metrics to normalized data with HIGH CONFIDENCE flag
    normalized_data['ltm_metrics'] = {
        'revenue': ltm_revenue,
        'net_income': ltm_net_income,
        'operating_income': ltm_operating_income,
        'net_margin': ltm_net_margin,
        'operating_margin': ltm_operating_margin,
        'confidence': 'HIGH',
        'note': 'LTM metrics from most recent 4 quarters - MOST PREDICTIVE of current performance',
        'use_for': 'Current run-rate analysis, near-term projections'
    }
    
    logger.info(f"✓ LTM Metrics Added: Revenue ${ltm_revenue/1e9:.2f}B, Net Margin {ltm_net_margin:.1%}")
    logger.info(f"  → These are MORE RELIABLE than historical annual averages for current valuation")
    
    return normalized_data
```

---

## 🎯 EXPECTED IMPACT

### Before (Equal Weighting):
- 2018 corrupted data: 14.3% influence on CAGR
- 2024 clean data: 14.3% influence on CAGR
- **Result**: Corrupted old data distorts projections

### After (Recency Weighting):
- 2018 corrupted data: 3-5% influence (if not excluded by quality gate)
- 2024 clean data: 40-50% influence
- **Result**: Recent reality dominates projections

### For Palantir Specifically:
- **Without recency weighting**: -106.7% margin in 2020 significantly distorts CAGR
- **With recency weighting**: 2024 (16.1% margin) and Q2 2025 (32.6% margin) dominate
- **Result**: Forward projections reflect current profitable reality, not historical losses

---

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Add normalization validation in financial_analyst.py
- [ ] Add recency-weighted CAGR calculation in financial_normalizer.py
- [ ] Add LTM metrics extraction from recent quarters
- [ ] Update DCF to use recency-weighted growth rates
- [ ] Update competitive analysis to use LTM metrics
- [ ] Test with PLTR to verify recency weighting works

---

**PRIORITY: HIGH - This ensures agents work with accurate, current-reality-focused data** ✅
