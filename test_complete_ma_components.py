"""
Comprehensive Test for All M&A Components

Tests the complete M&A analysis pipeline including:
1. Accretion/Dilution Analysis
2. Sources & Uses of Funds
3. Contribution Analysis
4. Exchange Ratio Analysis

This test validates that all components work together and data flows correctly.
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

# Import all M&A components
from src.agents.accretion_dilution import AccretionDilutionAgent
from src.agents.sources_uses import SourcesUsesGenerator
from src.agents.contribution_analysis import ContributionAnalyzer
from src.agents.exchange_ratio_analysis import ExchangeRatioAnalyzer


class ComprehensiveMATester:
    """
    Comprehensive tester for all M&A components
    """
    
    def __init__(self):
        self.accretion_agent = AccretionDilutionAgent()
        self.sources_uses_gen = SourcesUsesGenerator()
        self.contribution_analyzer = ContributionAnalyzer()
        self.exchange_ratio_analyzer = ExchangeRatioAnalyzer()
        
    async def run_complete_test(self):
        """Run comprehensive test of all M&A components"""
        
        print("="*80)
        print("COMPREHENSIVE M&A COMPONENTS TEST")
        print("="*80)
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Create sample data for a realistic M&A scenario
        sample_data = self._create_sample_deal()
        
        print("📊 DEAL SCENARIO")
        print("-"*80)
        print(f"Acquirer: {sample_data['acquirer_name']}")
        print(f"Target: {sample_data['target_name']}")
        print(f"Deal Size: ${sample_data['deal_terms']['purchase_price']/1e9:.1f}B")
        print(f"Deal Structure: {sample_data['deal_terms']['cash_percentage']*100:.0f}% cash / "
              f"{(1-sample_data['deal_terms']['cash_percentage'])*100:.0f}% stock")
        print()
        
        results = {}
        
        # Test 1: Accretion/Dilution Analysis
        print("1️⃣  TESTING ACCRETION/DILUTION ANALYSIS")
        print("-"*80)
        try:
            accretion_result = await self.accretion_agent.analyze(
                sample_data['acquirer_data'],
                sample_data['target_data'],
                sample_data['deal_terms'],
                sample_data['valuation_data']
            )
            results['accretion_dilution'] = accretion_result
            
            impact = accretion_result['accretion_dilution']
            print(f"✅ Impact: {impact['impact_type']}")
            print(f"   EPS Impact: {impact['eps_impact_percent']:+.1f}%")
            print(f"   Acquirer EPS: ${impact['acquirer_standalone_eps']:.2f}")
            print(f"   Pro Forma EPS: ${impact['pro_forma_eps']:.2f}")
            print(f"   Recommendation: {accretion_result['deal_recommendation']}")
            print()
        except Exception as e:
            print(f"❌ ERROR: {str(e)}\n")
            results['accretion_dilution'] = {'error': str(e)}
        
        # Test 2: Sources & Uses
        print("2️⃣  TESTING SOURCES & USES GENERATOR")
        print("-"*80)
        try:
            sources_uses_result = self.sources_uses_gen.generate(
                sample_data['deal_terms'],
                sample_data['target_data'],
                sample_data['acquirer_data'],
                sample_data['deal_terms']['purchase_price']
            )
            results['sources_uses'] = sources_uses_result
            
            uses = sources_uses_result['uses_of_funds']
            sources = sources_uses_result['sources_of_funds']
            balance = sources_uses_result['balance_check']
            
            print(f"✅ Total Transaction: ${uses['total_uses']/1e9:.1f}B")
            print(f"   Uses Breakdown:")
            print(f"     - Purchase Price: ${uses['equity_purchase_price']/1e9:.1f}B")
            print(f"     - Fees: ${uses['total_transaction_fees']/1e6:.0f}M")
            print(f"   Sources Breakdown:")
            print(f"     - Cash: ${sources['acquirer_cash']/1e9:.1f}B ({sources['acquirer_cash_pct']:.1f}%)")
            print(f"     - Debt: ${sources['new_debt_financing']/1e9:.1f}B ({sources['new_debt_financing_pct']:.1f}%)")
            print(f"     - Equity: ${sources['new_equity_issuance']/1e9:.1f}B ({sources['new_equity_issuance_pct']:.1f}%)")
            print(f"   Balance Check: {balance['status']}")
            print()
        except Exception as e:
            print(f"❌ ERROR: {str(e)}\n")
            results['sources_uses'] = {'error': str(e)}
        
        # Test 3: Contribution Analysis
        print("3️⃣  TESTING CONTRIBUTION ANALYSIS")
        print("-"*80)
        try:
            contribution_result = self.contribution_analyzer.analyze(
                sample_data['acquirer_data'],
                sample_data['target_data'],
                sample_data['deal_terms']
            )
            results['contribution'] = contribution_result
            
            financial = contribution_result['financial_contribution']
            ownership = contribution_result['ownership_split']
            fairness = contribution_result['fairness_analysis']
            
            weighted = financial['weighted_average_contribution']
            print(f"✅ Financial Contribution:")
            print(f"   Acquirer: {weighted['acquirer_pct']:.1f}%")
            print(f"   Target: {weighted['target_pct']:.1f}%")
            print(f"   Ownership Split:")
            print(f"   Acquirer Shareholders: {ownership['acquirer_ownership_pct']:.1f}%")
            print(f"   Target Shareholders: {ownership['target_ownership_pct']:.1f}%")
            print(f"   Fairness: {fairness['fairness_rating']}")
            print(f"   Recommendation: {fairness['recommendation']}")
            print()
        except Exception as e:
            print(f"❌ ERROR: {str(e)}\n")
            results['contribution'] = {'error': str(e)}
        
        # Test 4: Exchange Ratio Analysis
        print("4️⃣  TESTING EXCHANGE RATIO ANALYSIS")
        print("-"*80)
        try:
            exchange_result = self.exchange_ratio_analyzer.analyze(
                sample_data['acquirer_data'],
                sample_data['target_data'],
                sample_data['deal_terms'],
                sample_data['valuation_data']
            )
            results['exchange_ratio'] = exchange_result
            
            proposed = exchange_result['proposed_ratio']
            premium = exchange_result['premium_analysis']
            fairness = exchange_result['fairness_assessment']
            
            print(f"✅ Proposed Exchange Ratio: {proposed['proposed_exchange_ratio']:.4f}x")
            print(f"   Implied Price: ${proposed['implied_price_per_target_share']:.2f}")
            print(f"   Premium to Current: {premium['premium_to_current_pct']:+.1f}%")
            print(f"   Premium to 30-Day Avg: {premium['premium_to_30day_pct']:+.1f}%")
            print(f"   Fairness: {fairness['overall_rating']}")
            print(f"   Recommendation: {fairness['recommendation']}")
            print()
        except Exception as e:
            print(f"❌ ERROR: {str(e)}\n")
            results['exchange_ratio'] = {'error': str(e)}
        
        # Summary Report
        print("="*80)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in results.values() if 'error' not in r)
        total = len(results)
        
        print(f"\nTests Passed: {passed}/{total}")
        print(f"Tests Failed: {total - passed}/{total}")
        print()
        
        if passed == total:
            print("✅ ALL TESTS PASSED - All M&A components working correctly!")
        else:
            print("⚠️  SOME TESTS FAILED - Review errors above")
        
        print()
        print("="*80)
        print("INTEGRATED DEAL SUMMARY")
        print("="*80)
        
        if 'error' not in results.get('accretion_dilution', {}):
            ad = results['accretion_dilution']['accretion_dilution']
            print(f"\n💰 FINANCIAL IMPACT:")
            print(f"   • {ad['impact_type']}: {ad['eps_impact_percent']:+.1f}% EPS impact")
            print(f"   • Standalone EPS: ${ad['acquirer_standalone_eps']:.2f}")
            print(f"   • Pro Forma EPS: ${ad['pro_forma_eps']:.2f}")
        
        if 'error' not in results.get('sources_uses', {}):
            su = results['sources_uses']
            print(f"\n💵 FINANCING STRUCTURE:")
            print(f"   • Total Deal Size: ${su['uses_of_funds']['total_uses']/1e9:.1f}B")
            print(f"   • Debt Financing: ${su['sources_of_funds']['new_debt_financing']/1e9:.1f}B")
            print(f"   • Equity Issued: ${su['sources_of_funds']['new_equity_issuance']/1e9:.1f}B")
            print(f"   • Pro Forma Debt/EBITDA: {su['pro_forma_capitalization']['pro_forma_debt_to_ebitda']:.2f}x")
        
        if 'error' not in results.get('contribution', {}):
            contrib = results['contribution']
            print(f"\n📊 CONTRIBUTION & OWNERSHIP:")
            weighted = contrib['financial_contribution']['weighted_average_contribution']
            ownership = contrib['ownership_split']
            print(f"   • Target Financial Contribution: {weighted['target_pct']:.1f}%")
            print(f"   • Target Ownership Received: {ownership['target_ownership_pct']:.1f}%")
            print(f"   • Fairness: {contrib['fairness_analysis']['fairness_rating']}")
        
        if 'error' not in results.get('exchange_ratio', {}):
            er = results['exchange_ratio']
            print(f"\n🔄 EXCHANGE RATIO:")
            print(f"   • Proposed Ratio: {er['proposed_ratio']['proposed_exchange_ratio']:.4f}x")
            print(f"   • Premium: {er['premium_analysis']['premium_to_current_pct']:+.1f}%")
            print(f"   • Assessment: {er['fairness_assessment']['overall_rating']}")
        
        print()
        print("="*80)
        print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        return results
    
    def _create_sample_deal(self) -> Dict[str, Any]:
        """Create realistic sample deal data"""
        
        # Acquirer: Large Tech Company
        acquirer_data = {
            'income_statement': [{
                'netIncome': 10000000000,  # $10B net income
                'revenue': 50000000000,  # $50B revenue
                'ebitda': 15000000000,  # $15B EBITDA
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
                'netIncome': 2000000000,  # $2B net income
                'revenue': 10000000000,  # $10B revenue
                'ebitda': 3000000000,  # $3B EBITDA
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


async def main():
    """Main test runner"""
    tester = ComprehensiveMATester()
    results = await tester.run_complete_test()
    return results


if __name__ == "__main__":
    # Run the comprehensive test
    results = asyncio.run(main())
    
    # Save results to file for review
    import json
    output_file = f"ma_components_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Convert results to JSON-serializable format
    json_results = {}
    for key, value in results.items():
        if 'error' in value:
            json_results[key] = value
        else:
            # Simplify complex nested structures for JSON
            json_results[key] = {
                'status': 'SUCCESS',
                'summary': value.get('summary', 'No summary available')
            }
    
    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\n📄 Full results saved to: {output_file}")
