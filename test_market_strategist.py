"""
Unit test for Market Strategist Agent to verify it produces non-empty output
"""
import asyncio
import json
from datetime import datetime
from loguru import logger

from src.agents.market_strategist import MarketStrategistAgent
from src.core.state import DiligenceState


async def test_market_strategist_output():
    """
    Test that market_strategist agent produces non-empty output
    """
    logger.info("🔍 Testing Market Strategist Agent Output")
    logger.info("=" * 60)

    # Initialize state
    state = DiligenceState()
    state['target_company'] = 'Microsoft Corporation'
    state['target_ticker'] = 'MSFT'
    state['acquirer_company'] = 'Acquirer Inc.'
    state['deal_type'] = 'acquisition'
    state['deal_value'] = 75000000000  # $75B

    # Add some mock financial data to support news sentiment analysis
    state['financial_data'] = {
        'stock_news': [
            {'title': 'Microsoft reports strong quarterly earnings', 'text': 'Growth exceeds expectations', 'publishedDate': '2025-01-15', 'site': 'Bloomberg'},
            {'title': 'Tech giant expands AI capabilities', 'text': 'New products drive market share gains', 'publishedDate': '2025-01-12', 'site': 'Reuters'},
            {'title': 'Market analysis: Microsoft positioned for continued success', 'text': 'Strong competitive advantages maintained', 'publishedDate': '2025-01-10', 'site': 'WSJ'}
        ],
        'institutional_ownership': [
            {'investor': 'Vanguard', 'shares': 500000000, 'value': 150000000000, 'date': '2025-01-15'},
            {'investor': 'BlackRock', 'shares': 400000000, 'value': 120000000000, 'date': '2025-01-15'},
            {'investor': 'Fidelity', 'shares': 300000000, 'value': 90000000000, 'date': '2025-01-15'}
        ]
    }

    try:
        # Initialize and run agent
        agent = MarketStrategistAgent()
        logger.info("Running market_strategist agent...")

        result = await agent.run(state)

        # Check the result structure
        data = result.get('data', {})
        errors = result.get('errors', [])
        warnings = result.get('warnings', [])
        recommendations = result.get('recommendations', [])

        # Log results
        logger.info(f"Result structure: {list(result.keys())}")
        logger.info(f"Data keys: {list(data.keys()) if data else 'NO DATA'}")
        logger.info(f"Errors: {len(errors)} found")
        logger.info(f"Warnings: {len(warnings)} found")
        logger.info(f"Recommendations: {len(recommendations)} found")

        # Check if data is present
        has_data = bool(data and len(data) > 0)
        data_size = len(json.dumps(data)) if data else 0

        if has_data:
            logger.success("✅ SUCCESS: Market Strategist produced data!")
            logger.success(f"   Data size: {data_size} characters")
            logger.success(f"   Data keys: {list(data.keys())}")

            # Check specific expected data components
            expected_keys = [
                'competitive_analysis', 'market_position', 'industry_trends',
                'sentiment_analysis', 'strategic_recommendations'
            ]

            present_keys = [k for k in expected_keys if k in data and data[k]]
            missing_keys = [k for k in expected_keys if k not in data or not data[k]]

            logger.info(f"   Present keys: {present_keys}")
            if missing_keys:
                logger.warning(f"   Missing keys: {missing_keys}")

            # Verify output is not empty
            assert len(data) > 0, "Data dictionary is empty"
            assert 'competitive_analysis' in data, "Missing competitive_analysis"
            assert 'strategic_recommendations' in data, "Missing strategic_recommendations"

            # Check that recommendations is a list and not empty
            assert isinstance(recommendations, list), "Recommendations should be a list"
            assert len(recommendations) > 0, "No recommendations provided"

            logger.success("✅ ALL VALIDATION CHECKS PASSED")
            return True

        else:
            logger.error("❌ FAILURE: Market Strategist produced NO DATA")
            logger.error(f"   Errors: {errors}")
            logger.error(f"   Warnings: {warnings}")
            return False

    except Exception as e:
        logger.error(f"❌ EXCEPTION during test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_market_strategist_output())

    if success:
        logger.success("\n🎉 TEST PASSED: Market Strategist outputs non-empty data")
        exit(0)
    else:
        logger.error("\n💥 TEST FAILED: Market Strategist output validation failed")
        exit(1)
