# PPTX Report Placeholder Analysis & Board-Level Enhancement Plan

## Executive Summary

This document identifies all **placeholders and hardcoded values** in the PowerPoint presentation that need to be replaced with **real data from multi-agent analysis**, and recommends **additional board-level insights** that should be added.

---

## SECTION 1: IDENTIFIED PLACEHOLDERS & DATA MAPPING

### 🎯 Slide 1: "The Answer" Slide

**Current Issues:**
- Uses basic valuation range without probability weighting
- Missing confidence intervals from Monte Carlo simulation
- No risk-adjusted valuation display

**Required Real Data Mapping:**
```python
# FROM: financial_analyst -> advanced_valuation
base_ev = dcf_analysis['base']['enterprise_value']
optimistic_ev = dcf_analysis['optimistic']['enterprise_value']  
pessimistic_ev = dcf_analysis['pessimistic']['enterprise_value']
probability_weighted = dcf_analysis['probability_weighted']['enterprise_value']

# ADD: Monte Carlo confidence intervals
monte_carlo = advanced_valuation['monte_carlo_simulation']
percentile_5th = monte_carlo['percentiles']['5th']
percentile_95th = monte_carlo['percentiles']['95th']
```

**Board-Level Enhancement:**
- Display probability-weighted valuation prominently
- Show 90% confidence interval ($X.XB - $Y.YB at 90% confidence)
- Add valuation recommendation from synthesis agent

---

### 🔍 Slide 3: "Glass Box Summary" Slide

**CRITICAL PLACEHOLDERS (Hardcoded):**
```
❌ "[8] critical anomalies detected" 
❌ "$45M in hidden legal costs"
❌ EBITDA adjustment percentages
❌ "11 specialist agents vs 3-5 human analysts" (hardcoded text)
```

**Required Real Data Mapping:**
```python
# FROM: financial_analyst -> anomaly_detection
anomaly_count = len(anomaly_detection['anomalies_detected']) if anomaly_detection['anomalies_detected'] else 0
risk_level = anomaly_detection['risk_level']  # "High", "Medium", "Low"

# FROM: financial_analyst -> normalized_financials
adjustments = normalized_financials['adjustments']
total_ebitda_impact = sum([adj['ebitda_impact'] for adj in adjustments])
quality_score = normalized_financials['quality_score']
red_flags_count = len(normalized_financials['red_flags'])

# FROM: legal_counsel (when available)
# legal_costs = legal_counsel['change_of_control_costs']
# contract_count = legal_counsel['contracts_reviewed']

# FROM: metadata
agent_count = len(agent_outputs)  # Actual agent count
```

**Board-Level Enhancement:**
- Add **Financial Health Score**: `financial_health['health_score']` (e.g., "73/100 - GOOD")
- Add **Quality Score**: Show earnings quality rating
- Show **specific normalization items** with dollar amounts:
  - One-time charges removed
  - Non-recurring items adjusted
  - Stock-based compensation treatment

---

### 📊 Slide 6: Financial Highlights

**Missing Critical Metrics:**
```python
# FROM: ratio_analysis
profitability_ratios = ratio_analysis['profitability']  # ROE, ROA, ROIC, margins
liquidity_ratios = ratio_analysis['liquidity']  # Current ratio, quick ratio
leverage_ratios = ratio_analysis['leverage']  # Debt/Equity, Interest coverage
efficiency_ratios = ratio_analysis['efficiency']  # Asset turnover, inventory turns

# FROM: trend_analysis
cagr_metrics = trend_analysis['cagr_metrics']
revenue_cagr = cagr_metrics['revenue_cagr']
ebitda_cagr = cagr_metrics['ebitda_cagr']
```

**Board-Level Enhancement:**
- Add 3-5 year CAGR trends for key metrics
- Show trend direction indicators (↑ improving, ↓ declining, → stable)
- Add peer comparison benchmarks from competitive_benchmarking

---

### 🏦 Slide 7-9: Deep Dive Slides

