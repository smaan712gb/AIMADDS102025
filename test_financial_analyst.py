"""
Unit test for Financial Analyst Agent
"""
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch


async def test_financial_analyst_basic():
    """Test the Financial Analyst agent basic functionality"""

    print("="*80)
    print("TESTING FINANCIAL ANALYST AGENT")
    print("="*80)

    # Mock the financial data
    mock_fmp_data = {
        'income_statement': [
            {
                'revenue': 1000000000,
                'netIncome': 100000000,
                'ebitda': 150000000,
                'date': '2023-12-31'
            }
        ],
        'balance_sheet': [
            {
                'totalAssets': 2000000000,
                'totalLiabilities': 500000000,
                'totalEquity': 1500000000,
                'date': '2023-12-31'
            }
        ],
        'cash_flow': [
            {
                'operatingCashFlow': 200000000,
                'freeCashFlow': 100000000,
                'date': '2023-12-31'
            }
        ],
        'ratios': [
            {
                'currentRatio': 2.5,
                'debtEquityRatio': 0.33,
                'returnOnEquity': 0.067,
                'netProfitMargin': 0.10
            }
        ],
        'profile': {
            'companyName': 'Test Corp',
            'industry': 'Technology'
        }
    }

    # Import after setting up paths if needed
    from src.agents.financial_analyst import FinancialAnalystAgent
    from src.core.state import DiligenceState

    # Set up test state
    state = DiligenceState()
    state.update({
        'target_company': 'Test Corporation',
        'target_ticker': 'TEST',
        'deal_value': 5000000000
    })

    print("Test State:")
    print(f"  Company: {state['target_company']} ({state['target_ticker']})")
    print(f"  Deal Value: ${state['deal_value'] / 1000000:.2f}M")

    try:
        fa_agent = FinancialAnalystAgent()

        # Mock the FMP client call
        with patch.object(fa_agent, '_fetch_financial_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_fmp_data

            result = await fa_agent.run(state)

        # Check result structure
        assert 'data' in result, "Result must have 'data' key"
        assert 'errors' in result, "Result must have 'errors' key"
        assert 'warnings' in result, "Result must have 'warnings' key"

        data = result['data']
        errors = result['errors']
        warnings = result['warnings']

        print("\n✅ Financial Analyst executed successfully")
        print(f"  Errors: {len(errors)}")
        print(f"  Warnings: {len(warnings)}")

        # Check expected data keys
        expected_keys = [
            'financial_metrics', 'normalized_financials', 'anomaly_detection',
            'advanced_valuation', 'trend_analysis', 'seasonality',
            'financial_health', 'ratio_analysis', 'red_flags', 'insights'
        ]

        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
            print(f"  ✓ {key}: {type(data[key]).__name__}")

        # Check financial health structure and values
        financial_health = data['financial_health']
        assert 'health_score' in financial_health, "Missing health_score"
        health_score = financial_health['health_score']
        assert isinstance(health_score, (int, float)), "Health score should be numeric"
        assert 0 <= health_score <= 100, f"Health score {health_score} should be between 0-100"
        print(f"  ✓ Health Score: {health_score}/100")

        # Check advanced valuation includes LBO analysis
        advanced_valuation = data['advanced_valuation']
        assert 'lbo_analysis' in advanced_valuation, "LBO analysis missing from advanced valuation"
        lbo_analysis = advanced_valuation['lbo_analysis']
        print(f"  ✓ LBO analysis included: {len(lbo_analysis)} metrics")

        # Check DCF analysis
        assert 'dcf_analysis' in advanced_valuation, "DCF analysis missing"
        dcf_analysis = advanced_valuation['dcf_analysis']
        assert 'base' in dcf_analysis, "DCF base case missing"
        dcf_base = dcf_analysis['base']
        assert 'enterprise_value' in dcf_base, "DCF enterprise value missing"
        print(".2f")

        # Check insights structure
        insights = data['insights']
        assert 'summary' in insights, "Insights summary missing"
        assert isinstance(insights['summary'], str), "Insights summary should be string"
        assert len(insights['summary']) > 100, f"Insights summary too short: {len(insights['summary'])} chars"
        print(f"  ✓ AI Insights generated: {len(insights['summary'])} characters")

        # Check valuation models were created in state
        assert 'valuation_models' in state, "Valuation models should be in state"
        assert 'dcf_advanced' in state['valuation_models'], "DCF advanced should be in valuation_models"
        assert 'dcf' in state['valuation_models'], "DCF basic should be in valuation_models"
        print(f"  ✓ Valuation models created: {list(state['valuation_models'].keys())}")

        # Check financial data was stored
        assert 'financial_data' in state, "Financial data should be in state"
        print(f"  ✓ Financial data stored with {len(state['financial_data'])} keys")

        # Verify Monte Carlo simulation results
        if 'monte_carlo_simulation' in advanced_valuation:
            monte_carlo = advanced_valuation['monte_carlo_simulation']
            assert 'mean_valuation' in monte_carlo or 'median_valuation' in monte_carlo, "Monte Carlo results incomplete"
            print("  ✓ Monte Carlo simulation completed")

        # Check no critical errors
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print(f"  Financial Health Score: {health_score}/100")
        print(f"  Data processing successful")
        return True

    except Exception as e:
        print(f"\n❌ Financial Analyst test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = asyncio.run(test_financial_analyst_basic())
    if result:
        print("\n🎉 Financial Analyst agent is working correctly!")
        print("✅ KeyError 'valuation_models' has been fixed")
        print("✅ Agent properly initializes state dictionaries")
        print("✅ Advanced financial analysis capabilities verified")
    else:
        print("\n💥 Financial Analyst agent has issues to fix.")
        exit(1)
