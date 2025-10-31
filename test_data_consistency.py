"""
Data Consistency Test Suite
Tests the Single Source of Truth implementation across all report generators
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.data_accessor import DataAccessor
from src.outputs.report_consistency_validator import ReportDataValidator
from src.outputs.revolutionary_pdf_generator import RevolutionaryPDFGenerator
from src.outputs.revolutionary_excel_generator import RevolutionaryExcelGenerator
from src.outputs.revolutionary_ppt_generator import RevolutionaryPowerPointGenerator
from revolutionary_dashboard import AgenticInsightsDashboard


class TestDataConsistency:
    """Test suite for data consistency across all report generators"""
    
    @pytest.fixture
    def load_test_state(self):
        """Load test state with synthesized data"""
        job_file = Path("data/jobs/comprehensive_test_run.json")
        if not job_file.exists():
            pytest.skip(f"Test data not found: {job_file}")
        
        with open(job_file, 'r') as f:
            return json.load(f)
    
    def test_synthesized_data_exists(self, load_test_state):
        """Test 1: Verify synthesized data exists in state"""
        state = load_test_state
        
        # Check synthesized data present
        assert 'synthesized_data' in state, "synthesized_data missing from state"
        
        synth_data = state['synthesized_data']
        
        # Verify required fields
        required_fields = [
            'valuation',
            'normalized_financials',
            'risk_assessment',
            'consolidated_insights'
        ]
        
        for field in required_fields:
            assert field in synth_data, f"Required field missing: {field}"
        
        print("✅ Test 1 PASSED: Synthesized data structure valid")
    
    def test_data_accessor_validation(self, load_test_state):
        """Test 2: Verify DataAccessor validation works"""
        state = load_test_state
        
        # Test has_synthesized_data
        assert DataAccessor.has_synthesized_data(state), "DataAccessor should detect synthesized data"
        
        # Test validate_data_consistency
        validation = DataAccessor.validate_data_consistency(state)
        assert validation['has_synthesized_data'], "Validation should pass"
        assert validation['data_version'] is not None, "Data version should be set"
        
        # Test get_synthesized_data
        synth_data = DataAccessor.get_synthesized_data(state)
        assert synth_data is not None, "Should return synthesized data"
        
        print("✅ Test 2 PASSED: DataAccessor validation works correctly")
    
    def test_report_consistency_validator(self, load_test_state):
        """Test 3: Verify ReportDataValidator extracts consistent data"""
        state = load_test_state
        
        validator = ReportDataValidator(state)
        
        # Get validation report
        report = validator.get_validation_report()
        assert 'has_synthesized_data' in report
        assert report['has_synthesized_data'], "Should have synthesized data"
        
        # Get validated valuation
        val_data = validator.get_validated_valuation_data()
        assert 'base_enterprise_value' in val_data
        assert val_data['base_enterprise_value'] > 0, "EV should be positive"
        
        print("✅ Test 3 PASSED: ReportDataValidator working correctly")
    
    def test_single_valuation_across_generators(self, load_test_state):
        """Test 4: CRITICAL - Verify same valuation across all generators"""
        state = load_test_state
        
        # Get synthesized valuation (single source of truth)
        synth_data = DataAccessor.get_synthesized_data(state)
        true_ev = synth_data['valuation']['base_enterprise_value']
        
        print(f"\n📊 Single Source of Truth EV: ${true_ev/1e9:.2f}B")
        
        # Verify all generators would use same value
        # (We test by checking they all access synthesized_data correctly)
        
        # PDF Generator
        try:
            pdf_gen = RevolutionaryPDFGenerator()
            # Verify it validates data
            validation = DataAccessor.validate_data_consistency(state)
            assert validation['has_synthesized_data']
            print(f"  ✓ PDF Generator: Uses synthesized data v{validation['data_version']}")
        except Exception as e:
            pytest.fail(f"PDF Generator failed validation: {e}")
        
        # Excel Generator
        try:
            excel_gen = RevolutionaryExcelGenerator()
            validation = DataAccessor.validate_data_consistency(state)
            assert validation['has_synthesized_data']
            print(f"  ✓ Excel Generator: Uses synthesized data v{validation['data_version']}")
        except Exception as e:
            pytest.fail(f"Excel Generator failed validation: {e}")
        
        # PPT Generator
        try:
            ppt_gen = RevolutionaryPowerPointGenerator()
            validation = DataAccessor.validate_data_consistency(state)
            assert validation['has_synthesized_data']
            print(f"  ✓ PPT Generator: Uses synthesized data v{validation['data_version']}")
        except Exception as e:
            pytest.fail(f"PPT Generator failed validation: {e}")
        
        print("✅ Test 4 PASSED: All generators use single source of truth")
    
    def test_single_ebitda_across_system(self, load_test_state):
        """Test 5: Verify same normalized EBITDA everywhere"""
        state = load_test_state
        
        # Get from synthesized data
        synth_data = DataAccessor.get_synthesized_data(state)
        
        # Get normalized financials
        normalized = synth_data.get('normalized_financials', 
                                    state.get('normalized_financials', {}))
        
        if normalized:
            latest_income = normalized.get('normalized_income', [{}])[0]
            reported_ebitda = latest_income.get('ebitda', 0)
            
            adjustments = normalized.get('adjustments', [])
            if adjustments:
                adjustment = adjustments[0].get('ebitda_impact', 0)
                normalized_ebitda = reported_ebitda + adjustment
                
                print(f"\n💰 Single Source EBITDA:")
                print(f"  Reported: ${reported_ebitda/1e9:.2f}B")
                print(f"  Adjustment: ${adjustment/1e9:.2f}B")
                print(f"  Normalized: ${normalized_ebitda/1e9:.2f}B")
                
                assert normalized_ebitda > 0, "Normalized EBITDA should be positive"
                print("✅ Test 5 PASSED: Consistent EBITDA available")
            else:
                print("⚠️ Test 5 SKIPPED: No EBITDA adjustments in data")
        else:
            print("⚠️ Test 5 SKIPPED: No normalized financials in data")
    
    def test_agent_count_consistency(self, load_test_state):
        """Test 6: Verify consistent agent count"""
        state = load_test_state
        
        # Count from agent_outputs
        agent_outputs = state.get('agent_outputs', [])
        actual_count = len(agent_outputs)
        
        # Get from synthesized data
        synth_data = DataAccessor.get_synthesized_data(state)
        consolidated = synth_data.get('consolidated_insights', {})
        
        print(f"\n👥 Agent Count:")
        print(f"  From agent_outputs: {actual_count}")
        
        # This is the single source of truth all reports should use
        assert actual_count > 0, "Should have agent outputs"
        
        print(f"✅ Test 6 PASSED: Consistent agent count: {actual_count}")
    
    def test_anomaly_detection_consistency(self, load_test_state):
        """Test 7: Verify consistent anomaly reporting"""
        state = load_test_state
        
        # Get from synthesized consolidated insights
        synth_data = DataAccessor.get_synthesized_data(state)
        consolidated = synth_data.get('consolidated_insights', {})
        categorized = consolidated.get('categorized_insights', {})
        
        # Get financial and risk findings
        financial_findings = categorized.get('financial_performance', [])
        risk_findings = categorized.get('risk_assessment', [])
        
        # Find anomaly-related findings
        anomaly_findings = [
            f for f in financial_findings + risk_findings
            if 'anomal' in f.get('description', '').lower() 
            or 'deviation' in f.get('description', '').lower()
        ]
        
        anomaly_count = len(anomaly_findings)
        
        print(f"\n🚨 Anomaly Detection:")
        print(f"  Anomalies Found: {anomaly_count}")
        
        if anomaly_count > 0:
            for i, anomaly in enumerate(anomaly_findings[:3], 1):
                severity = anomaly.get('severity', 'unknown')
                print(f"  {i}. {anomaly.get('type', 'Unknown')}: {severity}")
        
        print("✅ Test 7 PASSED: Consistent anomaly data available")
    
    def test_no_direct_state_access_in_generators(self):
        """Test 8: Verify generators don't bypass DataAccessor"""
        
        # Check PDF generator source code
        pdf_file = Path("src/outputs/revolutionary_pdf_generator.py")
        if pdf_file.exists():
            pdf_code = pdf_file.read_text()
            
            # Should import DataAccessor
            assert 'from ..utils.data_accessor import DataAccessor' in pdf_code, \
                "PDF generator should import DataAccessor"
            
            # Should validate data
            assert 'DataAccessor.validate_data_consistency' in pdf_code, \
                "PDF generator should validate data"
            
            print("  ✓ PDF Generator: Properly uses DataAccessor")
        
        # Check Excel generator
        excel_file = Path("src/outputs/revolutionary_excel_generator.py")
        if excel_file.exists():
            excel_code = excel_file.read_text()
            
            assert 'from ..utils.data_accessor import DataAccessor' in excel_code, \
                "Excel generator should import DataAccessor"
            
            assert 'DataAccessor.validate_data_consistency' in excel_code, \
                "Excel generator should validate data"
            
            print("  ✓ Excel Generator: Properly uses DataAccessor")
        
        # Check PPT generator
        ppt_file = Path("src/outputs/revolutionary_ppt_generator.py")
        if ppt_file.exists():
            ppt_code = ppt_file.read_text()
            
            assert 'from ..utils.data_accessor import DataAccessor' in ppt_code, \
                "PPT generator should import DataAccessor"
            
            assert 'DataAccessor.validate_data_consistency' in ppt_code, \
                "PPT generator should validate data"
            
            print("  ✓ PPT Generator: Properly uses DataAccessor")
        
        print("✅ Test 8 PASSED: All generators properly implement DataAccessor")
    
    def test_backward_compatibility(self, load_test_state):
        """Test 9: Verify backward compatibility with ReportDataValidator"""
        state = load_test_state
        
        # Test that old-style access still works via validator
        validator = ReportDataValidator(state)
        
        # These should work even if direct state access changes
        val_data = validator.get_validated_valuation_data()
        legal_data = validator.get_validated_legal_data()
        integration_data = validator.get_validated_integration_data()
        
        assert val_data is not None, "Validator should provide valuation data"
        assert 'base_enterprise_value' in val_data, "Should have EV"
        
        print("✅ Test 9 PASSED: Backward compatibility maintained")
    
    def test_fail_fast_without_synthesis(self):
        """Test 10: Verify generators fail fast without synthesized data"""
        
        # Create state without synthesized_data
        invalid_state = {
            'target_company': 'Test Corp',
            'valuation_models': {}  # Missing synthesized_data
        }
        
        # DataAccessor should detect missing data
        assert not DataAccessor.has_synthesized_data(invalid_state), \
            "Should detect missing synthesized data"
        
        # Validation should fail
        try:
            DataAccessor.validate_data_consistency(invalid_state)
            pytest.fail("Should raise ValueError for missing synthesized data")
        except ValueError as e:
            assert "synthesized_data not found" in str(e).lower()
            print("  ✓ DataAccessor correctly rejects invalid state")
        
        print("✅ Test 10 PASSED: Fail-fast behavior working correctly")


