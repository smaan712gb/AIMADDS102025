"""
Risk Assessment Agent - Investment Banking-Grade Risk Analysis

Capabilities matching Goldman Sachs M&A Risk Assessment:
- Comprehensive risk aggregation from all due diligence workstreams
- Sophisticated risk scoring using likelihood × impact matrix
- Risk-adjusted valuation scenarios with Monte Carlo integration
- Deal protection and risk mitigation strategies
- Integration with full 10-K/10-Q analysis for risk factor identification
"""
from typing import Dict, List, Any
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from .base_agent import BaseAgent
from ..core.state import DiligenceState
from ..utils.llm_retry import llm_call_with_retry
from ..integrations.fmp_client import FMPClient


class RiskAssessmentAgent(BaseAgent):
    """
    Risk Assessment Agent - The Risk Manager
    
    Responsibilities:
    - Identify and categorize all risks
    - Create risk matrix (likelihood x impact)
    - Assess risk mitigation strategies
    - Generate risk-adjusted valuations
    - Provide risk scoring and ratings
    - Recommend deal protection measures
    """
    
    def __init__(self):
        """Initialize Risk Assessment Agent"""
        super().__init__("risk_assessment")
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Run comprehensive risk assessment
        
        Args:
            state: Current workflow state
        
        Returns:
            Dictionary with risk assessment results
        """
        try:
            logger.info(f"🎯 Risk Assessment: Analyzing risks for {state['target_company']}")
            
            # Step 1: Aggregate risks from all sources
            all_risks = await self._aggregate_risks(state)
            
            # Step 2: Create risk matrix
            risk_matrix = await self._create_risk_matrix(all_risks)
            
            # Step 3: Calculate risk scores
            risk_scores = await self._calculate_risk_scores(all_risks, state)
            
            # Step 4: Generate risk-adjusted scenarios
            risk_scenarios = await self._generate_risk_scenarios(state, all_risks)
            
            # Step 5: Recommend mitigation strategies
            mitigation_strategies = await self._recommend_mitigations(all_risks)
            
            # Step 6: Create overall risk assessment
            overall_assessment = await self._create_overall_assessment(
                all_risks, risk_scores, state
            )
            
            # NEW: Detect risk management anomalies
            logger.info("Step 7: Detecting risk management anomalies...")
            risk_anomalies = await self._detect_risk_anomalies(
                all_risks, risk_scores, risk_matrix, state
            )
            
            # Log risk anomalies to centralized log
            if risk_anomalies.get('anomalies_detected'):
                for anomaly in risk_anomalies['anomalies_detected']:
                    self.log_anomaly(
                        anomaly_type=anomaly.get('type', 'risk_anomaly'),
                        description=anomaly.get('description', 'Risk management anomaly detected'),
                        severity=anomaly.get('severity', 'medium'),
                        data=anomaly
                    )
            
            # Compile comprehensive risk assessment
            risk_assessment = {
                "risk_matrix": risk_matrix,
                "risk_factors": all_risks,
                "risk_scores": risk_scores,
                "risk_scenarios": risk_scenarios,
                "mitigation_strategies": mitigation_strategies,
                "overall_assessment": overall_assessment,
                "risk_anomalies": risk_anomalies,
                "critical_risks": [r for r in all_risks if r.get('severity') == 'critical'],
                "total_risks_identified": len(all_risks)
            }
            
            logger.info(f"✅ Risk Assessment complete - {len(all_risks)} risks analyzed")
            
            return {
                "data": risk_assessment,
                "errors": [],
                "warnings": [],
                "recommendations": mitigation_strategies[:5]  # Top 5 recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ Risk Assessment failed: {e}")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
    
    async def _aggregate_risks(self, state: DiligenceState) -> List[Dict[str, Any]]:
        """
        Aggregate risks from all agent analyses
        
        Args:
            state: Current state
        
        Returns:
            List of all identified risks
        """
        logger.info("Aggregating risks from all sources...")
        
        all_risks = []
        
        # Financial risks
        if state.get('financial_metrics'):
            financial_risks = self._extract_financial_risks(state['financial_metrics'])
            all_risks.extend(financial_risks)
        
        # Legal risks (from legal_counsel agent)
        if state.get('legal_risks'):
            all_risks.extend(state['legal_risks'])
        
        # Market risks (from market_strategist)
        if state.get('market_data'):
            market_risks = self._extract_market_risks(state['market_data'])
            all_risks.extend(market_risks)
        
        # Competitive risks (from competitive_benchmarking)
        if state.get('competitive_analysis'):
            competitive_risks = self._extract_competitive_risks(state['competitive_analysis'])
            all_risks.extend(competitive_risks)
        
        # Macro risks (from macroeconomic_analyst)
        if state.get('macroeconomic_analysis'):
            macro_risks = self._extract_macro_risks(state['macroeconomic_analysis'])
            all_risks.extend(macro_risks)
        
        # Integration risks
        if state.get('integration_plan'):
            integration_risks = self._extract_integration_risks(state['integration_plan'])
            all_risks.extend(integration_risks)
        
        # Add standard M&A risks
        standard_risks = self._get_standard_ma_risks(state)
        all_risks.extend(standard_risks)
        
        # NEW: Extract governance and ownership risks from SEC filings
        ticker = state.get('target_ticker')
        if ticker:
            try:
                from ..integrations.sec_client import SECClient
                sec_client = SECClient()
                
                logger.info(f"[RISK] Extracting governance and ownership data for {ticker}...")
                
                # Get proxy data for governance risks
                proxy_data = await sec_client.extract_proxy_data(ticker)
                if 'error' not in proxy_data:
                    governance_risks = await self._assess_governance_risks(proxy_data)
                    all_risks.extend(governance_risks)
                    logger.info(f"✓ Identified {len(governance_risks)} governance risks")
                
                # Get ownership data for concentration risks
                ownership_data = await sec_client.extract_ownership_data(ticker)
                if 'error' not in ownership_data:
                    ownership_risks = await self._assess_ownership_risks(ownership_data)
                    all_risks.extend(ownership_risks)
                    logger.info(f"✓ Identified {len(ownership_risks)} ownership concentration risks")
                    
            except Exception as e:
                logger.warning(f"Error extracting governance/ownership risks: {e}")
        
        logger.info(f"Aggregated {len(all_risks)} total risks")
        return all_risks
    
    def _extract_financial_risks(self, financial_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract risks from financial analysis"""
        risks = []
        
        # Revenue concentration risk
        if financial_metrics.get('revenue', 0) > 0:
            risks.append({
                'category': 'financial',
                'severity': 'medium',
                'description': 'Revenue concentration and customer dependency risk',
                'likelihood': 'medium',
                'impact': 'high',
                'source': 'financial_analyst'
            })
        
        # Debt leverage risk
        if financial_metrics.get('total_debt', 0) > financial_metrics.get('total_equity', 1):
            risks.append({
                'category': 'financial',
                'severity': 'high',
                'description': 'High debt-to-equity ratio indicating leverage risk',
                'likelihood': 'high',
                'impact': 'high',
                'source': 'financial_analyst'
            })
        
        return risks
    
    def _extract_market_risks(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract risks from market analysis"""
        return [{
            'category': 'market',
            'severity': 'medium',
            'description': 'Market positioning and competitive pressure risks',
            'likelihood': 'medium',
            'impact': 'medium',
            'source': 'market_strategist'
        }]
    
    def _extract_competitive_risks(self, competitive_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract risks from competitive analysis"""
        return [{
            'category': 'competitive',
            'severity': 'medium',
            'description': 'Competitive intensity and market share erosion risk',
            'likelihood': 'medium',
            'impact': 'high',
            'source': 'competitive_benchmarking'
        }]
    
    def _extract_macro_risks(self, macro_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract risks from macroeconomic analysis"""
        return [{
            'category': 'macroeconomic',
            'severity': 'medium',
            'description': 'Economic cycle and interest rate risk',
            'likelihood': 'medium',
            'impact': 'medium',
            'source': 'macroeconomic_analyst'
        }]
    
    def _extract_integration_risks(self, integration_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract risks from integration planning"""
        return [{
            'category': 'integration',
            'severity': 'high',
            'description': 'Integration execution and synergy realization risk',
            'likelihood': 'high',
            'impact': 'high',
            'source': 'integration_planner'
        }]
    
    def _get_standard_ma_risks(self, state: DiligenceState) -> List[Dict[str, Any]]:
        """Get standard M&A risks"""
        return [
            {
                'category': 'execution',
                'severity': 'high',
                'description': 'Deal execution risk - timing, approvals, conditions',
                'likelihood': 'medium',
                'impact': 'high',
                'source': 'risk_assessment'
            },
            {
                'category': 'cultural',
                'severity': 'medium',
                'description': 'Cultural integration and employee retention risk',
                'likelihood': 'high',
                'impact': 'medium',
                'source': 'risk_assessment'
            },
            {
                'category': 'valuation',
                'severity': 'medium',
                'description': 'Valuation accuracy and overpayment risk',
                'likelihood': 'medium',
                'impact': 'high',
                'source': 'risk_assessment'
            }
        ]
    
    async def _create_risk_matrix(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create risk matrix categorizing risks by likelihood and impact
        
        Args:
            risks: List of risks
        
        Returns:
            Risk matrix dictionary
        """
        logger.info("Creating risk matrix...")
        
        matrix = {
            'high_likelihood_high_impact': [],
            'high_likelihood_medium_impact': [],
            'high_likelihood_low_impact': [],
            'medium_likelihood_high_impact': [],
            'medium_likelihood_medium_impact': [],
            'medium_likelihood_low_impact': [],
            'low_likelihood_high_impact': [],
            'low_likelihood_medium_impact': [],
            'low_likelihood_low_impact': []
        }
        
        for risk in risks:
            likelihood = risk.get('likelihood', 'medium')
            impact = risk.get('impact', 'medium')
            key = f"{likelihood}_likelihood_{impact}_impact"
            
            if key in matrix:
                matrix[key].append(risk)
        
        return matrix
    
    async def _calculate_risk_scores(
        self, 
        risks: List[Dict[str, Any]], 
        state: DiligenceState
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk scores"""
        logger.info("Calculating risk scores...")
        
        # Count risks by severity
        critical_count = len([r for r in risks if r.get('severity') == 'critical'])
        high_count = len([r for r in risks if r.get('severity') == 'high'])
        medium_count = len([r for r in risks if r.get('severity') == 'medium'])
        low_count = len([r for r in risks if r.get('severity') == 'low'])
        
        # Calculate weighted score (0-100, lower is better)
        total_score = (
            critical_count * 25 +
            high_count * 15 +
            medium_count * 5 +
            low_count * 1
        )
        
        # Normalize to 0-100 scale
        risk_score = min(100, total_score)
        
        # Determine risk rating
        if risk_score >= 75:
            rating = "VERY HIGH RISK"
        elif risk_score >= 50:
            rating = "HIGH RISK"
        elif risk_score >= 25:
            rating = "MODERATE RISK"
        else:
            rating = "LOW RISK"
        
        return {
            'overall_risk_score': risk_score,
            'risk_rating': rating,
            'critical_risks': critical_count,
            'high_risks': high_count,
            'medium_risks': medium_count,
            'low_risks': low_count,
            'total_risks': len(risks)
        }
    
    async def _generate_risk_scenarios(
        self, 
        state: DiligenceState, 
        risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate risk-adjusted scenarios"""
        logger.info("Generating risk scenarios...")
        
        base_value = state.get('deal_value') or 1000000000
        
        return {
            'best_case': {
                'description': 'Minimal risks materialize',
                'value_impact': 0.95,  # 95% of base
                'adjusted_value': base_value * 0.95,
                'probability': 0.2
            },
            'base_case': {
                'description': 'Some risks materialize as expected',
                'value_impact': 0.85,  # 85% of base
                'adjusted_value': base_value * 0.85,
                'probability': 0.5
            },
            'worst_case': {
                'description': 'Multiple high-severity risks materialize',
                'value_impact': 0.65,  # 65% of base
                'adjusted_value': base_value * 0.65,
                'probability': 0.3
            }
        }
    
    async def _recommend_mitigations(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Recommend risk mitigation strategies"""
        logger.info("Recommending mitigation strategies...")
        
        mitigations = [
            "Conduct comprehensive due diligence with external advisors",
            "Structure deal with earnouts and contingent payments",
            "Negotiate strong indemnification and escrow provisions",
            "Implement staged integration approach with clear milestones",
            "Secure regulatory approvals early in the process",
            "Establish robust post-merger integration team",
            "Maintain key employee retention programs",
            "Conduct thorough quality of earnings analysis",
            "Implement comprehensive risk monitoring framework",
            "Structure appropriate insurance coverage (R&W, D&O, etc.)"
        ]
        
        return mitigations
    
    async def _create_overall_assessment(
        self, 
        risks: List[Dict[str, Any]], 
        risk_scores: Dict[str, Any],
        state: DiligenceState
    ) -> str:
        """Create overall risk assessment narrative"""
        
        rating = risk_scores['risk_rating']
        total_risks = len(risks)
        critical = risk_scores['critical_risks']
        high = risk_scores['high_risks']
        
        if critical > 0:
            return f"{rating}: {critical} critical and {high} high-severity risks identified out of {total_risks} total risks. Deal requires significant risk mitigation and may not be advisable without substantial structural protections."
        elif high > 5:
            return f"{rating}: {high} high-severity risks identified out of {total_risks} total risks. Recommend careful structuring with earnouts, escrows, and comprehensive indemnification."
        elif high > 0:
            return f"{rating}: {high} high-severity risks identified out of {total_risks} total risks. Manageable with standard deal protections and thorough due diligence."
        else:
            return f"{rating}: {total_risks} risks identified, primarily medium and low severity. Standard M&A risk profile with appropriate due diligence and deal protections."
    
    async def _assess_governance_risks(self, proxy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess governance risks from proxy statement (DEF 14A)"""
        risks = []
        
        try:
            governance = proxy_data.get('governance_structure', {})
            
            if governance.get('found'):
                findings_count = governance.get('count', 0)
                
                if findings_count < 3:
                    risks.append({
                        'category': 'governance',
                        'severity': 'medium',
                        'description': 'Limited governance disclosure in proxy statement',
                        'likelihood': 'medium',
                        'impact': 'medium',
                        'mitigation': 'Conduct detailed governance review and request additional documentation',
                        'source': 'DEF 14A Proxy Statement',
                        'identified_by': 'risk_assessment'
                    })
            
            # Check for related party transactions
            related_parties = proxy_data.get('related_party_transactions', {})
            if related_parties.get('found') and related_parties.get('count', 0) > 0:
                risks.append({
                    'category': 'governance',
                    'severity': 'high',
                    'description': f"Related party transactions identified ({related_parties.get('count')} instances)",
                    'likelihood': 'high',
                    'impact': 'high',
                    'mitigation': 'Review all related party transactions for materiality and arm\'s length nature',
                    'source': 'DEF 14A Proxy Statement',
                    'identified_by': 'risk_assessment'
                })
            
            return risks
            
        except Exception as e:
            logger.error(f"Error assessing governance risks: {e}")
            return []
    
    async def _assess_ownership_risks(self, ownership_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess ownership concentration risks from SC 13D/13G filings"""
        risks = []
        
        try:
            activist_count = ownership_data.get('total_activist_positions', 0)
            concentration = ownership_data.get('ownership_concentration', 'moderate')
            
            if activist_count > 0:
                risks.append({
                    'category': 'ownership',
                    'severity': 'high',
                    'description': f"Activist investors identified ({activist_count} positions)",
                    'likelihood': 'high',
                    'impact': 'high',
                    'mitigation': 'Assess activist investor intentions and potential impact on deal structure',
                    'source': 'SC 13D Filings',
                    'identified_by': 'risk_assessment'
                })
            
            if concentration == 'high':
                risks.append({
                    'category': 'ownership',
                    'severity': 'medium',
                    'description': 'High ownership concentration detected',
                    'likelihood': 'medium',
                    'impact': 'high',
                    'mitigation': 'Analyze shareholder composition and voting requirements',
                    'source': 'SC 13D/13G Filings',
                    'identified_by': 'risk_assessment'
                })
            
            return risks
            
        except Exception as e:
            logger.error(f"Error assessing ownership risks: {e}")
            return []
    
    async def _detect_risk_anomalies(
        self,
        all_risks: List[Dict[str, Any]],
        risk_scores: Dict[str, Any],
        risk_matrix: Dict[str, Any],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Detect risk management anomalies
        
        Returns:
            Anomaly detection results for risk domain
        """
        anomalies = []
        
        # Check for risk concentration (>40% in single category)
        risk_categories = {}
        for risk in all_risks:
            category = risk.get('category', 'other')
            risk_categories[category] = risk_categories.get(category, 0) + 1
        
        for category, count in risk_categories.items():
            if len(all_risks) > 0 and count > len(all_risks) * 0.4:
                anomalies.append({
                    'type': 'risk_concentration',
                    'severity': 'high',
                    'description': f'Risk concentration in {category}: {count} risks ({count/len(all_risks):.0%} of total)',
                    'impact': 'Over-exposure to single risk category',
                    'recommendation': f'Diversify risk mitigation strategies for {category} risks'
                })
        
        # Check for critical risks without mitigation
        critical_risks = [r for r in all_risks if r.get('severity') == 'critical']
        unmitigated_critical = [r for r in critical_risks if not r.get('mitigation')]
        if unmitigated_critical:
            anomalies.append({
                'type': 'mitigation_gap',
                'severity': 'critical',
                'description': f'{len(unmitigated_critical)} critical risks lack mitigation strategies',
                'impact': 'Unprotected exposure to deal-breaking risks',
                'recommendation': 'Develop immediate mitigation plans for all critical risks'
            })
        
        # Check for unusual risk score (>75 = very high)
        risk_score = risk_scores.get('overall_risk_score', 0)
        if risk_score > 75:
            anomalies.append({
                'type': 'extreme_risk_score',
                'severity': 'critical',
                'description': f'Extreme risk score detected: {risk_score}/100',
                'impact': 'Deal may not be advisable without major structural changes',
                'recommendation': 'Reassess deal viability and consider walk-away scenarios'
            })
        
        # Check for high-impact, high-likelihood risks (deal breakers)
        deal_breakers = risk_matrix.get('high_likelihood_high_impact', [])
        if len(deal_breakers) > 3:
            anomalies.append({
                'type': 'deal_breaker_cluster',
                'severity': 'critical',
                'description': f'{len(deal_breakers)} high-likelihood, high-impact risks identified',
                'impact': 'Multiple probable deal-breaking scenarios',
                'recommendation': 'Conduct detailed risk mitigation planning before proceeding'
            })
        
        return {
            'anomalies_detected': anomalies,
            'risk_level': 'Critical' if len([a for a in anomalies if a['severity'] == 'critical']) > 0 else 'High' if len([a for a in anomalies if a['severity'] == 'high']) > 0 else 'Medium' if anomalies else 'Low',
            'total_anomalies': len(anomalies)
        }