**Working Capital Slide - Required Data:**
```python
# FROM: financial_deep_dive -> working_capital
nwc_analysis = working_capital['nwc_analysis']
# Current NWC, Historical trend, Days working capital
# Interpretation and recommendations

# CURRENT ISSUE: Slide may not exist or lacks detail
```

**CapEx Slide - Required Data:**
```python
# FROM: financial_deep_dive -> capex_analysis
capex_trend = capex_analysis['capex_analysis']
capex_intensity = capex_analysis['interpretation']  # "16.6% of revenue"
# Historical average vs current
# Growth vs maintenance CapEx breakdown
```

**Debt Slide - Required Data:**
```python
# FROM: financial_deep_dive -> debt_schedule
debt_maturity_schedule = debt_schedule['debt_analysis']
interest_coverage = debt_schedule['interpretation']
covenant_analysis = debt_schedule['recommendations']

# ADD: From financial_analyst
debt_to_equity = financial_metrics['debt_to_equity']
current_ratio = financial_metrics['current_ratio']
```

**Board-Level Enhancement:**
- Add **debt refinancing roadmap**
- Show **covenant cushion analysis**
- Include **interest rate sensitivity**

---

### 💰 Slide 10: Valuation Slide

**CRITICAL ENHANCEMENT NEEDED:**

**Current Issues:**
- Only shows DCF analysis
- Missing comparable companies valuation
- Missing precedent transactions
- No valuation bridge/waterfall

**Required Real Data Mapping:**
```python
# FROM: advanced_valuation -> valuation_summary
valuation_methods = {
    'dcf_base': dcf_analysis['base']['enterprise_value'],
    'dcf_optimistic': dcf_analysis['optimistic']['enterprise_value'],
    'dcf_pessimistic': dcf_analysis['pessimistic']['enterprise_value'],
    'comparable_companies': comparable_companies['implied_valuation'],
    'precedent_transactions': precedent_transactions['implied_valuation'],
    'lbo_analysis': lbo_analysis['exit_assumptions']['exit_equity_value']
}

# Recommendation
recommendation = valuation_summary['recommendation']
rationale = valuation_summary['rationale']
```

**Board-Level Enhancement:**
- Create **valuation bridge slide**:
  - Start: Market Cap
  - Add: Synergies
  - Add: Control premium
  - Subtract: Integration costs
  - Result: Fair value range
- Add **sensitivity tornado chart** (top 5 value drivers)
- Show **transaction multiples** vs comparable deals

---

### 🚨 Slide 11: Critical Anomaly Slide

**CRITICAL PLACEHOLDERS (Hardcoded):**
```
❌ "3.5 standard deviations faster than revenue"
❌ "2% revenue forecast reduced"
❌ "$500M risk reserve"
❌ Inventory vs revenue divergence example
```

**Required Real Data Mapping:**
```python
# FROM: financial_analyst -> anomaly_detection
if anomaly_detection['anomalies_detected']:
    for anomaly in anomaly_detection['anomalies_detected']:
        anomaly_type = anomaly['type']
        severity = anomaly['severity']
        statistical_measure = anomaly['z_score'] or anomaly['deviation']
        description = anomaly['description']
        impact = anomaly['financial_impact']

# FROM: financial_deep_dive -> insights
anomaly_insights = insights['summary']  # Contains specific findings
```

**Board-Level Enhancement:**
- Show **ALL detected anomalies** (not just inventory example)
- Add **anomaly impact matrix**: Likelihood vs Impact
- Include **statistical confidence levels**
- Show **how anomalies affected valuation model**

---

### ⚖️ Slide 12: Market Position Slide

