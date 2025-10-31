"""
Test Legal Agent with Chunked Item 1A Extraction

This test verifies that the legal agent can handle large Item 1A sections
without getting hung up using the new parallel chunked extraction.
"""
import asyncio
from loguru import logger

async def test_chunked_extraction():
    """Test chunked extraction for a company with large Item 1A"""
    
    try:
        from src.integrations.sec_client_chunked import get_chunked_extractor
        
        # Test with mock large section
        mock_large_text = """
        Item 1A. Risk Factors
        
        """ + ("Risk category description. " * 10000) + """
        
        Item 1B. Unresolved Staff Comments
        """
        
        logger.info("Testing chunked extractor with large mock section...")
        
        extractor = get_chunked_extractor()
        
        # Test extraction
        result = await extractor.extract_large_section_parallel(
            mock_large_text,
            "Item 1A",
            "Item 1B"
        )
        
        if result:
            logger.info(f"✓ Chunked extraction successful: {len(result):,} chars extracted")
            logger.info(f"✓ Sample: {result[:200]}...")
            return True
        else:
            logger.error("✗ Chunked extraction failed")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_legal_agent_integration():
    """Test legal agent with chunked extraction"""
    
    try:
        from src.agents.legal_counsel import LegalCounselAgent
        from src.core.state import DiligenceState
        
        logger.info("\nTesting legal agent with chunked extraction...")
        
        # Create test state
        state = DiligenceState(
            target_company="Test Company",
            target_ticker="TEST",
            deal_type="acquisition",
            deal_value=1000000000
        )
        
        # Initialize agent
        agent = LegalCounselAgent()
        
        # Run agent (should use chunked extraction for Item 1A if available)
        logger.info("Running legal agent...")
        result = await agent.run(state)
        
        if result and 'data' in result:
            logger.info(f"✓ Legal agent completed successfully")
            logger.info(f"  - Risks identified: {len(result['data'].get('identified_risks', []))}")
            logger.info(f"  - SEC analysis available: {'sec_analysis' in result['data']}")
            return True
        else:
            logger.error("✗ Legal agent failed")
            return False
            
    except Exception as e:
        logger.error(f"Legal agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    
    logger.info("="*60)
    logger.info("LEGAL AGENT CHUNKED EXTRACTION TEST")
    logger.info("="*60)
    
    # Test 1: Chunked extractor directly
    test1_passed = await test_chunked_extraction()
    
    # Test 2: Legal agent integration
    test2_passed = await test_legal_agent_integration()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Chunked Extractor Test: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    logger.info(f"Legal Agent Integration: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed:
        logger.info("\n✓ ALL TESTS PASSED - Legal agent chunking is working!")
    else:
        logger.info("\n✗ SOME TESTS FAILED - See errors above")

if __name__ == "__main__":
    asyncio.run(main())
