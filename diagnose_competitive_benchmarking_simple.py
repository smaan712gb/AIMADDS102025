"""
Standalone Diagnostic for Competitive Benchmarking - HOOD
Tests percentile calculation and classification logic without full agent imports
"""
import asyncio
import json
from datetime import datetime


def calculate_percentile_manual(value: float, peer_values: list) -> float:
    """
    Calculate percentile - how many peers are BELOW this value
    """
    if not peer_values or value is None:
        return 50.0
    
    peer_values = [v for v in peer_values if v is not None]
    if not peer_values:
        return 50.0
    
    # Count how many peers are BELOW this value
    below_count = sum(1 for v in peer_values if v < value)
    
    # Percentile = (count below / total) * 100
    percentile = (below_count / len(peer_values)) * 100
    
    return round(percentile, 1)


async def fetch_hood_and_peers():
    """Fetch HOOD and peer data from FMP"""
    
    print("Fetching HOOD financial data from FMP...")
    
    # We'll fetch data manually without importing the full agent
    import aiohttp
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('FMP_API_KEY')
    
    if not api_key:
        print("❌ ERROR: FMP_API_KEY not found in environment")
        return None, None
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    async with aiohttp.ClientSession() as session:
        # Get HOOD ratios
        hood_url = f"{base_url}/ratios/HOOD?apikey={api_key}&limit=1"
        async with session.get(hood_url) as resp:
            hood_ratios = await resp.json()
        
        # Get HOOD profile
        profile_url = f"{base_url}/profile/HOOD?apikey={api_key}"
        async with session.get(profile_url) as resp:
            hood_profile_data = await resp.json()
            hood_profile = hood_profile_data[0] if hood_profile_data else {}
        
        # Try to get peers from FMP
        peers_url = f"{base_url}/stock_peers?symbol=HOOD&apikey={api_key}"
        async with session.get(peers_url) as resp:
            peers_data = await resp.json()
        
        # Extract peer list
        peers = []
        if isinstance(peers_data, list) and len(peers_data) > 0:
            peers = peers_data[0].get('peersList', [])[:5]  # Top 5 peers
        
        if not peers:
            print("⚠️ No peers found from FMP, using manual list")
            peers = ['COIN', 'SOFI', 'SQ', 'AFRM']  # Known fintech peers
        
        print(f"✓ Analyzing {len(peers)} peers: {', '.join(peers)}")
        
        # Fetch peer ratios
        peer_data = {}
        for peer in peers:
            try:
                peer_url = f"{base_url}/ratios/{peer}?apikey={api_key}&limit=1"
                async with session.get(peer_url) as resp:
                    peer_ratios = await resp.json()
                    if peer_ratios and len(peer_ratios) > 0:
                        peer_data[peer] = peer_ratios[0]
                await asyncio.sleep(0.2)  # Rate limiting
            except Exception as e:
                print(f"  Error fetching {peer}: {e}")
        
        hood_latest = hood_ratios[0] if hood_ratios else {}
        
        return {
            'ticker': 'HOOD',
            'profile': hood_profile,
            'gross_margin': hood_latest.get('grossProfitMargin', 0) * 100,
            'operating_margin': hood_latest.get('operatingProfitMargin', 0) * 100,
            'net_margin': hood_latest.get('netProfitMargin', 0) * 100,
            'roe': hood_latest.get('returnOnEquity', 0) * 100,
        }, peer_data


