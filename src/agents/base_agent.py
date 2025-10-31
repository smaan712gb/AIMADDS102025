"""
Base Agent class for all specialized agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from ..core.state import DiligenceState, AgentStatus, update_agent_status, add_agent_output
from ..core.llm_factory import get_llm
from ..core.config import get_config


class BaseAgent(ABC):
    """Base class for all diligence agents"""
    
    def __init__(self, agent_name: str):
        """
        Initialize base agent
        
        Args:
            agent_name: Name of the agent (must match config)
        """
        self.config = get_config()
        self.agent_name = agent_name
        self.agent_config = self.config.agents[agent_name]
        
        # Get the LLM for this agent
        llm_name = self.config.get_agent_llm(agent_name)
        self.llm = get_llm(llm_name)
        
        logger.info(f"Initialized {self.agent_config.name} with {llm_name} model")
    
    async def execute(self, state: DiligenceState) -> DiligenceState:
        """
        Execute the agent's task
        
        Args:
            state: Current diligence state
        
        Returns:
            Updated state
        """
        logger.info(f"Starting {self.agent_config.name}")
        
        # Update status to running
        state = update_agent_status(state, self.agent_name, AgentStatus.RUNNING)
        
        try:
            # Initialize anomalies list for this agent run
            self._anomalies = []
            
            # Run agent-specific logic
            result = await self.run(state)
            
            # CRITICAL FIX: Collect anomalies from this agent run
            if hasattr(self, '_anomalies') and self._anomalies:
                logger.info(f"[{self.agent_name}] Collected {len(self._anomalies)} anomalies")
                
                # Add anomalies to global anomaly log in state
                if 'anomaly_log' not in state:
                    state['anomaly_log'] = []
                state['anomaly_log'].extend(self._anomalies)
                
                # Also add to agent's own data for easy access
                if 'anomalies' not in result.get("data", {}):
                    result.setdefault("data", {})['anomalies'] = self._anomalies
            
            # Update status to completed
            state = update_agent_status(state, self.agent_name, AgentStatus.COMPLETED)
            
            # Add agent output to state
            state = add_agent_output(
                state,
                agent_name=self.agent_name,
                status=AgentStatus.COMPLETED,
                data=result.get("data", {}),
                errors=result.get("errors", []),
                warnings=result.get("warnings", []),
                recommendations=result.get("recommendations", [])
            )
            
            logger.info(f"Completed {self.agent_config.name}")
            
        except Exception as e:
            logger.error(f"Error in {self.agent_config.name}: {e}")
            
            # Update status to failed
            state = update_agent_status(state, self.agent_name, AgentStatus.FAILED)
            
            # Add error to state
            state["errors"].append(f"{self.agent_config.name}: {str(e)}")
            
            # Add failed agent output
            state = add_agent_output(
                state,
                agent_name=self.agent_name,
                status=AgentStatus.FAILED,
                data={},
                errors=[str(e)]
            )
        
        return state
    
    @abstractmethod
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Agent-specific logic to be implemented by subclasses
        
        Args:
            state: Current diligence state
        
        Returns:
            Dictionary with:
                - data: Agent output data
                - errors: List of errors
                - warnings: List of warnings
                - recommendations: List of recommendations
        """
        pass
    
    def get_capability_description(self) -> str:
        """
        Get description of agent capabilities
        
        Returns:
            Description string
        """
        capabilities = self.agent_config.capabilities
        return f"{self.agent_config.name} ({self.agent_config.role}): " + ", ".join(capabilities)
    
    def _create_system_prompt(self, context: str = "") -> str:
        """
        Create system prompt for the agent
        
        Args:
            context: Additional context to include
        
        Returns:
            System prompt string
        """
        base_prompt = f"""You are the {self.agent_config.name}, a specialized AI agent with the role of {self.agent_config.role}.

Your capabilities include:
{chr(10).join(f'- {cap}' for cap in self.agent_config.capabilities)}

Your task is to provide thorough, professional analysis suitable for M&A due diligence.
Be precise, cite your sources, and highlight both opportunities and risks."""

        if context:
            base_prompt += f"\n\nContext:\n{context}"
        
        return base_prompt
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from LLM response
        
        Args:
            text: LLM response text
        
        Returns:
            Structured data dictionary
        """
        # This can be enhanced with more sophisticated parsing
        # For now, returns the text as-is
        return {"analysis": text}
    
    def log_action(self, message: str, level: str = "info"):
        """
        Log an action performed by the agent
        
        Args:
            message: Message to log
            level: Log level (info, warning, error)
        """
        if level == "error":
            logger.error(f"[{self.agent_name}] {message}")
        elif level == "warning":
            logger.warning(f"[{self.agent_name}] {message}")
        else:
            logger.info(f"[{self.agent_name}] {message}")
    
    def update_state(self, updates: Dict[str, Any]):
        """
        Update state with agent-specific data
        
        Args:
            updates: Dictionary of updates to apply to state
        """
        # This is a placeholder - in the revolutionary agents this would
        # update a shared state manager, but for now we just log it
        logger.debug(f"[{self.agent_name}] State update: {list(updates.keys())}")
    
    def log_anomaly(self, anomaly_type: str, description: str, severity: str = "medium", data: Dict[str, Any] = None):
        """
        Log an anomaly to the centralized anomaly log
        
        Args:
            anomaly_type: Type of anomaly (e.g., 'valuation_discrepancy', 'data_inconsistency')
            description: Description of the anomaly
            severity: Severity level (low, medium, high, critical)
            data: Additional data related to the anomaly
        """
        anomaly_entry = {
            "agent": self.agent_name,
            "type": anomaly_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        # Log to console
        self.log_action(f"Anomaly detected: {anomaly_type} - {description}", level="warning")
        
        # CRITICAL FIX: Store in instance variable for collection by execute()
        if not hasattr(self, '_anomalies'):
            self._anomalies = []
        self._anomalies.append(anomaly_entry)
        
        logger.info(f"Anomaly logged: {anomaly_entry}")
    
    def _get_financial_data_smart(self, state: DiligenceState, prefer_normalized: bool = True) -> Dict[str, Any]:
        """
        Smart financial data accessor with quality-based decision logic
        Prioritizes normalized financials when available and high quality
        
        Args:
            state: Current diligence state
            prefer_normalized: If True, prefer normalized data when available
            
        Returns:
            Dict containing financial data with metadata about source
        """
        normalized_data = state.get('normalized_financials', {})
        financial_data = state.get('financial_data', {})
        
        # Check if normalized data is available and high quality
        has_normalized = bool(normalized_data and normalized_data.get('quality_score', 0) >= 60)
        
        if prefer_normalized and has_normalized:
            quality_score = normalized_data.get('quality_score', 0)
            logger.info(f"[{self.agent_name}] Using normalized financials (quality: {quality_score}/100)")
            
            return {
                'income_statement': normalized_data.get('normalized_income', []),
                'balance_sheet': normalized_data.get('normalized_balance', []),
                'cash_flow': normalized_data.get('normalized_cash_flow', []),
                'ebitda': normalized_data.get('ebitda', 0),
                'quality_score': quality_score,
                'adjustments': normalized_data.get('adjustments', []),
                'source': 'normalized',
                'data_confidence': 'high'
            }
        else:
            if prefer_normalized and not has_normalized:
                logger.warning(f"[{self.agent_name}] Normalized data not available or low quality, using raw financial_data")
            else:
                logger.info(f"[{self.agent_name}] Using raw financial_data (by design)")
            
            # Extract EBITDA from raw data
            ebitda = 0
            income_statements = financial_data.get('income_statement', [])
            if income_statements:
                ebitda = income_statements[0].get('ebitda', 0)
            
            return {
                'income_statement': financial_data.get('income_statement', []),
                'balance_sheet': financial_data.get('balance_sheet', []),
                'cash_flow': financial_data.get('cash_flow', []),
                'ebitda': ebitda,
                'quality_score': None,
                'adjustments': [],
                'source': 'raw',
                'data_confidence': 'medium'
            }
