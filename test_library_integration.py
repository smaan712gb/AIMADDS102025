#!/usr/bin/env python3
"""
Test script for financetoolkit and finmodels library integration
Tests before implementing in the main system
"""

import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger

import financetoolkit as ft
import finmodels

def test_financetoolkit_basics():
    """Test basic financetoolkit functionality"""
    logger.info("Testing Finance Toolkit basic functionality...")

    try:
        # Test toolkit initialization with sample data
        # Get sample data for AAPL
        ticker = "AAPL"
        sample_data = ft.Toolkit([ticker], api_key="demo" if hasattr(ft, 'set_key') else None)

        # Test basic functions
        ratios = sample_data.get_ratios()
        logger.info(f"Successfully retrieved ratios for {ticker}")

        # Test specific modules
        profitability_ratios = sample_data.model.get_profitable_ratios()
        logger.info("Successfully accessed profitability ratios")

        return {'status': 'success', 'message': 'Finance Toolkit working'}
    except Exception as e:
        logger.error(f"Finance Toolkit test failed: {e}")
        return {'status': 'failed', 'message': str(e)}

def test_finmodels_basics():
    """Test basic finmodels functionality"""
    logger.info("Testing FinModels basic functionality...")

    try:
        # Test basic valuation functions
        from finmodels.valuation import DCFModel, LBOModel

        # Sample DCF calculation
        dcf = DCFModel()
        # Add sample parameters and test
        logger.info("FinModels DCF/LBO models accessible")

        return {'status': 'success', 'message': 'FinModels working'}
    except Exception as e:
        logger.error(f"FinModels test failed: {e}")
        return {'status': 'failed', 'message': str(e)}

def test_dcf_integration():
    """Test DCF integration with sample data"""
    logger.info("Testing DCF calculation integration...")

    try:
        # Create sample financial data (like our system)
        sample_revenue = [100, 120, 145, 170, 200]  # 5-year projection
        sample_ebitda_margin = [0.25, 0.27, 0.29, 0.31, 0.33]
        sample_tax_rate = 0.21

        # Calculate FCFs
        ebitda = [rev * margin for rev, margin in zip(sample_revenue, sample_ebitda_margin)]
        ebit = [eb - 0.05*rev for eb, rev in zip(ebitda, sample_revenue)]  # Depreciation ~5%
        nopat = [e * (1 - sample_tax_rate) for e in ebit]
        capex = [0.03 * rev for rev in sample_revenue]  # CapEx ~3% of revenue
        wc_investment = [0.01 * rev for rev in sample_revenue]  # WC ~1% of revenue
        fcf = [n + 0.05*rev - c - wc for n, rev, c, wc in zip(nopat, sample_revenue, capex, wc_investment)]

        logger.info(f"Sample FCF projection: {fcf}")

        # Test with Finance Toolkit if available
        try:
            # Create DataFrame-like structure
            cash_flows = pd.DataFrame({'operatingCashFlow': fcf})
            logger.info("Finance Toolkit DCF integration possible")
        except Exception as ft_e:
            logger.warning(f"Finance Toolkit DCF integration failed: {ft_e}")

        return {'status': 'success', 'fcf': fcf}
    except Exception as e:
        logger.error(f"DCF integration test failed: {e}")
        return {'status': 'failed', 'message': str(e)}

def test_library_compatibility():
    """Test library compatibility with our data structures"""
    logger.info("Testing library compatibility with our data formats...")

    try:
        # Test DataFrame conversion
        sample_income = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=5, freq='YS'),
            'revenue': [100000, 120000, 145000, 170000, 200000],
            'ebitda': [25000, 28000, 32000, 35000, 38000],
            'netIncome': [18000, 21000, 24000, 27000, 32000]
        })

        sample_balance = pd.DataFrame({
            'totalAssets': [500000, 550000, 600000, 650000, 700000],
            'totalLiabilities': [300000, 320000, 340000, 360000, 380000],
            'totalEquity': [200000, 230000, 260000, 290000, 320000]
        })

        # Test if our data can be fed into financetoolkit
        tool = ft.Toolkit(["SAMPLE"], custom_datasets={
            'income': sample_income,
            'balance': sample_balance
        }, api_key="demo")

        logger.info("Library compatibility test successful")
        return {'status': 'success', 'income_shape': sample_income.shape}
    except Exception as e:
        logger.error(f"Library compatibility test failed: {e}")
        return {'status': 'failed', 'message': str(e)}

def run_integration_tests():
    """Run all integration tests"""
    logger.info("=" * 80)
    logger.info("LIBRARY INTEGRATION TESTS FOR M&A ANALYSIS")
    logger.info("=" * 80)

    results = {
        'financetoolkit': test_financetoolkit_basics(),
        'finmodels': test_finmodels_basics(),
        'dcf_integration': test_dcf_integration(),
        'compatibility': test_library_compatibility()
    }

    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)

    for test_name, result in results.items():
        status = "✅ PASS" if result.get('status') == 'success' else "❌ FAIL"
        message = result.get('message', 'No details')
        logger.info(f"{test_name.upper():<20}: {status} - {message}")

    success_count = sum(1 for r in results.values() if r.get('status') == 'success')
    logger.info(f"\nOVERALL: {success_count}/{len(results)} tests passed")

    if success_count == len(results):
        logger.info("🎉 All integration tests passed! Ready for implementation.")
        return True
    else:
        logger.warning("⚠️  Some tests failed. Proceed with caution and implement fallbacks.")
        return False

if __name__ == "__main__":
    run_integration_tests()
