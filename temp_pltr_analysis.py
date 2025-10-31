#!/usr/bin/env python3
"""
Analyze PLTR reports for missing information
"""
import PyPDF2
import pandas as pd
import json
from pathlib import Path

def analyze_pltr_pdf():
    """Analyze PLTR PDF for missing sections"""
    pdf_path = 'frontend_results/report_dd085132-03af-4ca8-ba94-f7ac057f50eb.pdf'

    missing_sections = []

    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()

            # Check for known incomplete sections
            if 'Competitive Benchmarking' in text and ('N/A' in text or 'Under analysis' in text or 'Analysis in progress' in text.lower()):
                missing_sections.append('6. COMPETITIVE BENCHMARKING - Missing market share, position, and competitor data')

            if 'Macroeconomic Analysis' in text and 'analysis in progress' in text.lower():
                missing_sections.append('7. MACROECONOMIC ANALYSIS - No macroeconomic analysis provided')

            if 'Risk Assessment' in text and 'in progress' in text.lower():
                missing_sections.append('9. RISK ASSESSMENT - Risk assessment not completed')

            # Check for incomplete data tables
            if 'SWOT Analysis:' in text and '0,"overall_risk"' in text:
                missing_sections.append('SWOT ANALYSIS - Contains incomplete/opportunistic data fragment')

            if 'Key Financial Ratios:' in text and not any(char.isdigit() for char in text):
                missing_sections.append('FINANCIAL RATIOS - No financial ratios provided')

    return missing_sections

def analyze_pltr_excel():
    """Analyze PLTR Excel for completeness"""
    excel_path = 'frontend_results/report_dd085132-03af-4ca8-ba94-f7ac057f50eb.xlsx'

    issues = []

    try:
        xl = pd.ExcelFile(excel_path)

        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)

            # Check for empty or minimal data
            if df.empty or len(df) < 2:
                issues.append(f'Sheet "{sheet_name}" - Empty or minimal data')
                continue

            # Check for placeholder values
            placeholders = ['N/A', 'TBD', 'Pending', 'placeholder', None]
            empty_cells = df.isnull().sum().sum() + sum(df.astype(str).isin(placeholders).sum())
            total_cells = df.size

            if empty_cells / total_cells > 0.5:  # More than 50% empty
                issues.append(f'Sheet "{sheet_name}" - {empty_cells}/{total_cells} empty/placeholder cells ({empty_cells/total_cells*100:.1f}%)')

            # Check for key financial metrics
            financial_cols = [col for col in df.columns if any(term in col.lower() for term in ['revenue', 'ebitda', 'margin', 'valuation', 'price', 'multiple'])]

            for col in financial_cols:
                if df[col].isnull().all():
                    issues.append(f'Sheet "{sheet_name}" - Financial column "{col}" is completely empty')

    except Exception as e:
        issues.append(f'Excel analysis failed: {e}')

    return issues

def check_ppt_content():
    """Try to extract some content from PPT"""
    ppt_path = r'frontend_results\report_dd085132-03af-4ca8-ba94-f7ac057f50eb.pptx'

    # Since PPTX text extraction didn't work earlier, we'll note this limitation
    return ['Cannot directly extract text from PPTX - manual review needed']

def main():
    """Main analysis"""

    print("=== PLTR REPORT ANALYSIS ===")
    print()

    print("PDF ANALYSIS:")
    pdf_issues = analyze_pltr_pdf()
    for issue in pdf_issues:
        print(f"  ⚠️  {issue}")

    print()
    print("EXCEL ANALYSIS:")
    excel_issues = analyze_pltr_excel()
    for issue in excel_issues:
        print(f"  ⚠️  {issue}")

    print()
    print("PPT ANALYSIS:")
    ppt_issues = check_ppt_content()
    for issue in ppt_issues:
        print(f"  ⚠️  {issue}")

    print()
    print("=== FIX PLAN ===")

    all_issues = pdf_issues + excel_issues + ppt_issues

    if pdf_issues:
        print("1. FIX PDF ISSUES:")
        print("   - Implement competitive benchmarking agent with market share calculations")
        print("   - Complete macroeconomic analysis with GDP, inflation, industry impacts")
        print("   - Finish risk assessment with comprehensive risk register")
        print("   - Remove incomplete data fragments from SWOT analysis")
        print("   - Add financial ratios in deep dive section")
        print()

    if excel_issues:
        print("2. FIX EXCEL ISSUES:")
        print("   - Populate empty sheets with historical financial data")
        print("   - Calculate missing financial metrics and ratios")
        print("   - Ensure all valuation models have complete input data")
        print("   - Add scenario analysis data")
        print()

    if ppt_issues:
        print("3. FIX PPT ISSUES:")
        print("   - Verify PPT generation includes all completed sections")
        print("   - Add slides for missing analysis areas")
        print("   - Ensure visual elements match PDF content")
        print()

    print("=== AGENTS NEEDING FIXES ===")
    print("- competitive_benchmarking.py - Add market analysis logic")
    print("- macroeconomic_analyst.py - Implement scenario analysis")
    print("- risk_assessment.py - Complete risk quantification")

    return all_issues

if __name__ == "__main__":
    issues = main()
    print(f"\nTotal issues found: {len(issues)}")
