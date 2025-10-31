"""
Test script to explore FMP As Reported Financial Statements API
Checking if it provides qualitative data like MD&A for the legal agent
"""
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

def test_as_reported_api(ticker: str = "AAPL"):
    """
    Test FMP As Reported Financial Statements API
    
    Args:
        ticker: Stock ticker to test
    """
    api_key = os.getenv("FMP_API_KEY")
    
    if not api_key:
        logger.error("FMP_API_KEY not found in environment variables")
        return None
    
    # FMP As Reported Financial Statements endpoint
    base_url = "https://financialmodelingprep.com/api/v4/financial-reports-json"
    
    logger.info(f"Testing FMP As Reported API for {ticker}")
    logger.info("=" * 80)
    
    # Test different periods
    test_periods = ["Q1", "Q2", "Q3", "Q4", "FY"]  # Quarterly and Annual
    
    results = {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }
    
    for period in test_periods:
        logger.info(f"\nTesting period: {period}")
        
        # Construct URL
        url = f"{base_url}?symbol={ticker}&period={period}&apikey={api_key}"
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data:
                    logger.info(f"✓ Successfully retrieved data for {period}")
                    logger.info(f"  Response type: {type(data)}")
                    
                    # Analyze structure
                    if isinstance(data, list) and len(data) > 0:
                        first_item = data[0]
                        logger.info(f"  First item type: {type(first_item)}")
                        logger.info(f"  Number of reports: {len(data)}")
                        
                        # Get latest report
                        latest = first_item
                        logger.info(f"\n  Latest Report Structure for {period}:")
                        logger.info(f"  Available keys: {list(latest.keys())}")
                        
                        # Check for qualitative data sections
                        qualitative_sections = [
                            'md&a',
                            'mda',
                            'management_discussion',
                            'text',
                            'content',
                            'notes',
                            'footnotes',
                            'risk_factors',
                            'business_description'
                        ]
                        
                        found_qualitative = []
                        for section in qualitative_sections:
                            if section in latest or section.upper() in latest:
                                found_qualitative.append(section)
                        
                        if found_qualitative:
                            logger.info(f"  ✓ Found qualitative sections: {found_qualitative}")
                        else:
                            logger.info(f"  ✗ No qualitative sections found")
                        
                        # Sample first few keys with their data types and sample values
                        logger.info(f"\n  Sample Data:")
                        for i, (key, value) in enumerate(list(latest.items())[:10]):
                            value_type = type(value).__name__
                            
                            # Get sample value
                            if isinstance(value, (str, int, float, bool)):
                                sample = str(value)[:100]
                            elif isinstance(value, dict):
                                sample = f"dict with {len(value)} keys: {list(value.keys())[:5]}"
                            elif isinstance(value, list):
                                sample = f"list with {len(value)} items"
                            else:
                                sample = str(value)[:50]
                            
                            logger.info(f"    {key} ({value_type}): {sample}")
                        
                        # Store result
                        results["tests"].append({
                            "period": period,
                            "success": True,
                            "num_reports": len(data),
                            "keys": list(latest.keys()),
                            "qualitative_sections": found_qualitative,
                            "sample_data": {k: str(v)[:200] for k, v in list(latest.items())[:5]}
                        })
                    
                    elif isinstance(data, dict):
                        logger.info(f"  Data is a dictionary with keys: {list(data.keys())}")
                        
                        results["tests"].append({
                            "period": period,
                            "success": True,
                            "structure": "dict",
                            "keys": list(data.keys())
                        })
                    
                    else:
                        logger.warning(f"  Unexpected data structure: {type(data)}")
                        results["tests"].append({
                            "period": period,
                            "success": False,
                            "error": f"Unexpected structure: {type(data)}"
                        })
                
                else:
                    logger.warning(f"  ✗ Empty response for {period}")
                    results["tests"].append({
                        "period": period,
                        "success": False,
                        "error": "Empty response"
                    })
            
            else:
                logger.error(f"  ✗ HTTP {response.status_code}: {response.text[:200]}")
                results["tests"].append({
                    "period": period,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text[:200]
                })
        
        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            results["tests"].append({
                "period": period,
                "success": False,
                "error": str(e)
            })
    
    # Save results to file
    output_file = f"fmp_as_reported_test_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Results saved to: {output_file}")
    logger.info(f"{'=' * 80}")
    
    # Summary
    successful_tests = sum(1 for t in results["tests"] if t.get("success"))
    logger.info(f"\nSummary:")
    logger.info(f"  Total tests: {len(results['tests'])}")
    logger.info(f"  Successful: {successful_tests}")
    logger.info(f"  Failed: {len(results['tests']) - successful_tests}")
    
    # Check if any qualitative data found
    all_qualitative = []
    for test in results["tests"]:
        if test.get("success") and test.get("qualitative_sections"):
            all_qualitative.extend(test["qualitative_sections"])
    
    if all_qualitative:
        logger.info(f"\n✓ QUALITATIVE DATA FOUND:")
        logger.info(f"  Sections: {set(all_qualitative)}")
        logger.info(f"\n  Recommendation: This API provides qualitative data for legal agent")
    else:
        logger.warning(f"\n✗ NO QUALITATIVE DATA FOUND")
        logger.warning(f"  This API may only provide structured financial numbers")
        logger.warning(f"  Legal agent may still need SEC EDGAR for MD&A and text content")
    
    return results


def test_alternative_endpoint(ticker: str = "AAPL"):
    """
    Test alternative FMP endpoint that might have more detail
    """
    api_key = os.getenv("FMP_API_KEY")
    
    logger.info(f"\n\nTesting ALTERNATIVE endpoint: SEC Filings")
    logger.info("=" * 80)
    
    # Try SEC filings endpoint
    url = f"https://financialmodelingprep.com/api/v3/sec_filings/{ticker}?type=10-K&page=0&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                logger.info(f"✓ SEC Filings endpoint returned {len(data)} filings")
                
                # Check first filing
                first_filing = data[0]
                logger.info(f"\nFirst Filing Structure:")
                logger.info(f"  Keys: {list(first_filing.keys())}")
                
                # Check for full text or links
                for key in first_filing.keys():
                    value = first_filing[key]
                    if isinstance(value, str) and len(value) > 500:
                        logger.info(f"  ✓ {key}: Contains {len(value)} characters (likely text content)")
                    elif 'url' in key.lower() or 'link' in key.lower():
                        logger.info(f"  ✓ {key}: {value}")
                
                return first_filing
            else:
                logger.warning("Empty or invalid response from SEC filings endpoint")
        else:
            logger.error(f"HTTP {response.status_code} from SEC filings endpoint")
    
    except Exception as e:
        logger.error(f"Error testing alternative endpoint: {e}")
    
    return None


if __name__ == "__main__":
    logger.info("FMP As Reported Financial Statements API Test")
    logger.info("=" * 80)
    
    # Test with AAPL
    ticker = "AAPL"
    
    logger.info(f"Testing ticker: {ticker}\n")
    
    # Test main endpoint
    results = test_as_reported_api(ticker)
    
    # Test alternative endpoint
    alt_results = test_alternative_endpoint(ticker)
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext Steps:")
    logger.info("1. Review the generated JSON file for detailed results")
    logger.info("2. Check if qualitative sections are available")
    logger.info("3. If qualitative data found, update legal agent to use this API")
    logger.info("4. If not found, legal agent should continue using SEC EDGAR for Item 7 MD&A")
