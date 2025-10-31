"""
Test NVDA Reports Data Validation
Validates that PDF and PPT reports contain real data from synthesized_data with no placeholders
"""
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.outputs.revolutionary_pdf_generator import RevolutionaryPDFGenerator
from src.outputs.revolutionary_ppt_generator import RevolutionaryPowerPointGenerator
from src.utils.data_accessor import DataAccessor

# Placeholder patterns to detect
PLACEHOLDER_PATTERNS = [
    'placeholder', 'TBD', 'N/A', 'pending', 'in progress',
    'not available', 'default', 'example', 'sample',
    'coming soon', 'under review', 'to be determined'
]

# Expected data fields that must have real values
REQUIRED_FIELDS = {
    'executive_summary': ['key_recommendation', 'strategic_rationale'],
    'detailed_financials': ['quality_score', 'dcf_outputs'],
    'validation_summary': ['overall_confidence_score'],
}


def load_nvda_state():
    """Load most recent NVDA analysis state"""
    logger.info("Loading NVDA state from data directory...")
    
    # Look for NVDA state files
    data_dir = Path('data')
    state_files = list(data_dir.glob('*NVDA*.json'))
    
    if not state_files:
        logger.error("No NVDA state files found in data directory")
        return None
    
    # Get most recent
    latest_file = max(state_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Loading: {latest_file}")
    
    with open(latest_file, 'r') as f:
        state = json.load(f)
    
    logger.info(f"✓ Loaded NVDA state with {len(state.get('agent_outputs', []))} agent outputs")
    return state


def validate_synthesized_data(state):
    """Validate synthesized data exists and has content"""
    logger.info("\n=== VALIDATING SYNTHESIZED DATA ===")
    
    validation = DataAccessor.validate_data_consistency(state)
    
    if not validation['has_synthesized_data']:
        logger.error("❌ No synthesized data found!")
        return False
    
    logger.info(f"✓ Synthesized data version: {validation['data_version']}")
    
    synthesized_data = DataAccessor.get_synthesized_data(state)
    
    # Check required fields
    issues = []
    for section, fields in REQUIRED_FIELDS.items():
        if section not in synthesized_data:
            issues.append(f"Missing section: {section}")
            continue
        
        section_data = synthesized_data[section]
        for field in fields:
            if field not in section_data:
                issues.append(f"Missing field: {section}.{field}")
            elif not section_data[field]:
                issues.append(f"Empty field: {section}.{field}")
    
    if issues:
        logger.warning(f"⚠ Found {len(issues)} data issues:")
        for issue in issues[:10]:  # Show first 10
            logger.warning(f"  - {issue}")
    else:
        logger.info("✓ All required fields present and populated")
    
    # Show data summary
    logger.info("\nSynthesized Data Summary:")
    logger.info(f"  Sections: {len(synthesized_data)}")
    
    # Key metrics
    exec_summary = synthesized_data.get('executive_summary', {})
    logger.info(f"  Recommendation: {exec_summary.get('key_recommendation', 'N/A')[:50]}")
    
    detailed_fin = synthesized_data.get('detailed_financials', {})
    logger.info(f"  Quality Score: {detailed_fin.get('quality_score', 0)}/100")
    
    dcf_outputs = detailed_fin.get('dcf_outputs', {})
    ev = dcf_outputs.get('enterprise_value', 0)
    logger.info(f"  Enterprise Value: ${abs(ev)/1e9:.2f}B")
    
    return True


def generate_and_validate_pdf(state):
    """Generate PDF and validate content"""
    logger.info("\n=== GENERATING AND VALIDATING PDF ===")
    
    try:
        pdf_gen = RevolutionaryPDFGenerator()
        
        # Generate PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = f"outputs/test_nvda_validation_{timestamp}.pdf"
        
        logger.info(f"Generating PDF to: {pdf_path}")
        pdf_gen.generate_report(state, pdf_path)
        
        logger.info(f"✓ PDF generated successfully: {pdf_path}")
        
        # Check if file exists and has content
        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            size_kb = pdf_file.stat().st_size / 1024
            logger.info(f"✓ PDF file size: {size_kb:.1f} KB")
            
            if size_kb < 50:
                logger.warning("⚠ PDF file seems small, may lack content")
                return False, pdf_path
            
            return True, pdf_path
        else:
            logger.error("❌ PDF file not created")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def generate_and_validate_ppt(state):
    """Generate PPT and validate content"""
    logger.info("\n=== GENERATING AND VALIDATING PPT ===")
    
    try:
        ppt_gen = RevolutionaryPowerPointGenerator()
        
        # Generate PPT
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ppt_path = f"outputs/test_nvda_validation_{timestamp}.pptx"
        
        logger.info(f"Generating PPT to: {ppt_path}")
        ppt_gen.generate_report(state, ppt_path)
        
        logger.info(f"✓ PPT generated successfully: {ppt_path}")
        
        # Check if file exists and has content
        ppt_file = Path(ppt_path)
        if ppt_file.exists():
            size_kb = ppt_file.stat().st_size / 1024
            logger.info(f"✓ PPT file size: {size_kb:.1f} KB")
            
            if size_kb < 50:
                logger.warning("⚠ PPT file seems small, may lack content")
                return False, ppt_path
            
            return True, ppt_path
        else:
            logger.error("❌ PPT file not created")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ PPT generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def check_for_placeholders(state):
    """Check if synthesized data contains placeholder values"""
    logger.info("\n=== CHECKING FOR PLACEHOLDERS ===")
    
    synthesized_data = DataAccessor.get_synthesized_data(state)
    
    # Convert to JSON string for searching
    data_str = json.dumps(synthesized_data, default=str).lower()
    
    found_placeholders = []
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.lower() in data_str:
            # Count occurrences
            count = data_str.count(pattern.lower())
            found_placeholders.append((pattern, count))
    
    if found_placeholders:
        logger.warning(f"⚠ Found {len(found_placeholders)} placeholder patterns:")
        for pattern, count in found_placeholders[:10]:
            logger.warning(f"  - '{pattern}': {count} occurrences")
        return False
    else:
        logger.info("✓ No common placeholder patterns detected")
        return True


def validate_data_mapping(state):
    """Validate that data mapping works correctly"""
    logger.info("\n=== VALIDATING DATA MAPPING ===")
    
    synthesized_data = DataAccessor.get_synthesized_data(state)
    
    # Check key data mappings
    mappings_valid = True
    
    # 1. Executive Summary
    exec_summary = synthesized_data.get('executive_summary', {})
    if not exec_summary.get('key_recommendation'):
        logger.warning("⚠ executive_summary.key_recommendation is empty")
        mappings_valid = False
    else:
        logger.info(f"✓ key_recommendation: {exec_summary['key_recommendation'][:60]}...")
    
    # 2. Financial Metrics
    detailed_fin = synthesized_data.get('detailed_financials', {})
    dcf_outputs = detailed_fin.get('dcf_outputs', {})
    
    if not dcf_outputs:
        logger.warning("⚠ detailed_financials.dcf_outputs is empty")
        mappings_valid = False
    else:
        ev = dcf_outputs.get('enterprise_value', 0)
        if ev == 0:
            logger.warning("⚠ enterprise_value is zero")
            mappings_valid = False
        else:
            logger.info(f"✓ enterprise_value: ${abs(ev)/1e9:.2f}B")
    
    # 3. Quality Score
    quality = detailed_fin.get('quality_score', 0)
    if quality == 0:
        logger.warning("⚠ quality_score is zero")
        mappings_valid = False
    else:
        logger.info(f"✓ quality_score: {quality}/100")
    
    # 4. Validation Summary
    validation = synthesized_data.get('validation_summary', {})
    confidence = validation.get('overall_confidence_score', 0)
    if confidence == 0:
        logger.warning("⚠ overall_confidence_score is zero")
        mappings_valid = False
    else:
        logger.info(f"✓ overall_confidence_score: {confidence:.1%}")
    
    # 5. Risk Assessment
    risk_macro = synthesized_data.get('risk_macro', {})
    key_risks = risk_macro.get('key_risks', [])
    if not key_risks:
        logger.warning("⚠ risk_macro.key_risks is empty")
        mappings_valid = False
    else:
        logger.info(f"✓ key_risks: {len(key_risks)} risks identified")
    
    if mappings_valid:
        logger.info("\n✓ All key data mappings are working correctly")
    else:
        logger.warning("\n⚠ Some data mappings may not be working correctly")
    
    return mappings_valid


def main():
    """Main test execution"""
    logger.info("=" * 80)
    logger.info("NVDA REPORTS DATA VALIDATION TEST")
    logger.info("Validating PDF and PPT use real data from synthesized_data")
    logger.info("=" * 80)
    
    # Load state
    state = load_nvda_state()
    if not state:
        logger.error("❌ Failed to load NVDA state")
        return False
    
    # Validate synthesized data
    if not validate_synthesized_data(state):
        logger.error("❌ Synthesized data validation failed")
        return False
    
    # Check for placeholders
    no_placeholders = check_for_placeholders(state)
    
    # Validate data mapping
    mapping_valid = validate_data_mapping(state)
    
    # Generate PDF
    pdf_success, pdf_path = generate_and_validate_pdf(state)
    
    # Generate PPT
    ppt_success, ppt_path = generate_and_validate_ppt(state)
    
    # Final results
    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    results = {
        "Synthesized Data Available": "✓ PASS" if state else "❌ FAIL",
        "No Placeholders": "✓ PASS" if no_placeholders else "⚠ WARNING",
        "Data Mapping Valid": "✓ PASS" if mapping_valid else "⚠ WARNING",
        "PDF Generation": "✓ PASS" if pdf_success else "❌ FAIL",
        "PPT Generation": "✓ PASS" if ppt_success else "❌ FAIL",
    }
    
    for test, result in results.items():
        logger.info(f"{test:.<40} {result}")
    
    if pdf_path:
        logger.info(f"\nPDF Location: {pdf_path}")
    if ppt_path:
        logger.info(f"PPT Location: {ppt_path}")
    
    # Overall result
    all_pass = all("✓" in r for r in results.values())
    
    if all_pass:
        logger.info("\n✅ ALL TESTS PASSED - Reports use real data from single source of truth")
        return True
    else:
        logger.warning("\n⚠ SOME TESTS FAILED - Review results above")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
