"""
Comprehensive Agent Data Flow Audit
Checks that ALL quantitative agents receive correct, complete data
Focus: Normalized data where needed, original data where appropriate
"""
import asyncio
import json
from datetime import datetime
from loguru import logger


async def mock_audit_agent_data():
    """
    Mock audit - documents what SHOULD be checked
    Since we can't run full orchestrator without triggering analysis
    """
    logger.info("=" * 100)
    logger.info("AGENT DATA REQUIREMENTS SPECIFICATION")
    logger.info("=" * 100)
    
    agent_data_requirements = {
        'financial_analyst': {
            'required_data': ['normalized_financials', 'raw_financial_data'],
            'critical_arrays': ['income_statement', 'balance_sheet', 'cash_flow'],
            'must_be_normalized': True,
            'reason': 'Valuation models require clean data without corrupted years'
        },
        'financial_deep_dive': {
            'required_data': ['normalized_financials', 'financial_metrics'],
            'critical_arrays': ['income_statement'],
            'must_be_normalized': True,
            'reason': 'Operational efficiency analysis needs normalized margins'
        },
        'competitive_benchmarking': {
            'required_data': ['normalized_financials OR raw_financial_data'],
            'critical_arrays': ['income_statement'],
            'must_be_normalized': False,
            'reason': 'Can use latest year ratios from either source, but normalized preferred'
        },
        'macroeconomic_analyst': {
            'required_data': ['raw_financial_data', 'analyst_estimates'],
            'critical_arrays': ['income_statement'],
            'must_be_normalized': False,
            'reason': 'Needs original data for economic correlation analysis'
        },
        'risk_assessment': {
            'required_data': ['normalized_financials', 'all_agent_outputs'],
            'critical_arrays': ['income_statement'],
            'must_be_normalized': True,
            'reason': 'Risk scoring needs clean normalized metrics'
        },
        'tax_structuring': {
            'required_data': ['normalized_financials', 'balance_sheet'],
            'critical_arrays': ['balance_sheet'],
            'must_be_normalized': False,
            'reason': 'Tax basis uses original book values, not normalized'
        },
        'deal_structuring': {
            'required_data': ['normalized_financials', 'valuation_models'],
            'critical_arrays': ['N/A'],
            'must_be_normalized': False,
            'reason': 'Uses DCF outputs, not direct financial data'
        },
        'integration_planner': {
            'required_data': ['normalized_financials', 'competitive_analysis'],
            'critical_arrays': ['income_statement'],
            'must_be_normalized': True,
            'reason': 'Synergy calculations need normalized baselines'
        }
    }
    
    logger.info("\n📋 AGENT DATA REQUIREMENTS:")
    for agent, reqs in agent_data_requirements.items():
        logger.info(f"\n{agent.upper()}:")
        logger.info(f"  Required: {reqs['required_data']}")
        logger.info(f"  Must use normalized: {reqs['must_be_normalized']}")
        logger.info(f"  Reason: {reqs['reason']}")
    
    logger.info("\n" + "=" * 100)
    logger.info("RECOMMENDATIONS FOR COMPREHENSIVE AUDIT")
    logger.info("=" * 100)
    
    logger.info("""
To run comprehensive agent audit:

1. Run full M&A analysis on PLTR
2. After completion, check logs for each agent:
   - Does log show "using normalized_financials" or "using raw data"?
   - Does log show "X income statements" count?
   - Does log show any "falling back" warnings?

3. Check state after analysis:
   - Does state['normalized_financials']['income_statement'] have data?
   - Does each agent_output have the expected data keys?
   - Are there any empty arrays that should be populated?

4. Key Success Criteria:
   ✅ financial_analyst: Uses normalized, has 6 clean years (2020 excluded)
   ✅ competitive_benchmarking: Uses normalized OR raw, has valid margins
   ✅ All agents: No "falling back" or "arrays are EMPTY" warnings
   ✅ Recency weighting: Recent years weighted 40-50% in CAGR calculations
    """)
    
    return agent_data_requirements


if __name__ == "__main__":
    results = asyncio.run(mock_audit_agent_data())
    
    # Save spec
    with open('agent_data_requirements_spec.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("\n✅ Agent data requirements saved to agent_data_requirements_spec.json")