async def main():
    print("\n" + "="*80)
    print("COMPETITIVE BENCHMARKING DIAGNOSTIC - HOOD (Standalone)")
    print("="*80 + "\n")
    
    # Fetch data
    hood_data, peer_data = await fetch_hood_and_peers()
    
    if not hood_data or not peer_data:
        print("❌ Failed to fetch data")
        return
    
    # Extract metrics
    hood_gross = hood_data['gross_margin']
    hood_operating = hood_data['operating_margin']
    hood_net = hood_data['net_margin']
    
    print(f"\n✓ HOOD Metrics:")
    print(f"  Gross Margin: {hood_gross:.1f}%")
    print(f"  Operating Margin: {hood_operating:.1f}%")
    print(f"  Net Margin: {hood_net:.1f}%")
    print(f"  Sector: {hood_data['profile'].get('sector', 'Unknown')}")
    
    # Extract peer margins
    print(f"\n{'Ticker':<10} {'Gross Margin':<15} {'Operating Margin':<18} {'Net Margin':<12}")
    print("-" * 60)
    
    peer_gross_margins = []
    peer_operating_margins = []
    peer_net_margins = []
    
    for peer_ticker, ratios in peer_data.items():
        peer_gross = ratios.get('grossProfitMargin', 0) * 100
        peer_operating = ratios.get('operatingProfitMargin', 0) * 100
        peer_net = ratios.get('netProfitMargin', 0) * 100
        
        print(f"{peer_ticker:<10} {peer_gross:>13.1f}%  {peer_operating:>16.1f}%  {peer_net:>10.1f}%")
        
        peer_gross_margins.append(peer_gross)
        peer_operating_margins.append(peer_operating)
        peer_net_margins.append(peer_net)
    
    print("-" * 60)
    print(f"{'HOOD':<10} {hood_gross:>13.1f}%  {hood_operating:>16.1f}%  {hood_net:>10.1f}%")
    print("-" * 60)
    
    # Calculate percentiles
    print(f"\n📊 PERCENTILE CALCULATIONS:")
    
    gross_percentile = calculate_percentile_manual(hood_gross, peer_gross_margins)
    operating_percentile = calculate_percentile_manual(hood_operating, peer_operating_margins)
    net_percentile = calculate_percentile_manual(hood_net, peer_net_margins)
    
    print(f"\n  Gross Margin:")
    print(f"    HOOD: {hood_gross:.1f}%")
    print(f"    Peer average: {sum(peer_gross_margins)/len(peer_gross_margins):.1f}%")
    print(f"    Peers below HOOD: {sum(1 for gm in peer_gross_margins if gm < hood_gross)}/{len(peer_gross_margins)}")
    print(f"    Percentile: {gross_percentile:.1f}th")
    print(f"    Classification: {'✓ TOP 25% (STRENGTH)' if gross_percentile >= 75 else '⚠ BOTTOM 25% (WEAKNESS)' if gross_percentile <= 25 else 'MIDDLE 50%'}")
    
    print(f"\n  Operating Margin:")
    print(f"    HOOD: {hood_operating:.1f}%")
    print(f"    Peer average: {sum(peer_operating_margins)/len(peer_operating_margins):.1f}%")
    print(f"    Peers below HOOD: {sum(1 for om in peer_operating_margins if om < hood_operating)}/{len(peer_operating_margins)}")
    print(f"    Percentile: {operating_percentile:.1f}th")
    print(f"    Classification: {'✓ TOP 25% (STRENGTH)' if operating_percentile >= 75 else '⚠ BOTTOM 25% (WEAKNESS)' if operating_percentile <= 25 else 'MIDDLE 50%'}")
    
    # ROOT CAUSE ANALYSIS
    print(f"\n" + "="*80)
    print("ROOT CAUSE ANALYSIS")
    print("="*80)
    
    # Check if classification would be correct
    should_be_strength = gross_percentile >= 75
    should_be_weakness = gross_percentile <= 25
    
    if should_be_strength:
        print(f"\n✅ EXPECTED CLASSIFICATION: Gross Margin should be a STRENGTH")
        print(f"   Percentile: {gross_percentile:.1f}th (≥75th percentile threshold)")
        print(f"   HOOD outperforms {gross_percentile:.0f}% of peers")
    elif should_be_weakness:
        print(f"\n⚠️ EXPECTED CLASSIFICATION: Gross Margin should be a WEAKNESS")
        print(f"   Percentile: {gross_percentile:.1f}th (≤25th percentile threshold)")
        print(f"   HOOD underperforms vs peers")
    else:
        print(f"\n📊 EXPECTED CLASSIFICATION: Gross Margin is MIDDLE 50%")
        print(f"   Percentile: {gross_percentile:.1f}th (between 25th-75th)")
        print(f"   Neither strength nor weakness")
    
    # Data quality check
    print(f"\n🔍 PEER DATA QUALITY CHECK:")
    valid_peers = sum(1 for gm in peer_gross_margins if gm > 0)
    print(f"   Peers with valid gross margin: {valid_peers}/{len(peer_gross_margins)}")
    
    if valid_peers < 3:
        print(f"   ❌ INSUFFICIENT PEER DATA - only {valid_peers} valid peers!")
        print(f"   ROOT CAUSE: Cannot do meaningful benchmarking with <3 peers")
    
    # Check if HOOD is truly better than peers
    peer_avg = sum(peer_gross_margins) / len(peer_gross_margins) if peer_gross_margins else 0
    delta = hood_gross - peer_avg
    
    print(f"\n   HOOD vs Peer Average:")
    print(f"     HOOD: {hood_gross:.1f}%")
    print(f"     Peer Avg: {peer_avg:.1f}%")
    print(f"     Delta: {delta:+.1f}pp")
    
    if delta > 10:
        print(f"     ✓ HOOD has significantly higher margin (+{delta:.1f}pp)")
        print(f"     This should be classified as TOP PERFORMER")
    elif delta < -10:
        print(f"     ⚠️ HOOD has significantly lower margin ({delta:.1f}pp)")
        print(f"     This should be classified as BOTTOM PERFORMER")
    else:
        print(f"     ≈ HOOD is close to peer average (±{abs(delta):.1f}pp)")
    
    # Final diagnosis
    print(f"\n" + "="*80)
    print("FINAL DIAGNOSIS")
    print("="*80)
    
    if should_be_strength and valid_peers >= 3:
        print(f"\n✅ DIAGNOSIS: Code fix is working correctly!")
        print(f"   Gross margin SHOULD be strength based on data")
        print(f"   If report still shows 'Bottom 25%', issue is likely:")
        print(f"   1. Using cached/old report generated before code fix")
        print(f"   2. Report CSV export using stale data")
        print(f"   3. Re-run analysis to regenerate with fixed code")
    elif not should_be_strength:
        print(f"\n⚠️ DIAGNOSIS: Peer data may be problematic")
        print(f"   HOOD percentile: {gross_percentile:.1f}th")
        print(f"   This genuinely puts HOOD in {'bottom' if should_be_weakness else 'middle'} tier")
        print(f"   Possible explanations:")
        print(f"   1. Peers are not comparable (different business models)")
        print(f"   2. HOOD's margin calculation is different (fintech vs traditional)")
        print(f"   3. Need to review peer selection criteria")
    elif valid_peers < 3:
        print(f"\n❌ DIAGNOSIS: Insufficient peer data")
        print(f"   Only {valid_peers} peers with valid data")
        print(f"   Cannot perform statistically valid benchmarking")
        print(f"   FIX: Improve peer selection algorithm")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'hood_metrics': {
            'gross_margin': hood_gross,
            'operating_margin': hood_operating,
            'net_margin': hood_net,
        },
        'peer_count': len(peer_data),
        'peer_gross_margins': {k: v.get('grossProfitMargin', 0) * 100 for k, v in peer_data.items()},
        'percentiles': {
            'gross_margin': gross_percentile,
            'operating_margin': operating_percentile,
            'net_margin': net_percentile,
        },
        'expected_classification': {
            'gross_margin': 'STRENGTH' if should_be_strength else 'WEAKNESS' if should_be_weakness else 'NEUTRAL',
        },
        'diagnosis': 'Code fix working' if should_be_strength else 'Data quality issue' if valid_peers < 3 else 'Peer selection issue',
    }
    
    output_file = f"competitive_diagnostic_HOOD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
