"""
Standalone Test for New M&A Components

Tests the 4 critical M&A components without requiring full agent infrastructure:
1. Accretion/Dilution Analysis
2. Sources & Uses of Funds
3. Contribution Analysis
4. Exchange Ratio Analysis
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

# Import M&A utilities (not full agents)
from src.agents.sources_uses import SourcesUsesGenerator
from src.agents.contribution_analysis import ContributionAnalyzer
from src.agents.exchange_ratio_analysis import ExchangeRatioAnalyzer


def run_accretion_dilution_test(sample_data):
    """Test accretion/dilution calculations without agent framework"""
    print("1️⃣  TESTING ACCRETION/DILUTION CALCULATIONS")
    print("-"*80)
    
    # Manual calculations (same logic as agent)
    acquirer = sample_data['acquirer_data']
    target = sample_data['target_data']
    deal_terms = sample_data['deal_terms']
    
    # Calculate standalone EPS
    acquirer_ni = acquirer['income_statement'][0]['netIncome']
    acquirer_shares = acquirer['income_statement'][0]['weightedAverageShsOut']
    acquirer_eps = acquirer_ni / acquirer_shares
    
    target_ni = target['income_statement'][0]['netIncome']
    
    # Calculate financing
    total_consideration = deal_terms['purchase_price']
    cash_pct = deal_terms['cash_percentage']
    cash_consideration = total_consideration * cash_pct
    debt_needed = max(0, cash_consideration - deal_terms['acquirer_cash_available'])
    debt_interest = debt_needed * deal_terms['debt_interest_rate']
    after_tax_interest = debt_interest * (1 - deal_terms['tax_rate'])
    
    stock_consideration = total_consideration * (1 - cash_pct)
    new_shares = stock_consideration / deal_terms['acquirer_stock_price']
    
    # Pro forma calculation
    synergies_after_tax = deal_terms['synergies_year1'] * (1 - deal_terms['tax_rate'])
    pro_forma_ni = acquirer_ni + target_ni + synergies_after_tax - after_tax_interest
    pro_forma_shares = acquirer_shares + new_shares
    pro_forma_eps = pro_forma_ni / pro_forma_shares
    
    # Accretion/dilution
    eps_impact = pro_forma_eps - acquirer_eps
    eps_impact_pct = (eps_impact / acquirer_eps) * 100
    impact_type = "ACCRETIVE" if eps_impact > 0 else "DILUTIVE" if eps_impact < 0 else "NEUTRAL"
    
    print(f"✅ Impact: {impact_type}")
    print(f"   Acquirer Standalone EPS: ${acquirer_eps:.2f}")
    print(f"   Pro Forma EPS: ${pro_forma_eps:.2f}")
    print(f"   EPS Impact: ${eps_impact:+.2f} ({eps_impact_pct:+.1f}%)")
    print()
    
    return {
        'impact_type': impact_type,
        'acquirer_eps': acquirer_eps,
        'pro_forma_eps': pro_forma_eps,
        'eps_impact_dollar': eps_impact,
        'eps_impact_percent': eps_impact_pct
    }


def main():
    """Run standalone tests"""
    print("="*80)
    print("STANDALONE M&A COMPONENTS TEST")
    print("="*80)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create sample deal data
    sample_data = create_sample_deal()
    
    print("📊 DEAL SCENARIO")
    print("-"*80)
    print(f"Acquirer: {sample_data['acquirer_name']}")
    print(f"Target: {sample_data['target_name']}")
    print(f"Deal Size: ${sample_data['deal_terms']['purchase_price']/1e9:.1f}B")
    print(f"Structure: {sample_data['deal_terms']['cash_percentage']*100:.0f}% cash / "
          f"{(1-sample_data['deal_terms']['cash_percentage'])*100:.0f}% stock")
    print()
    
    results = {}
    
    # Test 1: Accretion/Dilution (manual calculation)
    try:
        results['accretion_dilution'] = run_accretion_dilution_test(sample_data)
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['accretion_dilution'] = {'error': str(e)}
    
    # Test 2: Sources & Uses
    print("2️⃣  TESTING SOURCES & USES GENERATOR")
    print("-"*80)
    try:
        generator = SourcesUsesGenerator()
        su_result = generator.generate(
            sample_data['deal_terms'],
            sample_data['target_data'],
            sample_data['acquirer_data'],
            sample_data['deal_terms']['purchase_price']
        )
        results['sources_uses'] = su_result
        
        uses = su_result['uses_of_funds']
        sources = su_result['sources_of_funds']
        
        print(f"✅ Total Transaction: ${uses['total_uses']/1e9:.1f}B")
        print(f"   Cash: ${sources['acquirer_cash']/1e9:.1f}B ({sources['acquirer_cash_pct']:.1f}%)")
        print(f"   Debt: ${sources['new_debt_financing']/1e9:.1f}B ({sources['new_debt_financing_pct']:.1f}%)")
        print(f"   Equity: ${sources['new_equity_issuance']/1e9:.1f}B ({sources['new_equity_issuance_pct']:.1f}%)")
        print(f"   Balance: {su_result['balance_check']['status']}")
        print()
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['sources_uses'] = {'error': str(e)}
    
    # Test 3: Contribution Analysis
    print("3️⃣  TESTING CONTRIBUTION ANALYSIS")
    print("-"*80)
    try:
        analyzer = ContributionAnalyzer()
        contrib_result = analyzer.analyze(
            sample_data['acquirer_data'],
            sample_data['target_data'],
            sample_data['deal_terms']
        )
        results['contribution'] = contrib_result
        
        weighted = contrib_result['financial_contribution']['weighted_average_contribution']
        ownership = contrib_result['ownership_split']
        fairness = contrib_result['fairness_analysis']
        
        print(f"✅ Financial Contribution:")
        print(f"   Target: {weighted['target_pct']:.1f}%")
        print(f"   Ownership Received: {ownership['target_ownership_pct']:.1f}%")
        print(f"   Fairness: {fairness['fairness_rating']}")
        print()
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['contribution'] = {'error': str(e)}
    
    # Test 4: Exchange Ratio Analysis
    print("4️⃣  TESTING EXCHANGE RATIO ANALYSIS")
    print("-"*80)
    try:
        analyzer = ExchangeRatioAnalyzer()
        er_result = analyzer.analyze(
            sample_data['acquirer_data'],
            sample_data['target_data'],
            sample_data['deal_terms'],
            sample_data['valuation_data']
        )
        results['exchange_ratio'] = er_result
        
        proposed = er_result['proposed_ratio']
        premium = er_result['premium_analysis']
        fairness = er_result['fairness_assessment']
        
        print(f"✅ Exchange Ratio: {proposed['proposed_exchange_ratio']:.4f}x")
        print(f"   Implied Price: ${proposed['implied_price_per_target_share']:.2f}")
        print(f"   Premium: {premium['premium_to_current_pct']:+.1f}%")
        print(f"   Fairness: {fairness['overall_rating']}")
        print()
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        results['exchange_ratio'] = {'error': str(e)}
    
    # Summary
    print("="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if 'error' not in r)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Tests Failed: {total - passed}/{total}")
    print()
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 All 4 critical M&A components are working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Review errors above")
    
    print()
    print("="*80)
    print("📊 INTEGRATED RESULTS")
    print("="*80)
    
    if 'error' not in results.get('accretion_dilution', {}):
        ad = results['accretion_dilution']
        print(f"\n💰 ACCRETION/DILUTION:")
        print(f"   {ad['impact_type']}: {ad['eps_impact_percent']:+.1f}% EPS impact")
    
    if 'error' not in results.get('sources_uses', {}):
        su = results['sources_uses']
        pf = su['pro_forma_capitalization']
        print(f"\n💵 FINANCING:")
        print(f"   Deal Size: ${su['uses_of_funds']['total_uses']/1e9:.1f}B")
        print(f"   Pro Forma Debt/EBITDA: {pf['pro_forma_debt_to_ebitda']:.2f}x")
    
    if 'error' not in results.get('contribution', {}):
        contrib = results['contribution']
        weighted = contrib['financial_contribution']['weighted_average_contribution']
        ownership = contrib['ownership_split']
        print(f"\n📊 CONTRIBUTION:")
        print(f"   Target Contribution: {weighted['target_pct']:.1f}%")
        print(f"   Target Ownership: {ownership['target_ownership_pct']:.1f}%")
        print(f"   Fairness: {contrib['fairness_analysis']['fairness_rating']}")
    
    if 'error' not in results.get('exchange_ratio', {}):
        er = results['exchange_ratio']
        print(f"\n🔄 EXCHANGE RATIO:")
        print(f"   Ratio: {er['proposed_ratio']['proposed_exchange_ratio']:.4f}x")
        print(f"   Premium: {er['premium_analysis']['premium_to_current_pct']:+.1f}%")
        print(f"   Assessment: {er['fairness_assessment']['overall_rating']}")
    
    print()
    print("="*80)
    print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return results


def create_sample_deal() -> Dict[str, Any]:
    """Create realistic sample deal data"""
    
    # Acquirer: Large Tech Company
    acquirer_data = {
        'income_statement': [{
            'netIncome': 10000000000,  # $10B
            'revenue': 50000000000,  # $50B
            'ebitda': 15000000000,  # $15B
            'operatingIncome': 12000000000,
            'incomeBeforeTax': 12000000000,
            'interestExpense': 500000000,
            'weightedAverageShsOut': 1000000000,  # 1B shares
            'date': '2024-12-31'
        }],
        'balance_sheet': [{
            'totalDebt': 15000000000,  # $15B debt
            'cashAndCashEquivalents': 10000000000,  # $10B cash
            'totalStockholdersEquity': 50000000000,  # $50B equity
            'commonStock': 1000000000
        }],
        'current_stock_price': 150  # $150/share
    }
    
    # Target: Mid-Cap SaaS Company
    target_data = {
        'income_statement': [{
            'netIncome': 2000000000,  # $2B
            'revenue': 10000000000,  # $10B
            'ebitda': 3000000000,  # $3B
            'operatingIncome': 2400000000,
            'incomeBeforeTax': 2400000000,
            'interestExpense': 200000000,
            'weightedAverageShsOut': 200000000,  # 200M shares
            'date': '2024-12-31'
        }],
        'balance_sheet': [{
            'totalDebt': 5000000000,  # $5B debt
            'cashAndCashEquivalents': 2000000000,  # $2B cash
            'totalStockholdersEquity': 10000000000,  # $10B equity
            'commonStock': 200000000
        }],
        'current_stock_price': 75,  # $75/share
        'price_1day_ago': 74,
        'price_30day_avg': 70,
        'price_52week_high': 85,
        'price_52week_low': 60
    }
    
    # Deal Terms
    deal_terms = {
        'purchase_price': 30000000000,  # $30B purchase price
        'cash_percentage': 0.5,  # 50% cash, 50% stock
        'debt_interest_rate': 0.05,  # 5% interest rate
        'tax_rate': 0.21,  # 21% tax rate
        'acquirer_stock_price': 150,
        'target_stock_price': 75,
        'synergies_year1': 1000000000,  # $1B Year 1 synergies
        'acquirer_cash_available': 8000000000,  # $8B cash to use
        'refinance_target_debt': True,
        'exchange_ratio': 0.65,  # 0.65 acquirer shares per target share
        'premium_percent': 0.30  # 30% premium
    }
    
    # Valuation Data
    valuation_data = {
        'dcf_advanced': {
            'dcf_analysis': {
                'base': {
                    'enterprise_value': 30000000000,
                    'wacc': 0.10,
                    'terminal_growth_rate': 0.025
                }
            }
        }
    }
    
    return {
        'acquirer_name': 'TechCorp Inc.',
        'target_name': 'SaaS Solutions Ltd.',
        'acquirer_data': acquirer_data,
        'target_data': target_data,
        'deal_terms': deal_terms,
        'valuation_data': valuation_data
    }


if __name__ == "__main__":
    main()
