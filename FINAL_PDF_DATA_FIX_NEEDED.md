# Final PDF Data Extraction Fixes - Based on ACTUAL Data Structure

## Problem Summary
PDF sections are looking in wrong places or synthesis fields are empty. Individual agents HAVE the data.

## Data Structure Reality (from inspect_synthesis_structure.py)

### ✅ What EXISTS in Synthesis
- `market_analysis → competitive_landscape` → {market_share, competitive_position, key_competitors}
- `market_analysis → swot_analysis` → {strengths, weaknesses, opportunities, threats}
- `detailed_financials → dcf_outputs` → Has 9 keys
- `detailed_financials → quality_score` → int value

### ❌ What's EMPTY in Synthesis
- `risk_macro → macro_environment` → {} (EMPTY dict)
- `risk_macro → key_risks` → [] (EMPTY list)
- `risk_macro → economic_outlook` → {} (EMPTY)
- `detailed_financials → external_validation` → {} (EMPTY)

### ✅ What EXISTS in Individual Agents
- `competitive_benchmarking` → 8 keys including competitive_position, market_share_analysis
- `macroeconomic_analyst` → 7 keys including current_economic_conditions, scenario_models
- `financial_deep_dive` → 8 keys including **working_capital** (not working_capital_analysis!)
- `external_validator` → 11 keys including validation_type, confidence_score

## Exact Fixes Needed

### 1. Fix financial_sections.py - Working Capital
**Current Code** (WRONG):
```python
wc_analysis = detailed_financials.get('working_capital_analysis', {})  # Doesn't exist!
```

**Should Be** (from agent fallback):
```python
# Try synthesis first
wc_efficiency = detailed_financials.get('working_capital_efficiency_score', 0)

# If not in synthesis, get from financial_deep_dive agent
if not wc_efficiency and state:
    fd_agent = get_agent('financial_deep_dive', state)
    if fd_agent:
        wc_data = fd_agent.get('working_capital', {})  # ← RIGHT key name!
        wc_efficiency = wc_data.get('efficiency_score', 0)
```

### 2. Fix risk_sections.py - Competitive Section
**Current Code** (checks synthesis but doesn't extract properly):
```python
competitive_landscape = market_analysis.get('competitive_landscape', {})
if not competitive_landscape and state:
    # Fallback to agent
```

**Issue**: competitive_landscape EXISTS but may have limited data. Need to enhance.

**Fix**:
```python
# Get from synthesis
comp_landscape = market_analysis.get('competitive_landscape', {})
market_share = comp_landscape.get('market_share', 'N/A')
position = comp_landscape.get('competitive_position', 'N/A')
competitors = comp_landscape.get('key_competitors', [])

# If synthesis has empty/placeholder values, use agent data
if not competitors or position == 'N/A':
    comp_agent = get_agent('competitive_benchmarking', state)
    if comp_agent:
        position = comp_agent.get('competitive_position', position)
        competitors = comp_agent.get('peer_rankings', [])  # Has real data
        market_share = comp_agent.get('market_share_analysis', {}).get('target_share', market_share)
```

### 3. Fix risk_sections.py - Macro Section  
**Current Code** (looks in synthesis which is EMPTY):
```python
macro_environment = risk_macro.get('macro_environment', {})  # Returns {} - EMPTY!
```

**Fix** (use agent data directly since synthesis is empty):
```python
# Synthesis is empty, go straight to agent
macro_agent = get_agent('macroeconomic_analyst', state)
if macro_agent:
    current_conditions = macro_agent.get('current_economic_conditions', {})
    scenario_models = macro_agent.get('scenario_models', {})
    
    # Extract indicators
    gdp_growth = current_conditions.get('gdp_growth_rate', 0)
    inflation = current_conditions.get('inflation_rate', 0)
    # Build macro_environment from agent data
```

### 4. Fix risk_sections.py - Risk Assessment
**Current Code** (looks in synthesis which is EMPTY):
```python
key_risks = risk_macro.get('key_risks', [])  # Returns [] - EMPTY!
```

**Fix** (synthesis empty, but we have risk_assessor agent):
```python
# Synthesis key_risks is empty, check risk_assessor agent
# Note: diagnostic showed risk_assessor has NO DATA
# So show appropriate message
if not key_risks:
    content.append(Paragraph(
        "Risk assessment synthesized from individual agent findings. " +
        "Detailed risk breakdown available in agent-specific sections.",
        self.styles['Body']
    ))
```

### 5. Fix SWOT Corrupted Data
**Problem**: SWOT opportunities has:
```
"0,overall_risk:Low,recession:economic_changes:gdp_growth:change:-2"
```

**Fix**: Already have JSON cleaning in executive_sections.py - verify it's applied to SWOT in risk_sections.py too.

## Implementation Priority

1. **HIGH**: Fix `create_financial_deep_dive()` to use agent's `working_capital` key
2. **HIGH**: Fix `create_macro_section()` to use macroeconomic_analyst agent directly
3. **MEDIUM**: Enhance `create_competitive_section()` to merge synthesis + agent data
4. **MEDIUM**: Fix `create_risk_assessment()` to handle empty key_risks gracefully

## Testing After Fixes

Generate PDF and verify:
- [ ] Financial Deep Dive shows working capital metrics
- [ ] Competitive section shows real market share, position, competitors
- [ ] Macro section shows economic indicators (from agent)
- [ ] Risk assessment shows appropriate message (since synthesis empty)
- [ ] No corrupted JSON in SWOT

## Key Lesson

**Synthesis agent synthesized SOME data but not ALL fields**. PDF sections must:
1. Try synthesis first (single source of truth)
2. Fall back to individual agents when synthesis fields empty
3. Merge data intelligently when both have partial information
