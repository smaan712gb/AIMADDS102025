"""
Project Manager Agent - Orchestrates the entire M&A analysis workflow
"""
from typing import Dict, List, Any
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from .base_agent import BaseAgent
from ..core.state import DiligenceState
from ..core.llm_factory import get_llm


class ProjectManagerAgent(BaseAgent):
    """
    Project Manager Agent - The Orchestrator
    
    Responsibilities:
    - Create comprehensive task plans
    - Coordinate agent activities
    - Track progress and status
    - Handle errors and retries
    - Ensure all analyses are complete
    """
    
    def __init__(self):
        """Initialize Project Manager Agent"""
        super().__init__("project_manager")
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Run method - create project plan and return structured output

        Args:
            state: Current workflow state

        Returns:
            Dict with data, errors, warnings
        """
        try:
            # Ensure deal_id exists
            if 'deal_id' not in state:
                state['deal_id'] = f"DEAL_{state.get('target_ticker', 'UNK')}_{int(state.get('deal_value', 0) // 1000000000)}B"

            # Ensure errors list exists
            state.setdefault('errors', [])

            # Ensure metadata exists
            state.setdefault('metadata', {})

            logger.info(f"🎯 Project Manager: Starting orchestration for deal {state['deal_id']}")

            # Step 1: Create comprehensive project plan
            plan = await self._create_project_plan(state)
            state['metadata']["project_plan"] = plan

            # Step 2: Identify required analyses
            required_analyses = self._identify_required_analyses(state)
            state['metadata']["required_analyses"] = required_analyses

            # Step 3: Determine agent workflow
            workflow = self._determine_workflow(state, required_analyses)
            state['metadata']["agent_workflow"] = workflow

            # Step 4: Set priorities and timelines
            priorities = self._set_priorities(state)
            state['metadata']["priorities"] = priorities

            # Step 5: Create status tracking
            status = {
                "project_status": "in_progress",
                "completed_agents": [],
                "pending_agents": workflow,
                "current_phase": "planning",
                "overall_progress": 0
            }
            state['metadata']["project_status"] = status

            logger.info("✅ Project plan created successfully")
            logger.info(f"📋 Workflow: {' → '.join(workflow)}")

            # Return structured output with plan
            return {
                'data': {
                    'deal_id': state['deal_id'],
                    'plan': plan,
                    'required_analyses': required_analyses,
                    'workflow': workflow,
                    'priorities': priorities,
                    'status': status
                },
                'errors': [],
                'warnings': []
            }

        except Exception as e:
            logger.error(f"❌ Project Manager failed: {e}")
            return {
                'errors': [str(e)],
                'data': {},
                'warnings': []
            }
    
    async def _create_project_plan(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Create comprehensive project plan using Claude
        
        Args:
            state: Current state
        
        Returns:
            Project plan dictionary
        """
        logger.info("Creating project plan...")
        
        deal_value_str = f"${state['deal_value']:,.0f}" if state.get('deal_value') else "TBD"

        investment_thesis = state.get('investment_thesis', 'TBD - Further investment rationale to be determined')

        prompt = f"""You are a Project Manager for an M&A due diligence project.

Deal Information:
- Deal ID: {state['deal_id']}
- Target Company: {state['target_company']}
- Deal Type: {state['deal_type']}
- Deal Value: {deal_value_str}
- Investment Thesis: {investment_thesis}

Create a comprehensive project plan that includes:
1. Key objectives and success criteria
2. Critical milestones and timeline
3. Risk factors to monitor
4. Resource requirements
5. Deliverables checklist

Provide a structured plan in a clear format."""

        messages = [
            SystemMessage(content="You are an expert M&A Project Manager with 20 years of experience."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        plan = {
            "description": response.content,
            "created_at": state['metadata'].get("timestamp"),
            "objectives": [
                "Complete advanced financial analysis (Phase 2: normalization, anomaly detection, Monte Carlo valuation)",
                "Assess risks and opportunities with AI-powered insights",
                "Provide multi-scenario DCF valuation with sensitivity analysis",
                "Generate comprehensive report with executive summaries"
            ],
            "timeline": {
                "advanced_financial_analysis": "Day 1-2",
                "valuation_modeling": "Day 2",
                "legal_review": "Day 2-3",
                "market_analysis": "Day 3-4",
                "integration_planning": "Day 4-5",
                "final_report": "Day 5"
            }
        }
        
        return plan
    
    def _identify_required_analyses(self, state: DiligenceState) -> List[str]:
        """
        Identify which analyses are required based on deal type
        
        Args:
            state: Current state
        
        Returns:
            List of required analysis types
        """
        # Core analyses required for ALL M&A deals (matches orchestrator execution)
        required = [
            "financial_analysis",
            "financial_deep_dive",
            "legal_review",  # Always include legal review for M&A
            "market_analysis",  # Always analyze market position
            "competitive_benchmarking",
            "macroeconomic_analysis",
            "risk_assessment",  # Always assess risks
            "tax_structuring",  # Always analyze tax implications for M&A
            "integration_planning",  # Always plan integration for M&A
            "external_validation",
            "synthesis_reporting"
        ]
        
        # Add M&A-specific analyses (always required for M&A deals)
        required.extend([
            "deal_structuring",  # Structure the deal
            "sources_uses",  # Capital allocation analysis
            "accretion_dilution",  # EPS impact analysis
            "contribution_analysis",  # Value contribution analysis
            "exchange_ratio_analysis"  # For stock deals
        ])
        
        # Add if documents are provided
        if state['documents']:
            required.append("document_processing")
        
        # Always include conversational synthesis
        required.append("conversational_synthesis")
        
        logger.info(f"Required analyses: {required}")
        return required
    
    def _determine_workflow(
        self,
        state: DiligenceState,
        required_analyses: List[str]
    ) -> List[str]:
        """
        Determine the optimal agent workflow
        
        Args:
            state: Current state
            required_analyses: List of required analyses
        
        Returns:
            Ordered list of agent names
        """
        workflow = []
        
        # Phase 1: Data Ingestion (if documents exist)
        if "document_processing" in required_analyses:
            workflow.append("data_ingestion")
        
        # Phase 2: Core Financial Analysis
        if "financial_analysis" in required_analyses:
            workflow.append("financial_analyst")
            # Add deep dive analysis after financial analyst
            workflow.append("financial_deep_dive")
        
        # Phase 3: Deal Structuring (after financial analysis)
        if "deal_structuring" in required_analyses:
            workflow.append("deal_structuring")
        
        # Phase 4: Sources & Uses (after deal structuring)
        if "sources_uses" in required_analyses:
            workflow.append("sources_uses")
        
        # Phase 5: Legal Review (early to identify deal-breakers)
        if "legal_review" in required_analyses:
            workflow.append("legal_counsel")
        
        # Phase 6: Market Analysis
        if "market_analysis" in required_analyses:
            workflow.append("market_strategist")
        
        # Phase 7: Competitive Benchmarking
        if "competitive_benchmarking" in required_analyses:
            workflow.append("competitive_benchmarking")
        
        # Phase 8: Macroeconomic Analysis
        if "macroeconomic_analysis" in required_analyses:
            workflow.append("macroeconomic_analyst")
        
        # Phase 9: Risk Assessment (aggregates all risks from prior agents)
        if "risk_assessment" in required_analyses:
            workflow.append("risk_assessment")
        
        # Phase 10: Tax Structuring (always include for M&A)
        workflow.append("tax_structuring")
        
        # Phase 11: Accretion/Dilution Analysis (after tax structuring)
        if "accretion_dilution" in required_analyses:
            workflow.append("accretion_dilution")
        
        # Phase 12: Contribution Analysis
        if "contribution_analysis" in required_analyses:
            workflow.append("contribution_analysis")
        
        # Phase 13: Exchange Ratio Analysis (for stock deals)
        if "exchange_ratio_analysis" in required_analyses:
            workflow.append("exchange_ratio_analysis")
        
        # Phase 14: Integration Planning
        if "integration_planning" in required_analyses:
            workflow.append("integration_planner")
        
        # Phase 15: External Validation
        if "external_validation" in required_analyses:
            workflow.append("external_validator")
        
        # Phase 16: Synthesis & Reporting
        workflow.append("synthesis_reporting")
        
        # Phase 17: Conversational Synthesis (Final)
        if "conversational_synthesis" in required_analyses:
            workflow.append("conversational_synthesis")
        
        return workflow
    
    def _set_priorities(self, state: DiligenceState) -> Dict[str, str]:
        """
        Set priorities for different aspects
        
        Args:
            state: Current state
        
        Returns:
            Priority mapping
        """
        # Handle None deal_value
        deal_value = state.get('deal_value') or 0
        
        priorities = {
            "financial_health": "HIGH",
            "valuation": "HIGH",
            "risk_assessment": "HIGH",
            "legal_compliance": "MEDIUM",
            "market_position": "MEDIUM",
            "integration_complexity": "LOW" if deal_value < 500_000_000 else "MEDIUM"
        }
        
        # Adjust based on deal type
        if state['deal_type'] == "acquisition":
            priorities["integration_complexity"] = "HIGH"
        
        return priorities
    
    def get_progress_summary(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Get current project progress summary
        
        Args:
            state: Current state
        
        Returns:
            Progress summary
        """
        status = state['metadata'].get("project_status", {})
        workflow = state['metadata'].get("agent_workflow", [])
        
        # Get progress from status directly (it's calculated in mark_agent_complete)
        progress_pct = status.get("overall_progress", 0)
        
        return {
            "overall_progress": f"{progress_pct:.1f}%",
            "completed_agents": status.get("completed_agents", []),
            "pending_agents": status.get("pending_agents", []),
            "current_phase": status.get("current_phase", "unknown"),
            "status": status.get("project_status", "unknown")
        }
    
    def mark_agent_complete(
        self,
        state: DiligenceState,
        agent_name: str
    ) -> DiligenceState:
        """
        Mark an agent as completed
        
        Args:
            state: Current state
            agent_name: Name of completed agent
        
        Returns:
            Updated state
        """
        # Initialize status if needed
        if 'project_status' not in state['metadata']:
            state['metadata']['project_status'] = {
                "project_status": "in_progress",
                "completed_agents": [],
                "pending_agents": [],
                "current_phase": "execution",
                "overall_progress": 0
            }
        
        status = state['metadata']['project_status']
        
        # Add to completed if not already there
        if agent_name not in status.get("completed_agents", []):
            status.setdefault("completed_agents", []).append(agent_name)
        
        # Remove from pending
        if agent_name in status.get("pending_agents", []):
            status["pending_agents"].remove(agent_name)
        
        # Update progress based on workflow
        workflow = state['metadata'].get("agent_workflow", [])
        if workflow:
            completed = len(status["completed_agents"])
            total = len(workflow)
            status["overall_progress"] = (completed / total * 100) if total > 0 else 0
        else:
            # Fallback if no workflow defined
            status["overall_progress"] = 100.0 if len(status.get("completed_agents", [])) > 0 else 0
        
        # Update phase
        if workflow and len(status["completed_agents"]) >= len(workflow):
            status["project_status"] = "completed"
            status["current_phase"] = "final_review"
        
        state['metadata']["project_status"] = status
        
        logger.info(f"✅ Agent completed: {agent_name} ({status['overall_progress']:.1f}%)")
        
        return state
