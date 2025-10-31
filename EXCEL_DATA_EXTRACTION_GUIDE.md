# Excel Data Extraction Guide

## Problem Summary
Excel report tabs are empty because generator uses placeholder data instead of extracting from `agent_outputs` array.

## Agent Data Structure

Each agent output in `state['agent_outputs']` has this structure:
```json
{
  "agent_name": "financial_analyst",
  "status": "completed",
  "data": {
    "normalized_financials": {...},
    "anomaly_detection": {...},
    "advanced_valuation": {...}
  }
}
```

## Data Mapping for Each Tab

### 1. Normalization Ledger
**Source**: `financial_analyst` agent → `data.normalized_financials.adjustments[]`
**Current Issue**: Array is empty (no adjustments needed)
**Fix**: Show message "No adjustments required" or display normalized vs reported comparison

### 2. Anomaly Log
**Source**: `financial_analyst` agent → `data.anomaly_detection.anomalies_detected[]`
**Current Issue**: Using hardcoded placeholder anomalies
**Fix**: Extract from `anomalies_detected` array

### 3. Working Capital Analysis
**Source**: `financial_deep_dive` agent → `data.working_capital.nwc_analysis`
**Data Available**:
- `historical_trend[]` - NWC by year
- `cash_conversion_cycle` - Days metrics
- `efficiency_score` - Score out of 100

### 4. CapEx Analysis
**Source**: `financial_deep_dive` agent → `data.capex_analysis.capex_analysis`
**Data Available**:
- `total_capex`, `maintenance_capex`, `growth_capex`
- `capex_to_revenue_trend[]` - Historical analysis
- `asset_intensity` - Rating

### 5. Debt Schedule
**Source**: `financial_deep_dive` agent → `data.debt_schedule.debt_analysis`
**Data Available**:
- `maturity_schedule[]` - Debt by year
- `covenant_compliance` - Covenant status
- `total_debt`, `short_term_debt`, `long_term_debt`

### 6. Legal Risk Matrix
**Source**: `legal_counsel` agent → `data.legal_risks[]`
**Data Available**: Risk objects with category, severity, description

### 7. Risk Assessment
**Source**: `risk_assessment` agent → `data`
**Data Available**:
- `risk_matrix` - Categorized risks
- `risk_scores` - Overall scoring
- `risk_scenarios` - Scenario valuations

### 8. Tax Structuring
**Source**: `tax_structuring` agent → `data`
**Data Available**:
- `tax_position` - Current tax status
- `structure_comparison` - Asset/Stock/Merger comparison
- `structure_recommendations` - Optimal structure

### 9. Competitive Benchmarking
**Source**: `competitive_benchmarking` agent → `data`
**Data Available**:
- `relative_performance` - Metrics vs peers
- `peer_rankings` - Rank by metric
- `competitive_position` - Overall rating

### 10. Integration Roadmap
**Source**: `integration_planner` agent → `data.integration_roadmap`
**Data Available**: Day 1/30/100/365 milestones

### 11. External Validation
**Source**: `external_validator` agent → `data`
**Data Available**:
- `validation_results[]` - Each finding validation
- `confidence_score` - Overall confidence
- `critical_discrepancies[]` - Major issues

## Implementation Pattern

```python
def _create_tab(self, wb: Workbook, state: dict):
    # Extract agent data
    agent_output = next(
        (o for o in state.get('agent_outputs', []) 
         if o.get('agent_name') == 'agent_name'),
        None
    )
    
    if not agent_output or 'data' not in agent_output:
        # Handle missing data
        ws['A1'] = "Data not available"
        return
    
    # Extract specific data
    agent_data = agent_output['data']
    specific_data = agent_data.get('key', {})
    
    # Populate tab with real data
    for item in specific_data:
        # Write to cells
        pass
