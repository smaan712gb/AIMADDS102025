"""
Data Accessor - Enforces Single Source of Truth
Only allows access to consolidated, synthesized data

This module ensures that all report generators (PDF, Excel, PPT, Dashboard)
read from the SAME consolidated data source, preventing inconsistencies.
"""

from typing import Dict, Any, Optional
from loguru import logger


class DataAccessor:
    """
    Enforces access to synthesized data only
    
    All report generators MUST use this class to access data.
    Direct state.get() calls are FORBIDDEN.
    """
    
    @staticmethod
    def get_synthesized_data(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get synthesized data - ONLY valid data source for reports
        
        Args:
            state: Current diligence state
            
        Returns:
            Synthesized data dictionary
            
        Raises:
            ValueError: If synthesized_data not found in state
        """
        if 'synthesized_data' not in state:
            raise ValueError(
                "CRITICAL: synthesized_data not found in state. "
                "Synthesis agent must run before report generation. "
                "This indicates an orchestration error."
            )
        
        synth_data = state['synthesized_data']
        logger.debug(f"Retrieved synthesized data version: {synth_data.get('data_version', 'unknown')}")
        
        return synth_data
    
    @staticmethod
    def get_valuation(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get SINGLE validated valuation from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Valuation dictionary with DCF outputs
        """
        data = DataAccessor.get_synthesized_data(state)
        financials = data.get('detailed_financials', {})
        valuation = financials.get('dcf_outputs', {})
        
        if not valuation:
            logger.warning("Valuation data is empty in synthesized financials")
        
        return valuation
    
    @staticmethod
    def get_ebitda(state: Dict[str, Any]) -> float:
        """
        Get SINGLE normalized EBITDA from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Normalized EBITDA value
        """
        data = DataAccessor.get_synthesized_data(state)
        financials = data.get('detailed_financials', {})
        ebitda = financials.get('normalized_ebitda', 0)
        
        if ebitda == 0:
            logger.warning("Normalized EBITDA is zero in synthesized data")
        
        return ebitda
    
    @staticmethod
    def get_agent_count(state: Dict[str, Any]) -> int:
        """
        Get SINGLE agent count from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Number of agents that completed analysis
        """
        data = DataAccessor.get_synthesized_data(state)
        metadata = data.get('metadata', {})
        agent_count = metadata.get('agent_coverage', 0)
        
        return agent_count
    
    @staticmethod
    def get_metadata(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get metadata from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Metadata dictionary
        """
        data = DataAccessor.get_synthesized_data(state)
        return data.get('metadata', {})
    
    @staticmethod
    def get_executive_summary(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get executive summary from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Executive summary dictionary
        """
        data = DataAccessor.get_synthesized_data(state)
        return data.get('executive_summary', {})
    
    @staticmethod
    def get_detailed_financials(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed financials from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Detailed financials dictionary
        """
        data = DataAccessor.get_synthesized_data(state)
        return data.get('detailed_financials', {})
    
    @staticmethod
    def get_legal_diligence(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get legal diligence from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Legal diligence dictionary
        """
        data = DataAccessor.get_synthesized_data(state)
        return data.get('legal_diligence', {})
    
    @staticmethod
    def get_market_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get market analysis from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Market analysis dictionary
        """
        data = DataAccessor.get_synthesized_data(state)
        return data.get('market_analysis', {})
    
    @staticmethod
    def get_validation_summary(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get validation summary from synthesized data
        
        Args:
            state: Current diligence state
            
        Returns:
            Validation summary dictionary
        """
        data = DataAccessor.get_synthesized_data(state)
        return data.get('validation_summary', {})
    
    @staticmethod
    def validate_data_consistency(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that all reports will use same data
        
        Args:
            state: Current diligence state
            
        Returns:
            Validation result dictionary with status and details
        """
        try:
            data = DataAccessor.get_synthesized_data(state)
            
            required_fields = [
                'metadata',
                'executive_summary',
                'detailed_financials'
            ]
            
            fields_present = all(field in data for field in required_fields)
            
            return {
                'has_synthesized_data': True,
                'data_version': data.get('data_version', 'unknown'),
                'consolidated_timestamp': data.get('consolidated_timestamp', 'unknown'),
                'required_fields_present': fields_present,
                'source': data.get('source', 'unknown')
            }
        except ValueError as e:
            return {
                'has_synthesized_data': False,
                'error': str(e),
                'data_version': None,
                'consolidated_timestamp': None,
                'required_fields_present': False
            }
    
    @staticmethod
    def has_synthesized_data(state: Dict[str, Any]) -> bool:
        """
        Check if synthesized data exists in state
        
        Args:
            state: Current diligence state
            
        Returns:
            True if synthesized data exists, False otherwise
        """
        return 'synthesized_data' in state and isinstance(state['synthesized_data'], dict)