**Missing Competitive Intelligence:**
```python
# FROM: competitive_benchmarking
competitive_position = competitive_benchmarking['competitive_position']
overall_rating = competitive_position['overall_rating']  # e.g., "Strong Competitor"
strengths = competitive_position['strengths']  # List of competitive advantages
weaknesses = competitive_position['weaknesses']  # List of vulnerabilities

# FROM: relative_performance
revenue_growth_vs_peers = relative_performance['revenue_growth']
# "12% vs peer avg 8% (+4pp)"
margin_comparison = relative_performance['gross_margin']
roe_comparison = relative_performance['roe']

# FROM: peer_rankings
revenue_growth_rank = peer_rankings['revenue_growth']['rank']  # e.g., "2 of 5"
margin_rank = peer_rankings['net_margin']['rank']
```

**Board-Level Enhancement:**
- Add **market share trend** (if available)
- Show **competitive positioning map** (market share vs growth rate)
- Include **M&A activity context** from `ma_activity_context`
- Add **strategic insights** for positioning

---

### ⚖️ Slide 13: Legal "Smoking Gun" Slide

**CRITICAL PLACEHOLDERS (Hardcoded):**
```
❌ "$45M Hidden Cost" - completely hardcoded
❌ "1,247 Contracts scanned" - hardcoded
❌ "3 Change of Control clauses" - hardcoded
```

**DATA AVAILABILITY ISSUE:**
The `legal_counsel` agent shows "Status: completed, Has Data: ❌ NO"

**Recommended Approach:**
1. **IF** legal_counsel data becomes available, map to:
```python
# FROM: legal_counsel (future)
contracts_analyzed = legal_counsel['contracts_analyzed']
change_of_control_clauses = legal_counsel['change_of_control']['count']
total_cost = legal_counsel['change_of_control']['estimated_cost']
specific_agreements = legal_counsel['change_of_control']['agreements']
```

2. **CURRENTLY**: Either:
   - Remove this slide entirely (no data)
   - OR Replace with **"Legal Due Diligence Required"** placeholder slide
   - OR Use general legal risk factors from risk_assessment agent

---

### 🎯 Slide 14-15: Risk Slides

**CRITICAL DATA AVAILABLE BUT UNDERUTILIZED:**

**Required Real Data Mapping:**
```python
# FROM: risk_assessment -> risk_scores
overall_risk_score = risk_scores['overall_risk_score']  # 65
risk_rating = risk_scores['risk_rating']  # "HIGH RISK"
critical_risks = risk_scores['critical_risks']  # 0
high_risks = risk_scores['high_risks']  # 2
medium_risks = risk_scores['medium_risks']  # 7
total_risks = risk_scores['total_risks']  # 9

# FROM: risk_assessment -> risk_factors
for risk in risk_factors:
    category = risk['category']  # financial, operational, market, legal, etc.
    severity = risk['severity']  # critical, high, medium, low
    description = risk['description']
    likelihood = risk['likelihood']  # high, medium, low
    impact = risk['impact']
    
# FROM: risk_assessment -> risk_matrix
high_likelihood_high_impact = risk_matrix['high_likelihood_high_impact']  # List
# ... other matrix cells

# FROM: risk_assessment -> risk_scenarios
best_case = risk_scenarios['best_case']
base_case = risk_scenarios['base_case']
worst_case = risk_scenarios['worst_case']

# FROM: risk_assessment -> mitigation_strategies
mitigations = mitigation_strategies  # List of 10 strategies
```

**Board-Level Enhancement:**
- Create **risk heat map** visual (likelihood × impact)
- Show **top 5 risks** with specific mitigation plans
- Add **risk-adjusted valuation scenarios**:
  - Best case (low risk materialization)
  - Base case (expected risk)
  - Worst case (high risk materialization)
- Include **quantified risk impact** on valuation

---

### ✅ Slide 16: External Validation Slide

**CRITICAL PLACEHOLDERS (Hardcoded):**
```
❌ "Our $303B Valuation vs Street $285B Consensus"
❌ "+$18B (+6.3%) delta"
❌ "69.4% confidence"
❌ "10% WACC vs Street 9.5%"
```

