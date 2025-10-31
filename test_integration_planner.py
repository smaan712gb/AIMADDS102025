"""
Unit test for Integration Planner Agent to verify it produces non-empty output
"""
import asyncio
import json
from datetime import datetime
from loguru import logger

from src.agents.integration_planner import IntegrationPlannerAgent
from src.core.state import DiligenceState


async def test_integration_planner_output():
    """
    Test that integration_planner agent produces non-empty output
    """
    logger.info("🔍 Testing Integration Planner Agent Output")
    logger.info("=" * 60)

    # Initialize state
    state = DiligenceState()
    state['target_company'] = 'Microsoft Corporation'
    state['target_ticker'] = 'MSFT'
    state['acquirer_company'] = 'Acquirer Inc.'
    state['deal_type'] = 'acquisition'
    state['deal_value'] = 75000000000  # $75B

    try:
        # Initialize and run agent
        agent = IntegrationPlannerAgent()
        logger.info("Running integration_planner agent...")

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
            logger.success("✅ SUCCESS: Integration Planner produced data!")
            logger.success(f"   Data size: {data_size} characters")
            logger.success(f"   Data keys: {list(data.keys())}")

            # Check specific expected data components
            expected_keys = [
                'synergies', 'roadmap', 'org_design',
                'culture_assessment', 'critical_success_factors'
            ]

            present_keys = [k for k in expected_keys if k in data and data[k]]
            missing_keys = [k for k in expected_keys if k not in data or not data[k]]

            logger.info(f"   Present keys: {present_keys}")
            if missing_keys:
                logger.warning(f"   Missing keys: {missing_keys}")

            # Verify output is not empty
            assert len(data) > 0, "Data dictionary is empty"
            assert 'synergies' in data, "Missing synergies"
            assert 'roadmap' in data, "Missing roadmap"
            assert 'critical_success_factors' in data, "Missing critical_success_factors"

            # Check that recommendations is a list and not empty
            assert isinstance(recommendations, list), "Recommendations should be a list"
            assert len(recommendations) > 0, "No recommendations provided"

            logger.success("✅ ALL VALIDATION CHECKS PASSED")
            return True

        else:
            logger.error("❌ FAILURE: Integration Planner produced NO DATA")
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
    success = asyncio.run(test_integration_planner_output())

    if success:
        logger.success("\n🎉 TEST PASSED: Integration Planner outputs non-empty data")
        exit(0)
    else:
        logger.error("\n💥 TEST FAILED: Integration Planner output validation failed")
        exit(1)
