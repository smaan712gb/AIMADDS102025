"""
Inspect Synthesis Structure to Find Where Data Really Is
"""
import json
from pathlib import Path

def inspect_synthesis():
    """Load latest job and inspect synthesis structure"""
    data_dir = Path("data/jobs")
    job_files = sorted(data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not job_files:
        print("No job files found")
        return
    
    latest_job = job_files[0]
    print(f"Loading: {latest_job.name}\n")
    
    with open(latest_job, 'r') as f:
        state = json.load(f)
    
    # Find synthesis agent output
    synthesis_output = None
    for agent_output in state.get('agent_outputs', []):
        if agent_output.get('agent_name') == 'synthesis_reporting':
            synthesis_output = agent_output.get('data', {})
            break
    
    if not synthesis_output:
        print("No synthesis output found")
        return
    
    print("="*80)
    print("SYNTHESIS DATA STRUCTURE")
    print("="*80)
    
    # Inspect each top-level key
    for key in synthesis_output.keys():
        value = synthesis_output[key]
        print(f"\n{key}:")
        print(f"  Type: {type(value).__name__}")
        
        if isinstance(value, dict):
            print(f"  Keys ({len(value)}): {list(value.keys())[:10]}")
            
            # For critical sections, show deeper structure
            if key == 'detailed_financials':
                print("\n  DETAILED_FINANCIALS Deep Dive:")
                for sub_key in list(value.keys())[:15]:
                    sub_val = value[sub_key]
                    print(f"    {sub_key}: {type(sub_val).__name__}", end='')
                    if isinstance(sub_val, (list, dict)):
                        print(f" (len={len(sub_val)})", end='')
                    print()
            
            elif key == 'market_analysis':
                print("\n  MARKET_ANALYSIS Deep Dive:")
                for sub_key in value.keys():
                    sub_val = value[sub_key]
                    print(f"    {sub_key}: {type(sub_val).__name__}", end='')
                    if isinstance(sub_val, dict):
                        print(f" -> {list(sub_val.keys())[:5]}")
                    else:
                        print()
            
            elif key == 'risk_macro':
                print("\n  RISK_MACRO Deep Dive:")
                for sub_key in list(value.keys())[:15]:
                    sub_val = value[sub_key]
                    print(f"    {sub_key}: {type(sub_val).__name__}", end='')
                    if isinstance(sub_val, (list, dict)):
                        print(f" (len={len(sub_val)})", end='')
                    print()
        
        elif isinstance(value, list):
            print(f"  Length: {len(value)}")
            if value and isinstance(value[0], dict):
                print(f"  First item keys: {list(value[0].keys())[:5]}")
    
    # Now check if competitive_benchmarking agent has ANY data
    print("\n" + "="*80)
    print("CHECKING INDIVIDUAL AGENTS")
    print("="*80)
    
    for agent_name in ['competitive_benchmarking', 'macroeconomic_analyst', 'financial_deep_dive', 'external_validator', 'risk_assessor']:
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == agent_name),
            None
        )
        
        if agent_output and 'data' in agent_output:
            data = agent_output['data']
            print(f"\n{agent_name}:")
            print(f"  Has data: {len(data)} keys")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")

if __name__ == "__main__":
    inspect_synthesis()
