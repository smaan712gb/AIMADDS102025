"""
Diagnostic Script: PDF vs Excel Data Parity Check
Compares what data is available to Excel vs PDF generators
"""

import json
from pathlib import Path
from loguru import logger

def load_latest_job_data():
    """Find and load the most recent job data"""
    data_dir = Path("data/jobs")
    if not data_dir.exists():
        logger.error("No data/jobs directory found")
        return None
    
    # Find most recent job file
    job_files = sorted(data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not job_files:
        logger.error("No job files found")
        return None
    
    latest_job = job_files[0]
    logger.info(f"Loading latest job: {latest_job.name}")
    
    with open(latest_job, 'r') as f:
        return json.load(f)

def analyze_data_availability(state):
    """Analyze what data is available in state"""
    
    print("\n" + "="*80)
    print("PDF vs EXCEL DATA PARITY DIAGNOSTIC")
    print("="*80)
    
    # 1. Check synthesis_reporting output
    print("\n1. SYNTHESIS_REPORTING DATA (Used by both Excel & PDF)")
    print("-" * 80)
    
    synthesis_output = None
    for agent_output in state.get('agent_outputs', []):
        if agent_output.get('agent_name') == 'synthesis_reporting':
            synthesis_output = agent_output.get('data', {})
            break
    
    if synthesis_output:
        print("✅ Synthesis data found")
        
        # Check key sections
        sections = {
            'detailed_financials': synthesis_output.get('detailed_financials', {}),
            'market_analysis': synthesis_output.get('market_analysis', {}),
            'risk_macro': synthesis_output.get('risk_macro', {}),
            'legal_diligence': synthesis_output.get('legal_diligence', {}),
            'integration_tax': synthesis_output.get('integration_tax', {}),
            'validation_summary': synthesis_output.get('validation_summary', {})
        }
        
        for section_name, section_data in sections.items():
            if section_data:
                print(f"  ✅ {section_name}: {len(section_data)} keys")
                # Show top-level keys
                if isinstance(section_data, dict):
                    for key in list(section_data.keys())[:5]:
                        print(f"      - {key}")
            else:
                print(f"  ❌ {section_name}: EMPTY")
    else:
        print("❌ NO SYNTHESIS DATA FOUND")
    
    # 2. Check individual agent outputs (fallback for PDF)
    print("\n2. INDIVIDUAL AGENT OUTPUTS (PDF Fallback Source)")
    print("-" * 80)
    
    agents_to_check = [
        'financial_analyst',
        'financial_deep_dive',
        'competitive_benchmarking',
        'macroeconomic_analyst',
        'external_validator',
        'risk_assessor',
        'legal_counsel'
    ]
    
    agent_data_map = {}
    for agent_name in agents_to_check:
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == agent_name),
            None
        )
        
        if agent_output and 'data' in agent_output:
            agent_data = agent_output['data']
            agent_data_map[agent_name] = agent_data
            print(f"✅ {agent_name}: {len(agent_data)} keys")
            
            # Show key data points
            if agent_name == 'financial_deep_dive':
                ratios = agent_data.get('key_financial_ratios', {})
                print(f"    - key_financial_ratios: {len(ratios)} ratios")
                for key in list(ratios.keys())[:3]:
                    print(f"        • {key}: {ratios[key]}")
            
            elif agent_name == 'competitive_benchmarking':
                position = agent_data.get('overall_competitive_position', 'N/A')
                competitors = agent_data.get('key_competitors', [])
                print(f"    - competitive_position: {position}")
                print(f"    - key_competitors: {len(competitors)} competitors")
            
            elif agent_name == 'macroeconomic_analyst':
                macro_env = agent_data.get('macro_environment', {})
                print(f"    - macro_environment: {len(macro_env)} indicators")
                tailwinds = agent_data.get('tailwinds', [])
                print(f"    - tailwinds: {len(tailwinds)} items")
            
            elif agent_name == 'external_validator':
                consensus = agent_data.get('street_consensus_comparison', {})
                print(f"    - street_consensus_comparison: {len(consensus)} metrics")
            
            elif agent_name == 'risk_assessor':
                risks = agent_data.get('key_risks', [])
                print(f"    - key_risks: {len(risks)} risks identified")
        else:
            print(f"❌ {agent_name}: NO DATA")
    
    # 3. Check normalized financials
    print("\n3. NORMALIZED FINANCIALS DATA")
    print("-" * 80)
    
    norm_fin = state.get('normalized_financials', {})
    if norm_fin:
        adjustments = norm_fin.get('adjustments', [])
        print(f"✅ Normalized financials found: {len(adjustments)} adjustments")
        
        if adjustments:
            print(f"  Sample adjustment:")
            adj = adjustments[0]
            print(f"    - Type: {adj.get('type')}")
            print(f"    - Original R&D: ${adj.get('original_rd', 0)/1e9:.1f}B")
            print(f"    - EBITDA Impact: ${adj.get('ebitda_impact', 0)/1e9:.1f}B")
    else:
        print("❌ NO NORMALIZED FINANCIALS")
    
    # 4. Check valuation models
    print("\n4. VALUATION MODELS DATA")
    print("-" * 80)
    
    val_models = state.get('valuation_models', {})
    if val_models:
        dcf = val_models.get('dcf_advanced', {})
        if dcf:
            dcf_analysis = dcf.get('dcf_analysis', {})
            base = dcf_analysis.get('base', {})
            ev = base.get('enterprise_value', 0)
            print(f"✅ DCF valuation: ${ev/1e9:.1f}B")
            
            # Check LBO
            lbo = dcf.get('lbo_analysis', {})
            if lbo:
                returns = lbo.get('returns_analysis', {})
                irr = returns.get('irr_percent', 0)
                print(f"✅ LBO analysis: {irr:.1f}% IRR")
            else:
                print(f"❌ NO LBO ANALYSIS")
        else:
            print("❌ NO DCF DATA")
    else:
        print("❌ NO VALUATION MODELS")
    
    # 5. Data source comparison summary
    print("\n5. EXCEL VS PDF DATA SOURCE COMPARISON")
    print("-" * 80)
    
    print("\nEXCEL Data Sources:")
    print("  ✅ Uses agent_outputs directly")
    print("  ✅ Extracts from each agent's data dict")
    print("  ✅ Has direct access to all agent outputs")
    
    print("\nPDF Data Sources:")
    print("  Primary: synthesis_reporting output (synthesized_data)")
    print("  Fallback: agent_outputs (for missing synthesized sections)")
    
    if synthesis_output:
        print("\n  ⚠️  ISSUE: PDF relies on synthesis_reporting, which may not have all data")
        print("  ⚠️  Some agent data might not be included in synthesis")
    else:
        print("\n  ❌ CRITICAL: No synthesis data - PDF will show placeholders")
    
    # 6. Specific section checks
    print("\n6. SECTION-BY-SECTION DATA AVAILABILITY")
    print("-" * 80)
    
    sections_check = [
        {
            'name': 'Financial Deep Dive - Key Ratios',
            'excel_source': 'financial_deep_dive agent → key_financial_ratios',
            'pdf_source': 'synthesis → detailed_financials OR fallback to agent',
            'has_data': 'key_financial_ratios' in agent_data_map.get('financial_deep_dive', {})
        },
        {
            'name': 'Competitive Benchmarking',
            'excel_source': 'competitive_benchmarking agent → direct',
            'pdf_source': 'synthesis → market_analysis OR fallback to agent',
            'has_data': 'competitive_benchmarking' in agent_data_map
        },
        {
            'name': 'Macroeconomic Analysis',
            'excel_source': 'macroeconomic_analyst agent → direct',
            'pdf_source': 'synthesis → risk_macro OR fallback to agent',
            'has_data': 'macroeconomic_analyst' in agent_data_map
        },
        {
            'name': 'External Validation',
            'excel_source': 'external_validator agent → direct',
            'pdf_source': 'synthesis → validation_summary OR fallback to agent',
            'has_data': 'external_validator' in agent_data_map
        },
        {
            'name': 'Risk Assessment',
            'excel_source': 'risk_assessor agent → direct',
            'pdf_source': 'synthesis → risk_macro OR fallback to agent',
            'has_data': 'risk_assessor' in agent_data_map
        }
    ]
    
    for section in sections_check:
        status = "✅" if section['has_data'] else "❌"
        print(f"\n{status} {section['name']}")
        print(f"  Excel: {section['excel_source']}")
        print(f"  PDF:   {section['pdf_source']}")
        if not section['has_data']:
            print(f"  ⚠️  Data missing - will not appear in either Excel or PDF")
    
    # 7. Recommendations
    print("\n7. RECOMMENDATIONS")
    print("="*80)
    
    if not synthesis_output:
        print("❌ CRITICAL: Synthesis agent did not run or failed")
        print("   → PDF will show many placeholders")
        print("   → Need to ensure synthesis_reporting agent runs successfully")
    else:
        print("✅ Synthesis data exists")
    
    missing_agents = [a for a in agents_to_check if a not in agent_data_map]
    if missing_agents:
        print(f"\n⚠️  Missing agent data for: {', '.join(missing_agents)}")
        print("   → These sections will be empty in both Excel and PDF")
    
    print("\n" + "="*80)
    return agent_data_map

if __name__ == "__main__":
    state = load_latest_job_data()
    if state:
        analyze_data_availability(state)
    else:
        print("ERROR: Could not load job data")