**Required Real Data Mapping:**
```python
# FROM: external_validator
confidence_score = external_validator['confidence_score']  # 22.2% (ACTUAL!)
requires_reanalysis = external_validator['requires_reanalysis']  # True
critical_discrepancies = external_validator['critical_discrepancies']  # 3
validated_findings = external_validator['validated_findings']  # 1

# FROM: validation_results
for result in validation_results:
    status = result['status']  # "critical_discrepancy" or "validated"
    severity = result['severity']  # "critical", "moderate", "low"
    alignment_score = result['alignment_score']  # 0%, 10%, 100%
    finding_type = result.get('finding_type')  # "valuation", "working_capital", etc.
    comparison_summary = result['comparison_summary']

# FROM: adjustment_plan
adjustments_needed = adjustment_plan['adjustments']
agents_to_rerun = adjustment_plan['agents_to_rerun']
```

**CRITICAL BOARD CONCERN:**
The actual confidence score is **22.2%**, not 69.4%! This indicates **major discrepancies** that require board attention.

**Board-Level Enhancement:**
- Show **ACTUAL validation confidence**: 22.2%
- Highlight **3 critical discrepancies**:
  1. Valuation methodology (0% alignment)
  2. Working capital analysis (0% alignment)
  3. Debt structure (10% alignment)
- Add **"Requires Further Analysis"** banner
- Show **reanalysis plan** and timeline
- Be transparent about validation concerns

---

### 💡 Slide 17: Synergies Slide (if included)

**MISSING DATA SOURCE:**
No synergy analysis agent output available.

**Recommended Approach:**
1. **IF** including synergies, need:
   - Revenue synergies (cross-sell, upsell)
   - Cost synergies (overhead reduction, procurement)
   - Synergy realization timeline
   - Implementation costs
   - Risk factors

2. **CURRENTLY**: Either remove or use placeholder values with clear "TBD" markers

---

### 🔄 Slide 18: Integration Slide (if included)

**MISSING DATA SOURCE:**
Integration Planner Agent shows "Has Data: ❌ NO"

**Recommended Approach:**
1. Remove slide OR
2. Show high-level integration framework template
3. Mark as "Phase 2 Deliverable"

---

### 🎯 Slide 19: Recommendation Slide

**Required Real Data Mapping:**
```python
# FROM: synthesis_reporting (when available) OR metadata
final_recommendation = metadata['final_synthesis']['deal_recommendation']
recommendation_text = final_recommendation['recommendation']  # "PROCEED WITH CAUTION"
rationale = final_recommendation['rationale']
conditions = final_recommendation.get('conditions', [])
key_considerations = final_recommendation.get('key_considerations', [])

# FROM: insights across agents
financial_summary = financial_analyst_insights['summary']
competitive_summary = competitive_benchmarking['summary']
risk_summary = risk_assessment['overall_assessment']
```

**Board-Level Enhancement:**
- Clear **GO / NO-GO / CONDITIONAL** recommendation
- Top 3-5 **deal-breaker risks** to monitor
- **Deal conditions** that must be met
- **Price negotiation guidance** based on findings

---

### 📋 Slide 20: Due Diligence Questions Slide

**EXCELLENT CONCEPT - NEEDS REAL DATA:**

**Current Issues:**
- All questions are hardcoded examples
- Not derived from actual agent findings

**Required Real Data Generation:**
```python
# Generate from actual findings:
questions = []

# From anomaly detection findings
if anomaly_detection['anomalies_detected']:
    for anomaly in anomaly_detection['anomalies_detected']:
        questions.append({
            'agent': 'Financial Analyst',
            'topic': anomaly['type'],
            'question': f"Please explain {anomaly['description']}"
        })

# From risk assessment
high_risks = [r for r in risk_factors if r['severity'] in ['critical', 'high']]
for risk in high_risks:
    questions.append({
        'agent': 'Risk Assessment',
        'topic': risk['category'],
        'question': f"Mitigation plan for: {risk['description']}"
    })

# From validation discrepancies
for discrepancy in critical_discrepancies:
    questions.append({
        'agent': 'External Validator',
        'topic': discrepancy.get('finding_type'),
        'question': f"Resolve {discrepancy['alignment_score']} alignment: {discrepancy['comparison_summary']}"
    })

# From financial deep dive
if customer_concentration['customer_analysis']:
    questions.append({
        'agent': 'Deep Dive',
        'topic': 'Customer Concentration',
        'question': customer_concentration['recommendations']
    })
```

