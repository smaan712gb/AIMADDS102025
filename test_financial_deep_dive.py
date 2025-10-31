"""
Test script for Financial Deep Dive Agent
Validates all 5 modules with CRWD data
"""
import asyncio
from src.agents.financial_deep_dive import FinancialDeepDiveAgent
from src.agents.financial_analyst import FinancialAnalystAgent
from src.core.state import create_initial_state
from loguru import logger


async def test_financial_deep_dive():
    """Test Financial Deep Dive Agent with CRWD"""
    
    print("\n" + "="*80)
    print("FINANCIAL DEEP DIVE AGENT - TEST")
    print("="*80 + "\n")
    
    # Create deal state (same as production_crwd_analysis.py)
    state = create_initial_state(
        deal_id="TEST_DEEP_DIVE",
        target_company="CrowdStrike Holdings Inc.",
        target_ticker="CRWD",
        acquirer_company="Test Acquirer",
        investment_thesis="Testing Financial Deep Dive Agent",
        strategic_rationale="Test run for specialized financial analysis",
        deal_type="acquisition",
        currency="USD"
    )
    
    # Step 1: Run Financial Analyst first (Deep Dive depends on it)
    print("📊 Step 1: Running Financial Analyst (prerequisite)...")
    print("-" * 80)
    
    financial_analyst = FinancialAnalystAgent()
    fa_results = await financial_analyst.run(state)
    
    print(f"✅ Financial Analyst Complete")
    print(f"  - Financial Data Keys: {len(state.get('financial_data', {}).keys())}")
    print()
    
    # Step 2: Run Financial Deep Dive
    print("🔬 Step 2: Running Financial Deep Dive Agent...")
    print("-" * 80)
    
    deep_dive = FinancialDeepDiveAgent()
    dd_results = await deep_dive.run(state)
    
    # Validate results
    print("\n" + "="*80)
    print("RESULTS VALIDATION")
    print("="*80 + "\n")
    
    dd_data = dd_results.get('data', {})
    
    # Module 1: Working Capital
    print("MODULE 1: Working Capital Analysis")
    print("-" * 80)
    wc = dd_data.get('working_capital', {})
    if 'error' in wc:
        print(f"❌ ERROR: {wc['error']}")
    else:
        nwc_analysis = wc.get('nwc_analysis', {})
        ccc = nwc_analysis.get('cash_conversion_cycle', {})
        print(f"✅ Cash Conversion Cycle: {ccc.get('ccc_days', 0):.1f} days")
        print(f"  - Days Inventory Outstanding: {ccc.get('days_inventory_outstanding', 0):.1f}")
        print(f"  - Days Sales Outstanding: {ccc.get('days_sales_outstanding', 0):.1f}")
        print(f"  - Days Payables Outstanding: {ccc.get('days_payables_outstanding', 0):.1f}")
        print(f"✅ NWC Efficiency Score: {nwc_analysis.get('efficiency_score', 0):.1f}/100")
        print(f"✅ Volatility: {nwc_analysis.get('volatility_assessment', 'Unknown')}")
        print(f"✅ Interpretation: {wc.get('interpretation', 'N/A')}")
    print()
    
    # Module 2: CapEx & Depreciation
    print("MODULE 2: CapEx & Depreciation Analysis")
    print("-" * 80)
    capex = dd_data.get('capex_analysis', {})
    if 'error' in capex:
        print(f"❌ ERROR: {capex['error']}")
    else:
        capex_data = capex.get('capex_analysis', {})
        print(f"✅ Total CapEx: ${capex_data.get('total_capex', 0):,.0f}")
        print(f"✅ Maintenance CapEx: {capex_data.get('maintenance_capex_pct', 0):.1f}% of total")
        print(f"✅ Growth CapEx: {capex_data.get('growth_capex_pct', 0):.1f}% of total")
        print(f"✅ Avg CapEx/Revenue: {capex_data.get('avg_capex_pct_revenue', 0):.2f}%")
        print(f"✅ Asset Intensity: {capex_data.get('asset_intensity', 'Unknown')}")
        print(f"✅ Interpretation: {capex.get('interpretation', 'N/A')}")
    print()
    
    # Module 3: Customer Concentration
    print("MODULE 3: Customer Concentration Analysis")
    print("-" * 80)
    customer = dd_data.get('customer_concentration', {})
    if 'error' in customer:
        print(f"❌ ERROR: {customer['error']}")
    else:
        cust_data = customer.get('customer_analysis', {})
        geo = cust_data.get('geographic_breakdown', {})
        print(f"✅ Geographic Breakdown:")
        for region, pct in geo.items():
            print(f"  - {region.title()}: {pct}%")
        print(f"✅ Concentration Risk: {cust_data.get('concentration_risk', 'Unknown')}")
        print(f"✅ Interpretation: {customer.get('interpretation', 'N/A')}")
    print()
    
    # Module 4: Segment Analysis
    print("MODULE 4: Segment Analysis")
    print("-" * 80)
    segment = dd_data.get('segment_analysis', {})
    if 'error' in segment:
        print(f"❌ ERROR: {segment['error']}")
    else:
        seg_data = segment.get('segment_analysis', {})
        print(f"✅ Total Revenue: ${seg_data.get('total_revenue', 0):,.0f}")
        print(f"✅ Framework: {seg_data.get('note', 'N/A')}")
        print(f"✅ Interpretation: {segment.get('interpretation', 'N/A')}")
    print()
    
    # Module 5: Debt Schedule
    print("MODULE 5: Debt Schedule & Covenant Analysis")
    print("-" * 80)
    debt = dd_data.get('debt_schedule', {})
    if 'error' in debt:
        print(f"❌ ERROR: {debt['error']}")
    else:
        debt_data = debt.get('debt_analysis', {})
        print(f"✅ Total Debt: ${debt_data.get('total_debt', 0):,.0f}")
        print(f"✅ Debt/Equity: {debt_data.get('debt_to_equity', 0):.2f}x")
        print(f"✅ Refinancing Risk: {debt_data.get('refinancing_risk', 'Unknown')}")
        cov_data = debt_data.get('covenant_compliance', {}).get('interest_coverage', {})
        print(f"✅ Interest Coverage: {cov_data.get('actual', 0):.2f}x ({cov_data.get('headroom', 'Unknown')} headroom)")
        print(f"✅ Interpretation: {debt.get('interpretation', 'N/A')}")
    print()
    
    # Overall Insights
    print("OVERALL DEEP DIVE INSIGHTS")
    print("-" * 80)
    insights = dd_data.get('insights', {})
    if 'error' in insights:
        print(f"❌ ERROR: {insights['error']}")
    else:
        print("✅ Key Metrics:")
        metrics = insights.get('key_metrics', {})
        for metric, value in metrics.items():
            print(f"  - {metric}: {value}")
        print()
        print("✅ AI Summary:")
        print(insights.get('summary', 'N/A')[:500])
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    # Summary statistics
    print(f"\n📊 SUMMARY:")
    print(f"  - Errors: {len(dd_results.get('errors', []))}")
    print(f"  - Warnings: {len(dd_results.get('warnings', []))}")
    print(f"  - Recommendations: {len(dd_results.get('recommendations', []))}")
    print(f"\n✅ Financial Deep Dive Agent is operational!")
    
    return dd_results


if __name__ == "__main__":
    # Run test
    asyncio.run(test_financial_deep_dive())
