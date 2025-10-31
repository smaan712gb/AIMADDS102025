"""
Smart Agent Validation Script
Validates all 11 agents' outputs programmatically by checking JSON structure
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def validate_agent_output(
    agent_name: str,
    agent_data: Dict[str, Any],
    required_fields: List[str]
) -> Dict[str, Any]:
    """
    Validate an agent's output
    
    Returns validation result with pass/fail/warnings
    """
    result = {
        'agent': agent_name,
        'status': 'PASS',
        'issues': [],
        'warnings': [],
        'data_quality': 'REAL'
    }
    
    # Check if agent data exists
    if not agent_data:
        result['status'] = 'FAIL'
        result['issues'].append("No output data found")
        return result
    
    # Check for error indicators
    if 'error' in agent_data:
        result['status'] = 'FAIL'
        result['issues'].append(f"Error in output: {agent_data['error']}")
    
    # Check for required fields
    missing_fields = []
    for field in required_fields:
        if field not in agent_data:
            missing_fields.append(field)
    
    if missing_fields:
        result['warnings'].append(f"Missing fields: {', '.join(missing_fields)}")
    
    # Check for dummy/placeholder data indicators
    dummy_indicators = ['dummy', 'placeholder', 'not available', 'N/A', 'test', 'example']
    
    str_data = str(agent_data).lower()
    for indicator in dummy_indicators:
        if indicator in str_data and str_data.count(indicator) > 3:
            result['warnings'].append(f"Possible dummy data detected ('{indicator}' appears multiple times)")
            result['data_quality'] = 'QUESTIONABLE'
    
    return result


def validate_all_agents_from_job(job_file: str):
    """
    Validate all agents from a job file
    
    Args:
        job_file: Path to job JSON file
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE AGENT VALIDATION - M&A PRODUCTION QUALITY")
    print("="*80)
    print(f"\nJob File: {job_file}\n")
    
    # Load job data
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    deal_id = state.get('deal_id', 'Unknown')
    target = state.get('target_company', 'Unknown')
    ticker = state.get('target_ticker', 'Unknown')
    
    print(f"Deal: {target} ({ticker})")
    print(f"Deal ID: {deal_id}\n")
    
    print("="*80)
    print("AGENT-BY-AGENT VALIDATION")
    print("="*80 + "\n")
    
    agent_outputs = state.get('agent_outputs', [])
    
    # Define validation requirements for each agent (ALL 13 AGENTS)
    validations = [
        {
            'agent_name': 'Project Manager',
            'key': 'project_manager',
            'required_fields': ['project_plan', 'task_assignments'],
            'critical_checks': [
                ('Project plan exists', lambda d: 'project_plan' in d or state.get('project_plan')),
            ]
        },
        {
            'agent_name': 'Financial Analyst',
            'key': 'financial_analyst',
            'required_fields': ['financial_metrics', 'normalized_financials', 'advanced_valuation', 'ratio_analysis'],
            'critical_checks': [
                ('Revenue exists', lambda d: d.get('financial_metrics', {}).get('revenue', 0) > 0),
                ('DCF base case exists', lambda d: d.get('advanced_valuation', {}).get('dcf_analysis', {}).get('base', {}).get('enterprise_value', 0) > 0),
                ('Normalized financials exist', lambda d: len(d.get('normalized_financials', {}).get('normalized_income', [])) > 0),
                ('Quality score calculated', lambda d: d.get('normalized_financials', {}).get('quality_score', 0) > 0),
            ]
        },
        {
            'agent_name': 'Financial Deep Dive',
            'key': 'financial_deep_dive',
            'required_fields': ['working_capital', 'capex_analysis', 'debt_schedule'],
            'critical_checks': [
                ('Working capital analysis exists', lambda d: 'working_capital' in d and 'nwc_analysis' in d.get('working_capital', {})),
                ('CapEx analysis exists', lambda d: 'capex_analysis' in d),
                ('Debt schedule exists', lambda d: 'debt_schedule' in d and 'debt_analysis' in d.get('debt_schedule', {})),
                ('WC efficiency calculated', lambda d: d.get('working_capital', {}).get('nwc_analysis', {}).get('efficiency_score', 0) > 0),
            ]
        },
        {
            'agent_name': 'Legal Counsel',
            'key': 'legal_counsel',
            'required_fields': ['legal_risks', 'compliance_status'],
            'critical_checks': [
                ('Legal risks identified', lambda d: len(d.get('legal_risks', [])) > 0),
                ('Compliance status exists', lambda d: 'compliance_status' in d),
            ]
        },
        {
            'agent_name': 'Competitive Benchmarking',
            'key': 'competitive_benchmarking',
            'required_fields': ['competitive_position', 'peer_rankings'],
            'critical_checks': [
                ('Competitive position assessed', lambda d: 'competitive_position' in d),
                ('Peer rankings exist', lambda d: len(d.get('peer_rankings', {})) > 0),
                ('Peers analyzed', lambda d: d.get('summary', {}).get('peers_analyzed', 0) > 0),
            ]
        },
        {
            'agent_name': 'Macroeconomic Analyst',
            'key': 'macroeconomic_analyst',
            'required_fields': ['current_economic_conditions', 'scenario_models'],
            'critical_checks': [
                ('Economic conditions captured', lambda d: 'current_economic_conditions' in d),
                ('Scenario models exist', lambda d: len(d.get('scenario_models', {})) > 0),
                ('Multiple scenarios', lambda d: len(d.get('scenario_models', {})) >= 3),
            ]
        },
        {
            'agent_name': 'External Validator',
            'key': 'external_validator',
            'required_fields': ['confidence_score', 'validated_findings'],
            'critical_checks': [
                ('Confidence score exists', lambda d: 'confidence_score' in d),
                ('Findings validated', lambda d: len(d.get('validated_findings', [])) > 0),
                ('Confidence above 0', lambda d: d.get('confidence_score', 0) > 0),
            ]
        },
        {
            'agent_name': 'Integration Planner',
            'key': 'integration_planner',
            'required_fields': ['synergy_analysis', 'integration_roadmap'],
            'critical_checks': [
                ('Synergy analysis exists', lambda d: 'synergy_analysis' in d or state.get('synergy_analysis')),
                ('Integration roadmap exists', lambda d: 'integration_roadmap' in d or state.get('integration_roadmap')),
            ]
        },
        {
            'agent_name': 'Market Strategist',
            'key': 'market_strategist',
            'required_fields': ['market_analysis', 'competitive_landscape'],
            'critical_checks': [
                ('Market analysis exists', lambda d: 'market_analysis' in d or state.get('market_data')),
                ('Competitive landscape exists', lambda d: 'competitive_landscape' in d or state.get('competitive_landscape')),
            ]
        },
        {
            'agent_name': 'Synthesis Agent',
            'key': 'synthesis_reporting',
            'required_fields': ['executive_summary', 'key_findings'],
            'critical_checks': [
                ('Executive summary exists', lambda d: (
                    (isinstance(d.get('executive_summary'), dict) and len(d.get('executive_summary', {}).get('text', '')) > 100) or
                    (isinstance(d.get('executive_summary'), str) and len(d.get('executive_summary', '')) > 100) or
                    (isinstance(state.get('executive_summary'), dict) and len(state.get('executive_summary', {}).get('text', '')) > 100) or
                    (isinstance(state.get('executive_summary'), str) and len(state.get('executive_summary', '')) > 100)
                )),
                ('Key findings exist', lambda d: state.get('key_findings') and len(state.get('key_findings', [])) > 0),
                ('Recommendations exist', lambda d: state.get('recommendations') and len(state.get('recommendations', [])) > 0),
            ]
        },
        {
            'agent_name': 'Risk Assessment',
            'key': 'risk_assessment',
            'required_fields': ['risk_matrix', 'risk_factors'],
            'critical_checks': [
                ('Risk matrix exists', lambda d: 'risk_matrix' in d or state.get('risk_assessment', {}).get('risk_matrix')),
                ('Risk factors identified', lambda d: len(d.get('risk_factors', [])) > 0 or len(state.get('risk_assessment', {}).get('risk_factors', [])) > 0),
            ]
        },
        {
            'agent_name': 'Tax Structuring',
            'key': 'tax_structuring',
            'required_fields': ['tax_implications', 'structure_recommendations'],
            'critical_checks': [
                ('Tax implications analyzed', lambda d: 'tax_implications' in d or state.get('tax_analysis')),
                ('Structure recommendations exist', lambda d: 'structure_recommendations' in d or state.get('tax_structure')),
            ]
        }
    ]
    
    # Track overall results
    total_agents = len(validations)
    passed = 0
    failed = 0
    warnings_count = 0
    
    # Validate each agent
    for validation in validations:
        agent_name = validation['agent_name']
        agent_key = validation['key']
        required_fields = validation['required_fields']
        critical_checks = validation.get('critical_checks', [])
        
        print(f"\n{'─'*80}")
        print(f"Agent: {agent_name}")
        print(f"{'─'*80}")
        
        # Find agent output - check multiple locations due to synthesis
        agent_data = None
        
        # First check agent_outputs array
        for output in agent_outputs:
            if output.get('agent_type') == agent_key or output.get('agent_name') == agent_key:
                agent_data = output.get('result', output.get('data', {}))
                break
        
        # If not found, check synthesized top-level fields
        if not agent_data:
            # Map agent keys to their synthesized state locations
            synthesis_map = {
                'financial_analyst': ['financial_metrics', 'normalized_financials', 'financial_data'],
                'financial_deep_dive': ['financial_deep_dive', 'working_capital', 'capex_analysis', 'debt_schedule'],
                'legal_counsel': ['legal_analysis', 'legal_risks', 'compliance_status'],
                'competitive_benchmarking': ['competitive_analysis', 'competitive_landscape'],
                'macroeconomic_analyst': ['macroeconomic_analysis', 'scenario_models'],
                'external_validator': ['external_validator'],
                'integration_planner': ['integration_plan', 'synergy_analysis', 'integration_roadmap'],
                'market_strategist': ['market_data', 'competitive_landscape', 'sentiment_analysis'],
                'synthesis_reporting': ['executive_summary', 'key_findings', 'final_synthesis'],
                'risk_assessment': ['risk_assessment', 'critical_risks'],
                'tax_structuring': ['tax_analysis', 'tax_structure']
            }
            
            # Check if data exists in any mapped location
            if agent_key in synthesis_map:
                for field in synthesis_map[agent_key]:
                    if field in state and state[field]:
                        field_data = state[field]
                        # Handle different data types
                        if not agent_data:
                            agent_data = field_data
                        elif isinstance(agent_data, dict) and isinstance(field_data, dict):
                            agent_data = {**agent_data, **field_data}
                        elif isinstance(agent_data, dict):
                            agent_data[field] = field_data
            
            # Fallback to direct key lookup
            if not agent_data:
                agent_data = state.get(agent_key, {})
        
        # Perform basic validation
        result = validate_agent_output(agent_name, agent_data, required_fields)
        
        # Perform critical checks
        checks_passed = 0
        checks_failed = 0
        
        if agent_data and critical_checks:
            print("\nCritical Checks:")
            for check_name, check_func in critical_checks:
                try:
                    if check_func(agent_data):
                        print(f"  ✓ {check_name}")
                        checks_passed += 1
                    else:
                        print(f"  ✗ {check_name}")
                        checks_failed += 1
                        result['issues'].append(f"Critical check failed: {check_name}")
                except Exception as e:
                    print(f"  ⚠ {check_name} (check error: {str(e)})")
                    result['warnings'].append(f"Check error for '{check_name}': {str(e)}")
                    checks_failed += 1
        
        # Update status based on critical checks
        if checks_failed > 0 and checks_passed == 0:
            result['status'] = 'FAIL'
        elif checks_failed > 0:
            result['status'] = 'PARTIAL'
        
        # Print status
        print(f"\nStatus: {result['status']}")
        print(f"Data Quality: {result['data_quality']}")
        
        if result['issues']:
            print("\nIssues:")
            for issue in result['issues']:
                print(f"  ❌ {issue}")
        
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning}")
            warnings_count += len(result['warnings'])
        
        # Update counters
        if result['status'] == 'PASS':
            passed += 1
        elif result['status'] == 'FAIL':
            failed += 1
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"\nTotal Agents Validated: {total_agents}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Partial: {total_agents - passed - failed}")
    print(f"Total Warnings: {warnings_count}")
    
    success_rate = (passed / total_agents * 100) if total_agents > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n✅ EXCELLENT: System is production-ready")
    elif success_rate >= 75:
        print("\n⚠️  GOOD: Minor improvements needed")
    elif success_rate >= 50:
        print("\n⚠️  FAIR: Several issues need attention")
    else:
        print("\n❌ CRITICAL: Major issues detected")
    
    print("\n" + "="*80 + "\n")
    
    return {
        'total': total_agents,
        'passed': passed,
        'failed': failed,
        'warnings': warnings_count,
        'success_rate': success_rate
    }


if __name__ == '__main__':
    import sys
    
    # Find most recent job file
    jobs_dir = Path('data/jobs')
    
    if not jobs_dir.exists():
        print("❌ Error: data/jobs directory not found")
        sys.exit(1)
    
    job_files = list(jobs_dir.glob('*.json'))
    
    if not job_files:
        print("❌ Error: No job files found in data/jobs/")
        sys.exit(1)
    
    # Use most recent or specified file
    if len(sys.argv) > 1:
        job_file = Path(sys.argv[1])
        if not job_file.exists():
            print(f"❌ Error: File not found: {job_file}")
            sys.exit(1)
    else:
        job_file = max(job_files, key=lambda p: p.stat().st_mtime)
        print(f"Using most recent job file: {job_file.name}\n")
    
    # Run validation
    try:
        results = validate_all_agents_from_job(str(job_file))
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
