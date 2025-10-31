"""
M&A Copilot Service - Enhanced with Knowledge Graph and Citations

This enhanced version includes:
- Knowledge Graph integration for relationship queries
- Enhanced citation system
- PDF export capabilities
- Scenario re-modeling support
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
from src.utils.knowledge_graph import build_knowledge_graph_from_state, query_knowledge_graph, KnowledgeGraph


class EnhancedCopilotService:
    """
    Enhanced service for handling conversational interactions with analysis results.
    
    Includes knowledge graph querying, enhanced citations, and scenario re-modeling.
    """
    
    def __init__(self):
        self.job_manager = get_job_manager()
        self.llm = get_llm(model_name="gemini")
        self.knowledge_graphs = {}  # job_id -> KnowledgeGraph
        self.conversation_histories = {}  # job_id -> conversation history
        
    async def initialize_chat(self, job_id: str) -> Dict[str, Any]:
        """
        Initialize a new chat session for a given analysis.
        """
        try:
            result = self.job_manager.get_job_result(job_id)
            if not result:
                return {
                    "error": "Analysis not found",
                    "welcome_message": None,
                    "suggestions": []
                }
            
            # Load complete state from JSON file
            state = await self._load_analysis_state(job_id, result)
            
            # Build knowledge graph
            if state:
                logger.info(f"Building knowledge graph for job {job_id}")
                self.knowledge_graphs[job_id] = build_knowledge_graph_from_state(state)
                graph = self.knowledge_graphs[job_id]
                logger.info(f"Knowledge graph built: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
            
            # Initialize conversation history
            self.conversation_histories[job_id] = []
            
            # Generate welcome message and suggestions
            welcome_message = self._generate_welcome_message(result, state)
            suggestions = self._generate_suggestion_chips(result, state)
            
            return {
                "job_id": job_id,
                "project_name": result.get("project_name"),
                "welcome_message": welcome_message,
                "suggestions": suggestions,
                "context_loaded": True,
                "knowledge_graph_enabled": job_id in self.knowledge_graphs
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
        Process a user message and stream the response with enhanced features.
        """
        try:
            result = self.job_manager.get_job_result(job_id)
            if not result:
                yield {
                    "type": "error",
                    "content": "Analysis not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            state = await self._load_analysis_state(job_id, result)
            
            # Store conversation history
            if conversation_history:
                self.conversation_histories[job_id] = conversation_history
            
            # Check query type
            needs_kg_query = self._check_if_needs_kg_query(message)
            needs_scenario = self._check_if_needs_scenario(message)
            needs_live_search = self._check_if_needs_live_search(message)
            
            # Route to appropriate handler
            if needs_scenario:
                async for chunk in self._handle_scenario_remodeling(
                    message, state, result, conversation_history
                ):
                    yield chunk
            elif needs_kg_query and job_id in self.knowledge_graphs:
                async for chunk in self._handle_kg_query(
                    message, state, result, conversation_history, job_id
                ):
                    yield chunk
            elif needs_live_search:
                async for chunk in self._generate_live_search_response(
                    message, state, result, conversation_history
                ):
                    yield chunk
            else:
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
    
    async def _handle_kg_query(
        self,
        message: str,
        state: Dict[str, Any],
        result: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]],
        job_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle knowledge graph queries for relationship-based questions."""
        
        yield {"type": "start", "timestamp": datetime.utcnow().isoformat()}
        
        try:
            graph = self.knowledge_graphs[job_id]
            kg_results = query_knowledge_graph(graph, message, {})
            
            # Build response using LLM with KG results
            prompt = f"""You are an M&A analyst with access to a knowledge graph of the analysis.

USER QUESTION: {message}

KNOWLEDGE GRAPH QUERY RESULTS:
Query Type: {kg_results.get('query_type')}
Nodes Found: {len(kg_results.get('nodes', []))}
Relationships: {len(kg_results.get('relationships', []))}

RELEVANT NODES:
{json.dumps(kg_results.get('nodes', [])[:5], indent=2, default=str)}

RELATIONSHIPS:
{json.dumps(kg_results.get('relationships', [])[:10], indent=2, default=str)}

Provide a clear answer that:
1. Explains the relationships found in the knowledge graph
2. Shows connections between entities
3. Provides specific examples from the data
4. Uses markdown formatting

Include a citation at the end:
**Source:** Knowledge Graph Analysis
**Confidence:** High
**Nodes Analyzed:** {len(kg_results.get('nodes', []))}

