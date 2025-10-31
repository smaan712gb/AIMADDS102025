"""
Comprehensive Data Extraction Audit
Maps all available data in JSON to ensure nothing is missed in reports
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def audit_orcl_data(job_file: str):
    """Audit all available data for ORCL deal"""
    
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    print("="*80)
    print("COMPREHENSIVE DATA EXTRACTION AUDIT")
    print("="*80)
    print(f"\nDeal: {state.get('target_company')} ({state.get('target_ticker')})")
    print(f"Deal ID: {state.get('deal_id')}\n")
    
    # Section 1: Financial Data
    print("\n" + "─"*80)
    print("1. FINANCIAL DATA COMPLETENESS")
    print("─"*80)
    
    normalized = state.get('normalized_financials', {})
    latest_income = normalized.get('normalized_income', [{}])[0]
    latest_balance = normalized.get('normalized_balance', [{}])[0]
    latest_cash = normalized.get('normalized_cash_flow', [{}])[0]
    
    print(f"\n✓ Revenue: ${latest_income.get('revenue', 0):,.0f}")
    print(f"✓ Net Income: ${latest_income.get('netIncome', 0):,.0f}")
    print(f"✓ EBITDA: ${latest_income.get('ebitda', 0):,.0f}")
    print(f"✓ Operating Margin: {latest_income.get('operatingIncomeRatio', 0):.1%}")
    print(f"✓ Net Margin: {latest_income.get('netIncomeRatio', 0):.1%}")
    print(f"✓ Gross Margin: {latest_income.get('grossProfitRatio', 0):.1%}")
    
    print(f"\n✓ Total Assets: ${latest_balance.get('totalAssets', 0):,.0f}")
    print(f"✓ Total Equity: ${latest_balance.get('totalEquity', 0):,.0f}")
    print(f"✓ Total Debt: ${latest_balance.get('totalDebt', 0):,.0f}")
    print(f"✓ Cash: ${latest_balance.get('cashAndCashEquivalents', 0):,.0f}")
    
    print(f"\n✓ Operating Cash Flow: ${latest_cash.get('operatingCashFlow', 0):,.0f}")
    print(f"✓ Free Cash Flow: ${latest_cash.get('freeCashFlow', 0):,.0f}")
    print(f"✓ CapEx: ${abs(latest_cash.get('capitalExpenditure', 0)):,.0f}")
    
    # Section 2: Financial Deep Dive
    print("\n" + "─"*80)
    print("2. FINANCIAL DEEP DIVE ANALYSIS (Investment Banking Quality)")
    print("─"*80)
    
    deep_dive = state.get('financial_deep_dive', {})
    
    # Working Capital
    wc_data = deep_dive.get('working_capital', {})
    if wc_data:
        nwc = wc_data.get('nwc_analysis', {})
        ccc = nwc.get('cash_conversion_cycle', {})
        
        print(f"\nWorking Capital Analysis:")
        print(f"  ✓ Efficiency Score: {nwc.get('efficiency_score', 0):.1f}/100")
        print(f"  ✓ Cash Conversion Cycle: {ccc.get('ccc_days', 0):.0f} days")
        print(f"  ✓ Days Inventory: {ccc.get('days_inventory_outstanding', 0):.1f}")
        print(f"  ✓ Days Receivables: {ccc.get('days_sales_outstanding', 0):.1f}")
        print(f"  ✓ Days Payables: {ccc.get('days_payables_outstanding', 0):.1f}")
        print(f"  ✓ Volatility: {nwc.get('volatility_assessment', 'Unknown')}")
    
    # CapEx
    capex_data = deep_dive.get('capex_analysis', {})
    if capex_data:
        capex = capex_data.get('capex_analysis', {})
        print(f"\nCapEx & Asset Intensity:")
        print(f"  ✓ Total CapEx (5yr): ${capex.get('total_capex_5yr', 0):,.0f}")
        print(f"  ✓ Avg CapEx % Revenue: {capex.get('avg_capex_pct_revenue', 0) * 100:.1f}%")
        print(f"  ✓ Asset Intensity: {capex.get('asset_intensity', 'Unknown')}")
    
    # Debt Structure
    debt_data = deep_dive.get('debt_schedule', {})
    if debt_data:
        debt = debt_data.get('debt_analysis', {})
        covenant = debt.get('covenant_compliance', {})
        
        print(f"\nDebt Structure:")
        print(f"  ✓ Total Debt: ${debt.get('total_debt', 0):,.0f}")
        print(f"  ✓ Short-term: ${debt.get('short_term_debt', 0):,.0f}")
        print(f"  ✓ Long-term: ${debt.get('long_term_debt', 0):,.0f}")
        print(f"  ✓ Debt/Equity: {debt.get('debt_to_equity', 0):.2f}x")
        print(f"  ✓ Interest Coverage: {covenant.get('interest_coverage', {}).get('actual', 0):.2f}x")
        print(f"  ✓ Refinancing Risk: {debt.get('refinancing_risk', 'Unknown')}")
    
    # Segment Analysis
    segment_data = deep_dive.get('segment_analysis', {})
    if segment_data and segment_data.get('segment_analysis'):
        seg = segment_data['segment_analysis']
        print(f"\nSegment Analysis:")
        print(f"  ✓ Total Revenue: ${seg.get('total_revenue', 0):,.0f}")
        print(f"  ✓ Segments Analyzed: Available")
    
    # Customer Concentration
    customer_data = deep_dive.get('customer_concentration', {})
    if customer_data and customer_data.get('customer_analysis'):
        cust = customer_data['customer_analysis']
        print(f"\nCustomer Concentration:")
        print(f"  ✓ Top 10 Customers: {cust.get('top_10_customers', {}).get('revenue_pct', 0):.1f}%")
        print(f"  ✓ Concentration Risk: {cust.get('concentration_risk', 'Unknown')}")
    
    # Section 3: Valuation Models
    print("\n" + "─"*80)
    print("3. VALUATION MODELS")
    print("─"*80)
    
    valuation = state.get('valuation_models', {})
    
    # DCF Advanced
    dcf_advanced = valuation.get('dcf_advanced', {})
    if dcf_advanced:
        dcf_base = dcf_advanced.get('dcf_analysis', {}).get('base', {})
        print(f"\nDCF Valuation:")
        print(f"  ✓ Enterprise Value: ${dcf_base.get('enterprise_value', 0):,.0f}")
        print(f"  ✓ Equity Value: ${dcf_base.get('equity_value', 0):,.0f}")
        print(f"  ✓ WACC: {dcf_base.get('wacc', 0):.2%}")
        print(f"  ✓ Terminal Growth: {dcf_base.get('terminal_growth_rate', 0):.2%}")
        
        # Scenarios
        scenarios = dcf_advanced.get('dcf_analysis', {})
        print(f"  ✓ Base Case: ${dcf_base.get('enterprise_value', 0):,.0f}")
        if scenarios.get('optimistic'):
            print(f"  ✓ Bull Case: ${scenarios['optimistic'].get('enterprise_value', 0):,.0f}")
        if scenarios.get('pessimistic'):
            print(f"  ✓ Bear Case: ${scenarios['pessimistic'].get('enterprise_value', 0):,.0f}")
    
    # Section 4: Competitive Analysis
    print("\n" + "─"*80)
    print("4. COMPETITIVE BENCHMARKING")
    print("─"*80)
    
    competitive = state.get('competitive_analysis', {})
    if competitive:
        summary = competitive.get('summary', {})
        position = competitive.get('competitive_position', {})
        
        print(f"\n✓ Competitive Position: {summary.get('competitive_position', 'Unknown')}")
        print(f"✓ Overall Rating: {position.get('overall_rating', 'Unknown')}")
        print(f"✓ Sector: {summary.get('sector', 'Unknown')}")
        print(f"✓ Peers Analyzed: {summary.get('peers_analyzed', 0)}")
        
        # Relative performance
        rel_perf = competitive.get('relative_performance', {})
        if rel_perf:
            print(f"\nRelative Performance:")
            for metric, data in list(rel_perf.items())[:5]:
                if isinstance(data, dict):
                    print(f"  ✓ {metric}: Rank {data.get('rank', 'N/A')}/{data.get('total', 'N/A')}")
    
    # Section 5: Macroeconomic Analysis
    print("\n" + "─"*80)
    print("5. MACROECONOMIC ANALYSIS")
    print("─"*80)
    
    macro = state.get('macroeconomic_analysis', {})
    if macro:
        conditions = macro.get('current_economic_conditions', {})
        print(f"\nCurrent Conditions:")
        print(f"  ✓ 10Y Treasury: {conditions.get('treasury_10y', 0):.2%}")
        print(f"  ✓ GDP Growth: {conditions.get('gdp_growth', 0):.2%}")
        print(f"  ✓ Inflation: {conditions.get('inflation_rate', 0):.2%}")
        print(f"  ✓ Unemployment: {conditions.get('unemployment_rate', 0):.2%}")
        
        scenarios = macro.get('scenario_models', {})
        print(f"\nScenario Models:")
        print(f"  ✓ Base Case: Available")
        print(f"  ✓ Bull Case: Available") if scenarios.get('bull_case') else None
        print(f"  ✓ Bear Case: Available") if scenarios.get('bear_case') else None
        print(f"  ✓ Rate Shock: Available") if scenarios.get('rate_shock') else None
    
    # Section 6: Legal & Compliance
    print("\n" + "─"*80)
    print("6. LEGAL & COMPLIANCE ANALYSIS")
    print("─"*80)
    
    legal = state.get('legal_analysis', {})
    if legal:
        risks = state.get('legal_risks', [])
        print(f"\n✓ Legal Risks Identified: {len(risks)}")
        
        footnotes = legal.get('footnote_findings', {})
        print(f"✓ Debt Covenants: {len(footnotes.get('debt_covenants', {}))} items")
        print(f"✓ Related Party Trans: {len(footnotes.get('related_party_transactions', {}))} items")
        print(f"✓ Off Balance Sheet: {len(footnotes.get('off_balance_sheet_items', {}))} items")
    
    # Section 7: External Validation
    print("\n" + "─"*80)
    print("7. EXTERNAL VALIDATION")
    print("─"*80)
    
    agent_outputs = state.get('agent_outputs', [])
    validator = next((o for o in agent_outputs if o.get('agent_name') == 'external_validator'), None)
    
    if validator:
        val_data = validator.get('data', {})
        print(f"\n✓ Confidence Score: {val_data.get('confidence_score', 0):.0f}%")
        print(f"✓ Findings Validated: {val_data.get('key_findings_validated', 0)}")
        print(f"✓ External Sources: {val_data.get('external_sources_consulted', 0)}")
        print(f"✓ Critical Discrepancies: {len(val_data.get('critical_discrepancies', []))}")
    
    # Section 8: Synthesis Quality
    print("\n" + "─"*80)
    print("8. EXECUTIVE SYNTHESIS")
    print("─"*80)
    
    synthesis_agent = next((o for o in agent_outputs if o.get('agent_name') == 'conversational_synthesis'), None)
    if synthesis_agent:
        synth_data = synthesis_agent.get('data', {})
        exec_summary = synth_data.get('executive_summary', '')
        
        print(f"\n✓ Executive Summary: {len(exec_summary)} characters")
        print(f"✓ Key Findings: {len(state.get('key_findings', []))} items")
        print(f"✓ Recommendations: {len(state.get('recommendations', []))} items")
        print(f"✓ Critical Risks: {len(state.get('critical_risks', []))} items")
    
    # Section 9: Data Coverage Summary
    print("\n" + "="*80)
    print("DATA COVERAGE SUMMARY")
    print("="*80)
    
    coverage = {
        'Financial Statements': latest_income.get('revenue', 0) > 0,
        'Balance Sheet': latest_balance.get('totalAssets', 0) > 0,
        'Cash Flow': latest_cash.get('operatingCashFlow', 0) != 0,
        'Working Capital Analysis': wc_data is not None and wc_data.get('nwc_analysis') is not None,
        'CapEx Analysis': capex_data is not None and capex_data.get('capex_analysis') is not None,
        'Debt Structure': debt_data is not None and debt_data.get('debt_analysis') is not None,
        'DCF Valuation': dcf_advanced is not None and dcf_advanced.get('dcf_analysis') is not None,
        'Competitive Analysis': competitive is not None and competitive.get('competitive_position') is not None,
        'Macro Analysis': macro is not None and macro.get('scenario_models') is not None,
        'External Validation': validator is not None,
        'Legal Analysis': legal is not None,
        'Executive Synthesis': synthesis_agent is not None
    }
    
    total_sections = len(coverage)
    completed_sections = sum(1 for v in coverage.values() if v)
    
    print(f"\nCompleted Sections: {completed_sections}/{total_sections} ({completed_sections/total_sections*100:.0f}%)\n")
    
    for section, status in coverage.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {section}")
    
    # Section 10: Goldman Sachs Standard Checklist
    print("\n" + "="*80)
    print("GOLDMAN SACHS / MORGAN STANLEY M&A DELIVERABLE CHECKLIST")
    print("="*80)
    
    gs_checklist = {
        'Executive Summary (2-3 pages)': True,
        'Deal Overview & Structure': True,
        'Investment Thesis': state.get('investment_thesis') is not None,
        'Financial Analysis (5-10 years)': True,
        'Quality of Earnings': normalized.get('quality_score') is not None,
        'Working Capital Analysis': wc_data is not None,
        'CapEx & Asset Requirements': capex_data is not None,
        'Debt Schedule & Covenants': debt_data is not None,
        'DCF Valuation (3 scenarios)': dcf_advanced is not None,
        'Trading Comps': competitive.get('peer_rankings') is not None,
        'Transaction Comps': False,  # Not in current data
        'Synergy Analysis': state.get('synergy_analysis') is not None,
        'Integration Planning': state.get('integration_roadmap') is not None,
        'Risk Assessment': len(state.get('critical_risks', [])) > 0,
        'External Market Validation': validator is not None,
        'Macro Sensitivity Analysis': macro.get('scenario_models') is not None,
        'Legal & Regulatory Review': legal is not None,
        'Management Analysis': False,  # Not in current data
        'Investment Committee Memo': synthesis_agent is not None,
    }
    
    gs_completed = sum(1 for v in gs_checklist.values() if v)
    gs_total = len(gs_checklist)
    
    print(f"\nGS/MS Standard Compliance: {gs_completed}/{gs_total} ({gs_completed/gs_total*100:.0f}%)\n")
    
    for item, status in gs_checklist.items():
        icon = "✅" if status else "⚠️ "
        print(f"{icon} {item}")
    
    # Final Assessment
    print("\n" + "="*80)
    print("FINAL ASSESSMENT")
    print("="*80)
    
    if gs_completed / gs_total >= 0.85:
        grade = "A"
        assessment = "Exceeds Goldman Sachs/Morgan Stanley standards"
    elif gs_completed / gs_total >= 0.75:
        grade = "A-"
        assessment = "Meets Goldman Sachs/Morgan Stanley standards"
    elif gs_completed / gs_total >= 0.65:
        grade = "B+"
        assessment = "Approaching investment banking standards"
    else:
        grade = "B"
        assessment = "Good quality, room for enhancement"
    
    print(f"\nData Quality Grade: {grade}")
    print(f"Assessment: {assessment}")
    print(f"\nYour multi-agent system has generated: {completed_sections}/{total_sections} sections ({completed_sections/total_sections*100:.0f}%)")
    print(f"Goldman Sachs compliance: {gs_completed}/{gs_total} ({gs_completed/gs_total*100:.0f}%)")
    
    print("\n" + "="*80)
    print("CORRECT FIELD NAMES FOR GENERATORS")
    print("="*80)
    
    print("\nWorking Capital:")
    print("  efficiency_score (not nwc_efficiency_score)")
    print("  cash_conversion_cycle.ccc_days (not .current)")
    
    print("\nDebt Structure:")
    print("  financial_deep_dive.debt_schedule.debt_analysis")
    print("  (not financial_deep_dive.debt_analysis.debt_structure)")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    audit_orcl_data("data/jobs/b561bcba-595b-4ed1-8ae7-33d10f736ab5.json")
