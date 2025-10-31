# PDF Generator Guide

## Overview
The PDF Generator creates professional, investment banking-quality PDF reports from M&A due diligence analysis data.

## Features

### Executive Summary (2-3 pages)
- Cover page with confidentiality notice
- Executive overview
- Key performance indicators with traffic light indicators
- Financial highlights
- Investment recommendation with rationale
- Critical findings
- Risk summary

### Full Report (25-35 pages)
- Professional cover page
- Table of contents with page numbers
- 10 comprehensive sections:
  1. Executive Summary
  2. Deal Overview
  3. Financial Analysis
  4. **Financial Deep Dive** (Working Capital, CapEx, Debt)
  5. Valuation Analysis (DCF models)
  6. Competitive Benchmarking
  7. Macroeconomic Analysis
  8. **External Validation** (with confidence scores)
  9. Risk Assessment
  10. Investment Recommendation
- Appendix with methodology and assumptions

## Usage

```python
from src.outputs.pdf_generator import PDFGenerator
from src.core.state import DiligenceState

# Initialize generator
pdf_gen = PDFGenerator(output_dir="outputs")

# Generate executive summary (2-3 pages)
exec_summary_path = pdf_gen.generate_executive_summary(state)
print(f"Executive summary saved to: {exec_summary_path}")

# Generate full report (25-35 pages)
full_report_path = pdf_gen.generate_full_report(state)
print(f"Full report saved to: {full_report_path}")
```

## Report Structure

### Professional Formatting
- **Color Scheme**: Investment banking blue/grey theme
- **Typography**: Helvetica font family for professional appearance
- **Tables**: Professional styled tables with headers
- **Traffic Lights**: Visual indicators (GREEN/YELLOW/RED) for KPIs

### Data Sources
The PDF generator reads from `DiligenceState` object containing:
- `financial_deep_dive`: Working capital, CapEx, debt analysis
- `financial_metrics`: Revenue, EBITDA, ROE, ROA
- `valuation_models`: DCF valuations
- `competitive_analysis`: Peer benchmarking
- `agent_outputs`: External validator results
- `critical_risks`: Risk assessment
- `key_findings`: Critical findings

## Output Files

PDFs are saved with descriptive filenames:
- `{deal_id}_Executive_Summary_{date}.pdf`
- `{deal_id}_Full_Due_Diligence_Report_{date}.pdf`

Example:
- `CRWD_Executive_Summary_20251021.pdf`
- `CRWD_Full_Due_Diligence_Report_20251021.pdf`

## Professional Features

### Traffic Light Indicators
- **GREEN**: Strong performance (>70%)
- **YELLOW**: Moderate performance (50-70%)
- **RED**: Weak performance (<50%)

### Key Sections

#### Financial Deep Dive
- Working capital efficiency analysis
- Cash conversion cycle metrics
- CapEx intensity and asset analysis
- Debt structure and leverage ratios

#### External Validation
- Confidence score from external sources
- Number of findings validated
- Critical discrepancies identified
- Reanalysis recommendations

### Confidentiality
Every report includes prominent confidentiality notices on the cover page.

## Integration with Excel & PowerPoint

The PDF generator works alongside:
- **Excel Generator** (`excel_generator.py`): 13 detailed worksheets
- **PowerPoint Generator** (`ppt_generator.py`): Coming in Phase 3

All three formats read from the same `DiligenceState` for consistency.

## Requirements

Libraries used:
- `reportlab`: PDF generation
- `matplotlib`: Chart generation (prepared for future use)
- `loguru`: Logging

## Next Steps

1. Test with production CRWD data
2. Add embedded charts (matplotlib integration)
3. Create unified report interface
4. Build PowerPoint generator (Phase 3)

## Example Output Structure

```
outputs/
├── CRWD_Executive_Summary_20251021.pdf          # 2-3 pages
├── CRWD_Full_Due_Diligence_Report_20251021.pdf  # 25-35 pages
└── CRWD_Financial_Analysis_20251021.xlsx        # 13 worksheets
```

## Notes

- All monetary values are formatted with commas and currency symbols
- Percentages are formatted with 2 decimal places
- Large text blocks are truncated/wrapped appropriately
- Page numbers appear at the bottom center of each page
- Headers use consistent styling throughout