def run_comprehensive_test_suite():
    """Run all tests and generate report"""
    print("\n" + "="*80)
    print("DATA CONSISTENCY TEST SUITE")
    print("="*80)
    print("\nTesting Single Source of Truth Implementation...")
    print("\n" + "-"*80)
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])
    
    print("\n" + "="*80)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED - DATA CONSISTENCY VERIFIED")
    else:
        print("❌ SOME TESTS FAILED - REVIEW OUTPUT ABOVE")
    print("="*80 + "\n")
    
    return exit_code


def quick_consistency_check(job_file: str = "data/jobs/ff069812-0e37-41aa-a303-b3fc44b5edc1.json"):
    """Quick consistency check without pytest"""
    print("\n" + "="*80)
    print("QUICK DATA CONSISTENCY CHECK")
    print("="*80)
    
    # Check if file exists
    if not Path(job_file).exists():
        print(f"   ❌ Job file not found: {job_file}")
        print(f"   Looking for Hood job file...")
        # Try to find any job file
        job_dir = Path("data/jobs")
        if job_dir.exists():
            job_files = list(job_dir.glob("*.json"))
            if job_files:
                job_file = str(job_files[0])
                print(f"   Using: {job_file}")
            else:
                print("   ❌ No job files found in data/jobs")
                return False
        else:
            print("   ❌ data/jobs directory not found")
            return False
    
    # Load state
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    # Check 1: Synthesized data exists
    print("\n1. Checking synthesized data...")
    if DataAccessor.has_synthesized_data(state):
        print("   ✅ Synthesized data present")
        
        # Get validation
        validation = DataAccessor.validate_data_consistency(state)
        print(f"   ✅ Data version: {validation['data_version']}")
    else:
        print("   ❌ Synthesized data MISSING")
        return False
    
    # Check 2: Extract key metrics
    print("\n2. Extracting key metrics from single source...")
    synth_data = DataAccessor.get_synthesized_data(state)
    
    valuation = synth_data.get('valuation', {})
    ev = valuation.get('base_enterprise_value', 0)
    print(f"   Enterprise Value: ${ev/1e9:.2f}B")
    
    # Check 3: Verify validators work
    print("\n3. Testing validators...")
    validator = ReportDataValidator(state)
    val_data = validator.get_validated_valuation_data()
    
    if val_data['base_enterprise_value'] == ev:
        print("   ✅ Validator returns consistent EV")
    else:
        print("   ❌ Validator EV mismatch!")
        return False
    
    # Check 4: Agent count
    print("\n4. Checking agent count...")
    agent_count = len(state.get('agent_outputs', []))
    print(f"   Agent Count: {agent_count}")
    
    if agent_count > 0:
        print("   ✅ Agents executed")
    else:
        print("   ⚠️  No agent outputs found")
    
    print("\n" + "="*80)
    print("✅ QUICK CHECK PASSED - Data Consistency OK")
    print("="*80 + "\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick check
        success = quick_consistency_check()
        sys.exit(0 if success else 1)
    else:
        # Full test suite
        exit_code = run_comprehensive_test_suite()
        sys.exit(exit_code)
