"""
Comprehensive diagnostic for PDF 'list' object has no attribute 'get' error
This error has occurred multiple times - we need to find the root cause
"""
import json
import traceback
from pathlib import Path
from loguru import logger

# Add detailed logging
logger.add("pdf_diagnosis_{time}.log", rotation="1 MB", level="DEBUG")

def diagnose_job_state(job_id: str = "81a10a3d-5935-43f0-a5cf-811ad7cdd310"):
    """Diagnose the job state to find where list is being passed instead of dict"""
    
    logger.info(f"Starting comprehensive diagnosis for job: {job_id}")
    
    # Load the job state
    job_file = Path(f"data/jobs/{job_id}.json")
    
    if not job_file.exists():
        logger.error(f"Job file not found: {job_file}")
        return
    
    logger.info(f"Loading job state from: {job_file}")
    
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    logger.info(f"Job state loaded successfully. Keys: {list(state.keys())}")
    
    # DIAGNOSIS 1: Check all agent_outputs for lists instead of dicts
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSIS 1: Checking agent_outputs structure")
    logger.info("="*80)
    
    agent_outputs = state.get('agent_outputs', [])
    logger.info(f"Found {len(agent_outputs)} agent outputs")
    
    issues_found = []
    
    for i, output in enumerate(agent_outputs):
        agent_name = output.get('agent_name', 'UNKNOWN')
        data = output.get('data', {})
        
        logger.info(f"\nAgent {i+1}: {agent_name}")
        logger.info(f"  Data type: {type(data)}")
        
        if isinstance(data, list):
            issues_found.append({
                'location': f'agent_outputs[{i}].data',
                'agent_name': agent_name,
                'issue': 'Data is a list, should be dict',
                'data_preview': str(data)[:200]
            })
            logger.error(f"  ❌ ISSUE: Data is a list! Should be dict")
            logger.error(f"  Preview: {str(data)[:200]}")
        
        elif isinstance(data, dict):
            logger.success(f"  ✅ Data is correctly a dict")
            # Check nested structures
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    logger.debug(f"    {key}: {type(value).__name__} with {len(value)} items")
    
    # DIAGNOSIS 2: Check direct state fields
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSIS 2: Checking direct state fields")
    logger.info("="*80)
    
    critical_fields = [
        'financial_data',
        'valuation_models', 
        'risk_matrix',
        'integration_roadmap',
        'deal_structure_analysis',
        'eps_impact_analysis',
        'sources_uses_analysis',
        'contribution_analysis',
        'exchange_ratio_analysis'
    ]
    
    for field in critical_fields:
        if field in state:
            value = state[field]
            logger.info(f"\n{field}:")
            logger.info(f"  Type: {type(value)}")
            
            if isinstance(value, list):
                issues_found.append({
                    'location': f'state[\'{field}\']',
                    'agent_name': 'state_level',
                    'issue': f'{field} is a list, might need to be dict',
                    'data_preview': str(value)[:200]
                })
                logger.warning(f"  ⚠️  {field} is a list!")
                logger.warning(f"  Preview: {str(value)[:200]}")
            elif isinstance(value, dict):
                logger.success(f"  ✅ {field} is a dict")
                logger.debug(f"  Keys: {list(value.keys())[:10]}")
    
    # DIAGNOSIS 3: Check for any lists at root level
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSIS 3: Scanning all root-level fields")
    logger.info("="*80)
    
    for key, value in state.items():
        if isinstance(value, list) and key not in ['agent_outputs', 'errors', 'warnings']:
            logger.warning(f"Root level list found: {key}")
            logger.warning(f"  Length: {len(value)}")
            logger.warning(f"  Preview: {str(value)[:200]}")
            
            issues_found.append({
                'location': f'state[\'{key}\']',
                'agent_name': 'root_level',
                'issue': f'{key} is a list at root level',
                'data_preview': str(value)[:200]
            })
    
    # DIAGNOSIS 4: Simulate PDF generation with safe access
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSIS 4: Testing safe data access patterns")
    logger.info("="*80)
    
    # Test patterns that might fail
    test_patterns = [
        ("state.get('financial_data', {})", lambda: state.get('financial_data', {})),
        ("state['financial_data']", lambda: state['financial_data'] if 'financial_data' in state else {}),
        ("agent_outputs[0].get('data', {})", lambda: agent_outputs[0].get('data', {}) if agent_outputs else {}),
    ]
    
    for pattern_desc, pattern_func in test_patterns:
        try:
            result = pattern_func()
            logger.info(f"✅ {pattern_desc}: {type(result).__name__}")
            if isinstance(result, list):
                logger.error(f"   ❌ RETURNED A LIST!")
        except Exception as e:
            logger.error(f"❌ {pattern_desc}: {e}")
    
    # SUMMARY
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSIS SUMMARY")
    logger.info("="*80)
    
    if issues_found:
        logger.error(f"\n❌ Found {len(issues_found)} potential issues:")
        for i, issue in enumerate(issues_found, 1):
            logger.error(f"\nIssue {i}:")
            logger.error(f"  Location: {issue['location']}")
            logger.error(f"  Agent: {issue['agent_name']}")
            logger.error(f"  Problem: {issue['issue']}")
            logger.error(f"  Data preview: {issue['data_preview']}")
        
        # Write issues to file
        issues_file = Path("pdf_list_error_diagnosis.json")
        with open(issues_file, 'w') as f:
            json.dump({
                'job_id': job_id,
                'total_issues': len(issues_found),
                'issues': issues_found,
                'agent_outputs_count': len(agent_outputs),
                'state_keys': list(state.keys())
            }, f, indent=2)
        logger.info(f"\n📄 Detailed diagnosis saved to: {issues_file}")
    else:
        logger.success("\n✅ No obvious list/dict type issues found in state!")
        logger.info("The error might be happening during PDF generation logic itself")
    
    return state, issues_found

if __name__ == "__main__":
    logger.info("Starting PDF List Error Diagnosis")
    logger.info("="*80)
    
    try:
        state, issues = diagnose_job_state()
        
        if issues:
            logger.info(f"\n🔍 Found {len(issues)} issues - check pdf_list_error_diagnosis.json")
        else:
            logger.info("\n✅ State structure looks healthy - error likely in PDF generator code itself")
            logger.info("Next step: Check src/outputs/revolutionary_pdf_generator.py for .get() calls on lists")
    
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}")
        logger.error(traceback.format_exc())
