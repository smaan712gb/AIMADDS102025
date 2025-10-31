"""
Diagnostic script to check data freshness across all sources
Ensures we're getting the LATEST 10-K, 10-Q, and other filings
"""
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger
import json

# Load environment
load_dotenv()

from src.integrations.fmp_client import FMPClient
from src.integrations.sec_client import SECClient

async def check_fmp_data_freshness(ticker: str = "AAPL"):
    """Check FMP data freshness"""
    logger.info(f"\n{'='*80}")
    logger.info(f"CHECKING FMP DATA FRESHNESS FOR {ticker}")
    logger.info(f"{'='*80}\n")
    
    async with FMPClient() as client:
        # Check financial statements
        logger.info("1. Income Statement Dates:")
        income = await client.get_income_statement(ticker, limit=5)
        if income:
            for i, stmt in enumerate(income[:3]):
                date = stmt.get('date', 'Unknown')
                period = stmt.get('period', 'Unknown')
                logger.info(f"   [{i+1}] Date: {date} | Period: {period}")
                
                # Check if recent (within last 12 months)
                try:
                    stmt_date = datetime.strptime(date, '%Y-%m-%d')
                    days_old = (datetime.now() - stmt_date).days
                    if days_old > 365:
                        logger.warning(f"       ⚠️  Data is {days_old} days old!")
                    else:
                        logger.info(f"       ✓ Data is {days_old} days old (fresh)")
                except:
                    logger.warning(f"       ⚠️  Could not parse date")
        else:
            logger.error("   ✗ No income statement data returned")
        
        # Check SEC filings metadata from FMP
        logger.info("\n2. SEC Filings from FMP:")
        sec_filings = await client.get_sec_filings(ticker, filing_type="10-K", limit=5)
        if sec_filings:
            for i, filing in enumerate(sec_filings[:3]):
                filing_date = filing.get('fillingDate', filing.get('acceptedDate', 'Unknown'))
                filing_type = filing.get('type', 'Unknown')
                logger.info(f"   [{i+1}] Type: {filing_type} | Date: {filing_date}")
                
                # Check freshness
                try:
                    f_date = datetime.strptime(filing_date.split()[0], '%Y-%m-%d')
                    days_old = (datetime.now() - f_date).days
                    if days_old > 365:
                        logger.warning(f"       ⚠️  Filing is {days_old} days old!")
                    else:
                        logger.info(f"       ✓ Filing is {days_old} days old (fresh)")
                except:
                    logger.warning(f"       ⚠️  Could not parse date")
        else:
            logger.error("   ✗ No SEC filings returned")
        
        # Check quarterly data
        logger.info("\n3. Quarterly Income Statements:")
        quarterly = await client.get_income_statement(ticker, period="quarter", limit=5)
        if quarterly:
            for i, stmt in enumerate(quarterly[:3]):
                date = stmt.get('date', 'Unknown')
                period = stmt.get('period', 'Unknown')
                logger.info(f"   [{i+1}] Date: {date} | Period: {period}")
                
                # Check if recent quarter
                try:
                    stmt_date = datetime.strptime(date, '%Y-%m-%d')
                    days_old = (datetime.now() - stmt_date).days
                    if days_old > 120:  # Quarterly should be within 120 days
                        logger.warning(f"       ⚠️  Quarterly data is {days_old} days old!")
                    else:
                        logger.info(f"       ✓ Quarterly data is {days_old} days old (fresh)")
                except:
                    logger.warning(f"       ⚠️  Could not parse date")
        else:
            logger.error("   ✗ No quarterly data returned")

