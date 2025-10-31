"""
Synergy Calculator - Quantifies M&A synergies with realization timeline
Critical for justifying acquisition premiums in M&A deals
"""
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from loguru import logger
import numpy as np


@dataclass
class SynergyEstimate:
    """Synergy estimate with timeline"""
    synergy_type: str
    category: str
    description: str
    annual_value: float
    realization_timeline: Dict[str, float]  # Year 1, 2, 3 percentages
    confidence: str  # High, Medium, Low
    assumptions: List[str]


class SynergyCalculator:
    """
    Calculates revenue and cost synergies for M&A transactions
    """
    
    def __init__(self):
        """Initialize synergy calculator"""
        self.revenue_synergies = []
        self.cost_synergies = []
        
    def calculate_all_synergies(
        self,
        target_data: Dict[str, Any],
        acquirer_data: Dict[str, Any],
        deal_rationale: str = ""
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive synergy analysis
        
        Args:
            target_data: Target company financial data
            acquirer_data: Acquiring company financial data  
            deal_rationale: Strategic rationale for deal
            
        Returns:
            Complete synergy analysis with NPV
        """
        logger.info("Calculating M&A synergies...")
        
        # Calculate revenue synergies
        revenue_synergies = self._calculate_revenue_synergies(
            target_data, acquirer_data, deal_rationale
        )
        
        # Calculate cost synergies
        cost_synergies = self._calculate_cost_synergies(
            target_data, acquirer_data
        )
        
        # Calculate integration costs
        integration_costs = self._estimate_integration_costs(
            target_data, acquirer_data
        )
        
        # Calculate NPV of synergies
        synergy_npv = self._calculate_synergy_npv(
            revenue_synergies, cost_synergies, integration_costs
        )
        
        return {
            'revenue_synergies': revenue_synergies,
            'cost_synergies': cost_synergies,
            'total_annual_synergies': revenue_synergies['total_annual'] + cost_synergies['total_annual'],
            'integration_costs': integration_costs,
            'net_synergy_value': synergy_npv,
            'synergy_to_deal_value_ratio': self._calculate_synergy_ratio(synergy_npv, target_data),
            'realization_schedule': self._build_realization_schedule(revenue_synergies, cost_synergies),
            'risk_adjusted_synergies': self._apply_risk_adjustment(revenue_synergies, cost_synergies)
        }
    
    def _calculate_revenue_synergies(
        self,
        target_data: Dict[str, Any],
        acquirer_data: Dict[str, Any],
        rationale: str
    ) -> Dict[str, Any]:
        """Calculate revenue synergies"""
        
        target_revenue = target_data.get('income_statement', [{}])[0].get('revenue', 0)
        acquirer_revenue = acquirer_data.get('income_statement', [{}])[0].get('revenue', 0)
        
        synergies = []
        
        # Cross-sell opportunities
        cross_sell = target_revenue * 0.05  # 5% uplift estimate
        synergies.append({
            'category': 'Cross-sell',
            'description': 'Selling acquirer products to target customers',
            'annual_value': cross_sell,
            'realization': {'year1': 0.2, 'year2': 0.5, 'year3': 0.8},
            'confidence': 'Medium',
            'assumptions': ['5% revenue uplift', '3-year ramp']
        })
        
        # Pricing power
        pricing_power = target_revenue * 0.02  # 2% price increase
        synergies.append({
            'category': 'Pricing Power',
            'description': 'Market consolidation enables pricing improvements',
            'annual_value': pricing_power,
            'realization': {'year1': 0.3, 'year2': 0.7, 'year3': 1.0},
            'confidence': 'Medium',
            'assumptions': ['2% average price increase', '2-year realization']
        })
        
        # Geographic expansion
        geo_expansion = target_revenue * 0.03  # 3% from new markets
        synergies.append({
            'category': 'Geographic Expansion',
            'description': 'Leverage acquirer distribution in underserved markets',
            'annual_value': geo_expansion,
            'realization': {'year1': 0.0, 'year2': 0.4, 'year3': 0.7},
            'confidence': 'Low',
            'assumptions': ['3% revenue from new geographies', '3+ year horizon']
        })
        
        total_annual = sum(s['annual_value'] for s in synergies)
        
        return {
            'synergies': synergies,
            'total_annual': total_annual,
            'total_pct_of_target_revenue': (total_annual / target_revenue * 100) if target_revenue > 0 else 0
        }
    
    def _calculate_cost_synergies(
        self,
        target_data: Dict[str, Any],
        acquirer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate cost synergies"""
        
        target_revenue = target_data.get('income_statement', [{}])[0].get('revenue', 0)
        target_opex = target_data.get('income_statement', [{}])[0].get('operatingExpenses', 0)
        
        synergies = []
        
        # Headcount reduction (typically 10-15% of overlapping functions)
        headcount_savings = target_opex * 0.10  # 10% of OpEx
        synergies.append({
            'category': 'Headcount Optimization',
            'description': 'Eliminate duplicate roles (finance, HR, IT, admin)',
            'annual_value': headcount_savings,
            'realization': {'year1': 0.4, 'year2': 0.8, 'year3': 1.0},
            'confidence': 'High',
            'assumptions': ['10% headcount reduction', '18-month realization']
        })
        
        # Facilities consolidation
        facilities_savings = target_opex * 0.03  # 3% from real estate
        synergies.append({
            'category': 'Facilities Consolidation',
            'description': 'Consolidate offices, close redundant locations',
            'annual_value': facilities_savings,
            'realization': {'year1': 0.0, 'year2': 0.5, 'year3': 1.0},
            'confidence': 'High',
            'assumptions': ['3% cost reduction', 'Lease expiration dependent']
        })
        
        # Procurement savings
        procurement_savings = target_revenue * 0.02  # 2% from volume discounts
        synergies.append({
            'category': 'Procurement Optimization',
            'description': 'Volume discounts, vendor consolidation',
            'annual_value': procurement_savings,
            'realization': {'year1': 0.5, 'year2': 0.9, 'year3': 1.0},
            'confidence': 'Medium',
            'assumptions': ['2% cost savings', '12-month negotiation cycle']
        })
        
        # Technology platform consolidation
        tech_savings = target_opex * 0.05  # 5% from IT consolidation
        synergies.append({
            'category': 'Technology Platform',
            'description': 'Consolidate IT systems, eliminate duplicate licenses',
            'annual_value': tech_savings,
            'realization': {'year1': 0.0, 'year2': 0.6, 'year3': 1.0},
            'confidence': 'Medium',
            'assumptions': ['5% IT cost reduction', '24-month migration']
        })
        
        total_annual = sum(s['annual_value'] for s in synergies)
        
        return {
            'synergies': synergies,
            'total_annual': total_annual,
            'total_pct_of_target_opex': (total_annual / target_opex * 100) if target_opex > 0 else 0
        }
    
    def _estimate_integration_costs(
        self,
        target_data: Dict[str, Any],
        acquirer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate one-time integration costs"""
        
        target_revenue = target_data.get('income_statement', [{}])[0].get('revenue', 0)
        
        costs = []
        
        # Severance and retention
        severance = target_revenue * 0.02  # 2% for severance packages
        retention = target_revenue * 0.015  # 1.5% for retention bonuses
        
        costs.append({
            'category': 'Employee-Related',
            'items': [
                {'name': 'Severance Packages', 'amount': severance},
                {'name': 'Retention Bonuses', 'amount': retention}
            ],
            'total': severance + retention
        })
        
        # Systems integration
        systems_integration = target_revenue * 0.03  # 3% for IT integration
        costs.append({
            'category': 'Technology Integration',
            'items': [
                {'name': 'Systems Integration', 'amount': systems_integration},
                {'name': 'Data Migration', 'amount': systems_integration * 0.3}
            ],
            'total': systems_integration * 1.3
        })
        
        # Advisory and legal
        advisory = target_revenue * 0.01  # 1% for advisors
        costs.append({
            'category': 'Professional Fees',
            'items': [
                {'name': 'Integration Consultants', 'amount': advisory},
                {'name': 'Legal and Regulatory', 'amount': advisory * 0.5}
            ],
            'total': advisory * 1.5
        })
        
        total_integration_costs = sum(c['total'] for c in costs)
        
        return {
            'cost_categories': costs,
            'total_one_time_costs': total_integration_costs,
            'pct_of_target_revenue': (total_integration_costs / target_revenue * 100) if target_revenue > 0 else 0
        }
    
    def _calculate_synergy_npv(
        self,
        revenue_syn: Dict,
        cost_syn: Dict,
        integration_costs: Dict,
        discount_rate: float = 0.10,
        forecast_years: int = 5
    ) -> Dict[str, Any]:
        """Calculate NPV of synergies"""
        
        total_annual_synergies = revenue_syn['total_annual'] + cost_syn['total_annual']
        total_integration_costs = integration_costs['total_one_time_costs']
        
        # Build cash flow stream
        cash_flows = [-total_integration_costs]  # Year 0
        
        # Years 1-5 with realization curve
        realization_curve = [0.3, 0.6, 0.9, 1.0, 1.0]  # Typical S-curve
        
        for year in range(1, forecast_years + 1):
            realization = realization_curve[year - 1] if year <= len(realization_curve) else 1.0
            annual_synergy = total_annual_synergies * realization
            
            # Apply tax shield (synergies reduce taxable income)
            after_tax_synergy = annual_synergy * (1 - 0.21)  # 21% tax rate
            
            cash_flows.append(after_tax_synergy)
        
        # Calculate NPV
        npv = sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))
        
        # Payback period
        cumulative_cf = 0
        payback_years = None
        for i, cf in enumerate(cash_flows):
            cumulative_cf += cf
            if cumulative_cf > 0 and payback_years is None:
                payback_years = i
        
        return {
            'npv': npv,
            'total_integration_costs': total_integration_costs,
            'total_annual_run_rate': total_annual_synergies,
            'after_tax_run_rate': total_annual_synergies * 0.79,
            'payback_period_years': payback_years if payback_years else forecast_years,
            'cash_flows': cash_flows,
            'discount_rate': discount_rate
        }
    
    def _build_realization_schedule(self, revenue_syn: Dict, cost_syn: Dict) -> Dict[str, Any]:
        """Build detailed realization schedule"""
        
        schedule = {'year1': 0, 'year2': 0, 'year3': 0}
        
        # Add revenue synergies
        for syn in revenue_syn.get('synergies', []):
            schedule['year1'] += syn['annual_value'] * syn['realization']['year1']
            schedule['year2'] += syn['annual_value'] * syn['realization']['year2']
            schedule['year3'] += syn['annual_value'] * syn['realization']['year3']
        
        # Add cost synergies
        for syn in cost_syn.get('synergies', []):
            schedule['year1'] += syn['annual_value'] * syn['realization']['year1']
            schedule['year2'] += syn['annual_value'] * syn['realization']['year2']
            schedule['year3'] += syn['annual_value'] * syn['realization']['year3']
        
        return schedule
    
    def _apply_risk_adjustment(self, revenue_syn: Dict, cost_syn: Dict) -> Dict[str, Any]:
        """Apply probability weighting to synergies"""
        
        # Risk adjustment factors based on confidence
        confidence_factors = {'High': 0.9, 'Medium': 0.7, 'Low': 0.5}
        
        rev_adjusted = 0
        for syn in revenue_syn.get('synergies', []):
            factor = confidence_factors.get(syn['confidence'], 0.7)
            rev_adjusted += syn['annual_value'] * factor
        
        cost_adjusted = 0
        for syn in cost_syn.get('synergies', []):
            factor = confidence_factors.get(syn['confidence'], 0.7)
            cost_adjusted += syn['annual_value'] * factor
        
        return {
            'risk_adjusted_revenue_synergies': rev_adjusted,
            'risk_adjusted_cost_synergies': cost_adjusted,
            'total_risk_adjusted': rev_adjusted + cost_adjusted,
            'confidence_note': 'High=90%, Medium=70%, Low=50% probability'
        }
    
    def _calculate_synergy_ratio(self, npv: Dict, target_data: Dict) -> float:
        """Calculate synergy value as % of deal value"""
        # Estimate deal value as market cap + premium
        market_cap = target_data.get('income_statement', [{}])[0].get('revenue', 0) * 3  # Rough estimate
        
        synergy_npv = npv.get('npv', 0)
        
        return (synergy_npv / market_cap * 100) if market_cap > 0 else 0
