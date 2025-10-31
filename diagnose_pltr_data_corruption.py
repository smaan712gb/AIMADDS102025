"""
Diagnostic Script: Investigate Palantir Data Corruption
Specifically checking the -106% margin outlier in 2020 data
"""
import asyncio
import json
from datetime import datetime
from loguru import logger

from src.integrations.fmp_client import FMPClient


async def diagnose_pltr_data():
    """Investigate Palantir data quality issues"""
    logger.info("=" * 80)
    logger.info("DIAGNOSING PALANTIR DATA CORRUPTION")
    logger.info("=" * 80)
    
    ticker = "PLTR"
    
    async with FMPClient() as client:
        # Fetch all financial data
        logger.info("\n📊 Fetching comprehensive financial data...")
        
        # Get income statements (10 years annual)
        income_annual = await client.get_income_statement(ticker, period='annual', limit=10)
        
        # Get most recent quarterly data for validation
        income_quarterly = await client.get_income_statement(ticker, period='quarter', limit=4)
        
        # Get company profile
        profile = await client.get_company_profile(ticker)
        
        logger.info(f"\n✓ Company: {profile.get('companyName')}")
        logger.info(f"✓ IPO Date: {profile.get('ipoDate')}")
        logger.info(f"✓ Market Cap: ${profile.get('mktCap', 0)/1e9:.1f}B")
        
        # Analyze annual data
        logger.info("\n" + "=" * 80)
        logger.info("ANNUAL INCOME STATEMENT ANALYSIS")
        logger.info("=" * 80)
        
        for idx, stmt in enumerate(income_annual):
            date = stmt.get('date', 'Unknown')
            revenue = stmt.get('revenue', 0)
            net_income = stmt.get('netIncome', 0)
            operating_income = stmt.get('operatingIncome', 0)
            
            # Calculate margins
            net_margin = (net_income / revenue * 100) if revenue > 0 else 0
            operating_margin = (operating_income / revenue * 100) if revenue > 0 else 0
            
            # Flag suspicious data
            is_suspicious = abs(net_margin) > 100 or abs(operating_margin) > 100
            flag = "🔴 SUSPICIOUS" if is_suspicious else "✅ OK"
            
            logger.info(f"\n{flag} {date}:")
            logger.info(f"  Revenue: ${revenue/1e9:.2f}B")
            logger.info(f"  Net Income: ${net_income/1e9:.2f}B")
            logger.info(f"  Operating Income: ${operating_income/1e9:.2f}B")
            logger.info(f"  Net Margin: {net_margin:.1f}%")
            logger.info(f"  Operating Margin: {operating_margin:.1f}%")
            
            if is_suspicious:
                logger.error(f"  ⚠️ EXTREME MARGIN DETECTED - Likely data corruption or one-time event")
                logger.error(f"  ⚠️ This data should be EXCLUDED or NORMALIZED for valuation")
        
        # Analyze quarterly data
        logger.info("\n" + "=" * 80)
        logger.info("MOST RECENT QUARTERLY DATA (Q2 2025 Validation)")
        logger.info("=" * 80)
        
        if income_quarterly:
            latest_q = income_quarterly[0]
            date = latest_q.get('date', 'Unknown')
            revenue = latest_q.get('revenue', 0)
            net_income = latest_q.get('netIncome', 0)
            
            net_margin = (net_income / revenue * 100) if revenue > 0 else 0
            
            logger.info(f"\n✓ Latest Quarter ({date}):")
            logger.info(f"  Revenue: ${revenue/1e9:.2f}B")
            logger.info(f"  Net Income: ${net_income/1e9:.2f}B")
            logger.info(f"  Net Margin: {net_margin:.1f}%")
            logger.info(f"\n  📊 USER REPORTED: Q2 2025 GAAP net margin was 33%")
            logger.info(f"  📊 FMP API SHOWS: {net_margin:.1f}%")
            
            if abs(net_margin - 33) < 5:
                logger.info(f"  ✅ VALIDATION PASSED - Margin matches user report")
            else:
                logger.warning(f"  ⚠️ VARIANCE - FMP shows {net_margin:.1f}% vs user 33%")
        
        # DETAILED ANALYSIS OF 2020 DATA
        logger.info("\n" + "=" * 80)
        logger.info("DETAILED ANALYSIS OF 2020 DATA (THE OUTLIER YEAR)")
        logger.info("=" * 80)
        
        stmt_2020 = next((s for s in income_annual if '2020' in s.get('date', '')), None)
        
        if stmt_2020:
            logger.info(f"\n🔍 2020 Key Metrics:")
            logger.info(f"  revenue: ${stmt_2020.get('revenue', 0):,.0f}")
            logger.info(f"  netIncome: ${stmt_2020.get('netIncome', 0):,.0f}")
            logger.info(f"  operatingIncome: ${stmt_2020.get('operatingIncome', 0):,.0f}")
            
            revenue = stmt_2020.get('revenue', 1)
            net_income = stmt_2020.get('netIncome', 0)
            
            recalc_net_margin = (net_income / revenue * 100) if revenue > 0 else 0
            
            if abs(recalc_net_margin) > 100:
                logger.error("\n❌ DIAGNOSIS: FMP API data for 2020 is CORRUPTED")
                logger.error(f"   Net Margin: {recalc_net_margin:.1f}%")
                logger.error(f"   SOLUTION: EXCLUDE 2020 from analysis")
        
        # Recommendation
        logger.info("\n" + "=" * 80)
        logger.info("RECOMMENDATIONS")
        logger.info("=" * 80)
        
        clean_years = sum(1 for s in income_annual if abs((s.get('netIncome', 0) / s.get('revenue', 1) * 100)) < 100)
        total_years = len(income_annual)
        
        logger.info(f"\n✅ CLEAN DATA: {clean_years}/{total_years} years")
        logger.info(f"🔴 CORRUPTED DATA: {total_years - clean_years} years")
        logger.info(f"\n💡 IMPLEMENT: Data quality gates to auto-exclude corrupted years")
        
        results = {
            'ticker': ticker,
            'clean_years': clean_years,
            'corrupted_years': total_years - clean_years,
            'outlier_years': [s.get('date') for s in income_annual 
                            if abs((s.get('netIncome', 0) / s.get('revenue', 1) * 100)) > 100]
        }
        
        return results


if __name__ == "__main__":
    asyncio.run(diagnose_pltr_data())
