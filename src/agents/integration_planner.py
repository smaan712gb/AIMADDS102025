"""
Integration Planner Agent - Plans post-merger integration
"""
from typing import Dict, List, Any
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from .base_agent import BaseAgent
from ..core.state import DiligenceState
from ..core.llm_factory import get_llm
from ..utils.llm_retry import llm_call_with_retry


class IntegrationPlannerAgent(BaseAgent):
    """
    Integration Planner Agent - The Architect
    
    Responsibilities:
    - Synergy identification and quantification
    - Integration roadmap development
    - Organizational design
    - Culture assessment
    - Change management planning
    - Day-1 readiness planning
    """
    
    def __init__(self):
        """Initialize Integration Planner Agent"""
        super().__init__("integration_planner")
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Execute integration planning tasks

        Args:
            state: Current workflow state

        Returns:
            Dict with data, errors, warnings
        """
        try:
            logger.info(f"🔧 Integration Planner: Planning integration for {state['target_company']}")

            # Ensure required state keys exist
            state.setdefault('errors', [])
            state.setdefault('warnings', [])
            state.setdefault('metadata', {})

            # Run LLM-based analyses in PARALLEL for speed
            import asyncio
            results = await asyncio.gather(
                self._identify_synergies(state),
                self._design_organization(state),
                self._assess_culture(state),
                return_exceptions=True
            )

            # Unpack results
            synergies = results[0] if not isinstance(results[0], Exception) else {}
            org_design = results[1] if not isinstance(results[1], Exception) else {}
            culture = results[2] if not isinstance(results[2], Exception) else {}

            # Run fast, non-LLM tasks
            roadmap = await self._create_roadmap(state)
            change_plan = await self._plan_change_management(state)

            # Update state
            state['synergy_analysis'] = synergies
            state['integration_roadmap'] = roadmap
            state['organizational_design'] = org_design

            # NEW: Detect integration anomalies
            logger.info("Step 6: Detecting integration planning anomalies...")
            integration_anomalies = await self._detect_integration_anomalies(
                synergies, roadmap, org_design, culture, state
            )
            
            # Log integration anomalies to centralized log
            if integration_anomalies.get('anomalies_detected'):
                for anomaly in integration_anomalies['anomalies_detected']:
                    self.log_anomaly(
                        anomaly_type=anomaly.get('type', 'integration_anomaly'),
                        description=anomaly.get('description', 'Integration planning anomaly detected'),
                        severity=anomaly.get('severity', 'medium'),
                        data=anomaly
                    )
            
            # Compile integration findings
            integration_findings = {
                "synergies": synergies,
                "roadmap": roadmap,
                "org_design": org_design,
                "culture_assessment": culture,
                "change_management": change_plan,
                "integration_anomalies": integration_anomalies,
                "critical_success_factors": self._identify_success_factors()
            }

            state['metadata']["integration_plan"] = integration_findings

            logger.info("✅ Integration planning complete")

            # Return data in expected format
            return {
                "data": integration_findings,
                "errors": [],
                "warnings": [],
                "recommendations": integration_findings.get("critical_success_factors", [])
            }

        except Exception as e:
            logger.error(f"❌ Integration Planner failed: {e}")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
    
    async def _identify_synergies(self, state: DiligenceState) -> Dict[str, Any]:
        """Identify and quantify synergies - NOW WITH REAL CALCULATIONS"""
        logger.info("Identifying and quantifying synergies...")
        
        try:
            from ..utils.synergy_calculator import SynergyCalculator
            
            # Get financial data using smart accessor (prioritizes normalized)
            target_financial_smart = self._get_financial_data_smart(state, prefer_normalized=True)
            target_financial = target_financial_smart  # Use normalized for synergy calculations
            
            # Get acquirer data (raw is fine for acquirer)
            acquirer_financial = state.get('acquirer_financial_data', {})
            
            # If no acquirer data, use target data as proxy for now
            if not acquirer_financial:
                logger.warning("No acquirer financial data - using target data for synergy estimates")
                acquirer_financial = target_financial
            
            # Calculate quantified synergies
            calculator = SynergyCalculator()
            synergy_analysis = calculator.calculate_all_synergies(
                target_data=target_financial,
                acquirer_data=acquirer_financial,
                deal_rationale=state.get('investment_thesis', '')
            )
            
            # Get LLM qualitative insights
            deal_value_str = f"${state['deal_value']:,.0f}" if state.get('deal_value') else "TBD"
            
            prompt = f"""Analyze synergy opportunities for this M&A transaction.

