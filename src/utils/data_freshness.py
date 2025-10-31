"""
Data Freshness Validator - Ensures SEC filings and financial data are current
Prevents analysis on stale data that could lead to wrong decisions
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from loguru import logger


class DataFreshnessValidator:
    """Validates freshness of SEC filings and financial data"""
    
    def __init__(self):
        """Initialize freshness validator"""
        # Maximum acceptable ages
        self.max_ages = {
            '10-K': 456,  # 15 months (annual filing)
            '10-Q': 182,  # 6 months (quarterly filing)
            '8-K': 90,    # 3 months (current events)
            'DEF 14A': 456  # 15 months (annual proxy)
        }
        
    def validate_filing_freshness(
        self,
        filings: List[Dict[str, Any]],
        ticker: str
    ) -> Dict[str, Any]:
        """
        Validate freshness of SEC filings
        
        Args:
            filings: List of filings with dates
            ticker: Company ticker
            
        Returns:
            Freshness assessment with warnings
        """
        warnings = []
        stale_filings = []
        fresh_filings = []
        
        now = datetime.now()
        
        for filing in filings:
            filing_type = filing.get('type', '')
            filing_date_str = filing.get('filing_date', '')
            
            if not filing_date_str:
                warnings.append(f"{filing_type}: No filing date available")
                continue
            
            try:
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
                age_days = (now - filing_date).days
                
                # Check against max age
                max_age = self.max_ages.get(filing_type, 365)
                is_fresh = age_days <= max_age
                
                filing_info = {
                    'type': filing_type,
                    'date': filing_date_str,
                    'age_days': age_days,
                    'is_fresh': is_fresh,
                    'max_age_days': max_age
                }
                
                if is_fresh:
                    fresh_filings.append(filing_info)
                else:
                    stale_filings.append(filing_info)
                    warnings.append(
                        f"⚠️ {filing_type} is {age_days} days old (filed {filing_date_str}) "
                        f"- exceeds {max_age} day threshold"
                    )
                    
            except ValueError:
                warnings.append(f"{filing_type}: Invalid date format: {filing_date_str}")
        
        # Calculate freshness score (0-100)
        total_filings = len(fresh_filings) + len(stale_filings)
        freshness_score = (len(fresh_filings) / total_filings * 100) if total_filings > 0 else 0
        
        # Determine overall freshness
        if freshness_score >= 80:
            overall_freshness = 'Excellent'
        elif freshness_score >= 60:
            overall_freshness = 'Good'
        elif freshness_score >= 40:
            overall_freshness = 'Fair'
        else:
            overall_freshness = 'Poor'
        
        return {
            'ticker': ticker,
            'freshness_score': freshness_score,
            'overall_freshness': overall_freshness,
            'fresh_filings': fresh_filings,
            'stale_filings': stale_filings,
            'warnings': warnings,
            'is_acceptable': freshness_score >= 60
        }
    
    def validate_financial_data_freshness(
        self,
        financial_data: Dict[str, Any],
        ticker: str
    ) -> Dict[str, Any]:
        """
        Validate freshness of financial statements
        
        Args:
            financial_data: Financial data dictionary
            ticker: Company ticker
            
        Returns:
            Freshness assessment
        """
        warnings = []
        now = datetime.now()
        
        # Check income statement dates
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        cash_flows = financial_data.get('cash_flow', [])
        
        latest_dates = []
        
        for stmt_list, stmt_name in [
            (income_statements, 'Income Statement'),
            (balance_sheets, 'Balance Sheet'),
            (cash_flows, 'Cash Flow')
        ]:
            if stmt_list and len(stmt_list) > 0:
                latest = stmt_list[0]
                date_str = latest.get('date', '')
                
                if date_str:
                    try:
                        stmt_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        age_days = (now - stmt_date).days
                        
                        latest_dates.append({
                            'statement': stmt_name,
                            'date': date_str,
                            'age_days': age_days
                        })
                        
                        # Flag if > 6 months old
                        if age_days > 182:
                            warnings.append(
                                f"⚠️ {stmt_name} is {age_days} days old (dated {date_str[:10]}) "
                                f"- may not reflect current financial position"
                            )
                    except ValueError:
                        warnings.append(f"{stmt_name}: Invalid date format")
        
        # Calculate average age
        avg_age = np.mean([d['age_days'] for d in latest_dates]) if latest_dates else 365
        
        # Freshness scoring
        if avg_age <= 90:
            data_freshness = 'Excellent'
        elif avg_age <= 182:
            data_freshness = 'Good'
        elif avg_age <= 365:
            data_freshness = 'Fair'
        else:
            data_freshness = 'Poor'
        
        return {
            'ticker': ticker,
            'average_age_days': avg_age,
            'data_freshness': data_freshness,
            'statement_ages': latest_dates,
            'warnings': warnings,
            'is_acceptable': avg_age <= 365
        }
    
    def generate_freshness_report(
        self,
        filing_freshness: Dict,
        data_freshness: Dict
    ) -> str:
        """Generate human-readable freshness report"""
        report = []
        report.append("\n" + "="*80)
        report.append("DATA FRESHNESS REPORT")
        report.append("="*80 + "\n")
        
        # Filing freshness
        report.append(f"📄 SEC FILINGS: {filing_freshness['overall_freshness']}")
        report.append(f"   Score: {filing_freshness['freshness_score']:.1f}%")
        if filing_freshness['stale_filings']:
            report.append(f"   ⚠️  Stale Filings: {len(filing_freshness['stale_filings'])}")
        
        # Data freshness
        report.append(f"\n📊 FINANCIAL DATA: {data_freshness['data_freshness']}")
        report.append(f"   Average Age: {data_freshness['average_age_days']:.0f} days")
        
        # Warnings
        if filing_freshness['warnings'] or data_freshness['warnings']:
            report.append("\n⚠️  WARNINGS:")
            for w in (filing_freshness['warnings'] + data_freshness['warnings'])[:5]:
                report.append(f"   • {w}")
        
        report.append("\n" + "="*80 + "\n")
        
        return "\n".join(report)


# Convenience function
def validate_freshness(filings: List[Dict], financial_data: Dict, ticker: str) -> Tuple[Dict, Dict]:
    """
    Validate data freshness
    
    Args:
        filings: SEC filings list
        financial_data: Financial data
        ticker: Ticker symbol
        
    Returns:
        Tuple of (filing_freshness, data_freshness)
    """
    import numpy as np
    
    validator = DataFreshnessValidator()
    
    filing_freshness = validator.validate_filing_freshness(filings, ticker)
    data_freshness = validator.validate_financial_data_freshness(financial_data, ticker)
    
    # Print report
    report = validator.generate_freshness_report(filing_freshness, data_freshness)
    print(report)
    
    # Log results
    if not filing_freshness['is_acceptable'] or not data_freshness['is_acceptable']:
        logger.warning(f"[FRESHNESS] {ticker} has stale data - proceed with caution")
    else:
        logger.info(f"[FRESHNESS] {ticker} data is fresh and current")
    
    return filing_freshness, data_freshness
