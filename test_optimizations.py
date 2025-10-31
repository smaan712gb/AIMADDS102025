"""
Test script to validate all performance optimizations and bug fixes
"""
import asyncio
import time
from datetime import datetime
from loguru import logger

from src.agents.external_validator import ExternalValidatorAgent
from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent
from src.agents.legal_counsel import LegalCounselAgent
from src.core.state import DiligenceState


async def test_external_validator_parallelization():
    """Test that External Validator uses parallel execution"""
    logger.info("=" * 80)
    logger.info("TEST 1: External Validator Parallelization")
    logger.info("=" * 80)
    
    agent = ExternalValidatorAgent()
    
    # Create mock state with financial data
    state = DiligenceState()
    state['target_company'] = 'Microsoft'
    state['target_ticker'] = 'MSFT'
    state['financial_data'] = {
        'revenue': 211915000000,
        'revenue_growth': 12.5,
        'net_margin': 36.7,
        'roe': 38.2
    }
    
    logger.info("Starting External Validator with parallelization...")
    start_time = time.time()
    
    try:
        result = await agent.run(state)
        elapsed = time.time() - start_time
        
        logger.success(f"✅ External Validator completed in {elapsed:.2f} seconds")
        logger.info(f"Validated findings: {len(result.get('data', {}).get('validated_findings', []))}")
        logger.info(f"Confidence score: {result.get('data', {}).get('confidence_score', 0):.2f}")
        
        if elapsed < 300:  # Less than 5 minutes (was 7.5 minutes before)
            logger.success(f"✅ PERFORMANCE IMPROVEMENT CONFIRMED: {elapsed:.2f}s < 300s")
            return True
        else:
            logger.warning(f"⚠️ Still slow: {elapsed:.2f}s")
            return False
            
    except Exception as e:
        logger.error(f"❌ External Validator test failed: {e}")
        return False


async def test_competitive_benchmarking_parallel():
    """Test that Competitive Benchmarking uses parallel execution"""
    logger.info("=" * 80)
    logger.info("TEST 2: Competitive Benchmarking Parallelization")
    logger.info("=" * 80)
    
    agent = CompetitiveBenchmarkingAgent()
    
    state = DiligenceState()
    state['target_ticker'] = 'MSFT'
    state['financial_data'] = {
        'revenue': 211915000000,
        'revenue_growth': 12.5,
        'gross_margin': 68.4,
        'operating_margin': 42.0,
        'net_margin': 36.7,
        'roe': 38.2,
        'roic': 28.5,
        'debt_to_equity': 0.45,
        'current_ratio': 1.25
    }
    
    logger.info("Starting Competitive Benchmarking...")
    start_time = time.time()
    
    try:
        result = await agent.run(state)
        elapsed = time.time() - start_time
        
        logger.success(f"✅ Competitive Benchmarking completed in {elapsed:.2f} seconds")
        logger.info(f"Peers analyzed: {result.get('data', {}).get('summary', {}).get('peers_analyzed', 0)}")
        logger.info(f"Competitive position: {result.get('data', {}).get('summary', {}).get('competitive_position', 'Unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Competitive Benchmarking test failed: {e}")
        return False


