"""
Data Validation Framework
Validates financial data quality before analysis to prevent garbage-in-garbage-out
Implements schema validation, completeness scoring, outlier detection
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from loguru import logger
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    completeness_score: float  # 0-100
    errors: List[str]
    warnings: List[str]
    outliers: List[Dict[str, Any]]
    quality_grade: str  # A, B, C, D, F
    

class FinancialDataValidator:
    """
    Validates financial data quality
    
    Checks:
    - Required fields present
    - Data types correct
    - Values within reasonable ranges
    - No suspicious patterns (outliers)
    - Cross-field consistency
    """
    
    def __init__(self):
        """Initialize validator"""
        # Required fields for financial statements
        self.required_income_fields = [
            'revenue', 'costOfRevenue', 'grossProfit', 'operatingIncome',
            'netIncome', 'eps', 'ebitda'
        ]
        
        self.required_balance_fields = [
            'totalAssets', 'totalLiabilities', 'totalEquity',
            'totalCurrentAssets', 'totalCurrentLiabilities'
        ]
        
        # Cash can have multiple field names - check all alternatives
        self.cash_field_alternatives = [
            'cash',
            'cashAndCashEquivalents',
            'cashAndShortTermInvestments'
        ]
        
        self.required_cashflow_fields = [
            'operatingCashFlow', 'capitalExpenditure', 'freeCashFlow'
        ]
        
        # Reasonable ranges for financial ratios (outlier detection)
        self.ratio_ranges = {
            'gross_margin': (0.0, 1.0),  # 0-100%
            'operating_margin': (-0.5, 0.8),  # -50% to 80%
            'net_margin': (-0.5, 0.6),  # -50% to 60%
            'current_ratio': (0.1, 10.0),  # 0.1x to 10x
            'debt_to_equity': (0.0, 10.0),  # 0x to 10x
            'roe': (-1.0, 2.0),  # -100% to 200%
            'revenue_growth': (-0.9, 5.0),  # -90% to 500%
        }
    
    def validate_financial_data(
        self,
        financial_data: Dict[str, Any],
        ticker: str
    ) -> ValidationResult:
        """
        Validate complete financial data package
        
        Args:
            financial_data: Dictionary with income_statement, balance_sheet, cash_flow, etc.
            ticker: Company ticker for context
        
        Returns:
            ValidationResult with quality assessment
        """
        errors = []
        warnings = []
        outliers = []
        
        logger.info(f"[VALIDATOR] Validating financial data for {ticker}")
        
        # 1. Validate structure
        if not self._validate_structure(financial_data, errors):
            return ValidationResult(
                is_valid=False,
                completeness_score=0.0,
                errors=errors,
                warnings=warnings,
                outliers=outliers,
                quality_grade='F'
            )
        
        # 2. Validate income statements
        income_completeness = self._validate_income_statements(
            financial_data.get('income_statement', []),
            errors,
            warnings
        )
        
        # 3. Validate balance sheets
        balance_completeness = self._validate_balance_sheets(
            financial_data.get('balance_sheet', []),
            errors,
            warnings
        )
        
        # 4. Validate cash flow statements
        cashflow_completeness = self._validate_cash_flows(
            financial_data.get('cash_flow', []),
            errors,
            warnings
        )
        
        # 5. Cross-validate (consistency checks)
        self._cross_validate(financial_data, errors, warnings)
        
        # 6. Detect outliers
        outliers = self._detect_outliers(financial_data, warnings)
        
        # 7. Calculate overall completeness score
        completeness_score = np.mean([
            income_completeness,
            balance_completeness,
            cashflow_completeness
        ])
        
        # 8. Determine quality grade
        quality_grade = self._calculate_grade(completeness_score, len(errors), len(warnings))
        
        # 9. Determine if data is valid enough to proceed
        is_valid = len(errors) == 0 and completeness_score >= 60.0
        
        logger.info(f"[VALIDATOR] {ticker} - Completeness: {completeness_score:.1f}%, Grade: {quality_grade}, Valid: {is_valid}")
        
        return ValidationResult(
            is_valid=is_valid,
            completeness_score=completeness_score,
            errors=errors,
            warnings=warnings,
            outliers=outliers,
            quality_grade=quality_grade
        )
    
    def _validate_structure(self, data: Dict[str, Any], errors: List[str]) -> bool:
        """Validate top-level data structure"""
        required_keys = ['income_statement', 'balance_sheet', 'cash_flow']
        
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required section: {key}")
                return False
            
            if not isinstance(data[key], list):
                errors.append(f"Section {key} must be a list")
                return False
            
            if len(data[key]) == 0:
                errors.append(f"Section {key} is empty")
                return False
        
        return True
    
    def _validate_income_statements(
        self,
        statements: List[Dict],
        errors: List[str],
        warnings: List[str]
    ) -> float:
        """Validate income statements and return completeness score"""
        if not statements:
            errors.append("No income statements provided")
            return 0.0
        
        total_fields = 0
        present_fields = 0
        
        for i, stmt in enumerate(statements):
            year = stmt.get('date', f'Statement {i}')
            
            # Check required fields
            for field in self.required_income_fields:
                total_fields += 1
                if field in stmt and stmt[field] is not None:
                    present_fields += 1
                    
                    # Validate value is numeric
                    try:
                        float(stmt[field])
                    except (ValueError, TypeError):
                        warnings.append(f"{year}: {field} is not numeric")
                else:
                    if i == 0:  # Only warn for most recent statement
                        warnings.append(f"{year}: Missing {field}")
            
            # Sanity checks
            if 'revenue' in stmt and 'netIncome' in stmt:
                if stmt['revenue'] != 0:
                    margin = stmt['netIncome'] / stmt['revenue']
                    if margin > 1.0:
                        warnings.append(f"{year}: Net margin > 100% ({margin:.1%}) - suspicious")
                    elif margin < -1.0:
                        warnings.append(f"{year}: Net margin < -100% ({margin:.1%}) - suspicious")
        
        completeness = (present_fields / total_fields * 100) if total_fields > 0 else 0
        return completeness
    
    def _validate_balance_sheets(
        self,
        sheets: List[Dict],
        errors: List[str],
        warnings: List[str]
    ) -> float:
        """Validate balance sheets and return completeness score"""
        if not sheets:
            errors.append("No balance sheets provided")
            return 0.0
        
        total_fields = 0
        present_fields = 0
        
        for i, sheet in enumerate(sheets):
            year = sheet.get('date', f'Sheet {i}')
            
            # Check required fields
            for field in self.required_balance_fields:
                total_fields += 1
                if field in sheet and sheet[field] is not None:
                    present_fields += 1
                    
                    # Validate value is numeric
                    try:
                        float(sheet[field])
                    except (ValueError, TypeError):
                        warnings.append(f"{year}: {field} is not numeric")
                else:
                    if i == 0:
                        warnings.append(f"{year}: Missing {field}")
            
            # ENHANCED: Check for cash using expanded alternative field names
            total_fields += 1
            cash_found = False
            cash_value = None
            
            # Expanded cash field list to handle various reporting formats
            expanded_cash_fields = self.cash_field_alternatives + [
                'cashCashEquivalentsAndRestrictedCash',
                'cashAndRestrictedCash',
                'totalCash',
                'unrestricted_cash',
                'cashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'
            ]
            
            for cash_field in expanded_cash_fields:
                if cash_field in sheet and sheet[cash_field] is not None:
                    cash_found = True
                    cash_value = sheet[cash_field]
                    present_fields += 1
                    logger.info(f"✓ Found cash field: {cash_field} = ${cash_value:,.0f}")
                    break
            
            if not cash_found and i == 0:
                # CRITICAL FIX: Try to estimate cash from prior period + operating cash flow
                if len(sheets) > 1:
                    logger.warning(f"{year}: Cash field missing - attempting intelligent recovery")
                    estimated_cash = self._estimate_missing_cash(sheets, i)
                    if estimated_cash > 0:
                        sheet['cash'] = estimated_cash
                        sheet['_cash_estimated'] = True
                        present_fields += 1
                        warnings.append(f"{year}: Cash ESTIMATED at ${estimated_cash:,.0f} (use with caution)")
                        logger.info(f"✓ Estimated cash for {year}: ${estimated_cash:,.0f}")
                    else:
                        warnings.append(f"{year}: Missing cash (checked: {', '.join(expanded_cash_fields[:5])}... +{len(expanded_cash_fields)-5} more)")
                else:
                    warnings.append(f"{year}: Missing cash (checked: {', '.join(expanded_cash_fields[:5])}... +{len(expanded_cash_fields)-5} more)")
            
            # Accounting equation check: Assets = Liabilities + Equity
            if all(k in sheet for k in ['totalAssets', 'totalLiabilities', 'totalEquity']):
                assets = sheet['totalAssets']
                liabilities = sheet['totalLiabilities']
                equity = sheet['totalEquity']
                
                if assets != 0:
                    balance_error = abs(assets - (liabilities + equity)) / assets
                    if balance_error > 0.01:  # >1% error
                        warnings.append(
                            f"{year}: Balance sheet doesn't balance "
                            f"(Assets: {assets:,.0f}, L+E: {liabilities + equity:,.0f}, "
                            f"Error: {balance_error:.2%})"
                        )
        
        completeness = (present_fields / total_fields * 100) if total_fields > 0 else 0
        return completeness
    
    def _validate_cash_flows(
        self,
        flows: List[Dict],
        errors: List[str],
        warnings: List[str]
    ) -> float:
        """Validate cash flow statements and return completeness score"""
        if not flows:
            errors.append("No cash flow statements provided")
            return 0.0
        
        total_fields = 0
        present_fields = 0
        
        for i, flow in enumerate(flows):
            year = flow.get('date', f'Flow {i}')
            
            # Check required fields
            for field in self.required_cashflow_fields:
                total_fields += 1
                if field in flow and flow[field] is not None:
                    present_fields += 1
                else:
                    if i == 0:
                        warnings.append(f"{year}: Missing {field}")
            
            # Sanity check: FCF = Operating CF - CapEx
            if 'operatingCashFlow' in flow and 'capitalExpenditure' in flow and 'freeCashFlow' in flow:
                ocf = flow['operatingCashFlow']
                capex = abs(flow['capitalExpenditure'])  # CapEx often negative
                fcf = flow['freeCashFlow']
                
                calculated_fcf = ocf - capex
                if abs(fcf - calculated_fcf) / max(abs(fcf), 1) > 0.1:  # >10% diff
                    warnings.append(
                        f"{year}: FCF calculation inconsistent "
                        f"(Reported: {fcf:,.0f}, Calculated: {calculated_fcf:,.0f})"
                    )
        
        completeness = (present_fields / total_fields * 100) if total_fields > 0 else 0
        return completeness
    
    def _cross_validate(
        self,
        data: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ):
        """Cross-validate consistency across statements"""
        income = data.get('income_statement', [])
        balance = data.get('balance_sheet', [])
        cashflow = data.get('cash_flow', [])
        
        if not (income and balance and cashflow):
            return
        
        # Check that we have matching years
        income_years = set(s.get('date', '')[:4] for s in income)
        balance_years = set(s.get('date', '')[:4] for s in balance)
        cashflow_years = set(s.get('date', '')[:4] for s in cashflow)
        
        common_years = income_years & balance_years & cashflow_years
        if len(common_years) == 0:
            warnings.append("No common years across all financial statements")
        
        # Validate net income appears in cash flow statement
        for i, inc_stmt in enumerate(income[:3]):  # Check last 3 years
            year = inc_stmt.get('date', '')[:4]
            net_income = inc_stmt.get('netIncome')
            
            if net_income is not None:
                # Find matching cash flow statement
                cf_stmt = next((cf for cf in cashflow if cf.get('date', '')[:4] == year), None)
                if cf_stmt:
                    ocf = cf_stmt.get('operatingCashFlow')
                    if ocf is not None:
                        # OCF should be within reasonable range of net income
                        # (typically OCF > NI for healthy companies)
                        if abs(ocf - net_income) / max(abs(net_income), 1) > 3.0:  # >300% diff
                            warnings.append(
                                f"{year}: Large discrepancy between Net Income "
                                f"({net_income:,.0f}) and Operating CF ({ocf:,.0f})"
                            )
    
    def _detect_outliers(
        self,
        data: Dict[str, Any],
        warnings: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect statistical outliers in financial ratios"""
        outliers = []
        
        income = data.get('income_statement', [])
        balance = data.get('balance_sheet', [])
        
        if not (income and balance):
            return outliers
        
        # Calculate ratios for outlier detection
        for i in range(min(5, len(income))):  # Last 5 years
            inc = income[i]
            year = inc.get('date', f'Year {i}')
            
            revenue = inc.get('revenue', 0)
            gross_profit = inc.get('grossProfit', 0)
            operating_income = inc.get('operatingIncome', 0)
            net_income = inc.get('netIncome', 0)
            
            if revenue > 0:
                # Calculate margins
                gross_margin = gross_profit / revenue
                operating_margin = operating_income / revenue
                net_margin = net_income / revenue
                
                # Check against ranges
                self._check_ratio_range('gross_margin', gross_margin, year, outliers, warnings)
                self._check_ratio_range('operating_margin', operating_margin, year, outliers, warnings)
                self._check_ratio_range('net_margin', net_margin, year, outliers, warnings)
            
            # Balance sheet ratios
            if i < len(balance):
                bal = balance[i]
                
                current_assets = bal.get('totalCurrentAssets', 0)
                current_liabilities = bal.get('totalCurrentLiabilities', 1)
                total_debt = bal.get('totalDebt', 0)
                total_equity = bal.get('totalEquity', 1)
                
                if current_liabilities > 0:
                    current_ratio = current_assets / current_liabilities
                    self._check_ratio_range('current_ratio', current_ratio, year, outliers, warnings)
                
                if total_equity != 0:
                    debt_to_equity = total_debt / total_equity if total_equity > 0 else 999
                    self._check_ratio_range('debt_to_equity', debt_to_equity, year, outliers, warnings)
                    
                    if net_income != 0:
                        roe = net_income / total_equity
                        self._check_ratio_range('roe', roe, year, outliers, warnings)
        
        return outliers
    
    def _check_ratio_range(
        self,
        ratio_name: str,
        value: float,
        year: str,
        outliers: List[Dict],
        warnings: List[str]
    ):
        """Check if ratio is within expected range"""
        if ratio_name not in self.ratio_ranges:
            return
        
        min_val, max_val = self.ratio_ranges[ratio_name]
        
        if value < min_val or value > max_val:
            outlier_info = {
                'year': year,
                'ratio': ratio_name,
                'value': value,
                'expected_range': (min_val, max_val),
                'severity': 'high' if value < min_val * 0.5 or value > max_val * 2 else 'medium'
            }
            outliers.append(outlier_info)
            
            # Format value based on whether it's a percentage or ratio
            if ratio_name in ['gross_margin', 'operating_margin', 'net_margin', 'roe']:
                value_str = f"{value:.2%}"
                min_str = f"{min_val:.2%}"
                max_str = f"{max_val:.2%}"
            else:
                value_str = f"{value:.2f}x"
                min_str = f"{min_val:.2f}x"
                max_str = f"{max_val:.2f}x"
            
            warnings.append(
                f"{year}: {ratio_name.replace('_', ' ').title()} outlier - "
                f"Value: {value_str}, Expected range: {min_str} to {max_str}"
            )
    
    def _calculate_grade(
        self,
        completeness: float,
        error_count: int,
        warning_count: int
    ) -> str:
        """Calculate overall data quality grade"""
        if error_count > 0:
            return 'F'  # Any errors = F
        
        # Adjust completeness for warnings
        adjusted_score = completeness - (warning_count * 2)  # -2 points per warning
        
        if adjusted_score >= 90:
            return 'A'
        elif adjusted_score >= 80:
            return 'B'
        elif adjusted_score >= 70:
            return 'C'
        elif adjusted_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _estimate_missing_cash(self, balance_sheets: List[Dict], current_index: int) -> float:
        """
        INTELLIGENT RECOVERY: Estimate missing cash from prior period + cash flow changes
        
        Args:
            balance_sheets: List of balance sheets
            current_index: Index of the sheet missing cash
        
        Returns:
            Estimated cash value (0 if cannot estimate)
        """
        try:
            # Method 1: Get from prior period if available
            if current_index + 1 < len(balance_sheets):
                prior_sheet = balance_sheets[current_index + 1]
                
                # Check all possible cash field names in prior period
                expanded_cash_fields = self.cash_field_alternatives + [
                    'cashCashEquivalentsAndRestrictedCash',
                    'cashAndRestrictedCash',
                    'totalCash'
                ]
                
                prior_cash = None
                for field in expanded_cash_fields:
                    if field in prior_sheet and prior_sheet[field] is not None:
                        prior_cash = prior_sheet[field]
                        break
                
                if prior_cash and prior_cash > 0:
                    # Simple heuristic: assume cash grew with current assets
                    current_assets = balance_sheets[current_index].get('totalCurrentAssets', 0)
                    prior_assets = prior_sheet.get('totalCurrentAssets', 1)
                    
                    if prior_assets > 0 and current_assets > 0:
                        growth_factor = current_assets / prior_assets
                        estimated_cash = prior_cash * growth_factor
                        logger.info(f"Estimated cash using growth factor {growth_factor:.2f}x: ${estimated_cash:,.0f}")
                        return estimated_cash
                    else:
                        # Just use prior period cash if no growth data
                        logger.info(f"Using prior period cash as estimate: ${prior_cash:,.0f}")
                        return prior_cash
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error estimating cash: {e}")
            return 0.0
    
    def generate_quality_report(self, result: ValidationResult, ticker: str) -> str:
        """Generate human-readable quality report"""
        report = []
        report.append(f"\n{'='*80}")
        report.append(f"DATA QUALITY REPORT: {ticker}")
        report.append(f"{'='*80}\n")
        
        # Overall status
        status_icon = "✅" if result.is_valid else "❌"
        report.append(f"{status_icon} OVERALL STATUS: {'VALID' if result.is_valid else 'INVALID'}")
        report.append(f"📊 Completeness Score: {result.completeness_score:.1f}%")
        report.append(f"🎓 Quality Grade: {result.quality_grade}")
        report.append("")
        
        # Errors
        if result.errors:
            report.append(f"❌ ERRORS ({len(result.errors)}):")
            for error in result.errors:
                report.append(f"   • {error}")
            report.append("")
        
        # Warnings
        if result.warnings:
            report.append(f"⚠️  WARNINGS ({len(result.warnings)}):")
            for i, warning in enumerate(result.warnings[:10]):  # Limit to 10
                report.append(f"   • {warning}")
            if len(result.warnings) > 10:
                report.append(f"   ... and {len(result.warnings) - 10} more warnings")
            report.append("")
        
        # Outliers
        if result.outliers:
            report.append(f"🔍 OUTLIERS DETECTED ({len(result.outliers)}):")
            for outlier in result.outliers[:5]:  # Limit to 5
                report.append(
                    f"   • {outlier['year']}: {outlier['ratio']} = {outlier['value']:.2f} "
                    f"(expected: {outlier['expected_range']})"
                )
            if len(result.outliers) > 5:
                report.append(f"   ... and {len(result.outliers) - 5} more outliers")
            report.append("")
        
        report.append(f"{'='*80}\n")
        
        return "\n".join(report)


# Convenience function
def validate_data(financial_data: Dict[str, Any], ticker: str) -> ValidationResult:
    """
    Convenience function to validate financial data
    
    Args:
        financial_data: Financial data dictionary
        ticker: Company ticker
    
    Returns:
        ValidationResult
    """
    validator = FinancialDataValidator()
    result = validator.validate_financial_data(financial_data, ticker)
    
    # Print quality report
    report = validator.generate_quality_report(result, ticker)
    print(report)
    
    # Log result
    if not result.is_valid:
        logger.error(f"[VALIDATOR] {ticker} data validation FAILED - {len(result.errors)} errors")
    elif result.quality_grade in ['C', 'D']:
        logger.warning(f"[VALIDATOR] {ticker} data quality is LOW - Grade {result.quality_grade}")
    else:
        logger.info(f"[VALIDATOR] {ticker} data validation passed - Grade {result.quality_grade}")
    
    return result