async def check_sec_data_freshness(ticker: str = "AAPL"):
    """Check SEC EDGAR data freshness"""
    logger.info(f"\n{'='*80}")
    logger.info(f"CHECKING SEC EDGAR DATA FRESHNESS FOR {ticker}")
    logger.info(f"{'='*80}\n")
    
    sec_client = SECClient()
    
    # Check latest filings
    logger.info("1. Latest SEC Filings:")
    filings = sec_client.get_latest_filings(ticker, ['10-K', '10-Q'], count=5)
    
    if filings:
        for i, filing in enumerate(filings):
            filing_type = filing.get('type', 'Unknown')
            retrieved = filing.get('retrieved_at', 'Unknown')
            logger.info(f"   [{i+1}] Type: {filing_type} | Retrieved: {retrieved}")
            logger.warning(f"       ⚠️  Note: Filing metadata fetched but not actual filing date!")
    else:
        logger.error("   ✗ No filings returned")
    
    # Try to get actual filing with date
    logger.info("\n2. Attempting to fetch actual 10-K filing:")
    filing_data = await sec_client.get_filing_full_text(ticker, '10-K')
    
    if 'error' not in filing_data:
        accession = filing_data.get('accession_number', 'Unknown')
        retrieved = filing_data.get('retrieved_at', 'Unknown')
        text_length = filing_data.get('text_length', 0)
        
        logger.info(f"   ✓ Successfully fetched 10-K")
        logger.info(f"     Accession: {accession}")
        logger.info(f"     Retrieved: {retrieved}")
        logger.info(f"     Text length: {text_length:,} characters")
        
        # Try to extract date from text
        import re
        text = filing_data.get('full_text', '')
        date_patterns = [
            r'For the fiscal year ended (\w+ \d+, \d{4})',
            r'For the year ended (\w+ \d+, \d{4})',
            r'Fiscal year ended (\w+ \d+, \d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                fiscal_year = match.group(1)
                logger.info(f"     Fiscal year end: {fiscal_year}")
                break
    else:
        logger.error(f"   ✗ Failed to fetch 10-K: {filing_data.get('error')}")

async def check_data_sorting():
    """Check if data is properly sorted by date"""
    logger.info(f"\n{'='*80}")
    logger.info(f"CHECKING DATA SORTING (MOST RECENT FIRST)")
    logger.info(f"{'='*80}\n")
    
    ticker = "AAPL"
    
    async with FMPClient() as client:
        logger.info("1. Income Statement Ordering:")
        income = await client.get_income_statement(ticker, limit=10)
        
        if income and len(income) >= 2:
            dates = [stmt.get('date', '') for stmt in income[:5]]
            logger.info(f"   Dates: {dates}")
            
            # Check if sorted descending (newest first)
            is_descending = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
            
            if is_descending:
                logger.info(f"   ✓ Data is sorted correctly (newest first)")
            else:
                logger.warning(f"   ⚠️  Data may not be sorted correctly!")
                
            # Show newest vs oldest
            try:
                newest = datetime.strptime(dates[0], '%Y-%m-%d')
                oldest = datetime.strptime(dates[-1], '%Y-%m-%d')
                span_years = (newest - oldest).days / 365.25
                logger.info(f"   Data spans {span_years:.1f} years")
                logger.info(f"   Newest: {dates[0]}")
                logger.info(f"   Oldest: {dates[-1]}")
            except:
                logger.warning(f"   ⚠️  Could not calculate date span")
        else:
            logger.error("   ✗ Insufficient data to check sorting")

def check_financetoolkit_usage():
    """Check if financetoolkit is being used"""
    logger.info(f"\n{'='*80}")
    logger.info(f"CHECKING FINANCETOOLKIT USAGE")
    logger.info(f"{'='*80}\n")
    
    # Search for financetoolkit imports in agent files
    import os
    import re
    
    agent_dir = "src/agents"
    uses_ft = []
    
    for filename in os.listdir(agent_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(agent_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'financetoolkit' in content.lower() or 'finance_toolkit' in content.lower():
                        # Find specific imports
                        imports = re.findall(r'from financetoolkit.*import.*|import financetoolkit', content)
                        if imports:
                            uses_ft.append({
                                'file': filename,
                                'imports': imports
                            })
            except:
                pass
    
    if uses_ft:
        logger.info(f"   ✓ financetoolkit is used in {len(uses_ft)} agent(s):")
        for usage in uses_ft:
            logger.info(f"     - {usage['file']}")
            for imp in usage['imports']:
                logger.info(f"       {imp}")
    else:
        logger.info(f"   ℹ️  financetoolkit not currently used in agents")

async def main():
    """Run all diagnostic checks"""
    logger.info("="*80)
    logger.info("DATA FRESHNESS DIAGNOSTIC SCRIPT")
    logger.info("="*80)
    
    ticker = "AAPL"
    
    # Check FMP
    await check_fmp_data_freshness(ticker)
    
    # Check SEC
    await check_sec_data_freshness(ticker)
    
    # Check sorting
    await check_data_sorting()
    
    # Check financetoolkit
    check_financetoolkit_usage()
    
    # Summary and recommendations
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY AND RECOMMENDATIONS")
    logger.info(f"{'='*80}\n")
    
    logger.info("Issues Found:")
    logger.info("1. SEC client fetches filing metadata but doesn't extract/verify filing date")
    logger.info("2. No explicit date filtering in API calls (relies on limit parameter)")
    logger.info("3. FMP client assumes data is sorted newest-first (should verify)")
    logger.info("4. No cache invalidation mechanism for stale data")
    logger.info("5. Agents don't check data freshness before processing")

    logger.info("\nRecommendations:")
    logger.info("1. Add date filtering to FMP API calls (from_date, to_date)")
    logger.info("2. Extract and verify filing dates from SEC EDGAR")
    logger.info("3. Add data freshness validation in agents")
    logger.info("4. Implement cache with TTL for financial data")
    logger.info("5. Add fallback to alternative data sources if data too old")

    logger.info(f"\nDiagnostic completed for {ticker}")
