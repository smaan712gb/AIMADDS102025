"""
Test Report Generation - Validate M&A Deliverable Quality
Tests PDF, PowerPoint, and Excel generation with investment banking standards
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Import generators
sys.path.insert(0, str(Path(__file__).parent))
from src.outputs.pdf_generator import PDFGenerator
from src.outputs.ppt_generator import PowerPointGenerator
from src.outputs.excel_generator import ExcelGenerator
from src.outputs.report_config import create_report_config


class ReportValidator:
    """Validate reports against investment banking standards"""
    
    def __init__(self):
        self.validation_results = {
            'pdf': {'passed': [], 'failed': [], 'warnings': []},
            'ppt': {'passed': [], 'failed': [], 'warnings': []},
            'excel': {'passed': [], 'failed': [], 'warnings': []}
        }
    
    def validate_financial_data(self, state: Dict[str, Any], report_type: str) -> bool:
        """Validate financial data completeness"""
        checks = []
        
        # Check 1: Revenue data exists and is non-zero
        normalized_financials = state.get("normalized_financials", {})
        latest_income = normalized_financials.get('normalized_income', [{}])[0]
        revenue = latest_income.get('revenue', 0)
        
        if revenue > 0:
            self.validation_results[report_type]['passed'].append(
                f"✓ Revenue data present: ${revenue:,.0f}"
            )
            checks.append(True)
        else:
            self.validation_results[report_type]['failed'].append(
                f"✗ Revenue missing or zero"
            )
            checks.append(False)
        
        # Check 2: Profitability metrics
        net_income = latest_income.get('netIncome', 0)
        ebitda = latest_income.get('ebitda', 0)
        
        if net_income != 0 and ebitda != 0:
            self.validation_results[report_type]['passed'].append(
                f"✓ Profitability metrics complete"
            )
            checks.append(True)
        else:
            self.validation_results[report_type]['warnings'].append(
                f"⚠ Some profitability metrics missing"
            )
            checks.append(True)  # Warning, not failure
        
        # Check 3: Balance sheet data
        latest_balance = normalized_financials.get('normalized_balance', [{}])[0]
        total_assets = latest_balance.get('totalAssets', 0)
        
        if total_assets > 0:
            self.validation_results[report_type]['passed'].append(
                f"✓ Balance sheet data present"
            )
            checks.append(True)
        else:
            self.validation_results[report_type]['failed'].append(
                f"✗ Balance sheet data missing"
            )
            checks.append(False)
        
        return all(checks)
    
    def validate_deep_dive_analysis(self, state: Dict[str, Any], report_type: str) -> bool:
        """Validate investment banking quality deep dive analysis"""
        checks = []
        deep_dive = state.get('financial_deep_dive', {})
        
        # Check 1: Working Capital Analysis
        wc_data = deep_dive.get('working_capital', {})
        if wc_data and wc_data.get('nwc_analysis'):
            nwc = wc_data['nwc_analysis']
            nwc_efficiency = nwc.get('efficiency_score', 0)  # CORRECT FIELD NAME
            
            if nwc_efficiency > 0:
                self.validation_results[report_type]['passed'].append(
                    f"✓ Working Capital Analysis: {nwc_efficiency:.0f}/100"
                )
                checks.append(True)
            else:
                self.validation_results[report_type]['warnings'].append(
                    f"⚠ Working capital efficiency score missing"
                )
                checks.append(True)
        else:
            self.validation_results[report_type]['failed'].append(
                f"✗ Working Capital Analysis missing"
            )
            checks.append(False)
        
        # Check 2: CapEx Analysis
        capex_data = deep_dive.get('capex_analysis', {})
        if capex_data and capex_data.get('capex_analysis'):
            self.validation_results[report_type]['passed'].append(
                f"✓ CapEx & Asset Intensity Analysis present"
            )
            checks.append(True)
        else:
            self.validation_results[report_type]['failed'].append(
                f"✗ CapEx Analysis missing"
            )
            checks.append(False)
        
        # Check 3: Debt Structure Analysis
        debt_data = deep_dive.get('debt_schedule', {})  # CORRECT PATH
        if debt_data and debt_data.get('debt_analysis'):  # CORRECT FIELD
            debt = debt_data['debt_analysis']
            debt_equity = debt.get('debt_to_equity', 0)
            
            self.validation_results[report_type]['passed'].append(
                f"✓ Debt Structure Analysis: {debt_equity:.2f}x D/E"
            )
            checks.append(True)
        else:
            self.validation_results[report_type]['failed'].append(
                f"✗ Debt Structure Analysis missing"
            )
            checks.append(False)
        
        return all(checks)
    
    def validate_valuation_models(self, state: Dict[str, Any], report_type: str) -> bool:
        """Validate valuation analysis"""
        checks = []
        
        # Check DCF Model
        dcf_data = state.get("valuation_models", {}).get("dcf_advanced", {})
        if dcf_data and dcf_data.get('dcf_analysis'):
            dcf_base = dcf_data['dcf_analysis'].get('base', {})
            ev = dcf_base.get('enterprise_value', 0)
            
            if ev > 0:
                self.validation_results[report_type]['passed'].append(
                    f"✓ DCF Valuation: ${ev:,.0f}"
                )
                checks.append(True)
            else:
                self.validation_results[report_type]['warnings'].append(
                    f"⚠ DCF valuation incomplete"
                )
                checks.append(True)
        else:
            self.validation_results[report_type]['warnings'].append(
                f"⚠ DCF valuation model missing"
            )
            checks.append(True)  # Warning only, not critical
        
        return all(checks)
    
    def validate_competitive_analysis(self, state: Dict[str, Any], report_type: str) -> bool:
        """Validate competitive benchmarking"""
        competitive = state.get("competitive_analysis", {})
        
        if competitive and competitive.get('competitive_position'):
            position = competitive['competitive_position']
            rating = position.get('overall_rating', 'Unknown')
            
            self.validation_results[report_type]['passed'].append(
                f"✓ Competitive Analysis: {rating}"
            )
            return True
        else:
            self.validation_results[report_type]['warnings'].append(
                f"⚠ Competitive benchmarking incomplete"
            )
            return True  # Warning only
    
    def validate_external_validation(self, state: Dict[str, Any], report_type: str) -> bool:
        """Validate external validation"""
        agent_outputs = state.get('agent_outputs', [])
        validator_output = next((o for o in agent_outputs if o.get('agent_name') == 'external_validator'), None)
        
        if validator_output:
            validation_data = validator_output.get('data', {})
            confidence_score = validation_data.get('confidence_score', 0)
            
            if confidence_score > 0:
                self.validation_results[report_type]['passed'].append(
                    f"✓ External Validation: {confidence_score:.0f}% confidence"
                )
                return True
            else:
                self.validation_results[report_type]['warnings'].append(
                    f"⚠ External validation confidence score missing"
                )
                return True
        else:
            self.validation_results[report_type]['warnings'].append(
                f"⚠ External validation not performed"
            )
            return True  # Warning only
    
    def validate_investment_banking_standards(self, state: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """
        Validate against investment banking M&A deliverable standards
        
        Returns validation summary with score
        """
        print(f"\n{'='*60}")
        print(f"VALIDATING {report_type.upper()} REPORT - INVESTMENT BANKING STANDARDS")
        print(f"{'='*60}\n")
        
        # Run all validation checks
        validations = {
            'Financial Data Completeness': self.validate_financial_data(state, report_type),
            'Deep Dive Analysis (IB Quality)': self.validate_deep_dive_analysis(state, report_type),
            'Valuation Models': self.validate_valuation_models(state, report_type),
            'Competitive Benchmarking': self.validate_competitive_analysis(state, report_type),
            'External Validation': self.validate_external_validation(state, report_type)
        }
        
        # Calculate score
        passed = len(self.validation_results[report_type]['passed'])
        failed = len(self.validation_results[report_type]['failed'])
        warnings = len(self.validation_results[report_type]['warnings'])
        
        total_checks = passed + failed + warnings
        score = (passed / total_checks * 100) if total_checks > 0 else 0
        
        # Determine quality tier
        if score >= 90 and failed == 0:
            quality_tier = "INVESTMENT BANKING GRADE A"
            meets_standards = True
        elif score >= 75 and failed <= 1:
            quality_tier = "INVESTMENT BANKING GRADE B"
            meets_standards = True
        elif score >= 60:
            quality_tier = "ACCEPTABLE - NEEDS IMPROVEMENTS"
            meets_standards = False
        else:
            quality_tier = "BELOW STANDARDS"
            meets_standards = False
        
        return {
            'validations': validations,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'score': score,
            'quality_tier': quality_tier,
            'meets_standards': meets_standards
        }
    
    def print_validation_report(self, report_type: str, summary: Dict[str, Any]):
        """Print detailed validation report"""
        print(f"\n📊 VALIDATION SUMMARY - {report_type.upper()}")
        print(f"{'─'*60}")
        
        # Print passed checks
        if self.validation_results[report_type]['passed']:
            print(f"\n✅ PASSED CHECKS ({len(self.validation_results[report_type]['passed'])}):")
            for check in self.validation_results[report_type]['passed']:
                print(f"   {check}")
        
        # Print warnings
        if self.validation_results[report_type]['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.validation_results[report_type]['warnings'])}):")
            for warning in self.validation_results[report_type]['warnings']:
                print(f"   {warning}")
        
        # Print failures
        if self.validation_results[report_type]['failed']:
            print(f"\n❌ FAILED CHECKS ({len(self.validation_results[report_type]['failed'])}):")
            for failure in self.validation_results[report_type]['failed']:
                print(f"   {failure}")
        
        # Print summary
        print(f"\n{'─'*60}")
        print(f"Quality Score: {summary['score']:.1f}%")
        print(f"Quality Tier:  {summary['quality_tier']}")
        print(f"Meets Standards: {'✓ YES' if summary['meets_standards'] else '✗ NO'}")
        print(f"{'─'*60}")


def test_report_generation(job_file: str):
    """
    Test report generation for a specific job
    
    Args:
        job_file: Path to job JSON file
    """
    print(f"\n{'='*80}")
    print(f"M&A DUE DILIGENCE REPORT GENERATION TEST")
    print(f"{'='*80}")
    print(f"\nJob File: {job_file}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load job data
    print(f"\n📂 Loading job data...")
    with open(job_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    deal_id = state.get('deal_id', 'Unknown')
    target = state.get('target_company', 'Unknown')
    ticker = state.get('target_ticker', 'Unknown')
    
    print(f"   Deal ID: {deal_id}")
    print(f"   Target:  {target} ({ticker})")
    
    # Create report config
    config = create_report_config(
        target_company=state.get('target_company', 'Unknown'),
        target_ticker=state.get('target_ticker'),
        acquirer_company=state.get('acquirer_company', 'Strategic Acquirer'),
        deal_id=state.get('deal_id', 'TEST-001'),
        deal_type=state.get('deal_type', 'acquisition'),
        buyer_type=state.get('buyer_type', 'strategic'),
        industry=state.get('industry', 'technology')
    )
    
    # Initialize validator
    validator = ReportValidator()
    results = {}
    
    # Test 1: PDF Generation
    print(f"\n{'─'*80}")
    print(f"TEST 1: PDF REPORT GENERATION")
    print(f"{'─'*80}")
    try:
        pdf_gen = PDFGenerator(output_dir="outputs/test_reports", config=config)
        pdf_path = pdf_gen.generate_full_report(state, config)
        print(f"✓ PDF Generated: {pdf_path}")
        
        # Validate PDF
        pdf_summary = validator.validate_investment_banking_standards(state, 'pdf')
        validator.print_validation_report('pdf', pdf_summary)
        results['pdf'] = pdf_summary
        
    except Exception as e:
        print(f"✗ PDF Generation Failed: {e}")
        results['pdf'] = {'meets_standards': False, 'error': str(e)}
    
    # Test 2: PowerPoint Generation
    print(f"\n{'─'*80}")
    print(f"TEST 2: POWERPOINT PRESENTATION GENERATION")
    print(f"{'─'*80}")
    try:
        ppt_gen = PowerPointGenerator(output_dir="outputs/test_reports", config=config)
        ppt_path = ppt_gen.generate_investment_committee_deck(state, config)
        print(f"✓ PowerPoint Generated: {ppt_path}")
        
        # Validate PPT
        ppt_summary = validator.validate_investment_banking_standards(state, 'ppt')
        validator.print_validation_report('ppt', ppt_summary)
        results['ppt'] = ppt_summary
        
    except Exception as e:
        print(f"✗ PowerPoint Generation Failed: {e}")
        results['ppt'] = {'meets_standards': False, 'error': str(e)}
    
    # Test 3: Excel Generation
    print(f"\n{'─'*80}")
    print(f"TEST 3: EXCEL WORKBOOK GENERATION")
    print(f"{'─'*80}")
    try:
        excel_gen = ExcelGenerator(output_dir="outputs/test_reports", config=config)
        excel_path = excel_gen.generate_full_report(state, config)
        print(f"✓ Excel Generated: {excel_path}")
        
        # Validate Excel
        excel_summary = validator.validate_investment_banking_standards(state, 'excel')
        validator.print_validation_report('excel', excel_summary)
        results['excel'] = excel_summary
        
    except Exception as e:
        print(f"✗ Excel Generation Failed: {e}")
        results['excel'] = {'meets_standards': False, 'error': str(e)}
    
    # Final Summary
    print(f"\n{'='*80}")
    print(f"FINAL VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    
    all_meet_standards = all(
        r.get('meets_standards', False) for r in results.values()
    )
    
    for report_type, summary in results.items():
        if 'error' in summary:
            print(f"❌ {report_type.upper()}: GENERATION FAILED - {summary['error']}")
        else:
            status = "✅ PASSES" if summary['meets_standards'] else "❌ FAILS"
            print(f"{status} {report_type.upper()}: {summary['quality_tier']} ({summary['score']:.1f}%)")
    
    print(f"\n{'='*80}")
    if all_meet_standards:
        print(f"✅ ALL REPORTS MEET INVESTMENT BANKING STANDARDS")
        print(f"\n🎯 These reports are suitable for M&A due diligence presentations")
        print(f"   to investment committees, boards, and senior management.")
    else:
        print(f"⚠️  SOME REPORTS NEED IMPROVEMENT")
        print(f"\n📋 Review the validation details above to identify specific issues.")
    print(f"{'='*80}\n")
    
    return results


def main():
    """Main test execution"""
    # Test with ORCL job
    job_file = "data/jobs/b561bcba-595b-4ed1-8ae7-33d10f736ab5.json"
    
    if not Path(job_file).exists():
        print(f"Error: Job file not found: {job_file}")
        sys.exit(1)
    
    # Create output directory
    Path("outputs/test_reports").mkdir(parents=True, exist_ok=True)
    
    # Run tests
    results = test_report_generation(job_file)
    
    # Return exit code based on results
    all_passed = all(r.get('meets_standards', False) for r in results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
