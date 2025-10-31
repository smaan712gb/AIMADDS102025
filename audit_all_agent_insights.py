"""
Comprehensive Audit of All Agent Insights
Identifies what's in the data vs what's in the PDF
"""
import json
from pathlib import Path
from pprint import pprint

def audit_agent_outputs(job_id: str):
    """Audit all agent outputs for completeness"""
    
    job_file = Path(f"data/jobs/{job_id}.json")
    with open(job_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 100)
    print("COMPREHENSIVE AGENT OUTPUT AUDIT")
    print("=" * 100)
    print()
    
    # Check each agent
    for output in data.get('agent_outputs', []):
        agent_name = output.get('agent_name', output.get('agent_key', 'unknown'))
        has_data = bool(output.get('data'))
        
        print(f"\n{'='*100}")
        print(f"AGENT: {agent_name}")
        print(f"{'='*100}")
        print(f"Status: {output.get('status')}")
        print(f"Has Data: {'✅ YES' if has_data else '❌ NO'}")
        
        if has_data and output['data']:
            print(f"\n📊 DATA STRUCTURE:")
            print(f"Top-level keys: {list(output['data'].keys())}")
            
            # Deep dive into each key area
            for key, value in output['data'].items():
                if isinstance(value, dict):
                    print(f"\n  📁 {key}:")
                    if value:
                        for subkey in list(value.keys())[:10]:  # First 10 subkeys
                            print(f"     - {subkey}")
                        if len(value.keys()) > 10:
                            print(f"     ... and {len(value.keys()) - 10} more")
                elif isinstance(value, list):
                    print(f"\n  📋 {key}: {len(value)} items")
                    if value and isinstance(value[0], dict):
                        print(f"     Sample keys: {list(value[0].keys())[:5]}")
                else:
                    print(f"\n  📌 {key}: {type(value).__name__}")
    
    # Focus on Financial Analyst - the richest source
    print("\n\n" + "="*100)
    print("DETAILED FINANCIAL ANALYST BREAKDOWN")
    print("="*100)
    
    fa_output = next((o for o in data['agent_outputs'] 
                     if o.get('agent_name') == 'financial_analyst'), None)
    
    if fa_output and fa_output.get('data'):
        fa_data = fa_output['data']
        
        # Advanced Valuation
        if 'advanced_valuation' in fa_data:
            av = fa_data['advanced_valuation']
            print("\n📊 ADVANCED VALUATION COMPONENTS:")
            print(f"  - dcf_analysis: {list(av.get('dcf_analysis', {}).keys())}")
            print(f"  - sensitivity_analysis: {'✅ Present' if 'sensitivity_analysis' in av else '❌ Missing'}")
            print(f"  - monte_carlo_simulation: {'✅ Present' if 'monte_carlo_simulation' in av else '❌ Missing'}")
            print(f"  - comparable_companies: {'✅ Present' if 'comparable_companies' in av else '❌ Missing'}")
            print(f"  - precedent_transactions: {'✅ Present' if 'precedent_transactions' in av else '❌ Missing'}")
            print(f"  - valuation_summary: {'✅ Present' if 'valuation_summary' in av else '❌ Missing'}")
            print(f"  - lbo_analysis: {'✅ Present' if 'lbo_analysis' in av else '❌ Missing'}")
            print(f"  - earnings_quality: {'✅ Present' if 'earnings_quality' in av else '❌ Missing'}")
            
            # Sensitivity Analysis Details
            if 'sensitivity_analysis' in av:
                sa = av['sensitivity_analysis']
                print(f"\n  📈 SENSITIVITY ANALYSIS DETAILS:")
                print(f"     - sensitivity_matrix: {len(sa.get('sensitivity_matrix', []))} x {len(sa.get('sensitivity_matrix', [[]])[0] if sa.get('sensitivity_matrix') else [])} grid")
                print(f"     - wacc_range: {sa.get('wacc_range')}")
                print(f"     - terminal_growth_range: {sa.get('terminal_growth_range')}")
                print(f"     - dataframe: {'✅ Present' if 'dataframe' in sa else '❌ Missing'}")
            
            # Monte Carlo Details
            if 'monte_carlo_simulation' in av:
                mc = av['monte_carlo_simulation']
                print(f"\n  🎲 MONTE CARLO SIMULATION DETAILS:")
                print(f"     - num_simulations: {mc.get('num_simulations')}")
                print(f"     - mean_valuation: ${mc.get('mean_valuation', 0)/1e9:.1f}B")
                print(f"     - median_valuation: ${mc.get('median_valuation', 0)/1e9:.1f}B")
                print(f"     - std_deviation: ${mc.get('std_deviation', 0)/1e9:.1f}B")
                print(f"     - percentiles: {list(mc.get('percentiles', {}).keys())}")
                print(f"     - confidence_intervals: {list(mc.get('confidence_intervals', {}).keys())}")
            
            # LBO Analysis Details
            if 'lbo_analysis' in av:
                lbo = av['lbo_analysis']
                print(f"\n  💼 LBO ANALYSIS DETAILS:")
                print(f"     - entry_assumptions: {list(lbo.get('entry_assumptions', {}).keys())}")
                print(f"     - debt_structure: {list(lbo.get('debt_structure', {}).keys())}")
                print(f"     - projections: {len(lbo.get('projections', []))} years")
                print(f"     - exit_assumptions: {list(lbo.get('exit_assumptions', {}).keys())}")
                print(f"     - returns_analysis: {list(lbo.get('returns_analysis', {}).keys())}")
                print(f"     - deal_metrics: {list(lbo.get('deal_metrics', {}).keys())}")
                print(f"     - sensitivity: {list(lbo.get('sensitivity', {}).keys())}")
                
                # IRR and MoM Sensitivity
                if 'sensitivity' in lbo:
                    sens = lbo['sensitivity']
                    if 'irr_sensitivity' in sens:
                        irr_sens = sens['irr_sensitivity']
                        print(f"\n     📊 IRR SENSITIVITY MATRIX:")
                        print(f"        - Matrix size: {len(irr_sens.get('matrix', []))} x {len(irr_sens.get('matrix', [[]])[0] if irr_sens.get('matrix') else [])}")
                        print(f"        - Exit multiples: {irr_sens.get('exit_multiples')}")
                        print(f"        - EBITDA growth rates: {irr_sens.get('ebitda_growth_rates')}")
                    
                    if 'mom_sensitivity' in sens:
                        mom_sens = sens['mom_sensitivity']
                        print(f"\n     📊 MoM SENSITIVITY MATRIX:")
                        print(f"        - Matrix size: {len(mom_sens.get('matrix', []))} x {len(mom_sens.get('matrix', [[]])[0] if mom_sens.get('matrix') else [])}")
                        print(f"        - Exit multiples: {mom_sens.get('exit_multiples')}")
                        print(f"        - EBITDA growth rates: {mom_sens.get('ebitda_growth_rates')}")
    
    # External Validator - Check validation details
    print("\n\n" + "="*100)
    print("DETAILED EXTERNAL VALIDATOR BREAKDOWN")
    print("="*100)
    
    ev_output = next((o for o in data['agent_outputs'] 
                     if o.get('agent_name') == 'external_validator'), None)
    
    if ev_output and ev_output.get('data'):
        ev_data = ev_output['data']
        print(f"\n📊 EXTERNAL VALIDATION COMPONENTS:")
        print(f"  - validation_results: {len(ev_data.get('validation_results', []))} findings")
        print(f"  - adjustment_plan: {'✅ Present' if 'adjustment_plan' in ev_data else '❌ Missing'}")
        print(f"  - requires_reanalysis: {ev_data.get('requires_reanalysis')}")
        print(f"  - confidence_score: {ev_data.get('confidence_score', 0):.1%}")
        print(f"  - critical_discrepancies: {len(ev_data.get('critical_discrepancies', []))}")
        print(f"  - moderate_discrepancies: {len(ev_data.get('moderate_discrepancies', []))}")
        print(f"  - validated_findings: {len(ev_data.get('validated_findings', []))}")
        
        # Detail each validation result
        for i, result in enumerate(ev_data.get('validation_results', [])[:5], 1):
            print(f"\n  🔍 Validation Result #{i}:")
            print(f"     Status: {result.get('status')}")
            print(f"     Severity: {result.get('severity')}")
            print(f"     Alignment: {result.get('alignment_score', 0):.0%}")
            print(f"     Finding Type: {result.get('finding', {}).get('type')}")
    
    # Risk Assessment - Check risk details
    print("\n\n" + "="*100)
    print("DETAILED RISK ASSESSMENT BREAKDOWN")
    print("="*100)
    
    ra_output = next((o for o in data['agent_outputs'] 
                     if o.get('agent_name') == 'risk_assessment'), None)
    
    if ra_output and ra_output.get('data'):
        ra_data = ra_output['data']
        print(f"\n📊 RISK ASSESSMENT COMPONENTS:")
        print(f"  - risk_matrix: {list(ra_data.get('risk_matrix', {}).keys())}")
        print(f"  - risk_factors: {len(ra_data.get('risk_factors', []))} risks")
        print(f"  - risk_scores: {ra_data.get('risk_scores', {})}")
        print(f"  - risk_scenarios: {list(ra_data.get('risk_scenarios', {}).keys())}")
        print(f"  - mitigation_strategies: {len(ra_data.get('mitigation_strategies', []))}")
        
        # Detail each risk
        for i, risk in enumerate(ra_data.get('risk_factors', []), 1):
            print(f"\n  ⚠️ Risk #{i}:")
            print(f"     Category: {risk.get('category')}")
            print(f"     Severity: {risk.get('severity')}")
            print(f"     Likelihood: {risk.get('likelihood')}")
            print(f"     Impact: {risk.get('impact')}")
            print(f"     Description: {risk.get('description', '')[:80]}...")
    
    print("\n\n" + "="*100)
    print("AUDIT COMPLETE")
    print("="*100)

if __name__ == "__main__":
    audit_agent_outputs("360181db-a8a9-4885-87f7-b56b767bd952")