---

## SECTION 2: MISSING BOARD-LEVEL INSIGHTS

### 📊 NEW SLIDE RECOMMENDATIONS

#### **New Slide A: Tax Structure Optimization**
```python
# FROM: tax_structuring
current_structure = tax_position['current_structure']
recommended_structure = optimal_structure  # "Asset Purchase" or "Stock Purchase"
estimated_tax_impact = estimated_tax_impact  # Dollar amount
structure_comparison = structure_comparison  # Asset vs Stock comparison

# Board Value:
- Shows tax efficiency opportunities
- Quantifies structure choice impact ($X million difference)
- Provides implementation roadmap
```

**Content:**
- Asset Purchase vs Stock Purchase comparison table
- Tax benefit of step-up basis: $X million
- NOL utilization potential: $Y million
- Recommended structure with rationale
- International tax considerations (if applicable)

#### **New Slide B: Macroeconomic Sensitivity**
```python
# FROM: macroeconomic_analyst
current_conditions = current_economic_conditions
scenario_models = scenario_models  # bull, bear, base, rate_shock
correlation_analysis = correlation_analysis  # How economic factors affect target

# Board Value:
- Shows deal resilience to economic changes
- Quantifies interest rate risk
- Demonstrates scenario planning
```

**Content:**
- Current economic backdrop (rates, GDP, inflation)
- Target's sensitivity to macro factors
- Valuation under different scenarios:
  - Bull case (favorable conditions): $X.XB
  - Base case (current conditions): $Y.YB
  - Bear case (recession): $Z.ZB
  - Rate shock (+200bps): $W.WB

#### **New Slide C: LBO Analysis (Private Equity Perspective)**
```python
# FROM: advanced_valuation -> lbo_analysis
entry_assumptions = lbo_analysis['entry_assumptions']
returns_analysis = lbo_analysis['returns_analysis']
irr = returns_analysis['irr_percent']  # e.g., "18.5%"
multiple_of_money = returns_analysis['multiple_of_money']  # e.g., "2.3x"
debt_paydown = returns_analysis['debt_paydown_percent']  # e.g., "45%"

# Board Value:
- Alternative valuation perspective
- Shows deal returns potential
- Useful for financing discussions
```

**Content:**
- Entry valuation and leverage assumptions
- Projected IRR: X.X%
- Multiple of money: X.Xx
- Sensitivity analysis: IRR at different exit multiples
- Debt paydown capabilities

#### **New Slide D: Earnings Quality & Sustainability**
```python
# FROM: advanced_valuation -> earnings_quality
quality_metrics = earnings_quality
# Accrual quality, cash conversion, earnings stability

# Board Value:
- Assesses reliability of financial performance
- Identifies earnings manipulation risks
- Guides due diligence focus areas
```

**Content:**
- Cash conversion ratio
- Accrual quality score
- Earnings stability (volatility)
- One-time items as % of earnings
- Quality rating: High/Medium/Low

#### **New Slide E: Strategic Rationale Deep Dive**
```python
# FROM: competitive_benchmarking
strategic_insights = strategic_insights
ma_activity = ma_activity_context
competitive_strengths = competitive_position['strengths']

# Board Value:
- Answers "Why this deal, why now?"
- Shows strategic fit
- Addresses alternatives considered
```

**Content:**
- Strategic fit with acquirer
- Competitive advantages being acquired
- Market consolidation rationale
- Build vs buy analysis
- Alternative targets considered (if any)

---

## SECTION 3: DATA QUALITY CONCERNS

### 🚨 Critical Issues Requiring Board Attention

#### **1. External Validation Confidence: 22.2%**
**Issue**: The external validator found **3 critical discrepancies** with 0-10% alignment on key findings.

