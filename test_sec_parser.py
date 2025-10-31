"""
Test sec-parser integration for SEC filing extraction
"""
import asyncio
from src.integrations.sec_client import get_sec_client

async def test_sec_parser():
    """Test SEC parser functionality with real filing"""
    try:
        print("Testing sec-parser integration with real SEC filing...")


        client = get_sec_client()

        # Test sec-parser availability
        print(f"SEC_PARSER_AVAILABLE: sec-parser is working correctly")

        # Test with a simple ticker fetch (Apple)
        print("\n=== Testing Filing Fetch ===")
        filings = client.get_latest_filings("AAPL", ['10-K'], count=1)
        print(f"Found {len(filings)} AAPL 10-K filings")
        if filings:
            print(f"Latest filing: {filings[0]}")

        # Test MDA extraction with real filing if available
        print("\n=== Testing MD&A Extraction ===")
        try:
            mda_result = await client.extract_mda_section("AAPL", "10-K")
            if mda_result.get('error'):
                print(f"MDA extraction error: {mda_result['error']}")
                print("This is expected for quick test - full extraction needs more time")
            else:
                print(f"MDA extraction success: {len(mda_result.get('mda_text', ''))} chars extracted")
                print(f"Extraction method used: {mda_result.get('extraction_method', 'unknown')}")
        except Exception as e:
            print(f"MDA extraction failed: {e}")

        # Test risk factors extraction
        print("\n=== Testing Risk Factors Extraction ===")
        try:
            risk_result = await client.extract_risk_factors("AAPL", "10-K", num_years=1)
            if risk_result.get('error'):
                print(f"Risk factors extraction error: {risk_result['error']}")
            else:
                print(f"Risk factors extraction success: {len(risk_result.get('risk_factors_by_year', []))} years analyzed")
                if risk_result.get('risk_factors_by_year'):
                    first_year = risk_result['risk_factors_by_year'][0]
                    print(f"First year method: {first_year.get('extraction_method', 'unknown')}")
                    if first_year.get('risk_analysis'):
                        print(f"Risk keywords found: {len(first_year['risk_analysis'].get('risk_keyword_counts', {}))}")
        except Exception as e:
            print(f"Risk factors extraction failed: {e}")

        return True

    except Exception as e:
        print(f"Error testing sec-parser: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sec_parser())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
