"""
Quick diagnostic for PDF corruption issues
"""
from pathlib import Path
import sys

# Check if pdf_sections exist and what they contain
pdf_sections_dir = Path("src/outputs/pdf_sections")

if pdf_sections_dir.exists():
    print(f"✓ pdf_sections directory exists")
    
    files = list(pdf_sections_dir.glob("*.py"))
    print(f"\nFiles in pdf_sections:")
    for f in files:
        print(f"  - {f.name}")
        
    # Check executive_sections specifically
    exec_sections = pdf_sections_dir / "__init__.py"
    if exec_sections.exists():
        print(f"\n✓ __init__.py exists")
        with open(exec_sections) as f:
            content = f.read()
            if "ExecutiveSectionsGenerator" in content:
                print("  - Contains ExecutiveSectionsGenerator")
            if "create_investment_recommendation" in content:
                print("  - Has create_investment_recommendation method")
            if "create_key_findings" in content:
                print("  - Has create_key_findings method")
else:
    print("✗ pdf_sections directory does NOT exist")
    print("\nThis means the modular generators are missing!")
    print("The revolutionary_pdf_generator.py is trying to use:")
    print("  - self.exec_sections.create_investment_recommendation()")
    print("  - self.exec_sections.create_key_findings()")
    print("\nBut these don't exist, so it's falling back to corrupted data.")
