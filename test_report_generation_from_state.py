"""
Test Report Generation from Completed CRWD Analysis State

This script loads the completed CRWD analysis state and generates all reports
to verify the corrected architecture works properly.
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger

from src.outputs.report_generator import ReportGenerator
from src.outputs.report_config import create_report_config


async def test_report_generation():
    """Test report generation with the latest CRWD state"""
    
    print("\n" + "=" * 100)
    print("TESTING REPORT GENERATION - Architecture Verification".center(100))
    print("=" * 100 + "\n")
    
    # Find the most recent complete state file
    output_dir = Path("outputs/crwd_analysis")
    state_files = list(output_dir.glob("crwd_complete_state_*.json"))
    
    if not state_files:
        print("❌ No complete state files found!")
        print(f"   Looking in: {output_dir}")
        return
    
    # Get the most recent
    latest_state_file = max(state_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading state from: {latest_state_file.name}")
    
    # Load state
    with open(latest_state_file, 'r') as f:
        state = json.load(f)
    
    print(f"✅ State loaded successfully")
    print(f"   Deal ID: {state.get('deal_id')}")
    print(f"   Target: {state.get('target_company')} ({state.get('target_ticker')})")
    print(f"   Agents completed: {len(state.get('agent_outputs', []))}")
    print()
    
    # Verify key data is present
    print("🔍 Verifying synthesized data structure...")
    checks = [
        ('financial_data', state.get('financial_data')),
        ('financial_deep_dive', state.get('financial_deep_dive')),
        ('competitive_analysis', state.get('competitive_analysis')),
        ('macroeconomic_analysis', state.get('macroeconomic_analysis')),
        ('normalized_financials', state.get('normalized_financials')),
        ('key_findings', state.get('key_findings')),
        ('metadata.final_synthesis', state.get('metadata', {}).get('final_synthesis'))
    ]
    
    all_present = True
    for key, value in checks:
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {'Present' if value else 'MISSING'}")
        if not value:
            all_present = False
    
    print()
    
    if not all_present:
        print("⚠️  WARNING: Some synthesized data missing. Reports may be incomplete.")
        print()
    
    # Create report configuration
    print("⚙️  Creating report configuration...")
    config = create_report_config(
        target_company=state.get('target_company', 'Unknown'),
        target_ticker=state.get('target_ticker'),
        acquirer_company=state.get('acquirer_company', 'Strategic Acquirer'),
        deal_id=state.get('deal_id', 'UNKNOWN'),
        deal_type='acquisition',
        buyer_type='strategic',
        industry='technology'
    )
    print(f"✅ Config created: {config.report_title}")
    print()
    
    # Initialize report generator
    print("📊 Initializing Report Generator...")
    generator = ReportGenerator(config=config)
    print("✅ Generator initialized")
    print()
    
    # Generate all reports
    print("=" * 100)
    print("GENERATING REPORTS".center(100))
    print("=" * 100 + "\n")
    
    try:
        # Use the unified generate_all_reports method
        print("🔄 Generating all reports...")
        print("-" * 100)
        results = generator.generate_all_reports(state, config)
        
        print()
        print("📊 RESULTS:")
        print("-" * 100)
        
        for format_name, file_path in results.items():
            if file_path.startswith('ERROR:'):
                print(f"   ❌ {format_name.upper()}: {file_path}")
            else:
                print(f"   ✅ {format_name.upper()}: {Path(file_path).name}")
                print(f"      📍 {file_path}")
        
        print()
        
        # Summary
        print("=" * 100)
        print("REPORT GENERATION COMPLETE".center(100))
        print("=" * 100 + "\n")
        
        print("✅ Test completed - Check outputs above for results")
        print()
        print("📋 Next Steps:")
        print("   1. Open generated Excel file and verify all worksheets")
        print("   2. Check that data flows from synthesized state (not agent_outputs)")
        print("   3. If PDF/PPT failed, apply same architecture fix as Excel")
        print()
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        print(f"\n❌ CRITICAL FAILURE: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_report_generation())