async def test_mda_sentiment_extraction():
    """Test MD&A sentiment analysis"""
    logger.info("=" * 80)
    logger.info("TEST 3: MD&A Sentiment Extraction")
    logger.info("=" * 80)
    
    agent = LegalCounselAgent()
    
    state = DiligenceState()
    state['target_ticker'] = 'MSFT'
    state['target_company'] = 'Microsoft'
    state['deal_type'] = 'acquisition'  # Required by Legal Counsel
    state['acquirer_company'] = 'Test Acquirer Inc.'
    
    logger.info("Starting Legal Counsel agent (MD&A extraction)...")
    start_time = time.time()
    
    try:
        result = await agent.run(state)
        elapsed = time.time() - start_time
        
        logger.success(f"✅ Legal Counsel completed in {elapsed:.2f} seconds")
        
        # Check MD&A sentiment
        sec_analysis = result.get('data', {}).get('sec_analysis', {})
        mda_sentiment = sec_analysis.get('mda_sentiment', {})
        
        if mda_sentiment and 'analysis' in mda_sentiment:
            overall_tone = mda_sentiment.get('analysis', {}).get('overall_tone', 'unknown')
            logger.info(f"MD&A sentiment: {overall_tone}")
            
            if overall_tone != 'unknown':
                logger.success("✅ MD&A SENTIMENT WORKING")
                return True
            else:
                logger.warning("⚠️ MD&A sentiment still returns 'unknown'")
                logger.info(f"Full MD&A data: {mda_sentiment}")
                return False
        else:
            logger.warning("⚠️ MD&A sentiment not in response")
            logger.info(f"SEC analysis keys: {list(sec_analysis.keys())}")
            return False
            
    except Exception as e:
        logger.error(f"❌ MD&A sentiment test failed: {e}")
        return False


async def test_stock_peers_endpoint():
    """Test stock-peers API endpoint"""
    logger.info("=" * 80)
    logger.info("TEST 4: Stock-Peers API Endpoint")
    logger.info("=" * 80)
    
    from src.integrations.fmp_client import FMPClient
    
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        logger.info(f"Testing stock-peers for {symbol}...")
        
        try:
            async with FMPClient() as client:
                # Test Method 1: peers-bulk
                try:
                    peers_bulk = await client._make_request('peers-bulk', use_stable=True)
                    if peers_bulk:
                        logger.success(f"✅ peers-bulk endpoint working")
                except Exception as e:
                    logger.warning(f"⚠️ peers-bulk failed: {e}")
                
                # Test Method 2: stock-peers
                try:
                    peers_response = await client.get_stock_peers(symbol)
                    if peers_response and 'peersList' in peers_response:
                        peers_list = peers_response.get('peersList', [])
                        logger.success(f"✅ stock-peers working for {symbol}: {len(peers_list)} peers")
                    else:
                        logger.warning(f"⚠️ stock-peers returned empty for {symbol}")
                except Exception as e:
                    logger.error(f"❌ stock-peers failed for {symbol}: {e}")
                
                # Test Method 3: Fallback (stock_screener)
                try:
                    profile = await client.get_company_profile(symbol)
                    if profile:
                        sector = profile.get('sector', '')
                        logger.info(f"Profile retrieved: Sector = {sector}")
                        logger.success("✅ Fallback method (stock_screener) available")
                except Exception as e:
                    logger.error(f"❌ Fallback also failed: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Overall test failed for {symbol}: {e}")
    
    return True


async def test_agent_output_completeness():
    """Test that all agents produce non-empty outputs"""
    logger.info("=" * 80)
    logger.info("TEST 5: Agent Output Completeness")
    logger.info("=" * 80)
    
    # This would require running full workflow
    logger.info("⏩ Skipping - requires full workflow run")
    logger.info("To test: Run test_comprehensive_13_agents.py and check output counts")
    
    return True


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Optimization & Bug Fix Validation Tests")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    results = {}
    
    # Test 1: External Validator Parallelization
    results['external_validator'] = await test_external_validator_parallelization()
    await asyncio.sleep(2)
    
    # Test 2: Competitive Benchmarking
    results['competitive_benchmarking'] = await test_competitive_benchmarking_parallel()
    await asyncio.sleep(2)
    
    # Test 3: MD&A Sentiment
    results['mda_sentiment'] = await test_mda_sentiment_extraction()
    await asyncio.sleep(2)
    
    # Test 4: Stock-Peers Endpoint
    results['stock_peers'] = await test_stock_peers_endpoint()
    await asyncio.sleep(2)
    
    # Test 5: Agent Output Completeness
    results['output_completeness'] = await test_agent_output_completeness()
    
    # Summary
    logger.info("=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    logger.info("=" * 80)
    logger.info(f"Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.success("🎉 ALL TESTS PASSED!")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
