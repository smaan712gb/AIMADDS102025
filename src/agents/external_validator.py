"""
External Consensus & Validation Agent (The Validator)

This agent provides crucial external validation by:
1. Analyzing draft reports from internal analysis
2. Conducting targeted web research to validate key findings
3. Identifying discrepancies between internal and external consensus
4. Generating adjustment plans for re-analysis when needed
5. Ensuring the final valuation range reflects both internal and market reality
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent
from ..core.state import DiligenceState


class ExternalValidatorAgent(BaseAgent):
    """
    The Validator Agent challenges internal assumptions with external market consensus.
    
    This agent transforms the system from analytically complete to commercially viable
    by providing the critical outside-in perspective that prevents echo chambers.
    """
    
    def __init__(self):
        super().__init__("external_validator")
        self.validation_results = []
        self.adjustment_requests = []
        
        # Initialize Tavily for real web search
        try:
            from ..integrations.tavily_client import get_tavily_client
            self.tavily = get_tavily_client()
            if self.tavily:
                logger.info("✓ Tavily web search ENABLED for external validation")
            else:
                logger.warning("⚠️ Tavily not available - using LLM-only mode (less reliable)")
        except Exception as e:
            self.tavily = None
            logger.warning(f"⚠️ Tavily initialization failed: {e}")
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Perform high-level sanity checks on internal analysis instead of parallel valuations.
        
        Args:
            state: Current diligence state with draft analysis
            
        Returns:
            Dictionary with sanity check results and recommendations
        """
        self.log_action("Beginning external sanity checks")
        
        target_company = state.get("target_company", "Unknown")
        
        # Extract draft report from state
        draft_report = self._compile_draft_report(state)
        
        # Perform sanity checks on internal data
        sanity_checks = self._perform_sanity_checks(draft_report, state)
        
        # Calculate confidence score based on sanity checks
        confidence_score = self._calculate_sanity_confidence(sanity_checks)
        
        # Generate recommendations based on sanity checks
        recommendations = self._generate_sanity_recommendations(sanity_checks)
        
        # Compile final validation report
        validation_data = {
            "target_company": target_company,
            "validation_timestamp": datetime.now().isoformat(),
            "validation_type": "sanity_checks",
            "sanity_checks_performed": len(sanity_checks),
            "sanity_checks": sanity_checks,
            "confidence_score": confidence_score,
            "critical_issues": [s for s in sanity_checks if s.get("severity") == "critical"],
            "moderate_issues": [s for s in sanity_checks if s.get("severity") == "moderate"],
            "validated_findings": sanity_checks  # Use sanity checks as validated findings
        }
        
        self.validation_results.append(validation_data)
        
        # NEW: Detect validation anomalies
        logger.info("Detecting validation anomalies...")
        validation_anomalies = await self._detect_validation_anomalies(
            validation_data, sanity_checks, state
        )
        
        # Log validation anomalies
        if validation_anomalies.get('anomalies_detected'):
            for anomaly in validation_anomalies['anomalies_detected']:
                self.log_anomaly(
                    anomaly_type=anomaly.get('type', 'validation_anomaly'),
                    description=anomaly.get('description', 'Validation anomaly detected'),
                    severity=anomaly.get('severity', 'medium'),
                    data=anomaly
                )
        
        validation_data['validation_anomalies'] = validation_anomalies
        
        self.log_action(f"Sanity checks complete. Confidence: {confidence_score:.2f}, " +
                       f"Critical issues: {len(validation_data['critical_issues'])}")
        
        warnings = [s.get("warning", "") for s in sanity_checks 
                   if s.get("severity") in ["critical", "moderate"]]
        
        return {
            "data": validation_data,
            "errors": [],
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    def _compile_draft_report(self, state: DiligenceState) -> Dict[str, Any]:
        """Compile draft report from all agent outputs in state."""
        draft_report = {
            "target_company": state.get("target_company", "Unknown"),
            "financial_analysis": {},
            "risk_analysis": {},
            "market_analysis": {},
            "operational_analysis": {},
            "legal_analysis": {},
            "competitive_analysis": {},
            "macroeconomic_analysis": {}
        }
        
        # Read data directly from state keys where agents store their results
        # Financial data
        financial_data = state.get("financial_data", {})
        if financial_data:
            draft_report["financial_analysis"] = financial_data
        
        # Financial deep dive data
        financial_deep_dive = state.get("financial_deep_dive", {})
        if financial_deep_dive:
            draft_report["financial_deep_dive"] = financial_deep_dive
        
        # Market analysis
        market_analysis = state.get("market_analysis", {})
        if market_analysis:
            draft_report["market_analysis"] = market_analysis
        
        # Legal analysis
        legal_analysis = state.get("legal_analysis", {})
        if legal_analysis:
            draft_report["legal_analysis"] = legal_analysis
        
        # Competitive analysis
        competitive_analysis = state.get("competitive_analysis", {})
        if competitive_analysis:
            draft_report["competitive_analysis"] = competitive_analysis
        
        # Macroeconomic analysis
        macro_analysis = state.get("macroeconomic_analysis", {})
        if macro_analysis:
            draft_report["macroeconomic_analysis"] = macro_analysis
        
        # Integration planning
        integration_plan = state.get("integration_plan", {})
        if integration_plan:
            draft_report["operational_analysis"]["integration"] = integration_plan
        
        # Compile risk analysis from various sources
        if "risks" in financial_data:
            draft_report["risk_analysis"]["financial"] = financial_data["risks"]
        
        if "legal_risks" in legal_analysis or "risks" in legal_analysis:
            draft_report["risk_analysis"]["legal"] = legal_analysis.get("legal_risks", legal_analysis.get("risks", []))
        
        if "market_risks" in market_analysis or "risks" in market_analysis:
            draft_report["risk_analysis"]["market"] = market_analysis.get("market_risks", market_analysis.get("risks", []))
        
        return draft_report
    
    def _extract_key_findings(self, draft_report: Dict[str, Any], state: DiligenceState) -> List[Dict[str, Any]]:
        """
        Extract key findings from draft report that need external validation.
        
        Focus on:
        - Revenue/growth projections
        - Valuation ranges
        - Risk assessments
        - Market position claims
        - Competitive landscape
        - Supply chain/operational assumptions
        """
        key_findings = []
        target_company = state.get("target_company", "Unknown")
        
        # Extract financial projections
        financial = draft_report.get("financial_analysis", {})
        deep_dive = draft_report.get("financial_deep_dive", {})
        
        # Revenue growth projections
        if "revenue_growth_forecast" in financial or "growth_rate" in financial:
            growth_data = financial.get("revenue_growth_forecast", financial.get("growth_rate", {}))
            key_findings.append({
                "category": "financial",
                "type": "revenue_growth",
                "finding": growth_data,
                "rating": "high" if isinstance(growth_data, (int, float)) and growth_data > 30 else "medium",
                "source_agent": "Financial Analyst",
                "validation_priority": "high"
            })
        
        # Valuation range
        if "valuation" in financial or "enterprise_value" in financial:
            valuation_data = financial.get("valuation", financial.get("enterprise_value", {}))
            key_findings.append({
                "category": "financial",
                "type": "valuation",
                "finding": valuation_data,
                "source_agent": "Financial Analyst",
                "validation_priority": "critical"
            })
        
        # Extract financial deep dive findings
        if deep_dive:
            # Working capital findings
            if "working_capital" in deep_dive:
                wc_data = deep_dive["working_capital"]
                key_findings.append({
                    "category": "financial",
                    "type": "working_capital",
                    "finding": wc_data.get("nwc_analysis", {}),
                    "rating": wc_data.get("nwc_analysis", {}).get("volatility_assessment", "medium"),
                    "source_agent": "Financial Deep Dive",
                    "validation_priority": "high"
                })
            
            # CapEx findings
            if "capex_analysis" in deep_dive:
                capex_data = deep_dive["capex_analysis"]
                key_findings.append({
                    "category": "financial",
                    "type": "capex_intensity",
                    "finding": capex_data.get("capex_analysis", {}),
                    "rating": capex_data.get("capex_analysis", {}).get("asset_intensity", "medium"),
                    "source_agent": "Financial Deep Dive",
                    "validation_priority": "high"
                })
            
            # Debt findings
            if "debt_schedule" in deep_dive:
                debt_data = deep_dive["debt_schedule"]
                key_findings.append({
                    "category": "financial",
                    "type": "debt_structure",
                    "finding": debt_data.get("debt_analysis", {}),
                    "rating": debt_data.get("debt_analysis", {}).get("refinancing_risk", "medium"),
                    "source_agent": "Financial Deep Dive",
                    "validation_priority": "high"
                })
        
        # Extract risk assessments from all sources
        risk_analysis = draft_report.get("risk_analysis", {})
        for agent_name, risks in risk_analysis.items():
            if isinstance(risks, dict):
                for risk_category, risk_data in risks.items():
                    if isinstance(risk_data, dict) and "rating" in risk_data:
                        key_findings.append({
                            "category": "risk",
                            "type": risk_category,
                            "finding": risk_data.get("description", ""),
                            "rating": risk_data["rating"],
                            "source_agent": agent_name,
                            "validation_priority": "high" if risk_data["rating"] == "high" else "medium"
                        })
        
        # Extract market position claims
        market = draft_report.get("market_analysis", {})
        
        if "market_share" in market or "market_position" in market:
            market_position = market.get("market_share", market.get("market_position", {}))
            key_findings.append({
                "category": "market",
                "type": "market_share",
                "finding": market_position,
                "source_agent": "Market Strategist",
                "validation_priority": "high"
            })
        
        if "competitive_landscape" in market or "competitors" in market:
            competitive_data = market.get("competitive_landscape", market.get("competitors", {}))
            key_findings.append({
                "category": "market",
                "type": "competition",
                "finding": competitive_data,
                "rating": market.get("competitive_risk_rating", "medium"),
                "source_agent": "Market Strategist",
                "validation_priority": "high"
            })
        
        # Extract operational/supply chain assumptions
        legal = draft_report.get("legal_analysis", {})
        operational = draft_report.get("operational_analysis", {})
        
        for analysis in [legal, operational]:
            for key in ["supply_chain", "manufacturing", "distribution", "operations"]:
                if key in analysis:
                    data = analysis[key]
                    if isinstance(data, dict):
                        key_findings.append({
                            "category": "operational",
                            "type": key,
                            "finding": data.get("assessment", data),
                            "rating": data.get("risk_rating", "low"),
                            "source_agent": data.get("source_agent", "Legal Counsel"),
                            "validation_priority": "medium" if data.get("risk_rating") == "low" else "high"
                        })
        
        # NEW: Extract Risk Assessment findings for validation
        risk_assessment = state.get('risk_assessment', {})
        if risk_assessment:
            risk_scores = risk_assessment.get('risk_scores', {})
            risk_rating = risk_scores.get('risk_rating', 'Unknown')
            overall_score = risk_scores.get('overall_risk_score', 0)
            
            key_findings.append({
                "category": "risk_assessment",
                "type": "overall_risk_rating",
                "finding": {
                    "rating": risk_rating,
                    "score": overall_score,
                    "total_risks": risk_scores.get('total_risks', 0),
                    "critical_risks": risk_scores.get('critical_risks', 0)
                },
                "rating": "high" if overall_score > 70 else "medium",
                "source_agent": "Risk Assessment",
                "validation_priority": "high"
            })
            
            # Validate risk-adjusted scenarios
            risk_scenarios = risk_assessment.get('risk_scenarios', {})
            if risk_scenarios:
                key_findings.append({
                    "category": "risk_assessment",
                    "type": "risk_adjusted_valuation",
                    "finding": risk_scenarios,
                    "source_agent": "Risk Assessment",
                    "validation_priority": "critical"
                })
        
        # NEW: Extract Tax Structuring findings for validation
        tax_analysis = state.get('tax_analysis', {})
        if tax_analysis:
            optimal_structure = tax_analysis.get('optimal_structure', 'TBD')
            structure_comparison = tax_analysis.get('structure_comparison', {})
            
            key_findings.append({
                "category": "tax_structuring",
                "type": "deal_structure",
                "finding": {
                    "recommended_structure": optimal_structure,
                    "structures_analyzed": len(structure_comparison)
                },
                "source_agent": "Tax Structuring",
                "validation_priority": "high"
            })
            
            # Validate tax benefit calculations
            tax_implications = tax_analysis.get('tax_implications', {})
            if tax_implications:
                asset_benefit = tax_implications.get('asset_step_up_benefit', {})
                if asset_benefit:
                    key_findings.append({
                        "category": "tax_structuring",
                        "type": "tax_benefits",
                        "finding": asset_benefit,
                        "source_agent": "Tax Structuring",
                        "validation_priority": "high"
                    })
        
        self.log_action(f"Extracted {len(key_findings)} key findings for validation (including Risk Assessment & Tax Structuring)")
        return key_findings
    
    async def _conduct_targeted_research(
        self,
        key_findings: List[Dict[str, Any]],
        target_company: str,
        state: DiligenceState
    ) -> List[Dict[str, Any]]:
        """
        Conduct targeted external research based on key findings.
        
        Generate specific search queries for each finding and collect evidence.
        
        OPTIMIZED: Uses asyncio.gather to run all research queries in parallel,
        dramatically reducing runtime from 7.5 minutes to ~1-2 minutes.
        """
        import asyncio
        
        # Generate all search queries first
        research_tasks = []
        for finding in key_findings:
            search_query = self._generate_search_query(finding, target_company)
            research_tasks.append({
                'finding': finding,
                'search_query': search_query,
                'target_company': target_company
            })
        
        self.log_action(f"Starting parallel research for {len(research_tasks)} findings...")
        
        # Execute all research queries in parallel using asyncio.gather
        research_coroutines = [
            self._perform_research(task['search_query'], task['finding'], task['target_company'])
            for task in research_tasks
        ]
        
        research_results = await asyncio.gather(*research_coroutines, return_exceptions=True)
        
        # Compile results
        external_evidence = []
        for task, research_result in zip(research_tasks, research_results):
            # Handle exceptions from any failed queries
            if isinstance(research_result, Exception):
                self.log_action(f"Research failed for {task['finding']['type']}: {research_result}", "warning")
                continue
            
            if research_result:
                external_evidence.append({
                    "finding_category": task['finding']["category"],
                    "finding_type": task['finding']["type"],
                    "search_query": task['search_query'],
                    "evidence": research_result,
                    "timestamp": datetime.now().isoformat()
                })
        
        self.log_action(f"Collected {len(external_evidence)} external evidence items (parallel execution)")
        return external_evidence
    
    def _generate_search_query(self, finding: Dict[str, Any], target_company: str) -> str:
        """Generate targeted search query based on finding type."""
        category = finding["category"]
        finding_type = finding["type"]
        
        # Generate specific queries based on category and type
        query_templates = {
            ("financial", "revenue_growth"): f"{target_company} analyst revenue forecast consensus 2025 2026",
            ("financial", "valuation"): f"{target_company} valuation enterprise value analyst estimates",
            ("market", "market_share"): f"{target_company} market share industry position 2025",
            ("market", "competition"): f"{target_company} competitive landscape rivals threats 2025",
            ("operational", "supply_chain"): f"{target_company} supply chain risks bottlenecks 2025",
            ("operational", "manufacturing"): f"{target_company} manufacturing capacity production challenges",
            ("risk", "regulatory"): f"{target_company} regulatory risks compliance issues 2025",
            ("risk", "technology"): f"{target_company} technology risks innovation challenges"
        }
        
        query = query_templates.get((category, finding_type), 
                                    f"{target_company} {finding_type} analysis 2025")
        
        return query
    
    async def _perform_research(
        self,
        search_query: str,
        finding: Dict[str, Any],
        target_company: str
    ) -> Dict[str, Any]:
        """
        Perform real web research using Tavily + LLM analysis
        
        CORRECT APPROACH (Tavily → LLM):
        1. Use Tavily to get REAL web search results
        2. Use LLM to ANALYZE those real results
        """
        
        # METHOD 1: Try Tavily for real web search (BEST)
        if self.tavily:
            try:
                self.log_action(f"🌐 Tavily web search: '{search_query}'")
                
                # Use Tavily to get REAL search results
                search_results = await self.tavily.search_financial_data(
                    company=target_company,
                    topic=f"{finding['type']} {finding['category']}",
                    max_results=10
                )
                
                if search_results['success'] and search_results['result_count'] > 0:
                    # Tavily succeeded - now use LLM to ANALYZE the real data
                    self.log_action(f"✓ Tavily found {search_results['result_count']} sources")
                    
                    # Parse results (simplified - no LLM analysis needed for basic validation)
                    parsed_results = self.tavily.parse_search_results(search_results)
                    
                    return {
                        "summary": search_results.get('answer', 'No summary from Tavily'),
                        "structured_data": {
                            "confidence_level": parsed_results['confidence'],
                            "sources": parsed_results['sources'],
                            "source_count": parsed_results['total_sources'],
                            "financial_sources": parsed_results['financial_source_count'],
                            "tavily_answer": search_results.get('answer', ''),
                            "search_method": "tavily_web_search"
                        },
                        "confidence": parsed_results['confidence'],
                        "source_types": ["tavily_web_search"],
                        "research_date": datetime.now().isoformat(),
                        "data_freshness": "recent"
                    }
                    
            except Exception as e:
                self.log_action(f"⚠️ Tavily error: {e}, using fallback")
        
        # METHOD 2: Fallback to simple response if Tavily unavailable
        self.log_action(f"📝 No web search available for: '{search_query}'")
        return {
            "summary": f"External validation unavailable for: {search_query}",
            "confidence": "low",
            "source_types": ["none"],
            "warning": "No web search available"
        }
    
    def _parse_research_response(self, research_text: str, target_company: str) -> Dict[str, Any]:
        """
        Parse the deep research response to extract structured information.
        
        This helps identify:
        - Specific analyst firms mentioned
        - Numerical data points (revenues, growth rates, valuations)
        - Date ranges of data
        - Consensus vs outlier views
        """
        structured_data = {
            "confidence_level": "medium",
            "sources": [],
            "data_freshness": "unknown",
            "analyst_firms": [],
            "numerical_data": {},
            "key_dates": []
        }
        
        # Extract analyst firm names
        analyst_firms = [
            "Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America",
            "Credit Suisse", "Citi", "Wells Fargo", "Barclays",
            "Raymond James", "Piper Sandler", "Cowen", "Wedbush"
        ]
        
        for firm in analyst_firms:
            if firm.lower() in research_text.lower():
                structured_data["analyst_firms"].append(firm)
        
        # Determine confidence level based on content
        if len(structured_data["analyst_firms"]) >= 3:
            structured_data["confidence_level"] = "high"
            structured_data["sources"].append("multiple_analyst_reports")
        elif len(structured_data["analyst_firms"]) >= 1:
            structured_data["confidence_level"] = "medium"
            structured_data["sources"].append("analyst_reports")
        else:
            structured_data["confidence_level"] = "low"
        
        # Check for SEC filings
        sec_terms = ["10-K", "10-Q", "8-K", "proxy", "SEC filing"]
        if any(term in research_text for term in sec_terms):
            structured_data["sources"].append("sec_filings")
            structured_data["confidence_level"] = "high"
        
        # Check for earnings calls
        earnings_terms = ["earnings call", "investor presentation", "conference call"]
        if any(term.lower() in research_text.lower() for term in earnings_terms):
            structured_data["sources"].append("earnings_calls")
        
        # Check for financial news
        news_sources = ["Bloomberg", "Reuters", "Wall Street Journal", "Financial Times", "CNBC"]
        for source in news_sources:
            if source in research_text:
                structured_data["sources"].append("financial_news")
                break
        
        # Extract time references to assess data freshness
        time_terms = {
            "recent": ["recently", "last month", "last quarter", "Q1 2025", "Q2 2025", "2025"],
            "moderate": ["last year", "2024", "Q4 2024", "Q3 2024"],
            "stale": ["2023", "2022", "several years ago"]
        }
        
        for freshness, terms in time_terms.items():
            if any(term.lower() in research_text.lower() for term in terms):
                structured_data["data_freshness"] = freshness
                break
        
        # Look for percentage data (growth rates, margins, etc.)
        import re
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', research_text)
        if percentages:
            structured_data["numerical_data"]["percentages_found"] = len(percentages)
        
        # Look for dollar amounts (valuations, revenues)
        dollar_amounts = re.findall(r'\$\s*(\d+(?:\.\d+)?)\s*(billion|million|B|M)', research_text, re.IGNORECASE)
        if dollar_amounts:
            structured_data["numerical_data"]["dollar_amounts_found"] = len(dollar_amounts)
        
        return structured_data
    
    async def _compare_findings(
        self,
        key_findings: List[Dict[str, Any]],
        external_evidence: List[Dict[str, Any]],
        target_company: str
    ) -> List[Dict[str, Any]]:
        """
        Compare internal findings with external evidence.
        
        Identify:
        - Validated findings (internal matches external)
        - Discrepancies (internal conflicts with external)
        - Missing information (external reveals what internal missed)
        """
        validation_results = []
        
        for finding in key_findings:
            # Find corresponding external evidence
            matching_evidence = [
                ev for ev in external_evidence
                if ev["finding_category"] == finding["category"]
                and ev["finding_type"] == finding["type"]
            ]
            
            if not matching_evidence:
                validation_results.append({
                    "finding": finding,
                    "status": "no_external_data",
                    "severity": "low",
                    "message": "No external evidence found for validation"
                })
                continue
            
            # Use LLM to compare internal vs external
            comparison = await self._llm_compare_findings(finding, matching_evidence[0], target_company)
            
            validation_results.append(comparison)
        
        return validation_results
    
    async def _llm_compare_findings(
        self,
        internal_finding: Dict[str, Any],
        external_evidence: Dict[str, Any],
        target_company: str
    ) -> Dict[str, Any]:
        """Use LLM to intelligently compare internal vs external findings."""
        
        comparison_prompt = f"""Compare internal M&A analysis with external market consensus.

Target Company: {target_company}

INTERNAL FINDING:
Category: {internal_finding['category']}
Type: {internal_finding['type']}
Assessment: {internal_finding.get('finding', 'Not specified')}
Rating: {internal_finding.get('rating', 'Not specified')}
Source: {internal_finding['source_agent']}

EXTERNAL EVIDENCE:
{external_evidence['evidence'].get('summary', 'No summary available')}

Your task:
1. Determine if internal and external findings ALIGN, PARTIALLY ALIGN, or CONFLICT
2. Assess severity: CRITICAL (major discrepancy), MODERATE (notable difference), or LOW (minor variance)
3. Identify what the internal analysis may have MISSED based on external evidence
4. Provide a clear, specific comparison

Respond in JSON format:
{{
    "status": "validated" or "partial_discrepancy" or "critical_discrepancy",
    "severity": "critical" or "moderate" or "low",
    "alignment_score": 0.0 to 1.0,
    "comparison_summary": "Brief specific comparison",
    "external_consensus": "What external sources indicate",
    "internal_vs_external": "Specific differences or alignments",
    "missed_information": "What internal analysis missed (if any)",
    "recommendation": "What action to take"
}}
"""
        
        try:
            # Use async invoke for proper response
            response = await self.llm.ainvoke(comparison_prompt)
            comparison_text = response.content
            
            # Parse JSON response
            # Remove markdown code blocks if present
            comparison_text = comparison_text.strip()
            if comparison_text.startswith("```"):
                comparison_text = re.sub(r'^```json\s*\n?', '', comparison_text)
                comparison_text = re.sub(r'\n?```$', '', comparison_text)
            
            comparison_data = json.loads(comparison_text)
            
            # Add original finding reference
            comparison_data["finding"] = internal_finding
            comparison_data["external_evidence"] = external_evidence
            
            return comparison_data
            
        except (json.JSONDecodeError, Exception) as e:
            self.log_action(f"LLM comparison parsing error: {e}", "warning")
            # Fallback to basic comparison
            return {
                "finding": internal_finding,
                "status": "partial_discrepancy",
                "severity": "moderate",
                "alignment_score": 0.5,
                "comparison_summary": "Unable to perform detailed comparison",
                "recommendation": "Manual review recommended",
                "error": str(e)
            }
    
    def _generate_adjustment_plan(
        self,
        validation_results: List[Dict[str, Any]],
        draft_report: Dict[str, Any],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Generate adjustment plan for identified discrepancies.
        
        This plan tells the Orchestrator which agents need to re-run analysis
        and what specific changes to make.
        """
        adjustment_plan = {
            "requires_reanalysis": False,
            "adjustments": [],
            "agents_to_rerun": [],
            "priority": "low"
        }
        
        # Find critical and moderate discrepancies
        critical_discrepancies = [v for v in validation_results if v.get("severity") == "critical"]
        moderate_discrepancies = [v for v in validation_results if v.get("severity") == "moderate"]
        
        if not critical_discrepancies and not moderate_discrepancies:
            adjustment_plan["message"] = "All findings validated. No reanalysis required."
            return adjustment_plan
        
        # Requires reanalysis if we have critical discrepancies
        adjustment_plan["requires_reanalysis"] = len(critical_discrepancies) > 0
        adjustment_plan["priority"] = "critical" if critical_discrepancies else "moderate"
        
        # Generate specific adjustments for each discrepancy
        for discrepancy in critical_discrepancies + moderate_discrepancies:
            finding = discrepancy.get("finding", {})
            source_agent = finding.get("source_agent", "Unknown")
            
            adjustment = {
                "agent": source_agent,
                "finding_type": finding.get("type", "Unknown"),
                "category": finding.get("category", "Unknown"),
                "severity": discrepancy.get("severity", "moderate"),
                "current_assessment": finding.get("finding", ""),
                "external_consensus": discrepancy.get("external_consensus", ""),
                "recommended_action": discrepancy.get("recommendation", ""),
                "specific_changes": self._generate_specific_changes(discrepancy)
            }
            
            adjustment_plan["adjustments"].append(adjustment)
            
            # Track which agents need to rerun
            if source_agent not in adjustment_plan["agents_to_rerun"]:
                adjustment_plan["agents_to_rerun"].append(source_agent)
        
        # Generate summary message
        adjustment_plan["summary"] = self._generate_adjustment_summary(adjustment_plan)
        
        return adjustment_plan
    
    def _generate_specific_changes(self, discrepancy: Dict[str, Any]) -> List[str]:
        """Generate specific, actionable changes based on discrepancy."""
        changes = []
        
        finding = discrepancy.get("finding", {})
        category = finding.get("category", "")
        finding_type = finding.get("type", "")
        
        # Generate specific changes based on type
        if category == "financial" and finding_type == "revenue_growth":
            changes.append("Adjust revenue growth forecast to align with analyst consensus")
            changes.append("Update financial models with revised growth assumptions")
            changes.append("Recalculate valuation based on updated projections")
        
        elif category == "risk" and discrepancy.get("severity") == "critical":
            changes.append(f"Upgrade risk rating from '{finding.get('rating', 'unknown')}' to 'high'")
            changes.append("Add specific risk factors identified by external sources")
            changes.append("Update risk mitigation strategies")
        
        elif category == "operational":
            changes.append("Incorporate external supply chain risk factors")
            changes.append("Update operational risk assessment")
            changes.append("Add specific bottlenecks or constraints identified externally")
        
        elif category == "market":
            changes.append("Update competitive landscape analysis")
            changes.append("Revise market position assessment")
            changes.append("Incorporate latest competitor intelligence")
        
        # Add any missed information
        missed_info = discrepancy.get("missed_information", "")
        if missed_info and missed_info != "None" and len(missed_info) > 10:
            changes.append(f"Incorporate: {missed_info}")
        
        return changes if changes else ["Review and update assessment based on external consensus"]
    
    def _generate_adjustment_summary(self, adjustment_plan: Dict[str, Any]) -> str:
        """Generate human-readable summary of adjustment plan."""
        if not adjustment_plan["requires_reanalysis"]:
            return "No critical discrepancies found. Internal analysis aligns with external consensus."
        
        num_adjustments = len(adjustment_plan["adjustments"])
        num_agents = len(adjustment_plan["agents_to_rerun"])
        priority = adjustment_plan["priority"]
        
        summary = f"Found {num_adjustments} discrepancies requiring attention (Priority: {priority.upper()}). "
        summary += f"{num_agents} agent(s) should rerun analysis: {', '.join(adjustment_plan['agents_to_rerun'])}. "
        
        # Highlight most critical issues
        critical_issues = [a for a in adjustment_plan["adjustments"] if a["severity"] == "critical"]
        if critical_issues:
            summary += f"CRITICAL: {len(critical_issues)} major discrepancies that significantly impact valuation."
        
        return summary
    
    def _calculate_confidence_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence score based on validation results.
        
        Score ranges from 0.0 (no confidence) to 1.0 (full confidence)
        """
        if not validation_results:
            return 0.5  # Neutral when no validation performed
        
        total_score = 0.0
        total_weight = 0.0
        
        for result in validation_results:
            # Weight by priority
            finding = result.get("finding", {})
            priority = finding.get("validation_priority", "medium")
            weight = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5}.get(priority, 1.0)
            
            # Score by status
            status = result.get("status", "no_external_data")
            alignment_score = result.get("alignment_score", 0.5)
            
            if status == "validated":
                score = 1.0
            elif status == "partial_discrepancy":
                score = alignment_score
            elif status == "critical_discrepancy":
                score = 0.0
            else:
                score = 0.5
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _generate_recommendations(self, validation_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        confidence_score = validation_data["confidence_score"]
        adjustment_plan = validation_data["adjustment_plan"]
        critical_count = len(validation_data["critical_discrepancies"])
        moderate_count = len(validation_data["moderate_discrepancies"])
        
        # Overall assessment recommendation
        if confidence_score >= 0.85:
            recommendations.append(
                "HIGH CONFIDENCE: Internal analysis strongly aligns with external market consensus. " +
                "Proceed with draft valuation range."
            )
        elif confidence_score >= 0.70:
            recommendations.append(
                "MODERATE CONFIDENCE: Internal analysis generally aligns with market but has some discrepancies. " +
                "Review moderate discrepancies before finalizing."
            )
        elif confidence_score >= 0.50:
            recommendations.append(
                "LOW CONFIDENCE: Significant discrepancies found between internal and external analysis. " +
                "Reanalysis required before proceeding."
            )
        else:
            recommendations.append(
                "VERY LOW CONFIDENCE: Major conflicts with market consensus. " +
                "Comprehensive reanalysis and potential strategy revision required."
            )
        
        # Critical discrepancy recommendations
        if critical_count > 0:
            recommendations.append(
                f"CRITICAL: {critical_count} major discrepancies require immediate attention. " +
                "These significantly impact valuation and deal viability."
            )
            for discrepancy in validation_data["critical_discrepancies"]:
                finding = discrepancy.get("finding", {})
                recommendations.append(
                    f"  - {finding.get('category', 'Unknown').upper()}/{finding.get('type', 'Unknown')}: " +
                    f"{discrepancy.get('comparison_summary', 'Requires review')}"
                )
        
        # Moderate discrepancy recommendations
        if moderate_count > 0:
            recommendations.append(
                f"MODERATE: {moderate_count} notable discrepancies should be addressed. " +
                "These may affect valuation accuracy."
            )
        
        # Adjustment plan recommendations
        if adjustment_plan["requires_reanalysis"]:
            recommendations.append(
                f"REANALYSIS REQUIRED: {adjustment_plan['summary']}"
            )
            recommendations.append(
                "Execute adjustment plan to incorporate external consensus before finalizing report."
            )
        
        # Validation success recommendations
        validated_count = len(validation_data["validated_findings"])
        if validated_count > 0:
            recommendations.append(
                f"VALIDATED: {validated_count} findings successfully confirmed by external sources, " +
                "providing strong support for those assessments."
            )
        
        # Process improvement recommendations
        if critical_count > 2:
            recommendations.append(
                "PROCESS IMPROVEMENT: High number of critical discrepancies suggests internal analysis " +
                "may benefit from enhanced external data integration in initial stages."
            )
        
        return recommendations
    
    def _perform_sanity_checks(self, draft_report: Dict[str, Any], state: DiligenceState) -> List[Dict[str, Any]]:
        """
        Perform high-level sanity checks on internal analysis data.
        
        Args:
            draft_report: Compiled draft report from all agents
            state: Current diligence state
            
        Returns:
            List of sanity check results
        """
        sanity_checks = []
        
        # Sanity check 1: Valuation consistency
        financial = draft_report.get("financial_analysis", {})
        valuation_check = self._check_valuation_consistency(financial)
        sanity_checks.append(valuation_check)
        
        # Sanity check 2: EBITDA normalization consistency
        normalized_data = state.get("normalized_financials", {})
        ebitda_check = self._check_ebitda_consistency(financial, normalized_data)
        sanity_checks.append(ebitda_check)
        
        # Sanity check 3: Anomaly detection consistency
        anomaly_check = self._check_anomaly_consistency(state)
        sanity_checks.append(anomaly_check)
        
        # Sanity check 4: Agent count consistency
        agent_check = self._check_agent_count_consistency(state)
        sanity_checks.append(agent_check)
        
        # Sanity check 5: Data completeness
        completeness_check = self._check_data_completeness(draft_report)
        sanity_checks.append(completeness_check)
        
        # Sanity check 6: Risk assessment consistency
        risk_check = self._check_risk_consistency(draft_report)
        sanity_checks.append(risk_check)
        
        return sanity_checks
    
    def _check_valuation_consistency(self, financial: Dict[str, Any]) -> Dict[str, Any]:
        """Check for valuation consistency across different models"""
        valuation = financial.get("valuation", {})
        dcf_value = valuation.get("dcf_base_case", 0)
        fmp_dcf = financial.get("custom_dcf_levered", {}).get("dcf", 0)
        
        if dcf_value == 0:
            return {
                "check": "valuation_consistency",
                "status": "warning",
                "severity": "moderate",
                "message": "DCF valuation is zero or missing",
                "recommendation": "Review DCF model inputs and calculations"
            }
        
        if fmp_dcf > 0:
            variance = abs((dcf_value - fmp_dcf) / fmp_dcf)
            if variance > 0.5:  # 50% variance
                return {
                    "check": "valuation_consistency",
                    "status": "issue",
                    "severity": "critical",
                    "message": f"Large variance between internal DCF (${dcf_value:,.0f}) and FMP DCF (${fmp_dcf:,.0f})",
                    "recommendation": "Review DCF assumptions, especially WACC and growth rates"
                }
            else:
                return {
                    "check": "valuation_consistency",
                    "status": "pass",
                    "severity": "low",
                    "message": f"Good alignment between internal and FMP DCF (variance: {variance:.1%})",
                    "recommendation": "No action needed"
                }
        else:
            return {
                "check": "valuation_consistency",
                "status": "info",
                "severity": "low",
                "message": "FMP DCF not available for comparison",
                "recommendation": "Consider external validation if possible"
            }
    
    def _check_ebitda_consistency(self, financial: Dict[str, Any], normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check EBITDA normalization consistency"""
        raw_ebitda = financial.get("ebitda", 0)
        normalized_ebitda = normalized_data.get("adjusted_ebitda", 0)
        
        if normalized_data.get("adjustments"):
            adjustments = normalized_data["adjustments"]
            if raw_ebitda > 0 and normalized_ebitda > 0:
                ratio = normalized_ebitda / raw_ebitda
                if ratio > 2 or ratio < 0.5:  # More than 2x or less than 0.5x
                    return {
                        "check": "ebitda_consistency",
                        "status": "issue",
                        "severity": "critical",
                        "message": f"Large EBITDA adjustment: raw ${raw_ebitda:,.0f} vs normalized ${normalized_ebitda:,.0f}",
                        "recommendation": "Review normalization adjustments for R&D capitalization and other items"
                    }
                else:
                    return {
                        "check": "ebitda_consistency",
                        "status": "pass",
                        "severity": "low",
                        "message": f"Reasonable EBITDA normalization (ratio: {ratio:.2f})",
                        "recommendation": "No action needed"
                    }
            else:
                return {
                    "check": "ebitda_consistency",
                    "status": "warning",
                    "severity": "moderate",
                    "message": "EBITDA normalization data incomplete",
                    "recommendation": "Ensure normalization ledger is properly populated"
                }
        else:
            return {
                "check": "ebitda_consistency",
                "status": "info",
                "severity": "low",
                "message": "No EBITDA adjustments made",
                "recommendation": "Verify if adjustments are needed"
            }
    
    def _check_anomaly_consistency(self, state: DiligenceState) -> Dict[str, Any]:
        """Check anomaly detection consistency"""
        anomaly_results = state.get("anomaly_detection", {})
        financial_anomalies = state.get("financial_anomalies", [])
        
        if anomaly_results.get("anomalies_detected"):
            anomaly_count = len(anomaly_results["anomalies_detected"])
            if anomaly_count > 0:
                return {
                    "check": "anomaly_consistency",
                    "status": "issue",
                    "severity": "moderate",
                    "message": f"{anomaly_count} anomalies detected in financial data",
                    "recommendation": "Review anomaly log and address underlying issues"
                }
            else:
                return {
                    "check": "anomaly_consistency",
                    "status": "pass",
                    "severity": "low",
                    "message": "No anomalies detected",
                    "recommendation": "No action needed"
                }
        else:
            return {
                "check": "anomaly_consistency",
                "status": "warning",
                "severity": "moderate",
                "message": "Anomaly detection not performed",
                "recommendation": "Run anomaly detection on financial data"
            }
    
    def _check_agent_count_consistency(self, state: DiligenceState) -> Dict[str, Any]:
        """Check agent count consistency across reports"""
        agent_outputs = state.get("agent_outputs", [])
        completed_agents = [o for o in agent_outputs if o.get("status") == "completed"]
        
        # Check if all expected agents ran
        expected_agents = 13  # Based on user's feedback
        if len(completed_agents) < expected_agents:
            missing_agents = expected_agents - len(completed_agents)
            return {
                "check": "agent_count_consistency",
                "status": "warning",
                "severity": "moderate",
                "message": f"{missing_agents} agents did not complete ({len(completed_agents)}/{expected_agents})",
                "recommendation": "Ensure all agents run successfully"
            }
        else:
            return {
                "check": "agent_count_consistency",
                "status": "pass",
                "severity": "low",
                "message": f"All {len(completed_agents)} agents completed successfully",
                "recommendation": "No action needed"
            }
    
    def _check_data_completeness(self, draft_report: Dict[str, Any]) -> Dict[str, Any]:
        """Check data completeness across all sections"""
        completeness_score = 0
        max_score = 6
        missing_sections = []
        
        sections = ["financial_analysis", "legal_analysis", "market_analysis", "risk_analysis"]
        for section in sections:
            if draft_report.get(section):
                completeness_score += 1
            else:
                missing_sections.append(section)
        
        # Check for key financial metrics
        financial = draft_report.get("financial_analysis", {})
        if financial.get("ebitda") and financial.get("revenue"):
            completeness_score += 1
        else:
            missing_sections.append("key_financial_metrics")
        
        # Check for valuation
        if financial.get("valuation"):
            completeness_score += 1
        else:
            missing_sections.append("valuation")
        
        completeness_pct = (completeness_score / max_score) * 100
        
        if completeness_pct < 70:
            return {
                "check": "data_completeness",
                "status": "warning",
                "severity": "moderate",
                "message": f"Low data completeness ({completeness_pct:.0f}%): missing {', '.join(missing_sections)}",
                "recommendation": "Ensure all required data sections are populated"
            }
        else:
            return {
                "check": "data_completeness",
                "status": "pass",
                "severity": "low",
                "message": f"Good data completeness ({completeness_pct:.0f}%)",
                "recommendation": "No action needed"
            }
    
    def _check_risk_consistency(self, draft_report: Dict[str, Any]) -> Dict[str, Any]:
        """Check risk assessment consistency"""
        risk_analysis = draft_report.get("risk_analysis", {})
        financial_risks = risk_analysis.get("financial", [])
        legal_risks = risk_analysis.get("legal", [])
        
        total_risks = len(financial_risks) + len(legal_risks)
        
        if total_risks == 0:
            return {
                "check": "risk_consistency",
                "status": "warning",
                "severity": "moderate",
                "message": "No risks identified across all analyses",
                "recommendation": "Review if risk assessment is comprehensive"
            }
        elif total_risks > 10:
            return {
                "check": "risk_consistency",
                "status": "info",
                "severity": "low",
                "message": f"High number of risks identified ({total_risks})",
                "recommendation": "Prioritize and mitigate top risks"
            }
        else:
            return {
                "check": "risk_consistency",
                "status": "pass",
                "severity": "low",
                "message": f"Reasonable risk count ({total_risks})",
                "recommendation": "No action needed"
            }
    
    def _calculate_sanity_confidence(self, sanity_checks: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on sanity checks"""
        if not sanity_checks:
            return 0.5
        
        total_score = 0.0
        total_weight = 0.0
        
        severity_weights = {"critical": 3.0, "moderate": 2.0, "low": 1.0}
        
        for check in sanity_checks:
            severity = check.get("severity", "low")
            weight = severity_weights.get(severity, 1.0)
            
            if check.get("status") == "pass":
                score = 1.0
            elif check.get("status") == "warning":
                score = 0.5
            elif check.get("status") == "issue":
                score = 0.0
            else:
                score = 0.5
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _generate_sanity_recommendations(self, sanity_checks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on sanity checks"""
        recommendations = []
        
        critical_issues = [c for c in sanity_checks if c.get("severity") == "critical"]
        moderate_issues = [c for c in sanity_checks if c.get("severity") == "moderate"]
        
        if critical_issues:
            recommendations.append(f"CRITICAL: {len(critical_issues)} critical issues require immediate attention:")
            for issue in critical_issues:
                recommendations.append(f"  - {issue['check']}: {issue['recommendation']}")
        
        if moderate_issues:
            recommendations.append(f"MODERATE: {len(moderate_issues)} moderate issues should be addressed:")
            for issue in moderate_issues:
                recommendations.append(f"  - {issue['check']}: {issue['recommendation']}")
        
        if not critical_issues and not moderate_issues:
            recommendations.append("All sanity checks passed. Internal analysis appears consistent.")
        
        return recommendations
    
    def _validate_with_fmp_data(self, state: DiligenceState) -> Dict[str, Any]:
        """
        NEW: Use FMP endpoints for direct validation of key metrics.
        
        This provides immediate external validation without web search:
        - FMP DCF vs our DCF
        - Institutional ownership confidence
        - Earnings surprise consistency
        """
        financial_data = state.get('financial_data', {})
        
        validation = {
            'dcf_validation': self._validate_dcf_with_fmp(financial_data),
            'institutional_validation': self._validate_institutional_confidence(financial_data),
            'earnings_validation': self._validate_earnings_quality(financial_data)
        }
        
        return validation
    
    def _validate_dcf_with_fmp(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate our DCF against FMP's DCF calculation"""
        fmp_dcf = financial_data.get('custom_dcf_levered', {})
        
        if not fmp_dcf or not fmp_dcf.get('dcf'):
            return {'status': 'no_data', 'note': 'FMP DCF data not available'}
        
        fmp_value = fmp_dcf.get('dcf', 0)
        fmp_stock_price = fmp_dcf.get('Stock Price', 0)
        
        # Get our valuation from advanced valuation results
        our_dcf = financial_data.get('valuation', {}).get('dcf_base_case', 0)
        
        if our_dcf == 0:
            return {'status': 'incomplete', 'note': 'Our DCF not yet calculated'}
        
        variance = abs((our_dcf - fmp_value) / fmp_value * 100) if fmp_value > 0 else 0
        
        return {
            'status': 'validated' if variance < 15 else 'discrepancy',
            'fmp_dcf': fmp_value,
            'our_dcf': our_dcf,
            'variance_percent': round(variance, 2),
            'severity': 'low' if variance < 15 else 'moderate' if variance < 25 else 'high',
            'interpretation': f"{'Good alignment' if variance < 15 else 'Notable variance'} between our DCF and FMP's external benchmark"
        }
    
    def _validate_institutional_confidence(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate institutional ownership confidence"""
        institutional = financial_data.get('institutional_ownership', [])
        
        if not institutional:
            return {'status': 'no_data', 'note': 'Institutional ownership data not available'}
        
        holder_count = len(institutional)
        total_value = sum(h.get('value', 0) for h in institutional)
        
        # Calculate concentration
        top_5_value = sum(h.get('value', 0) for h in institutional[:5])
        concentration = (top_5_value / total_value * 100) if total_value > 0 else 0
        
        confidence_level = 'high' if holder_count > 500 else 'moderate' if holder_count > 200 else 'low'
        
        return {
            'status': 'validated',
            'holder_count': holder_count,
            'total_value_usd': total_value,
            'concentration_top_5': round(concentration, 2),
            'confidence_level': confidence_level,
            'interpretation': f"{confidence_level.title()} institutional confidence with {holder_count} holders"
        }
    
    def _validate_earnings_quality(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate earnings quality from surprise history"""
        earnings_surprises = financial_data.get('earnings_surprises', [])
        
        if not earnings_surprises:
            return {'status': 'no_data', 'note': 'Earnings surprise data not available'}
        
        beats = sum(1 for s in earnings_surprises if s.get('actualEarningResult', 0) > s.get('estimatedEarning', 0))
        total = len(earnings_surprises)
        beat_rate = (beats / total * 100) if total > 0 else 0
        
        quality = 'high' if beat_rate >= 75 else 'moderate' if beat_rate >= 50 else 'low'
        
        return {
            'status': 'validated',
            'beat_rate': round(beat_rate, 1),
            'beats': beats,
            'total_reports': total,
            'quality_level': quality,
            'interpretation': f"{quality.title()} earnings quality with {beat_rate:.1f}% beat rate"
        }
    
    async def _detect_validation_anomalies(
        self,
        validation_data: Dict[str, Any],
        sanity_checks: List[Dict[str, Any]],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Detect validation and data consistency anomalies
        
        Returns:
            Anomaly detection results for validation domain
        """
        anomalies = []
        
        # Check for low confidence score
        confidence = validation_data.get('confidence_score', 1.0)
        if confidence < 0.5:
            anomalies.append({
                'type': 'low_validation_confidence',
                'severity': 'high',
                'description': f'Low validation confidence: {confidence:.1%}',
                'impact': 'Internal analysis may not align with market reality',
                'recommendation': 'Review critical issues and consider reanalysis'
            })
        
        # Check for critical sanity check failures
        critical_issues = [c for c in sanity_checks if c.get('severity') == 'critical']
        if len(critical_issues) > 0:
            anomalies.append({
                'type': 'critical_sanity_failures',
                'severity': 'critical',
                'description': f'{len(critical_issues)} critical sanity check failures detected',
                'impact': 'Major data consistency or methodology issues',
                'recommendation': 'Address all critical issues before proceeding with analysis'
            })
        
        # Check for data completeness issues
        completeness_check = next((c for c in sanity_checks if c.get('check') == 'data_completeness'), None)
        if completeness_check and completeness_check.get('status') == 'warning':
            anomalies.append({
                'type': 'incomplete_data',
                'severity': 'medium',
                'description': 'Data completeness below threshold',
                'impact': 'Analysis may be missing key information',
                'recommendation': 'Ensure all required data sections are populated'
            })
        
        # Check for valuation discrepancies
        valuation_check = next((c for c in sanity_checks if c.get('check') == 'valuation_consistency'), None)
        if valuation_check and valuation_check.get('severity') == 'critical':
            anomalies.append({
                'type': 'valuation_discrepancy',
                'severity': 'high',
                'description': 'Large variance in valuation calculations',
                'impact': 'Valuation accuracy concerns',
                'recommendation': 'Reconcile valuation methodologies and assumptions'
            })
        
        return {
            'anomalies_detected': anomalies,
            'risk_level': 'Critical' if len([a for a in anomalies if a['severity'] == 'critical']) > 0 else 'High' if len([a for a in anomalies if a['severity'] == 'high']) > 0 else 'Medium' if anomalies else 'Low',
            'total_anomalies': len(anomalies)
        }
    
    async def _perform_research(
        self,
        search_query: str,
        finding: Dict[str, Any],
        target_company: str
    ) -> Dict[str, Any]:
        """
        Perform real web research using Tavily + LLM analysis
        
        CORRECT APPROACH (Tavily → LLM):
        1. Use Tavily to get REAL web search results
        2. Use LLM to ANALYZE those real results
        """
        
        # METHOD 1: Try Tavily for real web search (BEST)
        if self.tavily:
            try:
                self.log_action(f"🌐 Tavily web search: '{search_query}'")
                
                # Use Tavily to get REAL search results
                search_results = await self.tavily.search_financial_data(
                    company=target_company,
                    topic=f"{finding['type']} {finding['category']}",
                    max_results=10
                )
                
                if search_results['success'] and search_results['result_count'] > 0:
                    # Tavily succeeded - now use LLM to ANALYZE the real data
                    self.log_action(f"✓ Tavily found {search_results['result_count']} sources")
                    
                    # Format search results for LLM analysis
                    search_context = self._format_tavily_results(search_results)
                    
                    # Use LLM to ANALYZE real search results (not hallucinate them)
                    analysis_prompt = f"""Analyze these REAL web search results about {target_company}.

Finding Category: {finding['category']}
Finding Type: {finding['type']}
Internal Assessment: {finding.get('finding', 'Not specified')}

REAL SEARCH RESULTS FROM TAVILY:

TAVILY AI SUMMARY:
{search_results.get('answer', 'Not available')}

SOURCES:
{search_context}

Your task:
1. Extract key information from these REAL sources
2. Identify consensus views vs outliers
3. Note specific data points (numbers, dates, analyst names)
4. Assess data quality and freshness
5. Compare with internal assessment

Respond with structured analysis focusing on FACTS from the sources above."""

                    response = await self.llm.ainvoke(analysis_prompt)
                    analysis_text = response.content
                    
                    # Parse both Tavily and LLM results
                    parsed_results = self.tavily.parse_search_results(search_results)
                    
                    return {
                        "summary": analysis_text,
                        "structured_data": {
                            "confidence_level": parsed_results['confidence'],
                            "sources": parsed_results['sources'],
                            "source_count": parsed_results['total_sources'],
                            "financial_sources": parsed_results['financial_source_count'],
                            "tavily_answer": search_results.get('answer', ''),
                            "search_method": "tavily_web_search"
                        },
                        "confidence": parsed_results['confidence'],
                        "source_types": ["tavily_web_search"],
                        "research_date": datetime.now().isoformat(),
                        "data_freshness": "recent"
                    }
                    
            except Exception as e:
                self.log_action(f"⚠️ Tavily error: {e}, using LLM fallback")
        
        # METHOD 2: Fallback to LLM-only if Tavily unavailable
        return await self._llm_only_research(search_query, finding, target_company)
    
    def _format_tavily_results(self, search_results: Dict[str, Any]) -> str:
        """Format Tavily search results for LLM analysis"""
        results_text = []
        
        for i, result in enumerate(search_results.get('results', []), 1):
            title = result.get('title', 'No title')
            url = result.get('url', '')
            content = result.get('content', 'No content')
            
            results_text.append(f"{i}. {title}")
            results_text.append(f"   URL: {url}")
            results_text.append(f"   Content: {content[:300]}...")
            results_text.append("")
        
        return "\n".join(results_text)
    
    async def _llm_only_research(
        self,
        search_query: str,
        finding: Dict[str, Any],
        target_company: str
    ) -> Dict[str, Any]:
        """
        Fallback: LLM-only research when Tavily is unavailable
        
        NOTE: This is less reliable as LLM uses training data, not live web search
        """
        self.log_action(f"📝 LLM-only research (no live web search): '{search_query}'")
        
        research_prompt = f"""Based on your training data, provide analysis for: {search_query}

Target Company: {target_company}
Finding Category: {finding['category']}
Finding Type: {finding['type']}

NOTE: You're working from training data only (not live web search).
Provide what information you have, but clearly indicate limitations."""

        try:
            response = await self.llm.ainvoke(research_prompt)
            research_text = response.content
            
            # Use existing parser for LLM responses
            structured_research = self._parse_research_response(research_text, target_company)
            
            return {
                "summary": research_text,
                "structured_data": structured_research,
                "confidence": "low",
                "source_types": ["llm_training_data"],
                "research_date": datetime.now().isoformat(),
                "data_freshness": structured_research.get("data_freshness", "stale"),
                "warning": "No live web search available - using LLM training data only"
            }
        except Exception as e:
            self.log_action(f"LLM research error: {e}", "warning")
            return {
                "summary": f"Research unavailable: {str(e)}",
                "confidence": "none",
                "error": str(e)
            }