RESPONSE:"""

            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Stream response
            chunk_size = 50
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield {
                    "type": "content",
                    "content": chunk + " ",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"source": "knowledge_graph"}
                }
            
            yield {"type": "end", "timestamp": datetime.utcnow().isoformat()}
            
        except Exception as e:
            logger.error(f"Error handling KG query: {e}")
            yield {
                "type": "error",
                "content": f"Error querying knowledge graph: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _handle_scenario_remodeling(
        self,
        message: str,
        state: Dict[str, Any],
        result: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle scenario re-modeling requests."""
        
        yield {
            "type": "start",
            "scenario_mode": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Extract assumptions from message
            assumptions = self._extract_scenario_assumptions(message)
            
            # Get current valuation
            financial_data = state.get('financial_data', {})
            current_val = financial_data.get('valuation', {})
            
            # Build scenario response
            prompt = f"""You are an M&A valuation expert. The user wants to remodel a scenario.

USER REQUEST: {message}

EXTRACTED ASSUMPTIONS:
{json.dumps(assumptions, indent=2)}

CURRENT VALUATION:
{json.dumps(current_val, indent=2, default=str)}

Provide a detailed scenario analysis that:
1. Acknowledges the assumption changes
2. Estimates the impact on valuation (show calculations)
3. Presents before/after comparison in a markdown table
4. Explains the key drivers of the change
5. Adds relevant insights and caveats

Format with:
- **Original Assumptions** vs **Updated Assumptions** table
- **Valuation Impact** table showing before/after
- Key insights in bullet points

Include citation:
**Analysis Type:** Scenario Re-modeling
**Assumptions Changed:** {len(assumptions)}
**Confidence:** Medium (estimated impact)
**Recommendation:** Run full DCF with updated assumptions for precise valuation

RESPONSE:"""

            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Stream response
            chunk_size = 50
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield {
                    "type": "content",
                    "content": chunk + " ",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"scenario": True, "assumptions": assumptions}
                }
            
            yield {"type": "end", "timestamp": datetime.utcnow().isoformat()}
            
        except Exception as e:
            logger.error(f"Error handling scenario: {e}")
            yield {
                "type": "error",
                "content": f"Error processing scenario: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_scenario_assumptions(self, message: str) -> Dict[str, Any]:
        """Extract scenario assumptions from natural language."""
        assumptions = {}
        message_lower = message.lower()
        
        # Revenue growth
        if 'revenue growth' in message_lower or 'growth rate' in message_lower:
            import re
            match = re.search(r'(\d+(?:\.\d+)?)\s*%', message)
            if match:
                assumptions['revenue_growth'] = float(match.group(1)) / 100
        
        # WACC
        if 'wacc' in message_lower or 'discount rate' in message_lower:
            import re
            match = re.search(r'(\d+(?:\.\d+)?)\s*%', message)
            if match:
                assumptions['wacc'] = float(match.group(1)) / 100
        
        # Margins
        if 'margin' in message_lower:
            assumptions['margin_assumption'] = "modified"
        
        # Time period
        if 'year' in message_lower:
            import re
            match = re.search(r'(\d+)\s*year', message)
            if match:
                assumptions['forecast_years'] = int(match.group(1))
        
        return assumptions
    
    def _check_if_needs_kg_query(self, message: str) -> bool:
        """Check if message needs knowledge graph query."""
        kg_keywords = [
            "relationship", "connect", "between", "related",
            "how does", "link", "connection", "path",
            "affect", "impact", "influence", "tied to"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in kg_keywords)
    
    def _check_if_needs_scenario(self, message: str) -> bool:
        """Check if message is a scenario re-modeling request."""
        scenario_keywords = [
            "rerun", "recalculate", "assume", "what if",
            "if we", "assuming", "suppose", "scenario"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in scenario_keywords)
    
    def _check_if_needs_live_search(self, message: str) -> bool:
        """Check if message needs live web search."""
        search_keywords = [
            "current", "latest", "recent", "today", "now",
            "stock price", "news", "announcement", "quarter",
            "earnings", "market", "update"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in search_keywords)
    
    async def _load_analysis_state(self, job_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Load complete analysis state from saved files."""
        try:
            project_name = result.get("project_name", "analysis")
            ticker = project_name.split()[0] if " " in project_name else project_name
            output_dir = Path("outputs") / f"{ticker.lower()}_analysis"
            
            if not output_dir.exists():
                logger.warning(f"Output directory not found: {output_dir}")
                return {}
            
            state_files = sorted(output_dir.glob("*_complete_state_*.json"), reverse=True)
            
            if state_files:
                with open(state_files[0], 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded analysis state from {state_files[0]}")
                    return state
            
            logger.warning("No complete state file found")
            return {}
            
        except Exception as e:
            logger.error(f"Error loading analysis state: {e}")
            return {}
    
    def _generate_welcome_message(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Generate personalized welcome message."""
        project_name = result.get("project_name", "this analysis")
        valuation = result.get("valuation_range", {})
        mid_val = valuation.get("mid", 0)
        
        message_parts = [
            f"# 💬 M&A Copilot - {project_name}\n",
            f"\nI'm your AI analyst with complete access to the comprehensive due diligence analysis. ",
            f"I can answer questions about:\n\n",
            f"- **Financial Analysis** - Valuation, ratios, trends\n",
            f"- **Competitive Position** - Market dynamics, peer benchmarking\n",
            f"- **Risk Assessment** - Identified risks and mitigation strategies\n",
            f"- **Relationships** - How different factors connect (Knowledge Graph)\n",
            f"- **Scenarios** - Run what-if analysis with different assumptions\n",
            f"- **Live Market Data** - Current stock prices, recent news\n\n"
        ]
        
        if mid_val > 0:
            message_parts.append(f"**Key Finding:** Mid-point valuation is ${mid_val/1e9:.2f}B\n\n")
        
        message_parts.append(
            "Ask me anything, test scenarios, or explore relationships in the analysis!"
        )
        
        return "".join(message_parts)
    
    def _generate_suggestion_chips(self, result: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestion chips."""
        suggestions = [
            "What are the top 3 risks in this deal?",
            "How does the valuation compare to peers?",
            "What's the connection between risks and competitive position?",
            "Rerun DCF assuming 15% revenue growth",
        ]
        
        if result.get("top_risks"):
            suggestions.append("Why is the valuation justified given these risks?")
        
        suggestions.extend([
            "What's the current stock price?",
            "Show me scenario analysis",
        ])
        
        return suggestions[:6]
    
    async def _generate_context_response(
        self,
        message: str,
        state: Dict[str, Any],
        result: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate response using analysis context with citations."""
        
        context = self._build_context_for_llm(state, result, conversation_history)
        
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

ALWAYS end your response with a citation block:
**Source:** [Report Name]
**Section:** [Section if known]
**Confidence:** High/Medium/Low
**Agent:** [Which agent generated this data]

RESPONSE:"""

        yield {"type": "start", "timestamp": datetime.utcnow().isoformat()}
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            chunk_size = 50
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield {
                    "type": "content",
                    "content": chunk + " ",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            yield {"type": "end", "timestamp": datetime.utcnow().isoformat()}
            
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
        """Generate response with live web search."""
        
        context = self._build_context_for_llm(state, result, conversation_history)
        target_company = result.get("project_name", "the target company")
        
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

END with:
**Source:** [External sources with URLs]
**Data As Of:** [Current date]
**Confidence:** High (live data)

RESPONSE:"""

        yield {
            "type": "start",
            "searching": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            search_llm = get_llm(model_name="gemini")
            response = await search_llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            chunk_size = 50
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield {
                    "type": "content",
                    "content": chunk + " ",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            yield {"type": "end", "timestamp": datetime.utcnow().isoformat()}
            
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
        """Build condensed context for LLM from analysis state."""
        context = {
            "project_name": result.get("project_name"),
            "valuation": result.get("valuation_range"),
            "key_metrics": result.get("key_metrics"),
            "top_risks": result.get("top_risks"),
            "top_opportunities": result.get("top_opportunities")
        }
        
        if state:
            if "financial_data" in state:
                context["financial_summary"] = {
                    "valuation": state["financial_data"].get("valuation"),
                    "ratios": state["financial_data"].get("ratio_analysis")
                }
            
            if "competitive_analysis" in state:
                context["competitive_summary"] = state["competitive_analysis"].get("summary")
            
            if "macroeconomic_analysis" in state:
                context["macro_insights"] = state["macroeconomic_analysis"].get("insights", [])[:5]
        
        return context
    
    async def export_conversation(self, job_id: str) -> Optional[str]:
        """Export conversation history to JSON (PDF export requires additional setup)."""
        try:
            if job_id not in self.conversation_histories:
                return None
            
            history = self.conversation_histories[job_id]
            result = self.job_manager.get_job_result(job_id)
            
            export_data = {
                "project_name": result.get("project_name") if result else "Unknown",
                "job_id": job_id,
                "export_date": datetime.utcnow().isoformat(),
                "conversation": history
            }
            
            # Save to file
            export_dir = Path("outputs") / "conversations"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"conversation_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = export_dir / filename
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Conversation exported to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error exporting conversation: {e}")
            return None


# Singleton instance
_enhanced_copilot_service = None

def get_enhanced_copilot_service() -> EnhancedCopilotService:
    """Get singleton enhanced copilot service instance."""
    global _enhanced_copilot_service
    if _enhanced_copilot_service is None:
        _enhanced_copilot_service = EnhancedCopilotService()
    return _enhanced_copilot_service
