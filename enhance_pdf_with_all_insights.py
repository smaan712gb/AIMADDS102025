"""
Enhanced PDF Generator - Shows ALL Agent Insights
Including sensitivity matrices, Monte Carlo details, LBO tables, etc.
"""
import json
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.colors import HexColor

def load_job_data(job_id: str) -> dict:
    """Load job data"""
    with open(f"data/jobs/{job_id}.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def get_agent_data(job_data: dict, agent_name: str) -> dict:
    """Extract specific agent data"""
    for output in job_data.get('agent_outputs', []):
        if output.get('agent_name') == agent_name and output.get('data'):
            return output['data']
    return {}

def format_currency(value: float, decimals: int = 1) -> str:
    """Format currency in billions/trillions"""
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"${'-' if value < 0 else ''}${abs_val/1e12:.{decimals}f}T"
    elif abs_val >= 1e9:
        return f"${'-' if value < 0 else ''}{abs_val/1e9:.{decimals}f}B"
    elif abs_val >= 1e6:
        return f"${'-' if value < 0 else ''}{abs_val/1e6:.{decimals}f}M"
    else:
        return f"${'-' if value < 0 else ''}{abs_val:,.0f}"

def create_enhanced_pdf(job_id: str, output_path: str):
    """Create enhanced PDF with ALL insights"""
    
    # Load data
    job_data = load_job_data(job_id)
    fa_data = get_agent_data(job_data, 'financial_analyst')
    fdd_data = get_agent_data(job_data, 'financial_deep_dive')
    comp_data = get_agent_data(job_data, 'competitive_benchmarking')
    macro_data = get_agent_data(job_data, 'macroeconomic_analyst')
    risk_data = get_agent_data(job_data, 'risk_assessment')
    tax_data = get_agent_data(job_data, 'tax_structuring')
    val_data = get_agent_data(job_data, 'external_validator')
    
    # Setup PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(
        "COMPLETE M&A DUE DILIGENCE REPORT<br/>CRWV Analysis - All Agent Insights",
        ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=20, spaceAfter=12)
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Table of contents with ALL sections
    story.append(Paragraph("COMPLETE TABLE OF CONTENTS", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    toc_data = [
        ["1. Executive Summary", "Enhanced with all agent contributions"],
        ["2. Financial Analysis - Complete", "Revenue, EBITDA, margins, ratios"],
        ["3. DCF Valuation - 3 Scenarios", "Base/Bull/Bear with full assumptions"],
        ["4. Sensitivity Analysis - 5x5 Matrix", "WACC x Terminal Growth grid"],
        ["5. Monte Carlo Simulation", "10,000 iterations, percentiles, CI"],
        ["6. LBO Analysis - Complete", "Entry, projections, returns, sensitivity"],
        ["7. LBO Sensitivity Matrices", "5x5 IRR and MoM grids"],
        ["8. Working Capital Deep Dive", "CCC -561 days breakdown"],
        ["9. CapEx Analysis", "732% intensity, growth vs maintenance"],
        ["10. Debt Structure", "Maturity schedule, covenants, coverage"],
        ["11. Competitive Benchmarking", "10 peers, detailed rankings"],
        ["12. Macroeconomic Scenarios", "4 scenarios with projections"],
        ["13. Risk Assessment - 9 Risks", "Detailed matrix with mitigations"],
        ["14. External Validation", "4 findings, 22% confidence"],
        ["15. Tax Structuring", "3 options, NPV analysis"],
        ["16. Investment Recommendation", "RENEGOTIATE with rationale"],
    ]
    
    t
