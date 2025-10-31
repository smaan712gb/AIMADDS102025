"""
M&A Copilot Service - Conversational AI for Due Diligence Analysis

This service provides the backend for the conversational M&A Copilot, enabling
users to ask questions about their analysis results and get intelligent,
context-aware responses powered by Gemini 2.5 Pro.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

from src.agents.conversational_synthesis import ConversationalSynthesisAgent
from src.agents.external_validator import ExternalValidatorAgent
from src.core.llm_factory import get_llm
from src.api.job_manager import get_job_manager


class CopilotService:
    """
    Service for handling conversational interactions with analysis results.
    
    Provides context-aware responses by loading complete analysis state
    and leveraging Gemini 2.5 Pro's capabilities including live search.
    """
    
    def __init__(self):
        self.job_manager = get_job_manager()
        self.llm = get_llm(model_name="gemini-2.0-flash-exp", temperature=0.3)
        
    async def initialize_chat(self, job_id: str) -> Dict[str, Any]:
        """
        Initialize a new chat session for a given analysis.
        
        Args:
            job_id: The analysis job ID
            
        Returns:
            Initial chat context with welcome message and suggestions
        """
        try:
            # Load analysis results
            result = self.job_manager.get_job_result(job_id)
            if not result:
                return {
                    "error": "Analysis not found",
                    "welcome_message": None,
                    "suggestions": []
                }
            
            # Load complete state from JSON file
            state = await self._load_analysis_state(job_id, result)
            
            # Generate welcome message and suggestions
            welcome_message = self._generate_welcome_message(result, state)
            suggestions = self._generate_suggestion_chips(result, state)
            
            return {
                "job_id": job_id,
                "project_name": result.get("project_name"),
                "welcome_message": welcome_message,
                "suggestions": suggestions,
                "context_loaded": True
            }
            
        except Exception as e:
            logger.error(f"Error initializing chat for job {job_id}: {e}")
            return {
                "error": str(e),
                "welcome_message": "I'm ready to answer questions about your analysis.",
                "suggestions": []
            }
    
    async def process_message(
        self,
        job_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message and stream the response.
        
        Args:
            job_id: The analysis job ID
            message: User's message
            conversation_history: Previous conversation messages
            
        Yields:
            Response chunks for streaming
        """
        try:
            # Load analysis context
            result = self.job_manager.get_job_result(job_id)
            if not result:
                yield {
                    "type": "error",
                    "content": "Analysis not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            state = await self._load_analysis_state(job_id, result)
            
            # Determine if we need live search
            needs_live_search = self._check_if_needs_live_search(message)
            
            # Build context and generate response
            if needs_live_search:
                # Use external validator for live search capabilities
                async for chunk in self._generate_live_search_response(
                    message, state, result, conversation_history
                ):
                    yield chunk
            else:
                # Use conversational synthesis agent for context-based response
                async for chunk in self._generate_context_response(
                    message, state, result, conversation_history
                ):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error processing message for job {job_id}: {e}")
            yield {
                "type": "error",
                "content": f"Error processing your question: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _load_analysis_state(self, job_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Load complete analysis state with ALL data sources.
        
        Enhanced to provide comprehensive access to:
        - Complete job state with agent_outputs array
        - Individual agent results
        - Report file paths
        - Raw financial data
        """
        try:
            # PRIMARY: Load complete state directly from job manager
            # This gives us access to the new agent_outputs array and ALL state keys
            state = self.job_manager.get_job(job_id)
            
            if state:
                logger.info(f"Loaded complete job state for {job_id}")
                logger.info(f"State contains {len(state.get('agent_outputs', []))} agent outputs")
                logger.info(f"State keys: {list(state.keys())[:20]}")  # Log first 20 keys
                
                # Enhance state with report file access
                if 'output_files' in state:
                    state['_report_files_available'] = True
                    state['_report_paths'] = state['output_files']
                
                return state
            
            # FALLBACK: Try to load from saved JSON files
            logger.warning(f"Job {job_id} not in active jobs, attempting file load")
            
            job_file = Path("data/jobs") / f"{job_id}.json"
            if job_file.exists():
                with open(job_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state from job file: {job_file}")
                    return state
            
            logger.warning(f"No state found for job {job_id}")
            return {}
            
        except Exception as e:
            logger.error(f"Error loading analysis state: {e}")
            return {}
    
    def _generate_welcome_message(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Generate personalized welcome message."""
        project_name = result.get("project_name", "this analysis")
        
        # Extract key insights
        valuation = result.get("valuation_range", {})
        mid_val = valuation.get("mid", 0)
        
        message_parts = [
            f"# 💬 M&A Copilot - {project_name}\n",
            f"\nI'm your AI analyst with complete access to the comprehensive due diligence analysis. ",
            f"I can answer questions about:\n\n",
            f"- **Financial Analysis** - Valuation, ratios, trends\n",
            f"- **Competitive Position** - Market dynamics, peer benchmarking\n",
            f"- **Risk Assessment** - Identified risks and mitigation strategies\n",
            f"- **Integration Planning** - Synergies, timelines, challenges\n",
            f"- **Live Market Data** - Current stock prices, recent news\n\n"
        ]
        
        if mid_val > 0:
            message_parts.append(
                f"**Key Finding:** Mid-point valuation is ${mid_val/1e9:.2f}B\n\n"
            )
        
        message_parts.append(
            "Ask me anything about the analysis, request scenario modeling, "
            "or have me search for the latest market information."
        )
        
        return "".join(message_parts)
    
    def _generate_suggestion_chips(
        self,
        result: Dict[str, Any],
        state: Dict[str, Any]
    ) -> List[str]:
        """Generate contextual suggestion chips based on analysis content."""
        suggestions = [
            "What are the top 3 risks in this deal?",
            "How does the valuation compare to peers?",
            "Explain the key assumptions in the DCF model",
        ]
        
        # Add context-specific suggestions
        if result.get("top_risks"):
            suggestions.append("Why is the valuation justified given these risks?")
        
        if state.get("competitive_analysis"):
            suggestions.append("How does this company rank against competitors?")
        
        suggestions.extend([
            "What's the current stock price?",
            "Show me the latest news about this company",
            "What are the integration challenges?"
        ])
        
        return suggestions[:6]  # Limit to 6 suggestions
    
    def _check_if_needs_live_search(self, message: str) -> bool:
        """Determine if message requires live web search."""
        search_keywords = [
            "current", "latest", "recent", "today", "now",
            "stock price", "news", "announcement", "quarter",
            "earnings", "market", "update"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in search_keywords)
    
    async def _generate_context_response(
        self,
        message: str,
        state: Dict[str, Any],
        result: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate response using analysis context."""
        
        # Build comprehensive context
        context = self._build_context_for_llm(state, result, conversation_history)
        
        # Create prompt
        prompt = f"""You are an expert M&A analyst assistant helping a user understand their due diligence analysis.

ANALYSIS CONTEXT:
{json.dumps(context, indent=2, default=str)}

CONVERSATION HISTORY:
{json.dumps(conversation_history or [], indent=2, default=str)}

USER QUESTION: {message}

Provide a clear, detailed response based on the analysis data. When referencing specific data:
- Cite the source (e.g., "According to the Financial Analysis report...")
- Include specific numbers and metrics where relevant
- Explain the implications of the data
- Use markdown formatting for clarity

If the question requires information not in the analysis, acknowledge that and suggest what additional data would be helpful.

RESPONSE:"""

        # Stream response from LLM
        yield {
            "type": "start",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Stream in chunks
            chunk_size = 50
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield {
                    "type": "content",
                    "content": chunk + " ",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            yield {
                "type": "end",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating context response: {e}")
            yield {
                "type": "error",
                "content": f"Error generating response: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _generate_live_search_response(
        self,
        message: str,
        state: Dict[str, Any],
        result: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate response with live web search using Gemini 2.5 Pro."""
        
        # Build context
        context = self._build_context_for_llm(state, result, conversation_history)
        target_company = result.get("project_name", "the target company")
        
        # Create prompt with search directive
        prompt = f"""You are an expert M&A analyst with access to real-time web search capabilities.

TARGET COMPANY: {target_company}

INTERNAL ANALYSIS CONTEXT:
{json.dumps(context, indent=2, default=str)[:3000]}

USER QUESTION: {message}

Instructions:
1. Use web search to find the latest, real-time information requested
2. Compare any live data with the internal analysis if relevant
3. Cite all external sources with dates and URLs when possible
4. Provide actionable insights based on the new information

Format your response in markdown with clear sections and bullet points.

RESPONSE:"""

        yield {
            "type": "start",
            "searching": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Use Gemini 2.5 Pro with search capabilities
            search_llm = get_llm(model_name="gemini-2.0-flash-exp", temperature=0.3)
            response = await search_llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Stream the response
            chunk_size = 50
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield {
                    "type": "content",
                    "content": chunk + " ",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            yield {
                "type": "end",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating live search response: {e}")
            yield {
                "type": "error",
                "content": f"Error performing search: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _build_context_for_llm(
        self,
        state: Dict[str, Any],
        result: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Build comprehensive context for LLM from ALL analysis data sources.
        
        Enhanced to include:
        - agent_outputs array (structured collection of all 12 agent results)
        - Individual agent state keys (detailed analysis data)
        - Report file information
        - Raw financial data
        """
        context = {
            "project_name": result.get("project_name"),
            "target_ticker": state.get("target_ticker"),
            "valuation": result.get("valuation_range"),
            "key_metrics": result.get("key_metrics"),
            "top_risks": result.get("top_risks"),
            "top_opportunities": result.get("top_opportunities")
        }
        
        # Add comprehensive state data if available
        if state:
            # NEW: Add agent outputs summary (shows which agents ran and have data)
            if "agent_outputs" in state:
                context["agent_execution_summary"] = {
                    "total_agents": len(state["agent_outputs"]),
                    "agents_with_data": [
                        {
                            "agent": output["agent_name"],
                            "has_data": output.get("has_data", False),
                            "output_keys": output.get("output_keys", [])
                        }
                        for output in state["agent_outputs"]
                        if output.get("status") == "completed"
                    ]
                }
            
            # Financial Analysis (detailed)
            if "financial_data" in state:
                context["financial_analysis"] = {
                    "valuation": state["financial_data"].get("valuation"),
                    "dcf_analysis": state["financial_data"].get("dcf_summary"),
                    "ratio_analysis": state["financial_data"].get("ratio_analysis"),
                    "revenue": state["financial_data"].get("revenue"),
                    "ebitda": state["financial_data"].get("ebitda"),
                    "margins": state["financial_data"].get("margins")
                }
            
            # Competitive Analysis
            if "competitive_analysis" in state:
                context["competitive_intelligence"] = {
                    "summary": state["competitive_analysis"].get("summary"),
                    "competitive_position": state["competitive_analysis"].get("competitive_position"),
                    "strategic_insights": state["competitive_analysis"].get("strategic_insights", [])[:5]
                }
            
            # Risk Assessment
            if "risk_assessment" in state:
                context["risk_analysis"] = {
                    "risk_summary": state["risk_assessment"].get("risk_summary"),
                    "risk_scores": state["risk_assessment"].get("risk_scores"),
                    "mitigation_strategies": state["risk_assessment"].get("mitigation_strategies", [])[:5]
                }
            
            # Legal Analysis
            if "legal_analysis" in state:
                context["legal_findings"] = {
                    "legal_risks": state["legal_analysis"].get("legal_risks", [])[:5],
                    "compliance_issues": state["legal_analysis"].get("compliance_issues"),
                    "governance_assessment": state["legal_analysis"].get("governance")
                }
            
            # Tax Structuring
            if "tax_analysis" in state:
                context["tax_considerations"] = {
                    "recommended_structure": state["tax_analysis"].get("recommended_structure"),
                    "tax_benefits": state["tax_analysis"].get("tax_benefits"),
                    "nol_analysis": state["tax_analysis"].get("nol_analysis")
                }
            
            # Integration Planning
            if "integration_plan" in state:
                context["integration_roadmap"] = {
                    "synergies": state["integration_plan"].get("synergies"),
                    "timeline": state["integration_plan"].get("timeline"),
                    "key_milestones": state["integration_plan"].get("milestones", [])[:5]
                }
            
            # Macroeconomic Analysis
            if "macroeconomic_analysis" in state:
                context["macro_environment"] = {
                    "economic_factors": state["macroeconomic_analysis"].get("economic_factors"),
                    "market_timing": state["macroeconomic_analysis"].get("market_timing"),
                    "insights": state["macroeconomic_analysis"].get("insights", [])[:5]
                }
            
            # Report files available
            if state.get("_report_files_available"):
                context["available_reports"] = list(state.get("_report_paths", {}).keys())
        
        logger.info(f"Built comprehensive context with {len(context)} top-level keys")
        
        return context


# Singleton instance
_copilot_service = None

def get_copilot_service() -> CopilotService:
    """Get singleton copilot service instance."""
    global _copilot_service
    if _copilot_service is None:
        _copilot_service = CopilotService()
    return _copilot_service
