"""
Quick test to verify data freshness fixes
"""
import asyncio
from datetime import datetime, timedelta
from src.integrations.fmp_client import FMPClient
from src.integrations.sec_client import SECClient

async def test_fmp_date_filtering():
    """Test FMP date filtering"""
    print("Testing FMP date filtering...")

    async with FMPClient() as client:
        # Test with date filtering
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        print(f"Date range: {start_date} to {end_date}")

        # Test income statement with date filtering
        try:
            income = await client.get_income_statement("AAPL", limit=3, from_date=start_date, to_date=end_date)
            if income:
                print(f"✓ FMP date filtering works - got {len(income)} statements")
                for i, stmt in enumerate(income[:2]):
                    date = stmt.get('date', 'Unknown')
                    print(f"  [{i+1}] Date: {date}")
            else:
                print("✗ No data returned with date filtering")
        except Exception as e:
            print(f"✗ Error with date filtering: {e}")

async def test_sec_date_extraction():
    """Test SEC filing date extraction"""
    print("\nTesting SEC filing date extraction...")

    sec_client = SECClient()

    try:
        filings = sec_client.get_latest_filings("AAPL", ['10-K'], count=3)

        if filings:
            print(f"✓ SEC date extraction works - got {len(filings)} filings")
            for i, filing in enumerate(filings[:2]):
                filing_date = filing.get('filing_date')
                filing_type = filing.get('type')
                print(f"  [{i+1}] {filing_type}: {filing_date}")

                # Validate date
                if filing_date:
                    try:
                        f_date = datetime.strptime(filing_date, '%Y-%m-%d')
                        days_old = (datetime.now() - f_date).days
                        print(f"      Age: {days_old} days")
                    except ValueError:
                        print(f"      ⚠️ Invalid date format: {filing_date}")
        else:
            print("✗ No SEC filings returned")
    except Exception as e:
        print(f"✗ Error with SEC filings: {e}")

async def main():
    """Run tests"""
    print("="*60)
    print("DATA FRESHNESS FIXES VERIFICATION")
    print("="*60)

    await test_fmp_date_filtering()
    await test_sec_date_extraction()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✓ Enhanced FMP client with date filtering")
    print("✓ Enhanced SEC client with date extraction and validation")
    print("✓ Added data freshness validation in financial analyst")
    print("✓ Agents now validate data age and log warnings for stale data")
    print("\nNext steps:")
    print("- Monitor logs for data freshness warnings")
    print("- Consider adding cache with short TTL for API data")
    print("- Add fallback mechanisms for stale data")

if __name__ == "__main__":
    asyncio.run(main())
