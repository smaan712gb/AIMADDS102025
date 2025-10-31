"""
Test script for critical fixes:
1. MD&A extraction with HTML DOM parsing
2. Legal Counsel agent state management
"""
import asyncio
import sys
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")


async def test_mda_extraction():
    """Test MD&A extraction with HTML DOM parsing approach"""
    logger.info("=" * 80)
    logger.info("TEST 1: MD&A Extraction with HTML DOM Parsing")
    logger.info("=" * 80)
    
    try:
        from src.integrations.sec_client import SECClient
        
        sec_client = SECClient()
        
        # Test with a well-known company
        ticker = "CRWD"
        logger.info(f"\nTesting MD&A extraction for {ticker}...")
        
        # Test the extract_mda_section method
        result = await sec_client.extract_mda_section(ticker, filing_type="10-K")
        
        if 'error' in result:
            logger.warning(f"MD&A extraction returned error: {result['error']}")
            logger.info("This may be expected if SEC filing is not available or parsing failed")
            return False
        
        if 'mda_text' in result:
            mda_length = len(result['mda_text'])
            logger.success(f"✓ MD&A extracted successfully: {mda_length} characters")
            
            # Check sentiment analysis
            if 'analysis' in result:
                analysis = result['analysis']
                logger.info(f"  - Sentiment score: {analysis.get('sentiment_score', 'N/A')}")
                logger.info(f"  - Overall tone: {analysis.get('overall_tone', 'N/A')}")
                logger.info(f"  - Positive words: {analysis.get('positive_tone_count', 0)}")
                logger.info(f"  - Negative words: {analysis.get('negative_tone_count', 0)}")
            
            # Verify minimum length (should be substantial)
            if mda_length < 500:
                logger.warning(f"MD&A text seems short ({mda_length} chars). May need investigation.")
                return False
            
            logger.success("✓ MD&A extraction test PASSED")
            return True
        else:
            logger.error("MD&A text not found in result")
            return False
            
    except Exception as e:
        logger.error(f"MD&A extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_legal_counsel_state_management():
    """Test Legal Counsel agent state management"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Legal Counsel Agent State Management")
    logger.info("=" * 80)
    
    try:
        from src.agents.legal_counsel import LegalCounselAgent
        from src.core.state import DiligenceState
        
        # Create initial state
        state: DiligenceState = {
            'target_company': 'Test Corp',
            'target_ticker': 'CRWD',
            'deal_type': 'acquisition',
            'deal_value': 1000000000,
            'metadata': {},
            'legal_risks': [],
            'errors': [],
            'warnings': []
        }
        
        logger.info("\nExecuting Legal Counsel agent...")
        
        # Create and run agent
        agent = LegalCounselAgent()
        result_state = await agent.execute(state)
        
        # Verify state structure
        logger.info("\nVerifying state structure...")
        
        # Check that legal_analysis is NOT in the top level (bug fix verification)
        if 'legal_analysis' in result_state and isinstance(result_state['legal_analysis'], dict):
            # If it exists at top level, check it's not the SEC analysis only
            if 'sec_risk_factors' in result_state['legal_analysis']:
                logger.error("✗ State management bug detected: legal_analysis contains only SEC data")
                logger.error("  This indicates the line 'state['legal_analysis'] = sec_analysis' was not removed")
                return False
        
        # Check that legal findings are properly stored in metadata
        if 'legal_analysis' not in result_state['metadata']:
            logger.error("✗ Legal analysis not found in metadata")
            return False
        
        legal_findings = result_state['metadata']['legal_analysis']
        
        # Verify all expected components are present
        expected_keys = [
            'sec_analysis',
            'contract_analysis',
            'litigation_analysis',
            'identified_risks',
            'compliance_status',
            'governance_review',
            'overall_assessment'
        ]
        
        missing_keys = [key for key in expected_keys if key not in legal_findings]
        if missing_keys:
            logger.error(f"✗ Missing keys in legal findings: {missing_keys}")
            return False
        
        logger.success("✓ All expected keys present in legal findings")
        
        # Verify compliance_status is at top level (as required)
        if 'compliance_status' not in result_state:
            logger.error("✗ compliance_status not found at top level of state")
            return False
        
        logger.success("✓ compliance_status properly stored at top level")
        
        # Check legal risks were added
        if len(result_state['legal_risks']) == 0:
            logger.warning("⚠ No legal risks identified (may be expected for test)")
        else:
            logger.info(f"✓ {len(result_state['legal_risks'])} legal risks identified")
        
        # Verify no errors occurred
        if result_state['errors']:
            logger.warning(f"⚠ Errors occurred during execution: {result_state['errors']}")
        else:
            logger.success("✓ No errors during execution")
        
        # Check warnings
        if result_state.get('warnings'):
            logger.info(f"ℹ Warnings: {len(result_state['warnings'])}")
            for warning in result_state['warnings']:
                logger.info(f"  - {warning}")
        
        logger.success("✓ Legal Counsel state management test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Legal Counsel state management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("CRITICAL FIXES VALIDATION")
    logger.info("=" * 80)
    
    results = {
        'mda_extraction': False,
        'legal_counsel_state': False
    }
    
    # Test 1: MD&A extraction
    results['mda_extraction'] = await test_mda_extraction()
    
    # Test 2: Legal Counsel state management
    results['legal_counsel_state'] = await test_legal_counsel_state_management()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.success("\n✓ ALL CRITICAL FIXES VALIDATED SUCCESSFULLY")
        return 0
    else:
        logger.error("\n✗ SOME TESTS FAILED - REVIEW REQUIRED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
