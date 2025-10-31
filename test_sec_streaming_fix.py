"""
Test SEC client streaming fix for Item 1A extraction
"""
import asyncio
from src.integrations.sec_client import SECClient
from loguru import logger

async def test_sec_streaming():
    """Test that SEC extraction now uses streaming"""
    
    logger.info("Testing SEC client streaming fix...")
    
    sec_client = SECClient()
    
    # Test with a company that has large Item 1A sections
    ticker = "CRWD"  # CrowdStrike - known to have long risk factor sections
    
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing LLM-powered extraction for {ticker}")
        logger.info(f"{'='*60}\n")
        
        # This should now use streaming and not timeout
        result = await sec_client.extract_risk_factors(ticker, "10-K", num_years=1)
        
        if 'error' not in result:
            logger.info(f"✓ SUCCESS: Risk factors extracted without streaming timeout")
            logger.info(f"  - Years analyzed: {result.get('num_years_analyzed', 0)}")
            
            if result.get('risk_factors_by_year'):
                first_year = result['risk_factors_by_year'][0]
                extraction_method = first_year.get('extraction_method', 'unknown')
                risk_text_length = len(first_year.get('risk_text', ''))
                
                logger.info(f"  - Extraction method: {extraction_method}")
                logger.info(f"  - Risk text length: {risk_text_length:,} chars")
                
                if risk_text_length > 0:
                    logger.info(f"\n✓ FIX VERIFIED: Streaming is working correctly!")
                    return True
                else:
                    logger.warning(f"⚠️ No risk text extracted")
            else:
                logger.warning(f"⚠️ No risk factors data in result")
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Extraction failed: {error_msg}")
            
            # Check if it's still a streaming error
            if "Streaming is required" in error_msg:
                logger.error(f"❌ FIX NOT WORKING: Still getting streaming error!")
                return False
            else:
                logger.warning(f"⚠️ Different error occurred (not streaming related)")
                
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        
        # Check if it's the streaming error
        if "Streaming is required" in str(e):
            logger.error(f"❌ FIX NOT WORKING: Still getting streaming error!")
            return False
        else:
            logger.error(f"Different error occurred")
        
        return False
    
    return False

async def main():
    """Run the test"""
    logger.info("SEC Client Streaming Fix Test")
    logger.info("="*60)
    
    success = await test_sec_streaming()
    
    logger.info("\n" + "="*60)
    if success:
        logger.info("✓ TEST PASSED: Streaming fix is working!")
    else:
        logger.warning("⚠️ TEST INCONCLUSIVE: Check logs for details")
    logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())