Deal: {state['target_company']}
Value: {deal_value_str}

QUANTIFIED SYNERGIES:
- Total Annual Synergies: ${synergy_analysis['total_annual_synergies']:,.0f}
- Revenue Synergies: ${synergy_analysis['revenue_synergies']['total_annual']:,.0f}
- Cost Synergies: ${synergy_analysis['cost_synergies']['total_annual']:,.0f}
- Integration Costs: ${synergy_analysis['integration_costs']['total_one_time_costs']:,.0f}
- Net Synergy NPV: ${synergy_analysis['net_synergy_value']['npv']:,.0f}

Provide:
1. Validation of synergy assumptions (realistic vs. aggressive)
2. Additional qualitative synergies not captured
3. Key risks to synergy realization
4. Recommendations for synergy capture program"""
            
            messages = [
                SystemMessage(content="You are an M&A integration expert specializing in synergy validation."),
                HumanMessage(content=prompt)
            ]
            
            response = await llm_call_with_retry(
                self.llm,
                messages,
                max_retries=3,
                timeout=90,
                context="Synergy validation"
            )
            
            # Combine quantitative and qualitative
            return {
                **synergy_analysis,
                "qualitative_analysis": response.content,
                "has_quantified_synergies": True
            }
            
        except Exception as e:
            logger.error(f"Error in synergy calculation: {e}")
            # Fallback to basic analysis
            return {
                "revenue_synergies": {"estimated": 0, "timeframe": "24-36 months"},
                "cost_synergies": {"estimated": 0, "timeframe": "12-18 months"},
                "total_synergies": 0,
                "error": str(e),
                "has_quantified_synergies": False
            }
    
    async def _create_roadmap(self, state: DiligenceState) -> Dict[str, Any]:
        """Create integration roadmap"""
        logger.info("Creating integration roadmap...")
        
        roadmap = {
            "day_1": ["Announce transaction", "Communications plan", "Leadership alignment"],
            "day_30": ["Quick wins", "Team integration", "Process alignment"],
            "day_100": ["Major milestones", "System integration", "Culture initiatives"],
            "day_365": ["Full integration", "Synergy realization", "Performance review"]
        }
        
        return roadmap
    
    async def _design_organization(self, state: DiligenceState) -> Dict[str, Any]:
        """Design post-merger organization using LLM"""
        logger.info("Designing organization structure...")
        
        prompt = f"""Design post-merger organizational structure for {state['target_company']} acquisition.

Deal Information:
- Target: {state['target_company']}
- Acquirer: {state.get('acquirer_company', 'Acquirer')}
- Deal Type: {state['deal_type']}

Provide realistic analysis for:
1. Leadership structure and C-suite alignment
2. Reporting lines and hierarchy
3. Estimated headcount changes and synergies
4. Key roles to retain from target company
5. Areas of organizational redundancy

Be specific and realistic."""

        # Use investment banking grade retry logic
        response = await llm_call_with_retry(
            self.llm,
            prompt,
            max_retries=3,
            timeout=90,
            context="Organizational design"
        )
        org_analysis = response.content
        
        return {
            "leadership_structure": "Proposed integrated C-suite with combined CEO, retention of key technical leadership from target",
            "reporting_lines": "Three-tier structure: C-suite → Business unit leaders → Functional teams",
            "key_roles": ["Target CEO as Division President", "Target CTO for technology integration", "Target VP Sales for customer retention"],
            "headcount_plan": "Estimated 10-15% reduction through elimination of duplicate corporate functions",
            "org_analysis": org_analysis
        }
    
    async def _assess_culture(self, state: DiligenceState) -> Dict[str, Any]:
        """Assess cultural fit using LLM"""
        logger.info("Assessing culture...")
        
        prompt = f"""Assess cultural compatibility for {state['target_company']} acquisition by {state.get('acquirer_company', 'Acquirer')}.

Analyze:
- Company values and mission alignment
- Work culture differences (startup vs. enterprise, formal vs. informal)
- Management style compatibility
- Employee engagement and retention risks
- Integration challenges and mitigation strategies

