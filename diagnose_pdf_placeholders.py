"""
Diagnostic Script: Analyze PDF for Placeholder Text
Extracts text from PDF and identifies which sections have placeholders vs real data
"""

import PyPDF2
import re
from pathlib import Path
from datetime import datetime

def extract_pdf_text(pdf_path):
    """Extract all text from PDF"""
    text_by_page = []
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            text_by_page.append({
                'page': page_num,
                'text': text
            })
    
    return text_by_page

def identify_placeholder_sections(text_by_page):
    """Identify sections with placeholder text"""
    
    # Known placeholder patterns
    placeholder_patterns = [
        r'placeholder',
        r'Key metrics dashboard placeholder',
        r'Deal overview placeholder',
        r'Financial overview placeholder',
        r'Financial deep dive placeholder',
        r'Competitive analysis placeholder',
        r'Macroeconomic analysis placeholder',
        r'External validation placeholder',
        r'Risk assessment placeholder',
        r'Investment recommendation placeholder',
        r'Critical findings placeholder'
    ]
    
    # Section headers to track
    section_headers = [
        '1. EXECUTIVE SUMMARY',
        '2. DEAL OVERVIEW',
        '3. FINANCIAL ANALYSIS',
        '3A. FINANCIAL NORMALIZATION PROCESS',
        '3B. STATISTICAL ANOMALY DETECTION',
        '4. FINANCIAL DEEP DIVE',
        '5. VALUATION ANALYSIS',
        '5A. LBO ANALYSIS',
        '6. COMPETITIVE BENCHMARKING',
        '7. MACROECONOMIC ANALYSIS',
        '8. EXTERNAL VALIDATION',
        '8A. VALIDATION TEAR SHEET',
        '9. RISK ASSESSMENT',
        '9A. LEGAL RISK REGISTER',
        '9B. TAX STRUCTURING RECOMMENDATION',
        '10. INVESTMENT RECOMMENDATION',
        '11. AGENT COLLABORATION ANALYSIS'
    ]
    
    findings = {
        'has_placeholders': False,
        'placeholder_sections': [],
        'sections_with_data': [],
        'sections_analyzed': []
    }
    
    current_section = None
    
    for page_info in text_by_page:
        page_num = page_info['page']
        text = page_info['text']
        
        # Check for section headers
        for header in section_headers:
            if header in text:
                current_section = header
                findings['sections_analyzed'].append({
                    'section': header,
                    'page': page_num
                })
        
        # Check for placeholders
        for pattern in placeholder_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings['has_placeholders'] = True
                findings['placeholder_sections'].append({
                    'section': current_section or 'Unknown',
                    'page': page_num,
                    'pattern_found': pattern,
                    'context': text[:200]
                })
        
        # Check for real data indicators
        real_data_patterns = [
            r'\$\d+\.?\d*[BMK]',  # Dollar amounts
            r'\d+\.\d+%',  # Percentages
            r'DCF.*\$\d+',  # DCF with values
            r'EBITDA.*\$\d+',  # EBITDA with values
            r'Enterprise Value.*\$\d+',  # EV with values
        ]
        
        for pattern in real_data_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if current_section:
                    if current_section not in [s['section'] for s in findings['sections_with_data']]:
                        findings['sections_with_data'].append({
                            'section': current_section,
                            'page': page_num,
                            'has_numbers': True
                        })
    
    return findings

def main():
    """Main diagnostic function"""
    
    # Find most recent HOOD PDF
    pdf_path = Path("outputs/hood_analysis/revolutionary/HOOD_REVOLUTIONARY_Report_20251023.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"🔍 Analyzing PDF: {pdf_path}")
    print(f"📄 File size: {pdf_path.stat().st_size / 1024:.1f} KB")
    print("="*80)
    
    # Extract text
    print("\n📖 Extracting text from PDF...")
    text_by_page = extract_pdf_text(pdf_path)
    print(f"✓ Extracted {len(text_by_page)} pages")
    
    # Analyze for placeholders
    print("\n🔍 Analyzing for placeholders...")
    findings = identify_placeholder_sections(text_by_page)
    
    # Report findings
    print("\n" + "="*80)
    print("📊 ANALYSIS RESULTS")
    print("="*80)
    
    print(f"\n{'HAS PLACEHOLDERS:' : <30} {'YES ❌' if findings['has_placeholders'] else 'NO ✓'}")
    print(f"{'Total sections analyzed:' : <30} {len(findings['sections_analyzed'])}")
    print(f"{'Sections with data:' : <30} {len(findings['sections_with_data'])}")
    print(f"{'Sections with placeholders:' : <30} {len(findings['placeholder_sections'])}")
    
    if findings['placeholder_sections']:
        print("\n🚨 PLACEHOLDER SECTIONS FOUND:")
        print("-"*80)
        for item in findings['placeholder_sections']:
            print(f"\nSection: {item['section']}")
            print(f"Page: {item['page']}")
            print(f"Pattern: {item['pattern_found']}")
            print(f"Context: {item['context'][:150]}...")
    
    if findings['sections_with_data']:
        print("\n✓ SECTIONS WITH REAL DATA:")
        print("-"*80)
        for item in findings['sections_with_data']:
            print(f"  • {item['section']} (Page {item['page']})")
    
    # Summary
    print("\n" + "="*80)
    print("📋 SUMMARY")
    print("="*80)
    
    if findings['has_placeholders']:
        print("⚠️  PDF contains placeholder text in the following sections:")
        unique_sections = list(set([p['section'] for p in findings['placeholder_sections']]))
        for section in unique_sections:
            print(f"   - {section}")
        print(f"\n❌ TOTAL: {len(unique_sections)} sections need real data extraction")
    else:
        print("✅ NO PLACEHOLDERS FOUND - All sections contain real data!")
    
    # Save detailed report
    report_path = f"pdf_placeholder_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("PDF PLACEHOLDER DIAGNOSTIC REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"PDF: {pdf_path}\n")
        f.write(f"Analysis Time: {datetime.now()}\n\n")
        
        f.write(f"Has Placeholders: {findings['has_placeholders']}\n")
        f.write(f"Total Sections: {len(findings['sections_analyzed'])}\n")
        f.write(f"Sections with Data: {len(findings['sections_with_data'])}\n")
        f.write(f"Sections with Placeholders: {len(findings['placeholder_sections'])}\n\n")
        
        f.write("\nDETAILED FINDINGS:\n")
        f.write("-"*80 + "\n")
        
        for finding in findings['placeholder_sections']:
            f.write(f"\nSection: {finding['section']}\n")
            f.write(f"Page: {finding['page']}\n")
            f.write(f"Pattern: {finding['pattern_found']}\n")
            f.write(f"Context: {finding['context']}\n")
            f.write("-"*80 + "\n")
    
    print(f"\n📝 Detailed report saved to: {report_path}")

if __name__ == "__main__":
    main()
