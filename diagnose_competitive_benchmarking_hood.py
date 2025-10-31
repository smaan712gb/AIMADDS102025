"""
Diagnostic Script for Competitive Benchmarking Agent - HOOD Analysis
Identifies root cause of "Gross Margin (Bottom 25%)" false negative
"""
import asyncio
import json
from datetime import datetime
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)


async def diagnose_competitive_benchmarking():
    """Run diagnostic on competitive benchmarking agent for HOOD"""
    
    print("\n" + "="*80)
    print("COMPETITIVE BENCHMARKING DIAGNOSTIC - HOOD")
    print("="*80 + "\n")
    
    from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent
    from src.integrations.fmp_client import FMPClient
    
    ticker = "HOOD"
    
    # Step 1: Get HOOD's actual financial data
    print(f"\n[STEP 1] Fetching HOOD's actual financial metrics...")
    async with FMPClient() as client:
        income_stmt = await client.get_income_statement(ticker, period='annual', limit=3)
        ratios = await client.get_financial_ratios(ticker, period='annual', limit=3)
        profile = await client.get_company_profile(ticker)
    
    if not income_stmt or not ratios or not profile:
        print(f"❌ ERROR: Could not fetch HOOD financial data")
        return
    
    latest_income = income_stmt[0]
    latest_ratios = ratios[0]
    
    # Extract HOOD metrics
    hood_revenue = latest_income.get('revenue', 0)
    hood_gross_profit = latest_income.get('grossProfit', 0)
    hood_gross_margin = latest_ratios.get('grossProfitMargin', 0) * 100
    hood_operating_margin = latest_ratios.get('operatingProfitMargin', 0) * 100
    hood_net_margin = latest_ratios.get('netProfitMargin', 0) * 100
    
    print(f"\n✓ HOOD Financial Metrics:")
    print(f"  Revenue: ${hood_revenue/1e9:.2f}B")
    print(f"  Gross Profit: ${hood_gross_profit/1e9:.2f}B")
    print(f"  Gross Margin: {hood_gross_margin:.1f}%")
    print(f"  Operating Margin: {hood_operating_margin:.1f}%")
    print(f"  Net Margin: {hood_net_margin:.1f}%")
    print(f"  Sector: {profile.get('sector', 'Unknown')}")
    print(f"  Industry: {profile.get('industry', 'Unknown')}")
    
    # Step 2: Initialize agent and identify peers
    print(f"\n[STEP 2] Identifying peer companies...")
    agent = CompetitiveBenchmarkingAgent()
    peers = await agent._identify_peers(ticker)
    
    if not peers:
        print(f"❌ CRITICAL: NO PEERS FOUND for {ticker}")
        print(f"   This explains the competitive benchmarking failure!")
        print(f"   Without peers, percentile calculations are invalid.")
        return
    
    print(f"\n✓ Found {len(peers)} peers: {', '.join(peers)}")
    
    # Step 3: Analyze peer metrics
    print(f"\n[STEP 3] Analyzing peer metrics in parallel...")
    peer_metrics = await agent._analyze_peers_parallel(peers)
    
    if not peer_metrics:
        print(f"❌ CRITICAL: NO PEER METRICS COLLECTED")
        print(f"   This would cause all percentile calculations to fail!")
        return
    
    print(f"\n✓ Collected metrics for {len(peer_metrics)} peers")
    
    # Step 4: Examine gross margin data specifically
    print(f"\n[STEP 4] Examining gross margin data...")
    print(f"\n{'Ticker':<10} {'Gross Margin':<15} {'Operating Margin':<18} {'Net Margin':<12}")
    print("-" * 60)
    
    peer_gross_margins = []
    peer_operating_margins = []
    
    for peer_ticker, metrics in peer_metrics.items():
        peer_gross = metrics.get('gross_margin', 0)
        peer_operating = metrics.get('operating_margin', 0)
        peer_net = metrics.get('net_margin', 0)
        
        print(f"{peer_ticker:<10} {peer_gross:>13.1f}%  {peer_operating:>16.1f}%  {peer_net:>10.1f}%")
        
        peer_gross_margins.append(peer_gross)
        peer_operating_margins.append(peer_operating)
    
    print("-" * 60)
    print(f"{'HOOD':<10} {hood_gross_margin:>13.1f}%  {hood_operating_margin:>16.1f}%  {hood_net_margin:>10.1f}%")
    print("-" * 60)
    
    # Step 5: Calculate percentiles MANUALLY to verify
    print(f"\n[STEP 5] Calculating percentiles manually...")
    
    # Calculate gross margin percentile
    gross_margins_all = peer_gross_margins + [hood_gross_margin]
    hood_gross_below_count = sum(1 for gm in peer_gross_margins if gm < hood_gross_margin)
    hood_gross_percentile = (hood_gross_below_count / len(peer_gross_margins)) * 100 if peer_gross_margins else 50
    
    # Calculate operating margin percentile  
    operating_margins_all = peer_operating_margins + [hood_operating_margin]
    hood_op_below_count = sum(1 for om in peer_operating_margins if om < hood_operating_margin)
    hood_op_percentile = (hood_op_below_count / len(peer_operating_margins)) * 100 if peer_operating_margins else 50
    
    print(f"\n📊 PERCENTILE CALCULATIONS:")
    print(f"  Gross Margin:")
    print(f"    HOOD: {hood_gross_margin:.1f}%")
    print(f"    Peers below HOOD: {hood_gross_below_count}/{len(peer_gross_margins)}")
    print(f"    Percentile: {hood_gross_percentile:.1f}th")
    print(f"    Classification: {'TOP 25%' if hood_gross_percentile >= 75 else 'BOTTOM 25%' if hood_gross_percentile <= 25 else 'MIDDLE 50%'}")
    
    print(f"\n  Operating Margin:")
    print(f"    HOOD: {hood_operating_margin:.1f}%")
    print(f"    Peers below HOOD: {hood_op_below_count}/{len(peer_operating_margins)}")
    print(f"    Percentile: {hood_op_percentile:.1f}th")
    print(f"    Classification: {'TOP 25%' if hood_op_percentile >= 75 else 'BOTTOM 25%' if hood_op_percentile <= 25 else 'MIDDLE 50%'}")
    
    # Step 6: Check agent's actual calculation
    print(f"\n[STEP 6] Testing agent's percentile calculation method...")
    
    # Call the agent's internal percentile calculation
    calculated_gross_percentile = agent._calculate_percentile(hood_gross_margin, peer_gross_margins)
    calculated_op_percentile = agent._calculate_percentile(hood_operating_margin, peer_operating_margins)
    
    print(f"\n  Agent's _calculate_percentile() results:")
    print(f"    Gross Margin: {calculated_gross_percentile:.1f}th percentile")
    print(f"    Operating Margin: {calculated_op_percentile:.1f}th percentile")
    
    # Step 7: Identify discrepancies
    print(f"\n[STEP 7] Checking for discrepancies...")
    
    discrepancies_found = False
    
    if abs(hood_gross_percentile - calculated_gross_percentile) > 1:
        print(f"  ⚠️ DISCREPANCY: Manual calculation ({hood_gross_percentile:.1f}) != Agent calculation ({calculated_gross_percentile:.1f})")
        discrepancies_found = True
    else:
        print(f"  ✓ Gross margin percentile matches: {hood_gross_percentile:.1f}th")
    
    if abs(hood_op_percentile - calculated_op_percentile) > 1:
        print(f"  ⚠️ DISCREPANCY: Manual calculation ({hood_op_percentile:.1f}) != Agent calculation ({calculated_op_percentile:.1f})")
        discrepancies_found = True
    else:
        print(f"  ✓ Operating margin percentile matches: {hood_op_percentile:.1f}th")
    
    # Step 8: Test the classification logic
    print(f"\n[STEP 8] Testing classification logic...")
    
    target_metrics = {
        'revenue': hood_revenue,
        'gross_margin': hood_gross_margin,
        'operating_margin': hood_operating_margin,
        'net_margin': hood_net_margin,
    }
    
    # Create metric comparisons like the agent does
    metric_comparisons = {
        'gross_margin': {
            'target': hood_gross_margin,
            'peer_average': sum(peer_gross_margins) / len(peer_gross_margins) if peer_gross_margins else 0,
            'percentile': calculated_gross_percentile,
        },
        'operating_margin': {
            'target': hood_operating_margin,
            'peer_average': sum(peer_operating_margins) / len(peer_operating_margins) if peer_operating_margins else 0,
            'percentile': calculated_op_percentile,
        }
    }
    
    # Test the _assess_competitive_position method
    competitive_position = agent._assess_competitive_position(metric_comparisons, peer_metrics)
    
    print(f"\n  Agent's _assess_competitive_position() results:")
    print(f"    Overall Rating: {competitive_position.get('overall_rating', 'Unknown')}")
    print(f"    Strengths: {competitive_position.get('strengths', [])}")
    print(f"    Weaknesses: {competitive_position.get('weaknesses', [])}")
    
    # Step 9: ROOT CAUSE ANALYSIS
    print(f"\n" + "="*80)
    print("ROOT CAUSE ANALYSIS")
    print("="*80)
    
    # Check if gross margin is in strengths (it should be)
    gross_in_strengths = any('gross margin' in s.lower() for s in competitive_position.get('strengths', []))
    gross_in_weaknesses = any('gross margin' in w.lower() for w in competitive_position.get('weaknesses', []))
    
    if gross_in_weaknesses and not gross_in_strengths:
        print(f"\n🔴 ROOT CAUSE CONFIRMED:")
        print(f"   Gross Margin ({hood_gross_margin:.1f}%) is in WEAKNESSES")
        print(f"   Percentile: {calculated_gross_percentile:.1f}th (should trigger STRENGTH if ≥75th)")
        print(f"\n   Possible causes:")
        print(f"   1. Percentile threshold logic is still inverted in code")
        print(f"   2. Peer data quality is poor (margins are wrong)")
        print(f"   3. Percentile calculation has a bug")
        
        # Check peer data quality
        print(f"\n   Checking peer data quality:")
        valid_peer_count = sum(1 for gm in peer_gross_margins if gm > 0)
        print(f"     Peers with valid gross margin data: {valid_peer_count}/{len(peer_gross_margins)}")
        
        if valid_peer_count < 3:
            print(f"     ⚠️ INSUFFICIENT PEER DATA - only {valid_peer_count} valid peers!")
            print(f"     This could cause percentile miscalculation.")
        
        # Check if peers all have very high margins (would make HOOD look bad)
        peer_avg = sum(peer_gross_margins) / len(peer_gross_margins) if peer_gross_margins else 0
        peer_max = max(peer_gross_margins) if peer_gross_margins else 0
        peer_min = min(peer_gross_margins) if peer_gross_margins else 0
        
        print(f"     Peer gross margin range: {peer_min:.1f}% - {peer_max:.1f}%")
        print(f"     Peer average: {peer_avg:.1f}%")
        print(f"     HOOD vs average: {hood_gross_margin - peer_avg:+.1f}pp")
        
        if hood_gross_margin < peer_avg:
            print(f"     ⚠️ HOOD's margin is BELOW peer average!")
            print(f"     This would correctly classify as bottom performer.")
        else:
            print(f"     ✓ HOOD's margin is ABOVE peer average by {hood_gross_margin - peer_avg:.1f}pp")
            print(f"     Should be classified as TOP performer.")
    
    elif gross_in_strengths:
        print(f"\n✅ GROSS MARGIN CORRECTLY CLASSIFIED AS STRENGTH")
        print(f"   The code fix is working!")
    else:
        print(f"\n⚠️ GROSS MARGIN NOT IN STRENGTHS OR WEAKNESSES")
        print(f"   Percentile: {calculated_gross_percentile:.1f}th (between 25th-75th)")
        print(f"   This is correct - middle 50% are neither strengths nor weaknesses")
    
    # Save diagnostic results
    diagnostic_results = {
        'timestamp': datetime.now().isoformat(),
        'ticker': ticker,
        'hood_metrics': {
            'gross_margin': hood_gross_margin,
            'operating_margin': hood_operating_margin,
            'net_margin': hood_net_margin,
        },
        'peers_analyzed': len(peer_metrics),
        'peer_list': list(peer_metrics.keys()),
        'peer_gross_margins': {
            peer: metrics.get('gross_margin', 0)
            for peer, metrics in peer_metrics.items()
        },
        'percentiles': {
            'gross_margin': calculated_gross_percentile,
            'operating_margin': calculated_op_percentile,
        },
        'classification': {
            'strengths': competitive_position.get('strengths', []),
            'weaknesses': competitive_position.get('weaknesses', []),
            'overall_rating': competitive_position.get('overall_rating', 'Unknown'),
        },
        'root_cause_identified': gross_in_weaknesses and not gross_in_strengths,
        'issue': 'Gross margin incorrectly classified as weakness' if (gross_in_weaknesses and not gross_in_strengths) else 'Classification appears correct',
    }
    
    output_file = f"competitive_benchmarking_diagnostic_HOOD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(diagnostic_results, f, indent=2)
    
    print(f"\n✓ Diagnostic results saved to: {output_file}")
    
    # Final recommendation
    print(f"\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if gross_in_weaknesses:
        print(f"\n🔴 ACTION REQUIRED:")
        print(f"   1. Review peer selection - are these truly comparable companies?")
        print(f"   2. Check if peer gross margin data is accurate")
        print(f"   3. Verify percentile threshold logic in _assess_competitive_position()")
        print(f"   4. Consider if HOOD's business model is fundamentally different from peers")
    elif not gross_in_strengths and calculated_gross_percentile >= 75:
        print(f"\n⚠️ INVESTIGATION NEEDED:")
        print(f"   Gross margin is {calculated_gross_percentile:.1f}th percentile (top 25%)")
        print(f"   But NOT listed in strengths - check threshold logic")
    else:
        print(f"\n✅ CLASSIFICATION APPEARS CORRECT")
        print(f"   If you're still seeing 'Bottom 25%' in reports, the issue may be:")
        print(f"   1. Using cached/old data from a previous run")
        print(f"   2. Report generator using different data source")
        print(f"   3. CSV export happening before agent fix was applied")
    
    print("\n")


if __name__ == "__main__":
    asyncio.run(diagnose_competitive_benchmarking())