**Specific Discrepancies:**
1. **Valuation Methodology** (0% alignment)
2. **Working Capital Analysis** (0% alignment)  
3. **Debt Structure** (10% alignment)

**Board Implication:**
- Analysis requires revalidation before proceeding
- Presents major credibility risk
- Must address before board approval

**Recommendation:**
- Add slide: "Validation Gaps & Reanalysis Plan"
- Show specific discrepancies
- Provide timeline to resolution
- DON'T hide this - transparency builds trust

#### **2. Missing Agent Outputs**
Several agents completed but have no output data:
- Legal Counsel Agent (NO DATA)
- Integration Planner Agent (NO DATA)
- Market Strategist Agent (NO DATA)
- Synthesis & Reporting Agent (NO DATA)

**Board Implication:**
- Incomplete analysis
- Cannot make fully informed decision
- Legal risks not quantified

**Recommendation:**
- Clearly mark analysis as "Preliminary"
- List pending work streams
- Provide completion timeline

#### **3. High Risk Score (65 - HIGH RISK)**
**Issue**: Risk assessment agent flagged **9 total risks**:
- 0 critical risks
- 2 high risks
- 7 medium risks
- Overall rating: HIGH RISK

**Board Implication:**
- Deal has meaningful execution risks
- Requires robust mitigation plan
- May affect pricing/structure

**Recommendation:**
- Don't downplay risk level
- Show specific mitigation strategies (10 identified)
- Quantify risk-adjusted valuation

---

## SECTION 4: IMPLEMENTATION PRIORITIES

### 🎯 Phase 1: Fix Critical Placeholders (IMMEDIATE)

**Priority 1A: Remove ALL Hardcoded Values**
```python
# Replace these immediately:
✅ Anomaly count: Use actual anomaly_detection data
✅ Risk score: Use actual 65/100 HIGH RISK
✅ Validation confidence: Use actual 22.2% (not fake 69.4%)
✅ Agent count: Use actual len(agent_outputs)
✅ EBITDA adjustments: Use actual normalized_financials
```

**Priority 1B: Fix Validation Slide**
- Show REAL confidence score (22.2%)
- Display 3 critical discrepancies
- Add "Reanalysis Required" banner
- Remove fake Street consensus comparison

**Priority 1C: Fix Anomaly Slide**
- Use ACTUAL anomalies from detection results
- Remove inventory example if not real finding
- Show real statistical measures
- Map to actual valuation impacts

### 🎯 Phase 2: Add Missing Board Insights (HIGH PRIORITY)

**Add These Slides:**
1. Tax Structure Optimization slide
2. Macroeconomic Sensitivity slide
3. LBO Analysis slide
4. Earnings Quality slide
5. Strategic Rationale deep dive

**Enhance These Slides:**
1. Valuation slide - add comps & precedents
2. Risk slides - add heat map and quantification
3. Financial highlights - add peer benchmarks
4. Competitive position - add rankings & M&A context

### 🎯 Phase 3: Dynamic Question Generation (MEDIUM PRIORITY)

**Auto-Generate Due Diligence Questions From:**
- Anomalies detected
- High/critical risks identified
- Validation discrepancies
- Financial deep dive findings
- Competitive weaknesses

---

## SECTION 5: CODE CHANGES REQUIRED

### File: `src/outputs/revolutionary_ppt_generator.py`

#### **Change 1: Glass Box Summary Slide**
```python
def _add_glass_box_summary_slide(self, prs: Presentation, state: DiligenceState):
    # BEFORE (hardcoded):
    # f"  • [8] critical anomalies detected by statistical analysis"
    
    # AFTER (real data):
    anomaly_data = state.get('anomaly_detection', {})
    anomaly_count = len(anomaly_data.get('anomalies_detected', [])) if anomaly_data.get('anomalies_detected') else 0
    risk_level = anomaly_data.get('risk_level', 'Unknown')
    
    f"  • {anomaly_count} anomalies detected ({risk_level} risk level)"
    
    # Similar fixes for:
    # - Legal costs (from legal_counsel when available, else "TBD")
    # - EBITDA adjustments (from normalized_financials)
    # - Agent count (from actual agent_outputs)
```

