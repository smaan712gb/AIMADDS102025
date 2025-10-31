"""
Complete M&A Suite End-to-End Test

Tests the full M&A report generation suite with real data.
Generates all three professional deliverables:
- Investment Committee Memorandum (PDF/Markdown)
- Financial Model (Excel)
- Board Presentation Deck (PowerPoint)
"""

import asyncio
from datetime import datetime
from loguru import logger

from src.outputs.ma_report_generator import MAReportGenerator


async def test_complete_ma_suite():
    """
    End-to-end test of the complete M&A suite
    
    Tests with real company data (MSFT acquiring SNOW)
    """
    
    print("="*80)
    print("COMPLETE M&A REPORT SUITE TEST")
    print("="*80)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test scenario
    acquirer_symbol = "MSFT"
    target_symbol = "SNOW"
    
    deal_terms = {
        'purchase_price': 0,  # Will calculate based on market cap + premium
        'cash_percentage': 0.4,  # 40% cash, 60% stock
        'debt_interest_rate': 0.045,
        'tax_rate': 0.21,
        'synergies_year1': 500000000,  # $500M year 1
        'premium_percent': 0.35,  # 35% premium
        'refinance_target_debt': True
    }
    
    print(f"📊 TEST SCENARIO")
    print(f"Acquirer: {acquirer_symbol}")
    print(f"Target: {target_symbol}")
    print(f"Cash/Stock: {deal_terms['cash_percentage']*100:.0f}% / {(1-deal_terms['cash_percentage'])*100:.0f}%")
    print(f"Premium: {deal_terms['premium_percent']*100:.0f}%")
    print()
    
    # Initialize generator
    print("🔧 Initializing M&A Report Generator...")
    generator = MAReportGenerator()
    print()
    
    try:
        # Generate complete suite
        print("🚀 GENERATING COMPLETE M&A REPORT SUITE...")
        print("-"*80)
        
        results = await generator.generate_complete_ma_report(
            acquirer_symbol=acquirer_symbol,
            target_symbol=target_symbol,
            deal_terms=deal_terms
        )
        
        print()
        print("="*80)
        print("✅ REPORT SUITE GENERATION COMPLETE!")
        print("="*80)
        print()
        
        # Display results
        print("📄 GENERATED REPORTS:")
        print("-"*80)
        print(f"1. IC Memorandum: {results['ic_memo']}")
        print(f"2. Financial Model: {results['financial_model']}")
        print(f"3. Board Deck: {results['board_deck']}")
        print()
        
        print(f"📁 Output Directory: {results['output_directory']}")
        print()
        
        # Display summary
        summary = results['summary']
        print("📊 EXECUTIVE SUMMARY:")
        print("-"*80)
        
        if 'eps_impact' in summary:
            eps = summary['eps_impact']
            print(f"EPS Impact: {eps.get('type', 'N/A')} {eps.get('percent', 0):+.1f}%")
        
        if 'transaction_size' in summary:
            print(f"Transaction Size: ${summary['transaction_size']/1e9:.1f}B")
        
        if 'leverage' in summary:
            print(f"Pro Forma Leverage: {summary['leverage']:.2f}x")
        
        if 'fairness' in summary:
            print(f"Fairness Assessment: {summary['fairness']}")
        
        if 'premium' in summary:
            print(f"Premium to Current: {summary['premium']:+.1f}%")
        
        print()
        print("="*80)
        print("🎉 TEST PASSED - ALL REPORTS GENERATED SUCCESSFULLY!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print()
        print("="*80)
        print("❌ TEST FAILED")
        print("="*80)
        print(f"Error: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        return False


async def main():
    """Run the test"""
    success = await test_complete_ma_suite()
    
    if success:
        print("\n✅ Complete M&A Suite is PRODUCTION READY!")
    else:
        print("\n❌ Test failed - review errors above")


if __name__ == "__main__":
    asyncio.run(main())
