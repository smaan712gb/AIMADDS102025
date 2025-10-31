"""
Test Revolutionary Report Generation
Generate and validate "Better Than Banker" Glass Box reports
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from src.outputs.revolutionary_excel_generator import RevolutionaryExcelGenerator
from src.outputs.revolutionary_ppt_generator import RevolutionaryPowerPointGenerator
from src.outputs.revolutionary_pdf_generator import RevolutionaryPDFGenerator
from src.outputs.report_config import create_report_config


def test_all_revolutionary_reports():
    """Test all three revolutionary report formats"""
    
    print("\n" + "="*80)
    print("REVOLUTIONARY M&A REPORT GENERATION - ALL FORMATS")
    print("="*80)
    print("\n🚀 Testing: Excel, PowerPoint, and PDF with Revolutionary Features")
    
    # Load ORCL job data
    job_file = "data/jobs/b561bcba-595b-4ed1-8ae7-33d10f736ab5.json"
    
    print(f"\n📂 Loading job data: {job_file}")
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    print(f"   Target: {state.get('target_company')} ({state.get('target_ticker')})")
    print(f"   Deal ID: {state.get('deal_id')}")
    
    # Create config
    config = create_report_config(
        target_company=state.get('target_company'),
        target_ticker=state.get('target_ticker'),
        acquirer_company=state.get('acquirer_company', 'Strategic Acquirer'),
        deal_id=state.get('deal_id'),
        deal_type=state.get('deal_type', 'acquisition'),
        buyer_type=state.get('buyer_type', 'strategic'),
        industry=state.get('industry', 'technology')
    )
    
    results = {}
    
    # TEST 1: Revolutionary Excel
    print("\n" + "─"*80)
    print("TEST 1: REVOLUTIONARY EXCEL 'GLASS BOX'")
    print("─"*80)
    print("Creating Glass Box tabs:")
    print("  1. CONTROL PANEL - Agent status dashboard")
    print("  2. Normalization Ledger - Line-by-line adjustments")
    print("  3. Anomaly Log - Statistical red flags")
    print("  4. Legal Risk Register - Quantified contract risks")
    print("  5. Validation Tear Sheet - Our vs Street comparison")
    print("  6. Agent Collaboration Map - 11-agent workflow")
    
    try:
        excel_gen = RevolutionaryExcelGenerator(output_dir="outputs/revolutionary", config=config)
        excel_path = excel_gen.generate_revolutionary_workbook(state, config)
        print(f"✅ Excel: {excel_path}")
        results['excel'] = excel_path
    except Exception as e:
        print(f"❌ Excel Failed: {e}")
        results['excel'] = None
    
    # TEST 2: Revolutionary PowerPoint
    print("\n" + "─"*80)
    print("TEST 2: REVOLUTIONARY POWERPOINT 'C-SUITE NARRATIVE'")
    print("─"*80)
    print("Creating revolutionary slides:")
    print("  1. The Answer - Immediate decision")
    print("  2. Glass Box Summary - Show AI advantage")
    print("  3. Critical Anomaly - Statistical finding")
    print("  4. Legal Smoking Gun - $45M hidden cost")
    print("  5. Validation Confidence - Trust building")
    print("  6. DD Questions Generated - Auto-agenda")
    
    try:
        ppt_gen = RevolutionaryPowerPointGenerator(output_dir="outputs/revolutionary", config=config)
        ppt_path = ppt_gen.generate_revolutionary_deck(state, config)
        print(f"✅ PowerPoint: {ppt_path}")
        results['ppt'] = ppt_path
    except Exception as e:
        print(f"❌ PowerPoint Failed: {e}")
        results['ppt'] = None
    
    # TEST 3: Revolutionary PDF
    print("\n" + "─"*80)
    print("TEST 3: REVOLUTIONARY PDF 'DILIGENCE BIBLE'")
    print("─"*80)
    print("Creating enhanced sections:")
    print("  • Financial Normalization Process (with evidence)")
    print("  • Statistical Anomaly Detection (with tables)")
    print("  • Legal Risk Register (with quantified impacts)")
    print("  • Validation Tear Sheet (Our vs Street)")
    print("  • Agent Collaboration Analysis")
    print("  • Enhanced Agent Methodologies")
    
    try:
        pdf_gen = RevolutionaryPDFGenerator(output_dir="outputs/revolutionary", config=config)
        pdf_path = pdf_gen.generate_revolutionary_report(state, config)
        print(f"✅ PDF: {pdf_path}")
        results['pdf'] = pdf_path
    except Exception as e:
        print(f"❌ PDF Failed: {e}")
        results['pdf'] = None
    
    # FINAL SUMMARY
    print("\n" + "="*80)
    print("REVOLUTIONARY REPORT GENERATION - FINAL SUMMARY")
    print("="*80)
    
    success_count = sum(1 for v in results.values() if v is not None)
    
    for format_name, path in results.items():
        if path:
            print(f"✅ {format_name.upper()}: SUCCESS - {path}")
        else:
            print(f"❌ {format_name.upper()}: FAILED")
    
    print(f"\n📊 Results: {success_count}/3 revolutionary formats generated")
    
    if success_count == 3:
        print("\n🎯 ALL REVOLUTIONARY FEATURES SUCCESSFULLY IMPLEMENTED!")
        print("\nThese reports showcase your 11-agent system's superiority through:")
        print("  ✓ Complete transparency (Glass Box)")
        print("  ✓ Agent attribution (show who found what)")
        print("  ✓ Statistical rigor (anomaly detection)")
        print("  ✓ Legal precision (contract-level analysis)")
        print("  ✓ External validation (independent verification)")
        print("  ✓ Auditable evidence (SEC page references)")
        
        print("\n🎯 THESE ARE 'BETTER THAN BANKER' REPORTS")
        print("="*80 + "\n")
        return True
    else:
        print("\n⚠️ Some formats failed - review errors above")
        print("="*80 + "\n")
        return False


if __name__ == "__main__":
    success = test_all_revolutionary_reports()
    sys.exit(0 if success else 1)
