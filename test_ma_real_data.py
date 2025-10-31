"""
Test M&A Components with Real Company Data

Tests all 4 M&A components using actual financial data from FMP API.
This validates that the components work with real-world data.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from src.integrations.fmp_client import FMPClient
from src.agents.sources_uses import SourcesUsesGenerator
from src.agents.contribution_analysis import ContributionAnalyzer
from src.agents.exchange_ratio_analysis import ExchangeRatioAnalyzer


async def fetch_company_data(symbol: str, fmp: FMPClient) -> Dict[str, Any]:
    """Fetch real financial data for a company using most recent 10-Q/10-K and real-time quotes"""
    
    logger.info(f"Fetching data for {symbol}")
    
    # Fetch most recent financial statements (limit=1 gets the most recent 10-Q or 10-K)
    income_statements = await fmp.get_income_statement(symbol, limit=1)
    balance_sheets = await fmp.get_balance_sheet(symbol, limit=1)
    
    # Get real-time data using FMP APIs
    import aiohttp
    from src.core.config import Config
    config = Config()
    api_key = config.get_api_key('fmp')
    
    # Get stock quote for current price
    quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
    
    # Get market cap data
    marketcap_url = f"https://financialmodelingprep.com/api/v3/market-capitalization/{symbol}?apikey={api_key}"
    
    async with aiohttp.ClientSession() as session:
        # Fetch quote
        async with session.get(quote_url) as response:
            quote_data = await response.json()
        
        # Fetch market cap
        async with session.get(marketcap_url) as response:
            marketcap_data = await response.json()
    
    # Extract current price from quote
    if quote_data and len(quote_data) > 0:
        current_price = quote_data[0].get('price', 0)
        market_cap_from_api = quote_data[0].get('marketCap', 0)
        logger.info(f"Got real-time quote for {symbol}: ${current_price:.2f}, Market Cap: ${market_cap_from_api/1e9:.1f}B")
    else:
        current_price = 0
        market_cap_from_api = 0
        logger.warning(f"No quote data found for {symbol}")
    
    # Fetch historical prices for premium analysis (last year)
    historical_data = await fmp.get_historical_price(symbol)
    
    # FMP returns {symbol: [data...]} or directly a list
    if isinstance(historical_data, dict):
        # If dict, try to extract the symbol key or 'historical' key
        historical = historical_data.get(symbol, historical_data.get('historical', []))
    elif isinstance(historical_data, list):
        historical = historical_data
    else:
        historical = []
    
    # Limit to last 252 days (1 year of trading)
    historical = historical[:252] if len(historical) > 252 else historical
    
    price_1day_ago = historical[1].get('close', current_price) if len(historical) > 1 else current_price
    
    # Calculate 30-day average
    if len(historical) >= 30:
        prices_30day = [h.get('close', 0) for h in historical[:30]]
        price_30day_avg = sum(prices_30day) / len(prices_30day)
    else:
        price_30day_avg = current_price
    
    # Get 52-week high/low
    if len(historical) >= 252:
        prices_52week = [h.get('close', 0) for h in historical[:252]]
        price_52week_high = max(prices_52week)
        price_52week_low = min(prices_52week)
    else:
        price_52week_high = current_price * 1.2
        price_52week_low = current_price * 0.8
    
    return {
        'symbol': symbol,
        'income_statement': income_statements,
        'balance_sheet': balance_sheets,
        'current_stock_price': current_price,
        'price_1day_ago': price_1day_ago,
        'price_30day_avg': price_30day_avg,
        'price_52week_high': price_52week_high,
        'price_52week_low': price_52week_low
    }


def calculate_accretion_dilution_manual(acquirer_data, target_data, deal_terms):
    """Manual accretion/dilution calculation with real data"""
    
    # Extract data
    acquirer_income = acquirer_data['income_statement'][0]
    target_income = target_data['income_statement'][0]
    
    acquirer_ni = acquirer_income.get('netIncome', 0)
    acquirer_shares = acquirer_income.get('weightedAverageShsOut', 0)
    acquirer_eps = acquirer_ni / acquirer_shares if acquirer_shares > 0 else 0
    
    target_ni = target_income.get('netIncome', 0)
    
    # Calculate financing
    purchase_price = deal_terms['purchase_price']
    cash_pct = deal_terms['cash_percentage']
    
    cash_consideration = purchase_price * cash_pct
    debt_needed = max(0, cash_consideration - deal_terms.get('acquirer_cash_available', 0))
    debt_interest = debt_needed * deal_terms.get('debt_interest_rate', 0.05)
    after_tax_interest = debt_interest * (1 - deal_terms.get('tax_rate', 0.21))
    
    stock_consideration = purchase_price * (1 - cash_pct)
    acquirer_stock_price = deal_terms.get('acquirer_stock_price', acquirer_data['current_stock_price'])
    new_shares = stock_consideration / acquirer_stock_price if acquirer_stock_price > 0 else 0
    
    # Pro forma
    synergies = deal_terms.get('synergies_year1', 0)
    synergies_after_tax = synergies * (1 - deal_terms.get('tax_rate', 0.21))
    
    pro_forma_ni = acquirer_ni + target_ni + synergies_after_tax - after_tax_interest
    pro_forma_shares = acquirer_shares + new_shares
    pro_forma_eps = pro_forma_ni / pro_forma_shares if pro_forma_shares > 0 else 0
    
    # Impact
    eps_impact = pro_forma_eps - acquirer_eps
    eps_impact_pct = (eps_impact / acquirer_eps * 100) if acquirer_eps > 0 else 0
    impact_type = "ACCRETIVE" if eps_impact > 0 else "DILUTIVE" if eps_impact < 0 else "NEUTRAL"
    
    return {
        'acquirer_eps': acquirer_eps,
        'pro_forma_eps': pro_forma_eps,
        'eps_impact_dollar': eps_impact,
        'eps_impact_percent': eps_impact_pct,
        'impact_type': impact_type,
        'new_shares_issued': new_shares,
        'pro_forma_shares': pro_forma_shares,
        'debt_financing': debt_needed
    }


async def run_real_data_test(acquirer_symbol: str, target_symbol: str, deal_terms: Dict[str, Any]):
    """
    Run complete M&A analysis with real company data
    
    Args:
        acquirer_symbol: Ticker symbol for acquiring company
        target_symbol: Ticker symbol for target company
        deal_terms: Deal structure parameters
    """
    
    print("="*80)
    print("M&A ANALYSIS WITH REAL DATA")
    print("="*80)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fetch real data
    print("📡 FETCHING REAL COMPANY DATA")
    print("-"*80)
    
    try:
        async with FMPClient() as fmp:
            acquirer_data = await fetch_company_data(acquirer_symbol, fmp)
            print(f"✅ Acquirer ({acquirer_symbol}): ${acquirer_data['current_stock_price']:.2f}/share")
            
            target_data = await fetch_company_data(target_symbol, fmp)
            print(f"✅ Target ({target_symbol}): ${target_data['current_stock_price']:.2f}/share")
            print()
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    # Display deal scenario
    print("📊 DEAL SCENARIO")
    print("-"*80)
    
    acquirer_income = acquirer_data['income_statement'][0]
    target_income = target_data['income_statement'][0]
    
    print(f"Acquirer: {acquirer_symbol}")
    print(f"  Market Cap: ${acquirer_income.get('weightedAverageShsOut', 0) * acquirer_data['current_stock_price']/1e9:.1f}B")
    print(f"  Revenue: ${acquirer_income.get('revenue', 0)/1e9:.1f}B")
    print(f"  Net Income: ${acquirer_income.get('netIncome', 0)/1e9:.1f}B")
    print()
    
    print(f"Target: {target_symbol}")
    print(f"  Market Cap: ${target_income.get('weightedAverageShsOut', 0) * target_data['current_stock_price']/1e9:.1f}B")
    print(f"  Revenue: ${target_income.get('revenue', 0)/1e9:.1f}B")
    print(f"  Net Income: ${target_income.get('netIncome', 0)/1e9:.1f}B")
    print()
    
    # Auto-calculate purchase price if not provided
    if 'purchase_price' not in deal_terms or deal_terms['purchase_price'] == 0:
        target_market_cap = target_income.get('weightedAverageShsOut', 0) * target_data['current_stock_price']
        premium = deal_terms.get('premium_percent', 0.30)
        deal_terms['purchase_price'] = target_market_cap * (1 + premium)
    
    print(f"Deal Structure:")
    print(f"  Purchase Price: ${deal_terms['purchase_price']/1e9:.1f}B")
    print(f"  Cash/Stock Mix: {deal_terms.get('cash_percentage', 0.5)*100:.0f}% / {(1-deal_terms.get('cash_percentage', 0.5))*100:.0f}%")
    print()
    
    # Set prices in deal terms
    deal_terms['acquirer_stock_price'] = acquirer_data['current_stock_price']
    deal_terms['target_stock_price'] = target_data['current_stock_price']
    
    # Estimate available cash (20% of cash on balance sheet)
    acquirer_balance = acquirer_data['balance_sheet'][0]
    deal_terms['acquirer_cash_available'] = acquirer_balance.get('cashAndCashEquivalents', 0) * 0.8
    
    results = {}
    
    # Test 1: Accretion/Dilution
    print("1️⃣  ACCRETION/DILUTION ANALYSIS")
    print("-"*80)
    try:
        ad_result = calculate_accretion_dilution_manual(acquirer_data, target_data, deal_terms)
        results['accretion_dilution'] = ad_result
        
        print(f"✅ Impact: {ad_result['impact_type']}")
        print(f"   Acquirer Standalone EPS: ${ad_result['acquirer_eps']:.2f}")
        print(f"   Pro Forma EPS: ${ad_result['pro_forma_eps']:.2f}")
        print(f"   EPS Impact: ${ad_result['eps_impact_dollar']:+.2f} ({ad_result['eps_impact_percent']:+.1f}%)")
        print(f"   New Shares: {ad_result['new_shares_issued']/1e6:.1f}M ({ad_result['new_shares_issued']/(ad_result['pro_forma_shares'])*100:.1f}% dilution)")
        print()
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['accretion_dilution'] = {'error': str(e)}
    
    # Test 2: Sources & Uses
    print("2️⃣  SOURCES & USES ANALYSIS")
    print("-"*80)
    try:
        generator = SourcesUsesGenerator()
        su_result = generator.generate(
            deal_terms,
            target_data,
            acquirer_data,
            deal_terms['purchase_price']
        )
        results['sources_uses'] = su_result
        
        uses = su_result['uses_of_funds']
        sources = su_result['sources_of_funds']
        pf_cap = su_result['pro_forma_capitalization']
        
        print(f"✅ Total Transaction: ${uses['total_uses']/1e9:.1f}B")
        print(f"   Uses:")
        print(f"     - Purchase Price: ${uses['equity_purchase_price']/1e9:.1f}B")
        print(f"     - Refinance Debt: ${uses['refinance_target_debt']/1e9:.1f}B")
        print(f"     - Fees: ${uses['total_transaction_fees']/1e6:.0f}M")
        print(f"   Sources:")
        print(f"     - Cash: ${sources['acquirer_cash']/1e9:.1f}B ({sources['acquirer_cash_pct']:.1f}%)")
        print(f"     - Debt: ${sources['new_debt_financing']/1e9:.1f}B ({sources['new_debt_financing_pct']:.1f}%)")
        print(f"     - Equity: ${sources['new_equity_issuance']/1e9:.1f}B ({sources['new_equity_issuance_pct']:.1f}%)")
        print(f"   Pro Forma:")
        print(f"     - Total Debt: ${pf_cap['pro_forma_total_debt']/1e9:.1f}B")
        print(f"     - Debt/EBITDA: {pf_cap['pro_forma_debt_to_ebitda']:.2f}x")
        print()
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['sources_uses'] = {'error': str(e)}
    
    # Test 3: Contribution Analysis
    print("3️⃣  CONTRIBUTION ANALYSIS")
    print("-"*80)
    try:
        analyzer = ContributionAnalyzer()
        contrib_result = analyzer.analyze(
            acquirer_data,
            target_data,
            deal_terms
        )
        results['contribution'] = contrib_result
        
        financial = contrib_result['financial_contribution']
        ownership = contrib_result['ownership_split']
        fairness = contrib_result['fairness_analysis']
        
        weighted = financial['weighted_average_contribution']
        print(f"✅ Financial Contribution:")
        print(f"   Acquirer: {weighted['acquirer_pct']:.1f}%")
        print(f"   Target: {weighted['target_pct']:.1f}%")
        print(f"   Ownership Split:")
        print(f"   Acquirer Shareholders: {ownership['acquirer_ownership_pct']:.1f}%")
        print(f"   Target Shareholders: {ownership['target_ownership_pct']:.1f}%")
        print(f"   Fairness: {fairness['fairness_rating']}")
        print(f"   Delta: {fairness['fairness_delta_percentage_points']:+.1f} percentage points")
        print()
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['contribution'] = {'error': str(e)}
    
    # Test 4: Exchange Ratio Analysis
    print("4️⃣  EXCHANGE RATIO ANALYSIS")
    print("-"*80)
    try:
        analyzer = ExchangeRatioAnalyzer()
        
        # Create minimal valuation data
        valuation_data = {
            'dcf_advanced': {
                'dcf_analysis': {
                    'base': {
                        'enterprise_value': deal_terms['purchase_price']
                    }
                }
            }
        }
        
        # Calculate exchange ratio from deal terms
        target_price_with_premium = target_data['current_stock_price'] * (1 + deal_terms.get('premium_percent', 0.30))
        deal_terms['exchange_ratio'] = target_price_with_premium / acquirer_data['current_stock_price']
        
        er_result = analyzer.analyze(
            acquirer_data,
            target_data,
            deal_terms,
            valuation_data
        )
        results['exchange_ratio'] = er_result
        
        proposed = er_result['proposed_ratio']
        premium = er_result['premium_analysis']
        fairness = er_result['fairness_assessment']
        
        print(f"✅ Exchange Ratio: {proposed['proposed_exchange_ratio']:.4f}x")
        print(f"   ({proposed['proposed_exchange_ratio']:.4f} {acquirer_symbol} shares per {target_symbol} share)")
        print(f"   Implied Price: ${proposed['implied_price_per_target_share']:.2f}")
        print(f"   Current Price: ${target_data['current_stock_price']:.2f}")
        print(f"   Premium to Current: {premium['premium_to_current_pct']:+.1f}%")
        print(f"   Premium to 30-Day Avg: {premium['premium_to_30day_pct']:+.1f}%")
        print(f"   Fairness Assessment: {fairness['overall_rating']}")
        print()
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['exchange_ratio'] = {'error': str(e)}
    
    # Summary
    print("="*80)
    print("📋 ANALYSIS SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if 'error' not in r)
    total = len(results)
    
    print(f"\nComponents Tested: {passed}/{total} successful\n")
    
    if 'error' not in results.get('accretion_dilution', {}):
        ad = results['accretion_dilution']
        print(f"💰 DEAL IMPACT: {ad['impact_type']} {ad['eps_impact_percent']:+.1f}%")
    
    if 'error' not in results.get('sources_uses', {}):
        su = results['sources_uses']
        pf = su['pro_forma_capitalization']
        print(f"💵 FINANCING: ${su['uses_of_funds']['total_uses']/1e9:.1f}B deal, {pf['pro_forma_debt_to_ebitda']:.2f}x leverage")
    
    if 'error' not in results.get('contribution', {}):
        contrib = results['contribution']
        fairness = contrib['fairness_analysis']
        print(f"📊 FAIRNESS: {fairness['fairness_rating']}")
    
    if 'error' not in results.get('exchange_ratio', {}):
        er = results['exchange_ratio']
        premium = er['premium_analysis']
        print(f"🔄 PREMIUM: {premium['premium_to_current_pct']:+.1f}%")
    
    print()
    print("="*80)
    print(f"Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return results


async def main():
    """Run real data test with actual companies"""
    
    # Example: Microsoft acquiring a mid-cap software company
    # For testing, we'll use MSFT as acquirer and CRM (Salesforce) as hypothetical target
    
    acquirer_symbol = "MSFT"  # Large cap acquirer
    target_symbol = "SNOW"    # Mid-cap target (Snowflake)
    
    # Deal terms
    deal_terms = {
        'purchase_price': 0,  # Will calculate based on market cap + premium
        'cash_percentage': 0.4,  # 40% cash, 60% stock
        'debt_interest_rate': 0.045,  # 4.5% interest rate
        'tax_rate': 0.21,
        'synergies_year1': 500000000,  # $500M year 1 synergies
        'premium_percent': 0.35,  # 35% premium to current price
        'refinance_target_debt': True
    }
    
    results = await run_real_data_test(acquirer_symbol, target_symbol, deal_terms)
    
    # Save results
    if results:
        import json
        output_file = f"ma_real_data_test_{acquirer_symbol}_{target_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Simplify for JSON
        json_results = {}
        for key, value in results.items():
            if 'error' not in value:
                json_results[key] = {
                    'status': 'SUCCESS',
                    'summary': str(value.get('summary', 'Analysis complete'))[:500]
                }
            else:
                json_results[key] = value
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
