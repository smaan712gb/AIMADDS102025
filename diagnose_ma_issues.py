"""
Diagnose M&A tabs and data flow issues
"""
from pathlib import Path

def main():
    print("=" * 80)
    print("M&A TABS AND DATA FLOW DIAGNOSIS")
    print("=" * 80)
    
    # Check if tabs were added
    excel_file = Path("src/outputs/revolutionary_excel_generator.py")
    content = excel_file.read_text(encoding='utf-8')
    
    print("\n1. CHECKING EXCEL GENERATOR:")
    print("-" * 80)
    
    # Check for methods
    methods_added = {
        'Sources & Uses': '_create_sources_uses_tab' in content,
        'Deal Structure': '_create_deal_structure_tab' in content,
        'Contribution Analysis': '_create_contribution_analysis_tab' in content,
        'Exchange Ratio': '_create_exchange_ratio_tab' in content,
    }
    
    for tab_name, exists in methods_added.items():
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {tab_name} method: {status}")
    
    # Check if tabs in list
    tabs_in_list = {
        'Sources & Uses': '("Sources & Uses", self._create_sources_uses_tab)' in content,
        'Deal Structure': '("Deal Structure", self._create_deal_structure_tab)' in content,
        'Contribution Analysis': '("Contribution Analysis", self._create_contribution_analysis_tab)' in content,
        'Exchange Ratio': '("Exchange Ratio", self._create_exchange_ratio_tab)' in content,
    }
    
    print("\n  Tabs in all_sheets list:")
    for tab_name, exists in tabs_in_list.items():
        status = "✓ ADDED" if exists else "✗ MISSING"
        print(f"    {tab_name}: {status}")
    
    # Check data flow issues
    print("\n2. CHECKING DATA FLOW ISSUES:")
    print("-" * 80)
    
    # Check orchestrator for acquirer data storage
    orch_file = Path("src/api/orchestrator.py")
    if orch_file.exists():
        orch_content = orch_file.read_text(encoding='utf-8')
        acquirer_storage = "state['acquirer_data']" in orch_content
        print(f"  Acquirer data storage: {'✓ IMPLEMENTED' if acquirer_storage else '✗ MISSING'}")
        
        # Check if M&A agents in workflow
        ma_agents = ['sources_uses', 'deal_structuring', 'contribution_analysis', 'exchange_ratio_analysis']
        for agent in ma_agents:
            agent_in_workflow = agent in orch_content
            print(f"  {agent} in orchestrator: {'✓ YES' if agent_in_workflow else '✗ NO'}")
    
    # Check synergy calculator
    synergy_file = Path("src/utils/synergy_calculator.py")
    if synergy_file.exists():
        synergy_content = synergy_file.read_text(encoding='utf-8')
        has_numeric_output = 'return total_synergies' in synergy_content or 'return revenue_synergies' in synergy_content
        print(f"\n  Synergy calculator returns numeric: {'✓ YES' if has_numeric_output else '✗ NO (returns dict)'}")
    
    # Summary
    print("\n3. SUMMARY:")
    print("-" * 80)
    
    all_methods = all(methods_added.values())
    all_in_list = all(tabs_in_list.values())
    
    if all_methods and all_in_list:
        print("  ✓ All M&A tabs properly added to Excel generator")
    else:
        print("  ✗ M&A tabs NOT properly added")
        if not all_methods:
            print("    - Some methods missing")
        if not all_in_list:
            print("    - Some tabs not in all_sheets list")
    
    print("\n4. ISSUES IDENTIFIED:")
    print("-" * 80)
    print("  From screenshot and logs:")
    print("  1. Acquirer data showing $0.00 (data flow issue)")
    print("  2. Synergy data format warnings (dict vs numeric)")
    print("  3. PDF generation failed")
    print("  4. M&A tabs may not be showing in Excel output")
    
    print("\n5. RECOMMENDED FIXES:")
    print("-" * 80)
    print("  Priority 1: Fix acquirer data flow in orchestrator")
    print("  Priority 2: Fix synergy calculator output format")
    print("  Priority 3: Verify tabs showing in Excel (check file size)")
    print("  Priority 4: Fix PDF generation errors")

if __name__ == "__main__":
    main()