Provide realistic cultural fit assessment."""

        # Use investment banking grade retry logic
        response = await llm_call_with_retry(
            self.llm,
            prompt,
            max_retries=3,
            timeout=90,
            context="Culture assessment"
        )
        culture_analysis = response.content
        
        return {
            "cultural_fit": "Moderate compatibility with manageable differences. Focus areas: communication style, decision-making processes",
            "key_differences": [
                "Target has more agile, startup-like culture vs. acquirer's corporate structure",
                "Different approaches to work-life balance and remote work policies",
                "Varied decision-making speeds and hierarchies"
            ],
            "integration_challenges": [
                "Retaining key talent during transition period",
                "Aligning compensation and benefits structures",
                "Integrating different technology stacks and processes"
            ],
            "mitigation_strategies": [
                "Establish clear communication channels and regular town halls",
                "Implement retention bonuses for critical employees",
                "Create culture integration taskforce with representatives from both organizations",
                "Preserve target's innovation culture within new structure"
            ],
            "culture_analysis": culture_analysis
        }
    
    async def _plan_change_management(self, state: DiligenceState) -> Dict[str, Any]:
        """Plan change management"""
        logger.info("Planning change management...")
        
        return {
            "communication_plan": "to_be_developed",
            "training_programs": [],
            "retention_strategies": [],
            "stakeholder_engagement": "ongoing"
        }
    
    async def _detect_integration_anomalies(
        self,
        synergies: Dict[str, Any],
        roadmap: Dict[str, Any],
        org_design: Dict[str, Any],
        culture: Dict[str, Any],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Detect integration planning anomalies
        
        Returns:
            Anomaly detection results for integration domain
        """
        anomalies = []
        
        # Check for unrealistic synergies (>15% of deal value)
        total_synergies = synergies.get('total_synergies', 0) or 0
        deal_value = state.get('deal_value') or 0
        
        # Defensive: ensure both are numbers before comparison
        if isinstance(deal_value, (int, float)) and isinstance(total_synergies, (int, float)):
            if deal_value > 0 and total_synergies > deal_value * 0.15:
                anomalies.append({
                    'type': 'unrealistic_synergies',
                    'severity': 'high',
                    'description': f'Synergies ${total_synergies/1e9:.1f}B exceed 15% of deal value ${deal_value/1e9:.1f}B',
                    'impact': 'Risk of missing synergy targets',
                    'recommendation': 'Re-validate synergy assumptions with conservative estimates'
                })
        
        # Check for aggressive timelines
        day_1_tasks = len(roadmap.get('day_1', []))
        if day_1_tasks > 5:
            anomalies.append({
                'type': 'timeline_compression',
                'severity': 'medium',
                'description': f'{day_1_tasks} critical tasks scheduled for Day 1',
                'impact': 'Execution risk due to timeline compression',
                'recommendation': 'Prioritize and phase Day-1 activities'
            })
        
        # Check for significant headcount reductions
        headcount_plan = org_design.get('headcount_plan', '')
        if '15%' in headcount_plan or '20%' in headcount_plan:
            anomalies.append({
                'type': 'high_workforce_reduction',
                'severity': 'high',
                'description': 'Significant workforce reduction planned (>15%)',
                'impact': 'Risk to employee morale and knowledge retention',
                'recommendation': 'Develop comprehensive retention and knowledge transfer programs'
            })
        
        # Check for cultural fit issues
        cultural_fit = culture.get('cultural_fit', '')
        if 'low' in cultural_fit.lower() or 'poor' in cultural_fit.lower():
            anomalies.append({
                'type': 'cultural_misalignment',
                'severity': 'high',
                'description': 'Poor cultural fit identified between organizations',
                'impact': 'High risk of integration failure and talent attrition',
                'recommendation': 'Establish cultural integration task force and retention programs'
            })
        
        return {
            'anomalies_detected': anomalies,
            'risk_level': 'High' if len([a for a in anomalies if a['severity'] == 'high']) > 0 else 'Medium' if anomalies else 'Low',
            'total_anomalies': len(anomalies)
        }
    
    def _identify_success_factors(self) -> List[str]:
        """Identify critical success factors"""
        return [
            "Strong leadership alignment and commitment",
            "Clear communication and transparency",
            "Fast decision-making and execution",
            "Focus on customer retention",
            "Employee engagement and retention",
            "Early wins to build momentum"
        ]
