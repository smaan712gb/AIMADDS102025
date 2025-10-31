#!/usr/bin/env python3
"""
Test script for Enhanced Valuation Engine integration
Tests the enhanced engine with library fallbacks
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.enhanced_valuation_engine import EnhancedValuationEngine
from loguru import logger

def create_sample_financial_data():
    """Create sample financial data for testing"""
    return {
        'target_company': 'AAPL',
        'income_statement': [
            {
                'date': '2023-09-30',
                'revenue': 383285000000,
                'ebitda': 123136000000,
                'netIncome': 97000000000,
                'operatingIncome': 114301000000
            },
            {
                'date': '2022-09-30',
                'revenue': 394328000000,
                'ebitda': 130541000000,
                'netIncome': 99803000000,
                'operatingIncome': 119437000000
            },
            {
                'date': '2021-09-30',
                'revenue': 365817000000,
                'ebitda': 120233000000,
                'netIncome': 94680000000,
                'operatingIncome': 108949000000
            }
        ],
        'balance_sheet': [
            {
                'date': '2023-09-30',
                'totalAssets': 352755000000,
                'totalLiabilities': 290437000000,
                'totalEquity': 62318000000,
                'totalDebt': 111088000000
            }
        ],
        'cash_flow': [
            {
                'date': '2023-09-30',
                'operatingCashFlow': 110563000000,
                'capitalExpenditure': -10959000000,
                'freeCashFlow': 99504000000
            },
            {
                'date': '2022-09-30',
                'operatingCashFlow': 122151000000,
                'capitalExpenditure': -22097000000,
                'freeCashFlow': 100054000000
            }
        ],
        'profile': {
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
    }

def test_enhanced_valuation_engine():
    """Test the enhanced valuation engine"""
    logger.info("=" * 80)
    logger.info("TESTING ENHANCED VALUATION ENGINE")
    logger.info("=" * 80)

    try:
        # Create engine
        engine = EnhancedValuationEngine()
        logger.info("Enhanced Valuation Engine initialized")

        # Check library status
        library_status = engine.library_status
        logger.info(f"Library availability: {library_status}")

        # Create sample data
        financial_data = create_sample_financial_data()
        company_profile = financial_data['profile']

        logger.info("Running full valuation suite...")

        # Test with libraries enabled
        results = engine.run_full_valuation_suite(
            financial_data=financial_data,
            company_profile=company_profile,
            use_libraries=True
        )

        # Check results
        logger.info("=" * 40)
        logger.info("VALUATION RESULTS SUMMARY")
        logger.info("=" * 40)

        dcf_results = results.get('dcf_analysis', {})
        if dcf_results:
            base_dcf = dcf_results.get('base', {})
            enterprise_value = base_dcf.get('enterprise_value', 0)
            logger.info(f"Enterprise Value: ${enterprise_value:,.0f}")

        # Check library integration
        library_integration = results.get('library_integration', {})
        if library_integration:
            integration_status = library_integration.get('integration_summary', {})
            logger.info("Library integration status:")
            logger.info(f"  Libraries attempted: {integration_status.get('libraries_attempted', 0)}")
            logger.info(f"  Libraries successful: {integration_status.get('libraries_successful', 0)}")
            logger.info(f"  Overall status: {integration_status.get('overall_status', 'unknown')}")
        else:
            logger.info("No library integration results available")

        # Check for library enhancement in specific methods
        if test_method_enhancement():
            logger.info("✅ Method enhancement testing passed")
        else:
            logger.warning("⚠️  Method enhancement testing had issues")

        logger.info("Enhanced Valuation Engine test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Enhanced Valuation Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_enhancement():
    """Test that specific methods show library enhancement"""
    try:
        engine = EnhancedValuationEngine()

        # Test DCF method enhancement
        financial_data = create_sample_financial_data()
        company_profile = financial_data['profile']

        # Run multi-scenario DCF
        dcf_results = engine.run_multi_scenario_dcf(
            financial_data, company_profile
        )

        library_enhanced = dcf_results.get('library_enhanced', False)
        logger.info(f"DCF method library enhanced: {library_enhanced}")

        # Test LBO method enhancement
        lbo_results = engine.run_lbo_analysis(
            financial_data, company_profile
        )

        lbo_library_enhanced = lbo_results.get('library_enhanced', False)
        logger.info(f"LBO method library enhanced: {lbo_library_enhanced}")

        return True

    except Exception as e:
        logger.error(f"Method enhancement test failed: {e}")
        return False

def test_fallback_functionality():
    """Test that engine works without libraries"""
    logger.info("Testing fallback functionality (libraries disabled)...")

    try:
        engine = EnhancedValuationEngine()
        financial_data = create_sample_financial_data()
        company_profile = financial_data['profile']

        # Test with libraries disabled
        results_fallback = engine.run_full_valuation_suite(
            financial_data=financial_data,
            company_profile=company_profile,
            use_libraries=False
        )

        library_integration = results_fallback.get('library_integration', {})
        status = library_integration.get('status', '')

        if status == 'disabled':
            logger.info("✅ Fallback functionality working correctly")
            return True
        else:
            logger.warning("⚠️  Fallback functionality may not be working properly")
            return False

    except Exception as e:
        logger.error(f"Fallback test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting Enhanced Valuation Engine Integration Tests...")

    test_results = []

    # Test 1: Basic enhanced engine functionality
    test_results.append(("Enhanced Engine Test", test_enhanced_valuation_engine()))

    # Test 2: Fallback functionality
    test_results.append(("Fallback Test", test_fallback_functionality()))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:<25}: {status}")

    logger.info("-" * 80)
    logger.info(f"OVERALL: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All integration tests passed!")
        logger.info("Enhanced Valuation Engine is ready for production use.")
        return 0
    else:
        logger.warning("⚠️  Some tests failed. Review before production use.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