#### **Change 2: Validation Slide**
```python
def _add_validation_confidence_slide(self, prs: Presentation, state: DiligenceState):
    # Get REAL validation data
    agent_outputs = state.get('agent_outputs', [])
    validator = next((o for o in agent_outputs if o.get('agent_name') == 'external_validator'), None)
    
    if validator:
        val_data = validator.get('data', {})
        confidence = val_data.get('confidence_score', 0)  # Use REAL score
        critical_discrep = val_data.get('critical_discrepancies', [])
        requires_reanalysis = val_data.get('requires_reanalysis', False)
        
        # Show actual confidence, not fake
        f"External Validator Confidence: {confidence:.1%}"  # Shows 22.2%
        
        # MUST show discrepancies if critical
        if critical_discrep:
            # Add warning about validation issues
            # List specific discrepancies
            # Show reanalysis plan
```

#### **Change 3: Critical Anomaly Slide**
```python
def _add_critical_anomaly_slide(self, prs: Presentation, state: DiligenceState):
    # Get REAL anomalies
    anomaly_data = state.get('anomaly_detection', {})
    anomalies = anomaly_data.get('anomalies_detected', [])
    
    if not anomalies:
        # Either skip slide or show "No Critical Anomalies Detected"
        return
    
    # Show ACTUAL first/most critical anomaly
    critical_anomaly = anomalies[0]
    anomaly_type = critical_anomaly.get('type', 'Unknown')
    severity = critical_anomaly.get('severity', 'Unknown')
    statistical_measure = critical_anomaly.get('z_score') or critical_anomaly.get('deviation', 'N/A')
    description = critical_anomaly.get('description', '')
    impact = critical_anomaly.get('financial_impact', 'Under assessment')
```

#### **Change 4: Legal Slide**
```python
def _add_legal_smoking_gun_slide(self, prs: Presentation, state: DiligenceState):
    # Check if legal data available
    agent_outputs = state.get('agent_outputs', [])
    legal_agent = next((o for o in agent_outputs if o.get('agent_name') == 'legal_counsel'), None)
    
    if not legal_agent or not legal_agent.get('data'):
        # Skip this slide or replace with "Legal DD Required" placeholder
        return self._add_legal_dd_required_slide(prs, state)
    
    # Otherwise use real data
    legal_data = legal_agent.get('data', {})
    # Map to actual fields
```

#### **Change 5: Risk Slides**
```python
def _add_risk_slides(self, prs: Presentation, state: DiligenceState):
    # Get REAL risk data
    risk_data = state.get('risk_assessment', {})
    if not risk_data:
        agent_outputs = state.get('agent_outputs', [])
        risk_agent = next((o for o in agent_outputs if o.get('agent_name') == 'risk_assessment'), None)
        if risk_agent:
            risk_data = risk_agent.get('data', {})
    
    risk_scores = risk_data.get('risk_scores', {})
    overall_score = risk_scores.get('overall_risk_score', 0)  # 65
    risk_rating = risk_scores.get('risk_rating', 'Unknown')  # "HIGH RISK"
    
    # Create slides showing:
    # 1. Overall risk profile with REAL score
    # 2. Risk matrix heat map
    # 3. Top risks with mitigations
```

#### **Change 6: Add New Slides**
```python
# Add these new methods:
def _add_tax_structure_slide(self, prs: Presentation, state: DiligenceState):
    """New slide: Tax structure optimization"""
    # FROM tax_structuring agent
    pass

def _add_macro_sensitivity_slide(self, prs: Presentation, state: DiligenceState):
    """New slide: Macroeconomic scenarios"""
    # FROM macroeconomic_analyst agent
    pass

def _add_lbo_analysis_slide(self, prs: Presentation, state: DiligenceState):
    """New slide: LBO perspective"""
    # FROM advanced_valuation -> lbo_analysis
    pass
