"""
Script to analyze ORCL report generation and identify data loss points.
This script extracts key information from JSON logs to diagnose report quality issues.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def load_json_file(filepath: str) -> Dict:
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def analyze_job_state(job_data: Dict) -> Dict[str, Any]:
    """Analyze a job state file and extract key metrics."""
    analysis = {
        'job_id': job_data.get('job_id', 'Unknown'),
        'ticker': job_data.get('ticker', 'Unknown'),
        'status': job_data.get('status', 'Unknown'),
        'created_at': job_data.get('created_at', 'Unknown'),
        'completed_at': job_data.get('completed_at', 'Unknown'),
        'agent_outputs': {},
        'total_data_points': 0,
        'synthesis_data': {},
        'report_generation': {}
    }
    
    # Analyze agent outputs
    agents_data = job_data.get('agents', {})
    for agent_name, agent_info in agents_data.items():
        output = agent_info.get('output', {})
        status = agent_info.get('status', 'Unknown')
        
        # Count data points
        data_points = 0
        if isinstance(output, dict):
            data_points = count_dict_items(output)
        elif isinstance(output, list):
            data_points = len(output)
        
        analysis['agent_outputs'][agent_name] = {
            'status': status,
            'data_points': data_points,
            'has_output': bool(output),
            'output_keys': list(output.keys()) if isinstance(output, dict) else []
        }
        analysis['total_data_points'] += data_points
    
    # Analyze synthesis data
    synthesis = job_data.get('synthesis', {})
    if synthesis:
        analysis['synthesis_data'] = {
            'exists': True,
            'data_points': count_dict_items(synthesis),
            'keys': list(synthesis.keys()) if isinstance(synthesis, dict) else []
        }
    
    # Check report generation status
    reports = job_data.get('reports', {})
    if reports:
        analysis['report_generation'] = {
            'pdf_generated': reports.get('pdf', {}).get('status') == 'completed',
            'pptx_generated': reports.get('pptx', {}).get('status') == 'completed',
            'excel_generated': reports.get('excel', {}).get('status') == 'completed',
        }
    
    return analysis

def count_dict_items(data: Any, max_depth: int = 5, current_depth: int = 0) -> int:
    """Recursively count items in a nested dictionary."""
    if current_depth > max_depth:
        return 0
    
    count = 0
    if isinstance(data, dict):
        for key, value in data.items():
            count += 1  # Count the key itself
            if isinstance(value, (dict, list)):
                count += count_dict_items(value, max_depth, current_depth + 1)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                count += count_dict_items(item, max_depth, current_depth + 1)
            else:
                count += 1
    return count

def extract_sample_data(job_data: Dict, agent_name: str, max_chars: int = 500) -> str:
    """Extract a sample of agent output data."""
    try:
        output = job_data.get('agents', {}).get(agent_name, {}).get('output', {})
        if not output:
            return "No output data"
        
        # Get a sample of the output
        sample = json.dumps(output, indent=2)[:max_chars]
        return sample + "..." if len(json.dumps(output)) > max_chars else sample
    except Exception as e:
        return f"Error extracting sample: {e}"

def compare_synthesis_to_agents(job_data: Dict) -> Dict[str, Any]:
    """Compare synthesis output to raw agent outputs to identify data loss."""
    comparison = {
        'agent_data_available': {},
        'synthesis_coverage': {},
        'potential_data_loss': []
    }
    
    # Check what data agents produced
    agents = job_data.get('agents', {})
    for agent_name, agent_info in agents.items():
        output = agent_info.get('output', {})
        comparison['agent_data_available'][agent_name] = {
            'has_data': bool(output),
            'output_size': len(json.dumps(output)) if output else 0,
            'key_count': len(output.keys()) if isinstance(output, dict) else 0
        }
    
    # Check what synthesis captured
    synthesis = job_data.get('synthesis', {})
    if synthesis:
        comparison['synthesis_coverage']['total_size'] = len(json.dumps(synthesis))
        comparison['synthesis_coverage']['keys'] = list(synthesis.keys()) if isinstance(synthesis, dict) else []
        
        # Check if synthesis references agent outputs
        synthesis_str = json.dumps(synthesis).lower()
        for agent_name in agents.keys():
            if agent_name.lower() not in synthesis_str:
                comparison['potential_data_loss'].append(
                    f"Agent '{agent_name}' data may not be included in synthesis"
                )
    else:
        comparison['potential_data_loss'].append("No synthesis data found!")
    
    return comparison

def main():
    """Main analysis function."""
    print("=" * 80)
    print("ORCL REPORT ANALYSIS - Root Cause Investigation")
    print("=" * 80)
    print()
    
    # Find ORCL job
    jobs_dir = Path("data/jobs")
    orcl_job = None
    orcl_job_file = None
    
    print("Scanning job files for ORCL analysis...")
    for job_file in jobs_dir.glob("*.json"):
        job_data = load_json_file(job_file)
        if job_data.get('ticker', '').upper() == 'ORCL':
            orcl_job = job_data
            orcl_job_file = job_file
            print(f"✓ Found ORCL job: {job_file.name}")
            break
    
    if not orcl_job:
        print("✗ No ORCL job found in data/jobs/")
        print("\nSearching for most recent job...")
        job_files = list(jobs_dir.glob("*.json"))
        if job_files:
            # Use most recent file
            orcl_job_file = max(job_files, key=os.path.getmtime)
            orcl_job = load_json_file(orcl_job_file)
            print(f"  Using most recent job: {orcl_job_file.name}")
    
    if not orcl_job:
        print("ERROR: No job files found!")
        return
    
    print()
    print("-" * 80)
    print("JOB OVERVIEW")
    print("-" * 80)
    
    # Basic job info
    print(f"Job ID: {orcl_job.get('job_id', 'Unknown')}")
    print(f"Ticker: {orcl_job.get('ticker', 'Unknown')}")
    print(f"Status: {orcl_job.get('status', 'Unknown')}")
    print(f"Created: {orcl_job.get('created_at', 'Unknown')}")
    print(f"Completed: {orcl_job.get('completed_at', 'Unknown')}")
    print()
    
    # Analyze job state
    analysis = analyze_job_state(orcl_job)
    
    print("-" * 80)
    print("AGENT OUTPUT ANALYSIS")
    print("-" * 80)
    
    for agent_name, agent_info in analysis['agent_outputs'].items():
        print(f"\n{agent_name}:")
        print(f"  Status: {agent_info['status']}")
        print(f"  Has Output: {agent_info['has_output']}")
        print(f"  Data Points: {agent_info['data_points']}")
        if agent_info['output_keys']:
            print(f"  Output Keys: {', '.join(agent_info['output_keys'][:10])}")
            if len(agent_info['output_keys']) > 10:
                print(f"    ... and {len(agent_info['output_keys']) - 10} more")
    
    print(f"\nTotal Data Points from All Agents: {analysis['total_data_points']}")
    print()
    
    print("-" * 80)
    print("SYNTHESIS ANALYSIS")
    print("-" * 80)
    
    if analysis['synthesis_data'].get('exists'):
        print(f"Synthesis Data: EXISTS")
        print(f"Data Points in Synthesis: {analysis['synthesis_data']['data_points']}")
        print(f"Synthesis Keys: {', '.join(analysis['synthesis_data']['keys'][:10])}")
        if len(analysis['synthesis_data']['keys']) > 10:
            print(f"  ... and {len(analysis['synthesis_data']['keys']) - 10} more")
    else:
        print("Synthesis Data: MISSING")
        print("⚠️  WARNING: No synthesis data found - this is a critical issue!")
    print()
    
    print("-" * 80)
    print("REPORT GENERATION STATUS")
    print("-" * 80)
    
    if analysis['report_generation']:
        print(f"PDF Generated: {analysis['report_generation'].get('pdf_generated', False)}")
        print(f"PPTX Generated: {analysis['report_generation'].get('pptx_generated', False)}")
        print(f"Excel Generated: {analysis['report_generation'].get('excel_generated', False)}")
    else:
        print("No report generation data found")
    print()
    
    print("-" * 80)
    print("DATA FLOW COMPARISON")
    print("-" * 80)
    
    comparison = compare_synthesis_to_agents(orcl_job)
    
    print("\nAgent Data Available:")
    for agent_name, info in comparison['agent_data_available'].items():
        print(f"  {agent_name}:")
        print(f"    Has Data: {info['has_data']}")
        print(f"    Output Size: {info['output_size']:,} bytes")
        print(f"    Keys: {info['key_count']}")
    
    print("\nSynthesis Coverage:")
    if comparison['synthesis_coverage']:
        print(f"  Total Size: {comparison['synthesis_coverage'].get('total_size', 0):,} bytes")
        print(f"  Top-Level Keys: {len(comparison['synthesis_coverage'].get('keys', []))}")
    else:
        print("  No synthesis data to analyze")
    
    print("\n⚠️  POTENTIAL DATA LOSS POINTS:")
    if comparison['potential_data_loss']:
        for issue in comparison['potential_data_loss']:
            print(f"  • {issue}")
    else:
        print("  None detected")
    print()
    
    print("-" * 80)
    print("ROOT CAUSE ANALYSIS")
    print("-" * 80)
    print()
    
    # Determine root cause
    has_agent_data = any(info['has_output'] for info in analysis['agent_outputs'].values())
    has_synthesis = analysis['synthesis_data'].get('exists', False)
    has_reports = any(analysis['report_generation'].values()) if analysis['report_generation'] else False
    
    agent_data_count = analysis['total_data_points']
    synthesis_data_count = analysis['synthesis_data'].get('data_points', 0)
    
    print("Diagnosis:")
    print()
    
    if not has_agent_data:
        print("🔴 PRIMARY ISSUE: Agents are not producing output data")
        print("   - The root cause is in the agent execution layer")
        print("   - Agents may be failing silently or not completing")
        print("   - Check agent configurations and API connections")
    elif not has_synthesis:
        print("🔴 PRIMARY ISSUE: Synthesis layer is not processing agent outputs")
        print("   - Agents are producing data but synthesis is failing")
        print("   - The Report Synthesizer is not receiving or processing agent data")
        print("   - Check synthesis workflow and data pipeline")
    elif synthesis_data_count < agent_data_count * 0.5:
        print("🟡 PRIMARY ISSUE: Significant data loss in synthesis layer")
        print(f"   - Agents produced {agent_data_count} data points")
        print(f"   - Synthesis only captured {synthesis_data_count} data points")
        print(f"   - Data loss: ~{100 - (synthesis_data_count/agent_data_count*100):.1f}%")
        print("   - The Report Synthesizer is not capturing all agent outputs")
    elif not has_reports or not all(analysis['report_generation'].values()):
        print("🟡 PRIMARY ISSUE: Report conversion/generation is failing")
        print("   - Agent data and synthesis exist")
        print("   - The Reports Converter is not generating all formats properly")
        print("   - Check PDF/PPTX/Excel generation code")
    else:
        print("🟢 Data pipeline appears complete")
        print("   - Check report content quality manually")
    
    print()
    print("-" * 80)
    print("DETAILED OUTPUT SAMPLES (First 500 chars per agent)")
    print("-" * 80)
    print()
    
    for agent_name in list(analysis['agent_outputs'].keys())[:5]:  # Show first 5 agents
        print(f"\n{agent_name} Sample Output:")
        print("-" * 40)
        sample = extract_sample_data(orcl_job, agent_name)
        print(sample)
        print()
    
    # Save detailed analysis
    output_file = f"orcl_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'job_analysis': analysis,
            'data_flow_comparison': comparison,
            'raw_job_metadata': {
                'job_id': orcl_job.get('job_id'),
                'ticker': orcl_job.get('ticker'),
                'status': orcl_job.get('status'),
                'agent_list': list(orcl_job.get('agents', {}).keys()),
                'synthesis_keys': list(orcl_job.get('synthesis', {}).keys()) if isinstance(orcl_job.get('synthesis'), dict) else []
            }
        }, f, indent=2)
    
    print("-" * 80)
    print(f"Detailed analysis saved to: {output_file}")
    print("-" * 80)

if __name__ == "__main__":
    main()
