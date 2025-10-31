"""
Tax Structuring Agent - Tax analysis and optimal structure recommendations
"""
from typing import Dict, List, Any
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from .base_agent import BaseAgent
from ..core.state import DiligenceState
from ..utils.llm_retry import llm_call_with_retry
from ..utils.financial_calculator import FinancialCalculator


class TaxStructuringAgent(BaseAgent):
    """
    Tax Structuring Agent - The Tax Advisor
    
    Responsibilities:
    - Analyze tax implications of transaction
    - Recommend optimal deal structure (asset vs. stock)
    - Calculate tax liability and benefits
    - Assess tax loss carryforwards (NOLs)
    - Evaluate international tax considerations
    - Recommend tax-efficient structuring strategies
    """
    
    def __init__(self):
        """Initialize Tax Structuring Agent"""
        super().__init__("tax_structuring")
        self.financial_calculator = FinancialCalculator()
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Run comprehensive tax structuring analysis
        
        Args:
            state: Current workflow state
        
        Returns:
            Dictionary with tax analysis results
        """
        try:
            logger.info(f"💰 Tax Structuring: Analyzing tax implications for {state['target_company']}")
            
            # Step 1: Analyze current tax position
            tax_position = await self._analyze_tax_position(state)
            
            # Step 2: Compare structure alternatives
            structure_comparison = await self._compare_structures(state)
            
            # Step 3: Calculate tax implications
            tax_calculations = await self._calculate_tax_implications(state)
            
            # Step 4: Assess NOLs and tax attributes
            tax_attributes = await self._assess_tax_attributes(state)
            
            # Step 5: Evaluate international considerations
            international_tax = await self._evaluate_international_tax(state)
            
            # Step 6: Generate recommendations
            recommendations = await self._generate_tax_recommendations(
                state, structure_comparison, tax_calculations
            )
            
            # Step 7: Detect tax anomalies
            anomalies = await self._detect_tax_anomalies(
                state, tax_position, structure_comparison, tax_calculations, tax_attributes
            )
            
            # Log detected anomalies
            for anomaly in anomalies.get('anomalies_detected', []):
                self.log_anomaly(
                    anomaly_type=anomaly['type'],
                    description=anomaly['description'],
                    severity=anomaly['severity'],
                    data=anomaly
                )
            
            # Compile comprehensive tax analysis
            tax_analysis = {
                "tax_position": tax_position,
                "structure_comparison": structure_comparison,
                "tax_implications": tax_calculations,
                "tax_attributes": tax_attributes,
                "international_considerations": international_tax,
                "structure_recommendations": recommendations,
                "estimated_tax_impact": tax_calculations.get('total_tax_impact', 0),
                "optimal_structure": recommendations.get('recommended_structure', 'TBD')
            }
            
            logger.info(f"✅ Tax Structuring complete - {recommendations.get('recommended_structure', 'TBD')} structure recommended")
            
            # Add anomaly information to return data
            tax_analysis['anomalies'] = anomalies
            
            return {
                "data": tax_analysis,
                "errors": [],
                "warnings": [],
                "recommendations": [recommendations.get('primary_recommendation', 'Conduct detailed tax due diligence')],
                "anomalies_detected": anomalies.get('anomalies_detected', []),
                "anomaly_count": len(anomalies.get('anomalies_detected', []))
            }
            
        except Exception as e:
            logger.error(f"❌ Tax Structuring failed: {e}")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
    
    async def _analyze_tax_position(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Analyze target's current tax position
        
        Args:
            state: Current state
        
        Returns:
            Tax position analysis
        """
        logger.info("Analyzing current tax position...")
        
        # Get financial metrics
        financial_metrics = state.get('financial_metrics', {})
        revenue = financial_metrics.get('revenue', 0)
        ebitda = financial_metrics.get('ebitda', 0)
        
        # Calculate effective tax rate and tax expense using FinancialCalculator
        federal_rate = 0.21  # Federal corporate rate
        state_rate = 0.06
        estimated_etr = federal_rate + state_rate
        
        # Calculate annual tax expense with audit trail
        if ebitda > 0:
            tax_calc = self.financial_calculator.calculate_tax_expense(
                taxable_income=ebitda,
                tax_rate=estimated_etr,
                adjustments={}
            )
            annual_tax_expense = tax_calc['tax_expense']
        else:
            annual_tax_expense = 0
        
        return {
            "current_structure": "C-Corporation (assumed)",
            "federal_rate": federal_rate,
            "estimated_state_rate": state_rate,
            "estimated_effective_rate": estimated_etr,
            "annual_tax_expense": annual_tax_expense,
            "tax_jurisdiction": "United States",
            "analysis_basis": "Based on typical corporate structure"
        }
    
    async def _compare_structures(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Compare asset vs. stock purchase structures
        
        Args:
            state: Current state
        
        Returns:
            Structure comparison
        """
        logger.info("Comparing deal structures...")
        
        deal_value = state.get('deal_value') or 1000000000
        financial_metrics = state.get('financial_metrics', {})
        assets = financial_metrics.get('total_assets') or (deal_value * 0.7)
        
        # Asset Purchase Analysis with FinancialCalculator
        # Calculate buyer tax benefit
        amortizable_amount = deal_value * 0.25  # 25% of purchase price
        buyer_benefit_calc = self.financial_calculator.calculate_percentage_of_revenue(
            amount=amortizable_amount * 0.21,
            revenue=deal_value
        )
        
        # Calculate seller tax cost
        corporate_tax_rate = 0.21
        shareholder_tax_rate = 0.238
        combined_tax_rate = corporate_tax_rate + shareholder_tax_rate  # Simplified double taxation
        seller_cost_calc = self.financial_calculator.calculate_percentage_of_revenue(
            amount=deal_value * combined_tax_rate,
            revenue=deal_value
        )
        
        asset_purchase = {
            "structure": "Asset Purchase (338(h)(10) election)",
            "buyer_benefits": [
                "Step-up in asset basis to fair market value",
                "Depreciation and amortization deductions",
                "No assumption of unknown liabilities",
                "Tax deduction on goodwill amortization (15 years)"
            ],
            "seller_implications": [
                "Double taxation - corporate + shareholder level",
                "Ordinary income treatment on depreciation recapture",
                "Capital gains on goodwill and appreciated assets"
            ],
            "estimated_buyer_tax_benefit": deal_value * 0.21 * 0.25,
            "estimated_seller_tax_cost": deal_value * combined_tax_rate,
            "net_tax_efficiency": "Favorable to buyer, costly to seller",
            "calculation_audit": {
                "buyer_benefit_methodology": buyer_benefit_calc.get('methodology', ''),
                "seller_cost_methodology": seller_cost_calc.get('methodology', '')
            }
        }
        
        # Stock Purchase Analysis with FinancialCalculator
        capital_gains_rate = 0.238
        seller_stock_cost = self.financial_calculator.calculate_percentage_of_revenue(
            amount=deal_value * capital_gains_rate,
            revenue=deal_value
        )
        
        stock_purchase = {
            "structure": "Stock Purchase",
            "buyer_benefits": [
                "Simpler transaction structure",
                "Preserve target's NOLs (subject to limitations)",
                "Continuity of contracts and licenses",
                "Lower transaction costs"
            ],
            "seller_implications": [
                "Single layer of taxation",
                "Capital gains treatment (23.8% max rate)",
                "Lower overall tax cost"
            ],
            "estimated_buyer_tax_benefit": 0,  # No step-up
            "estimated_seller_tax_cost": deal_value * capital_gains_rate,
            "net_tax_efficiency": "Neutral to buyer, favorable to seller",
            "calculation_audit": {
                "seller_cost_methodology": seller_stock_cost.get('methodology', '')
            }
        }
        
        # Merger Structure Analysis
        merger_structure = {
            "structure": "Tax-Free Reorganization (Type A/B/C merger)",
            "buyer_benefits": [
                "Stock consideration reduces cash requirements",
                "Potential for tax-deferred transaction",
                "Preserve NOLs with proper structuring"
            ],
            "seller_implications": [
                "Tax deferral if structured properly",
                "Shareholders receive acquirer stock",
                "Continuity of interest requirements"
            ],
            "estimated_buyer_tax_benefit": 0,
            "estimated_seller_tax_cost": 0,  # Tax-deferred
            "net_tax_efficiency": "Most efficient if continuity requirements met"
        }
        
        return {
            "asset_purchase": asset_purchase,
            "stock_purchase": stock_purchase,
            "merger_structure": merger_structure,
            "analysis_date": "2025-01-20"
        }
    
    async def _calculate_tax_implications(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Calculate detailed tax implications
        
        Args:
            state: Current state
        
        Returns:
            Tax calculations
        """
        logger.info("Calculating tax implications...")
        
        deal_value = state.get('deal_value') or 1000000000
        
        # Calculate asset step-up benefit using FinancialCalculator
        amortizable_amount = deal_value * 0.25  # 25% of purchase price
        amortization_period = 15  # years
        annual_deduction = amortizable_amount / amortization_period
        tax_rate = 0.21
        annual_tax_savings = annual_deduction * tax_rate
        
        # Calculate NPV of tax shield using synergy NPV method (same concept)
        discount_rate = 0.10
        synergy_calc = self.financial_calculator.calculate_synergies(
            revenue_synergies=0,
            cost_synergies=annual_tax_savings,
            synergy_realization_years=amortization_period,
            tax_rate=0,  # Tax already applied to annual_tax_savings
            wacc=discount_rate
        )
        npv_tax_shield = synergy_calc['npv_synergies']
        
        # Calculate seller tax costs using percentage calculator for audit trail
        asset_sale_rate = 0.396  # Corporate 21% + shareholder 23.8%
        stock_sale_rate = 0.238  # Capital gains
        
        asset_sale_cost = self.financial_calculator.calculate_percentage_of_revenue(
            amount=deal_value * asset_sale_rate,
            revenue=deal_value
        )
        
        stock_sale_cost = self.financial_calculator.calculate_percentage_of_revenue(
            amount=deal_value * stock_sale_rate,
            revenue=deal_value
        )
        
        # Calculate transaction taxes
        transfer_tax_rate = 0.001  # 0.1%
        recording_fees = 50000
        transfer_taxes = self.financial_calculator.calculate_percentage_of_revenue(
            amount=deal_value * transfer_tax_rate,
            revenue=deal_value
        )
        
        calculations = {
            "purchase_price": deal_value,
            "asset_step_up_benefit": {
                "description": "NPV of tax shield from asset step-up",
                "annual_deduction": annual_deduction,
                "annual_tax_savings": annual_tax_savings,
                "npv_at_10_percent": npv_tax_shield,
                "calculation_methodology": synergy_calc.get('methodology', ''),
                "calculation_audit": synergy_calc.get('calculation_steps', [])
            },
            "seller_tax_cost": {
                "asset_sale_scenario": deal_value * asset_sale_rate,
                "stock_sale_scenario": deal_value * stock_sale_rate,
                "tax_free_reorg": 0,
                "asset_sale_audit": asset_sale_cost.get('methodology', ''),
                "stock_sale_audit": stock_sale_cost.get('methodology', '')
            },
            "transaction_taxes": {
                "transfer_taxes": deal_value * transfer_tax_rate,
                "recording_fees": recording_fees,
                "estimated_total": deal_value * transfer_tax_rate + recording_fees,
                "calculation_audit": transfer_taxes.get('methodology', '')
            },
            "total_tax_impact": 0  # Will be calculated based on chosen structure
        }
        
        return calculations
    
    async def _assess_tax_attributes(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Assess tax attributes like NOLs
        
        Args:
            state: Current state
        
        Returns:
            Tax attributes assessment
        """
        logger.info("Assessing tax attributes...")
        
        financial_metrics = state.get('financial_metrics', {})
        
        return {
            "nol_analysis": {
                "estimated_nols": "To be determined in due diligence",
                "section_382_considerations": "Change of ownership may limit NOL usage",
                "potential_annual_limitation": "Requires detailed analysis",
                "utilization_period": "Indefinite carryforward (post-TCJA)"
            },
            "tax_credits": {
                "r_and_d_credits": "To be identified",
                "foreign_tax_credits": "To be reviewed",
                "other_credits": "To be assessed"
            },
            "deferred_tax_assets": {
                "gross_dtas": "To be calculated",
                "valuation_allowance": "To be reviewed",
                "net_dtas": "To be determined"
            }
        }
    
    async def _evaluate_international_tax(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Evaluate international tax considerations
        
        Args:
            state: Current state
        
        Returns:
            International tax analysis
        """
        logger.info("Evaluating international tax considerations...")
        
        return {
            "foreign_operations": "To be assessed in due diligence",
            "repatriation_considerations": {
                "gilti_implications": "Global Intangible Low-Taxed Income analysis required",
                "subpart_f_income": "Controlled Foreign Corporation rules to be reviewed",
                "beat_considerations": "Base Erosion Anti-Abuse Tax applicability"
            },
            "transfer_pricing": {
                "intercompany_transactions": "To be documented and defended",
                "arm_length_pricing": "Requires transfer pricing study",
                "documentation_requirements": "Country-by-country reporting assessment"
            },
            "treaty_considerations": "Tax treaty analysis for international operations",
            "withholding_taxes": "Cross-border payment withholding to be assessed"
        }
    
    async def _generate_tax_recommendations(
        self,
        state: DiligenceState,
        structure_comparison: Dict[str, Any],
        tax_calculations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate tax structuring recommendations
        
        Args:
            state: Current state
            structure_comparison: Structure comparison data
            tax_calculations: Tax calculation data
        
        Returns:
            Tax recommendations
        """
        logger.info("Generating tax recommendations...")
        
        deal_type = state.get('deal_type', 'acquisition')
        
        # Determine optimal structure based on deal characteristics
        if deal_type == 'merger':
            recommended = "Tax-Free Reorganization (Type A)"
            rationale = "Most tax-efficient for both parties with stock consideration"
        else:
            recommended = "Stock Purchase with 338(h)(10) Election"
            rationale = "Provides buyer with step-up benefits while minimizing seller's tax burden through negotiated purchase price adjustment"
        
        return {
            "recommended_structure": recommended,
            "rationale": rationale,
            "primary_recommendation": f"Pursue {recommended} structure",
            "key_considerations": [
                "Engage tax counsel early in structuring discussions",
                "Conduct comprehensive tax due diligence",
                "Model various scenarios to optimize tax efficiency",
                "Consider state and local tax implications",
                "Address international tax planning if applicable",
                "Negotiate purchase price adjustment for tax benefits",
                "Document tax basis and attribute preservation",
                "Plan for post-closing tax integration"
            ],
            "implementation_steps": [
                "1. Retain experienced M&A tax advisors",
                "2. Complete detailed tax due diligence",
                "3. Model after-tax economics for all structures",
                "4. Negotiate tax allocation and indemnification",
                "5. Obtain necessary tax rulings if applicable",
                "6. Structure deal documents to optimize tax treatment",
                "7. File required elections and forms timely",
                "8. Implement post-closing tax planning strategies"
            ],
            "estimated_value_creation": tax_calculations.get('asset_step_up_benefit', {}).get('npv_at_10_percent', 0),
            "risk_factors": [
                "IRS challenge to structure or valuations",
                "State tax authority disputes",
                "Section 382 limitations on NOL usage",
                "Earnings and profits calculations",
                "Transfer pricing adjustments"
            ]
        }
    
    async def _detect_tax_anomalies(
        self,
        state: DiligenceState,
        tax_position: Dict[str, Any],
        structure_comparison: Dict[str, Any],
        tax_calculations: Dict[str, Any],
        tax_attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect tax-related anomalies and risks
        
        Args:
            state: Current state
            tax_position: Tax position data
            structure_comparison: Structure comparison data
            tax_calculations: Tax calculations data
            tax_attributes: Tax attributes data
        
        Returns:
            Dictionary with detected anomalies
        """
        logger.info("Detecting tax anomalies...")
        
        anomalies = []
        deal_value = state.get('deal_value') or 1000000000
        
        # 1. Abnormal Effective Tax Rate
        effective_rate = tax_position.get('estimated_effective_rate', 0.27)
        if effective_rate < 0.10 or effective_rate > 0.45:
            anomalies.append({
                'type': 'abnormal_effective_tax_rate',
                'severity': 'high',
                'description': f'Effective tax rate of {effective_rate:.1%} is outside normal range (10%-45%)',
                'impact': 'May indicate aggressive tax positions, transfer pricing issues, or compliance risks',
                'recommendation': 'Conduct detailed review of tax returns and planning strategies',
                'data': {
                    'effective_rate': effective_rate,
                    'normal_range': '10%-45%',
                    'federal_rate': tax_position.get('federal_rate', 0),
                    'state_rate': tax_position.get('estimated_state_rate', 0)
                }
            })
        
        # 2. High Seller Tax Burden (Asset Sale)
        asset_sale = structure_comparison.get('asset_purchase', {})
        seller_cost = asset_sale.get('estimated_seller_tax_cost', 0)
        if seller_cost > deal_value * 0.35:
            anomalies.append({
                'type': 'excessive_seller_tax_burden',
                'severity': 'critical',
                'description': f'Asset sale structure creates ${seller_cost:,.0f} seller tax burden ({seller_cost/deal_value:.1%} of deal value)',
                'impact': 'Seller unlikely to accept asset sale; may require significant price adjustment',
                'recommendation': 'Consider stock purchase or negotiate purchase price increase to offset tax burden',
                'data': {
                    'seller_tax_cost': seller_cost,
                    'deal_value': deal_value,
                    'tax_as_percent_of_deal': seller_cost / deal_value,
                    'structure': 'Asset Purchase'
                }
            })
        
        # 3. Substantial Transfer Taxes
        transaction_taxes = tax_calculations.get('transaction_taxes', {})
        transfer_tax_total = transaction_taxes.get('estimated_total', 0)
        if transfer_tax_total > deal_value * 0.02:  # >2% of deal value
            anomalies.append({
                'type': 'high_transfer_taxes',
                'severity': 'medium',
                'description': f'Transfer and recording taxes of ${transfer_tax_total:,.0f} exceed 2% of deal value',
                'impact': 'Significant additional transaction cost',
                'recommendation': 'Explore tax-efficient structuring alternatives and jurisdiction optimization',
                'data': {
                    'transfer_taxes': transfer_tax_total,
                    'deal_value': deal_value,
                    'percentage': transfer_tax_total / deal_value,
                    'threshold': 0.02
                }
            })
        
        # 4. Missing NOL Analysis
        nol_analysis = tax_attributes.get('nol_analysis', {})
        if nol_analysis.get('estimated_nols') == "To be determined in due diligence":
            anomalies.append({
                'type': 'incomplete_nol_assessment',
                'severity': 'medium',
                'description': 'Net Operating Loss (NOL) carryforwards not yet quantified',
                'impact': 'Potential loss of significant tax asset if not properly structured',
                'recommendation': 'Prioritize NOL due diligence and Section 382 limitation analysis',
                'data': {
                    'nol_status': 'Not assessed',
                    'section_382_risk': 'Unknown',
                    'annual_limitation': 'Not calculated'
                }
            })
        
        # 5. International Tax Complexity
        international = state.get('international_considerations', {})
        if international or tax_position.get('tax_jurisdiction') != "United States":
            anomalies.append({
                'type': 'international_tax_complexity',
                'severity': 'high',
                'description': 'International operations present complex tax structuring challenges',
                'impact': 'GILTI, BEAT, and transfer pricing rules may significantly impact after-tax returns',
                'recommendation': 'Engage international tax specialists for cross-border structuring',
                'data': {
                    'considerations': ['GILTI', 'Subpart F', 'BEAT', 'Transfer Pricing', 'Withholding Taxes'],
                    'complexity_level': 'High',
                    'required_expertise': 'International tax counsel'
                }
            })
        
        # 6. Lack of Tax-Free Reorganization Benefits
        merger = structure_comparison.get('merger_structure', {})
        deal_type = state.get('deal_type', 'acquisition')
        if deal_type == 'merger' and merger.get('estimated_seller_tax_cost', 0) > 0:
            anomalies.append({
                'type': 'missed_tax_free_opportunity',
                'severity': 'medium',
                'description': 'Deal structure may not be optimized for tax-free reorganization treatment',
                'impact': 'Both parties paying unnecessary taxes on transaction',
                'recommendation': 'Evaluate Type A/B/C reorganization structures for tax deferral',
                'data': {
                    'deal_type': deal_type,
                    'current_structure': 'Taxable',
                    'alternative': 'Tax-free reorganization',
                    'potential_savings': merger.get('estimated_seller_tax_cost', 0)
                }
            })
        
        # 7. Excessive Tax Uncertainty
        risk_factors = state.get('risk_factors', [])
        tax_risks = [r for r in risk_factors if 'tax' in str(r).lower() or 'irs' in str(r).lower()]
        if len(tax_risks) > 3:
            anomalies.append({
                'type': 'high_tax_risk_exposure',
                'severity': 'high',
                'description': f'{len(tax_risks)} significant tax risk factors identified',
                'impact': 'Multiple areas of potential IRS challenge or state audit exposure',
                'recommendation': 'Obtain tax opinion letters and consider tax indemnification provisions',
                'data': {
                    'tax_risk_count': len(tax_risks),
                    'risk_areas': tax_risks[:3],  # First 3
                    'mitigation': 'Tax insurance and indemnification'
                }
            })
        
        # 8. Step-Up Benefit vs. Transaction Cost Imbalance
        step_up_benefit = tax_calculations.get('asset_step_up_benefit', {})
        npv_benefit = step_up_benefit.get('npv_at_10_percent', 0)
        if npv_benefit > 0 and npv_benefit < deal_value * 0.05:  # Less than 5% of deal value
            anomalies.append({
                'type': 'limited_step_up_benefit',
                'severity': 'medium',
                'description': f'Asset step-up NPV of ${npv_benefit:,.0f} is less than 5% of deal value',
                'impact': 'Tax benefits may not justify additional complexity of asset purchase',
                'recommendation': 'Consider simpler stock purchase structure given limited tax benefit',
                'data': {
                    'npv_benefit': npv_benefit,
                    'deal_value': deal_value,
                    'benefit_percentage': npv_benefit / deal_value if deal_value > 0 else 0,
                    'threshold': 0.05
                }
            })
        
        # Determine overall risk level
        critical_count = sum(1 for a in anomalies if a['severity'] == 'critical')
        high_count = sum(1 for a in anomalies if a['severity'] == 'high')
        
        if critical_count > 0:
            risk_level = 'Critical'
        elif high_count > 2:
            risk_level = 'High'
        elif len(anomalies) > 3:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        logger.info(f"Tax anomaly detection complete: {len(anomalies)} anomalies found, risk level: {risk_level}")
        
        return {
            'anomalies_detected': anomalies,
            'total_anomalies': len(anomalies),
            'risk_level': risk_level,
            'critical_issues': critical_count,
            'high_issues': high_count
        }
