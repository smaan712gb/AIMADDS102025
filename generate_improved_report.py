"""
Generate Improved Due Diligence Report
Fixes data extraction and presentation issues in PDF reports
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ImprovedReportGenerator:
    """Generate properly formatted due diligence reports"""
    
    def __init__(self, job_file: str):
        self.job_file = Path(job_file)
        with open(self.job_file, 'r', encoding='utf-8') as f:
            self.job_data = json.load(f)
    
    def format_currency(self, value: Optional[float]) -> str:
        """Format currency values"""
        if value is None or value == 0:
            return "N/A"
        
        if abs(value) >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        elif abs(value) >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        elif abs(value) >= 1_000:
            return f"${value / 1_000:.2f}K"
        else:
            return f"${value:,.2f}"
    
    def format_percentage(self, value: Optional[float]) -> str:
        """Format percentage values"""
        if value is None:
            return "N/A"
        return f"{value * 100:.1f}%"
    
    def format_number(self, value: Optional[float], decimals: int = 2) -> str:
        """Format numeric values"""
        if value is None:
            return "N/A"
        return f"{value:,.{decimals}f}"
    
    def get_status_indicator(self, value: float, good_threshold: float, bad_threshold: float, 
                           higher_is_better: bool = True) -> str:
        """Get status indicator (GREEN/YELLOW/RED)"""
        if value is None:
            return "N/A"
        
        if higher_is_better:
            if value >= good_threshold:
                return "GREEN"
            elif value >= bad_threshold:
                return "YELLOW"
            else:
                return "RED"
        else:
            if value <= good_threshold:
                return "GREEN"
            elif value <= bad_threshold:
                return "YELLOW"
            else:
                return "RED"
    
    def extract_financial_summary(self) -> Dict[str, Any]:
        """Extract key financial metrics"""
        try:
            # Get latest financials
            normalized_income = self.job_data.get('normalized_financials', {}).get('normalized_income', [])
            normalized_balance = self.job_data.get('normalized_financials', {}).get('normalized_balance', [])
            normalized_cash = self.job_data.get('normalized_financials', {}).get('normalized_cashflow', [])
            
            latest_income = normalized_income[0] if normalized_income else {}
            latest_balance = normalized_balance[0] if normalized_balance else {}
            latest_cash = normalized_cash[0] if normalized_cash else {}
            
            # Get financial metrics
            metrics = self.job_data.get('financial_metrics', {})
            
            return {
                'revenue': latest_income.get('revenue', 0),
                'net_income': latest_income.get('netIncome', 0),
                'operating_income': latest_income.get('operatingIncome', 0),
                'ebitda': latest_income.get('ebitda', 0),
                'gross_margin': latest_income.get('grossProfitRatio', 0),
                'operating_margin': latest_income.get('operatingIncomeRatio', 0),
                'net_margin': latest_income.get('netIncomeRatio', 0),
                'total_assets': latest_balance.get('totalAssets', 0),
                'total_equity': latest_balance.get('totalEquity', 0),
                'total_debt': latest_balance.get('totalDebt', 0),
                'cash': latest_balance.get('cashAndCashEquivalents', 0),
                'operating_cashflow': latest_cash.get('operatingCashFlow', 0),
                'fcf': latest_cash.get('freeCashFlow', 0),
                'capex': abs(latest_cash.get('capitalExpenditure', 0)),
                'date': latest_income.get('date', 'Unknown'),
            }
        except Exception as e:
            print(f"Error extracting financial summary: {e}")
            return {}
    
    def extract_valuation_summary(self) -> Dict[str, Any]:
        """Extract valuation metrics"""
        try:
            valuation = self.job_data.get('valuation_models', {}).get('dcf_advanced', {})
            dcf_base = valuation.get('dcf_analysis', {}).get('base', {})
            
            return {
                'enterprise_value': dcf_base.get('enterprise_value', 0),
                'equity_value': dcf_base.get('equity_value', 0),
                'wacc': dcf_base.get('wacc', 0),
                'terminal_growth': dcf_base.get('terminal_growth_rate', 0),
            }
        except Exception as e:
            print(f"Error extracting valuation summary: {e}")
            return {}
    
    def extract_deep_dive_summary(self) -> Dict[str, Any]:
        """Extract financial deep dive metrics"""
        try:
            deep_dive = self.job_data.get('financial_deep_dive', {})
            
            # Working capital
            wc_analysis = deep_dive.get('working_capital', {}).get('nwc_analysis', {})
            wc_efficiency = wc_analysis.get('nwc_efficiency_score', 0)
            cash_conversion = wc_analysis.get('cash_conversion_cycle', {}).get('current', 0)
            
            # CapEx
            capex_data = deep_dive.get('capex_analysis', {}).get('capex_analysis', {})
            total_capex = capex_data.get('total_capex_5yr', 0)
            avg_capex_pct = capex_data.get('avg_capex_pct_revenue', 0)
            
            # Debt
            debt_data = deep_dive.get('debt_analysis', {}).get('debt_structure', {})
            total_debt = debt_data.get('total_debt', 0)
            debt_equity = debt_data.get('debt_to_equity', 0)
            interest_coverage = debt_data.get('interest_coverage', 0)
            
            return {
                'wc_efficiency': wc_efficiency,
                'cash_conversion_cycle': cash_conversion,
                'total_capex': total_capex,
                'capex_pct_revenue': avg_capex_pct * 100 if avg_capex_pct else 0,
                'total_debt': total_debt,
                'debt_equity': debt_equity,
                'interest_coverage': interest_coverage,
            }
        except Exception as e:
            print(f"Error extracting deep dive summary: {e}")
            return {}
    
    def extract_competitive_summary(self) -> Dict[str, Any]:
        """Extract competitive analysis summary"""
        try:
            competitive = self.job_data.get('competitive_analysis', {})
            summary = competitive.get('summary', {})
            position = competitive.get('competitive_position', {})
            
            return {
                'competitive_position': summary.get('competitive_position', 'Unknown'),
                'sector': summary.get('sector', 'Unknown'),
                'peers_analyzed': summary.get('peers_analyzed', 0),
                'overall_rating': position.get('overall_rating', 'Unknown'),
                'strengths': position.get('strengths', []),
                'weaknesses': position.get('weaknesses', []),
            }
        except Exception as e:
            print(f"Error extracting competitive summary: {e}")
            return {}
    
    def extract_macro_summary(self) -> Dict[str, Any]:
        """Extract macroeconomic analysis summary"""
        try:
            macro = self.job_data.get('macroeconomic_analysis', {})
            conditions = macro.get('current_economic_conditions', {})
            insights = macro.get('insights', [])
            
            return {
                'treasury_10y': conditions.get('treasury_10y', 0),
                'gdp_growth': conditions.get('gdp_growth', 0),
                'inflation': conditions.get('inflation_rate', 0),
                'unemployment': conditions.get('unemployment_rate', 0),
                'insights': insights[:3] if insights else [],
            }
        except Exception as e:
            print(f"Error extracting macro summary: {e}")
            return {}
    
    def extract_external_validation(self) -> Dict[str, Any]:
        """Extract external validation summary"""
        try:
            # Try to find external validation in agent outputs
            agent_outputs = self.job_data.get('agent_outputs', [])
            
            for output in agent_outputs:
                if output.get('agent_name') == 'external_validator':
                    validation = output.get('data', {})
                    return {
                        'confidence_score': validation.get('confidence_score', 0),
                        'findings_validated': validation.get('findings_validated', 0),
                        'discrepancies': validation.get('critical_discrepancies', 0),
                        'overall_assessment': validation.get('overall_assessment', 'Not available'),
                    }
            
            return {
                'confidence_score': 0,
                'findings_validated': 0,
                'discrepancies': 0,
                'overall_assessment': 'External validation not available',
            }
        except Exception as e:
            print(f"Error extracting validation: {e}")
            return {}
    
    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report"""
        
        # Extract all data
        deal_info = {
            'deal_id': self.job_data.get('deal_id', 'Unknown'),
            'target': self.job_data.get('target_company', 'Unknown'),
            'ticker': self.job_data.get('target_ticker', 'Unknown'),
            'acquirer': self.job_data.get('acquirer_company', 'Unknown'),
            'deal_type': self.job_data.get('deal_type', 'Unknown').title(),
        }
        
        financials = self.extract_financial_summary()
        valuation = self.extract_valuation_summary()
        deep_dive = self.extract_deep_dive_summary()
        competitive = self.extract_competitive_summary()
        macro = self.extract_macro_summary()
        validation = self.extract_external_validation()
        
        # Get executive summary and recommendations
        exec_summary = self.job_data.get('executive_summary', 'Not available')
        recommendations = self.job_data.get('recommendations', [])
        
        # Build report
        report = f"""# COMPREHENSIVE DUE DILIGENCE REPORT

**Target:** {deal_info['target']} ({deal_info['ticker']})  
**Deal ID:** {deal_info['deal_id']}  
**Acquirer:** {deal_info['acquirer']}  
**Deal Type:** {deal_info['deal_type']}  
**Analysis Date:** {datetime.now().strftime('%B %d, %Y')}

---

## EXECUTIVE SUMMARY

### Deal Overview

| Parameter | Value |
|-----------|-------|
| Target Company | {deal_info['target']} |
| Ticker | {deal_info['ticker']} |
| Acquirer | {deal_info['acquirer']} |
| Deal Type | {deal_info['deal_type']} |
| Industry | {competitive.get('sector', 'Unknown')} |

### Key Performance Indicators

| Category | Metric | Value | Status |
|----------|--------|-------|--------|
| **Financial Scale** | Annual Revenue | {self.format_currency(financials.get('revenue'))} | {self.get_status_indicator(financials.get('revenue', 0), 10_000_000_000, 1_000_000_000)} |
| **Profitability** | Net Income | {self.format_currency(financials.get('net_income'))} | {self.get_status_indicator(financials.get('net_margin', 0), 0.15, 0.05)} |
| **Margins** | Operating Margin | {self.format_percentage(financials.get('operating_margin'))} | {self.get_status_indicator(financials.get('operating_margin', 0), 0.20, 0.10)} |
| **Margins** | Net Margin | {self.format_percentage(financials.get('net_margin'))} | {self.get_status_indicator(financials.get('net_margin', 0), 0.15, 0.05)} |
| **Cash Flow** | Free Cash Flow | {self.format_currency(financials.get('fcf'))} | {self.get_status_indicator(financials.get('fcf', 0), 5_000_000_000, 1_000_000_000)} |
| **Working Capital** | WC Efficiency | {self.format_number(deep_dive.get('wc_efficiency', 0), 0)}/100 | {self.get_status_indicator(deep_dive.get('wc_efficiency', 0), 80, 60)} |
| **Operations** | Cash Conversion Cycle | {self.format_number(deep_dive.get('cash_conversion_cycle', 0), 0)} days | {self.get_status_indicator(abs(deep_dive.get('cash_conversion_cycle', 0)), 30, 60, False)} |
| **Leverage** | Debt/Equity Ratio | {self.format_number(deep_dive.get('debt_equity', 0), 2)}x | {self.get_status_indicator(deep_dive.get('debt_equity', 0), 2.0, 3.5, False)} |
| **Leverage** | Interest Coverage | {self.format_number(deep_dive.get('interest_coverage', 0), 1)}x | {self.get_status_indicator(deep_dive.get('interest_coverage', 0), 5.0, 2.5)} |
| **Validation** | Confidence Score | {self.format_percentage(validation.get('confidence_score', 0) / 100)} | {self.get_status_indicator(validation.get('confidence_score', 0), 70, 50)} |

---

## DETAILED FINANCIAL ANALYSIS

### Income Statement Summary (Latest: {financials.get('date', 'N/A')})

| Metric | Value | Margin |
|--------|-------|--------|
| **Revenue** | {self.format_currency(financials.get('revenue'))} | 100.0% |
| **Gross Profit** | {self.format_currency(financials.get('revenue', 0) * financials.get('gross_margin', 0))} | {self.format_percentage(financials.get('gross_margin'))} |
| **Operating Income** | {self.format_currency(financials.get('operating_income'))} | {self.format_percentage(financials.get('operating_margin'))} |
| **EBITDA** | {self.format_currency(financials.get('ebitda'))} | {self.format_percentage(financials.get('ebitda', 0) / financials.get('revenue', 1) if financials.get('revenue') else 0)} |
| **Net Income** | {self.format_currency(financials.get('net_income'))} | {self.format_percentage(financials.get('net_margin'))} |

### Balance Sheet Summary

| Metric | Value |
|--------|-------|
| **Total Assets** | {self.format_currency(financials.get('total_assets'))} |
| **Total Equity** | {self.format_currency(financials.get('total_equity'))} |
| **Total Debt** | {self.format_currency(financials.get('total_debt'))} |
| **Cash & Equivalents** | {self.format_currency(financials.get('cash'))} |
| **Debt/Equity Ratio** | {self.format_number(deep_dive.get('debt_equity', 0), 2)}x |

### Cash Flow Summary

| Metric | Value |
|--------|-------|
| **Operating Cash Flow** | {self.format_currency(financials.get('operating_cashflow'))} |
| **Capital Expenditures** | ({self.format_currency(financials.get('capex'))}) |
| **Free Cash Flow** | {self.format_currency(financials.get('fcf'))} |
| **FCF Margin** | {self.format_percentage(financials.get('fcf', 0) / financials.get('revenue', 1) if financials.get('revenue') else 0)} |

---

## FINANCIAL DEEP DIVE

### Working Capital Analysis

- **NWC Efficiency Score:** {self.format_number(deep_dive.get('wc_efficiency', 0), 1)}/100
- **Cash Conversion Cycle:** {self.format_number(deep_dive.get('cash_conversion_cycle', 0), 0)} days
- **Interpretation:** {"Highly efficient working capital management" if deep_dive.get('wc_efficiency', 0) >= 80 else "Room for improvement in working capital efficiency"}

### CapEx & Asset Intensity

- **Total CapEx (5-year):** {self.format_currency(deep_dive.get('total_capex'))}
- **CapEx % of Revenue:** {self.format_number(deep_dive.get('capex_pct_revenue', 0), 1)}%
- **Asset Intensity:** {"High" if deep_dive.get('capex_pct_revenue', 0) > 10 else "Moderate" if deep_dive.get('capex_pct_revenue', 0) > 5 else "Low"}

### Debt Structure

- **Total Debt:** {self.format_currency(deep_dive.get('total_debt'))}
- **Debt/Equity Ratio:** {self.format_number(deep_dive.get('debt_equity', 0), 2)}x
- **Interest Coverage:** {self.format_number(deep_dive.get('interest_coverage', 0), 1)}x
- **Assessment:** {"Manageable leverage" if deep_dive.get('debt_equity', 0) < 3.0 else "High leverage - requires monitoring"}

---

## VALUATION ANALYSIS

### DCF Valuation (Base Case)

| Metric | Value |
|--------|-------|
| **Enterprise Value** | {self.format_currency(valuation.get('enterprise_value'))} |
| **Equity Value** | {self.format_currency(valuation.get('equity_value'))} |
| **WACC** | {self.format_percentage(valuation.get('wacc'))} |
| **Terminal Growth Rate** | {self.format_percentage(valuation.get('terminal_growth'))} |

---

## COMPETITIVE BENCHMARKING

### Market Position

- **Competitive Position:** {competitive.get('competitive_position', 'Unknown')}
- **Overall Rating:** {competitive.get('overall_rating', 'Unknown')}
- **Sector:** {competitive.get('sector', 'Unknown')}
- **Peers Analyzed:** {competitive.get('peers_analyzed', 0)}

### Key Strengths

{chr(10).join([f"- {strength}" for strength in competitive.get('strengths', ['No strengths identified'])])}

### Key Weaknesses

{chr(10).join([f"- {weakness}" for weakness in competitive.get('weaknesses', ['No weaknesses identified'])])}

---

## MACROECONOMIC ANALYSIS

### Current Economic Conditions

| Indicator | Value |
|-----------|-------|
| **10-Year Treasury** | {self.format_percentage(macro.get('treasury_10y', 0))} |
| **GDP Growth** | {self.format_percentage(macro.get('gdp_growth', 0))} |
| **Inflation Rate** | {self.format_percentage(macro.get('inflation', 0))} |
| **Unemployment Rate** | {self.format_percentage(macro.get('unemployment', 0))} |

### Key Insights

{chr(10).join([f"{i+1}. {insight}" for i, insight in enumerate(macro.get('insights', ['No insights available']))])}

---

## EXTERNAL VALIDATION

### Validation Summary

- **Confidence Score:** {self.format_percentage(validation.get('confidence_score', 0) / 100)}
- **Findings Validated:** {validation.get('findings_validated', 0)}
- **Critical Discrepancies:** {validation.get('discrepancies', 0)}
- **Overall Assessment:** {validation.get('overall_assessment', 'Not available')}

---

## EXECUTIVE SYNTHESIS

{exec_summary}

---

## INVESTMENT RECOMMENDATION

### Recommendations

{chr(10).join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)]) if recommendations else "No specific recommendations provided"}

---

## APPENDIX: METHODOLOGY

### Data Sources
- Financial Modeling Prep (FMP) API
- SEC EDGAR Database
- Market data providers

### Analysis Framework
- Multi-agent AI system for comprehensive analysis
- External validation of key findings
- Analysis date: {datetime.now().strftime('%B %d, %Y')}

### Key Metrics Definitions
- **Working Capital Efficiency:** Measure of how effectively company manages working capital (0-100 scale)
- **Cash Conversion Cycle:** Days to convert investments in inventory to cash
- **Interest Coverage:** EBIT / Interest Expense (measures debt service capacity)
- **Asset Intensity:** CapEx as % of revenue (measures capital requirements)

---

*This report is confidential and proprietary. Generated by AIMADDS M&A Due Diligence System.*
"""
        
        return report
    
    def save_report(self, output_file: str):
        """Generate and save markdown report"""
        report = self.generate_markdown_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Report generated: {output_file}")
        return output_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_improved_report.py <job_json_file> [output_file]")
        sys.exit(1)
    
    job_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not output_file:
        # Auto-generate output filename
        job_path = Path(job_file)
        ticker = "unknown"
        try:
            with open(job_file, 'r') as f:
                data = json.load(f)
                ticker = data.get('target_ticker', 'unknown')
        except:
            pass
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{ticker}_improved_report_{timestamp}.md"
    
    generator = ImprovedReportGenerator(job_file)
    generator.save_report(output_file)
    
    print(f"\n✓ Improved report generated successfully!")
    print(f"  Input:  {job_file}")
    print(f"  Output: {output_file}")


if __name__ == "__main__":
    main()
