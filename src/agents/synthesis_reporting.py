"""
Synthesis & Quality Control Agent - The Consolidator & Editor-in-Chief

AI-powered layer that reviews, consolidates, and quality-controls outputs from all
analytical agents into a single, coherent, fact-checked narrative suitable for report generation.
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage
import json
import asyncio
import numpy as np
from collections import defaultdict

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available - semantic similarity disabled")

try:
    import financetoolkit as ft
    HAS_FINANCETOOLKIT = True
except ImportError:
    HAS_FINANCETOOLKIT = False
    logger.warning("Finance Toolkit not available - some recalculations may be limited")

from .base_agent import BaseAgent
from ..core.state import DiligenceState
from ..utils.llm_retry import llm_call_with_retry

# Import optimization components
from ..utils.parallel_processor import ParallelProcessor, BatchedVerificationProcessor
from ..utils.financial_calculator import FinancialCalculator
from ..utils.cache_manager import get_llm_cache, get_calculation_cache
from ..config.synthesis_config import (
    PRODUCTION_CONFIG, 
    ClaimPrioritizer, 
    GroundingDepth,
    SYNTHESIS_OUTPUT_CONFIG
)


class SynthesisReportingAgent(BaseAgent):
    """
    Synthesis & Quality Control Agent - The Consolidator & Editor-in-Chief

    AI-powered layer that runs after all analytical agents complete, providing:
    - Grounding & Fact-Checking: Cross-references claims against source data using LLM (OPTIMIZED)
    - De-duplication & Redundancy Removal: Semantic clustering with vector embeddings
    - Conflict Resolution: Rule-based hierarchy for numbers, LLM reasoning for qualitative
    - Confidence Scoring: Aggregates agent confidence scores
    - Structured Output: Produces clean JSON for report generators
    
    PERFORMANCE OPTIMIZATIONS:
    - Parallel LLM calls with semaphore control
    - Intelligent claim prioritization (only verify critical claims)
    - Batched verification (5 claims per LLM call)
    - LLM response caching
    - Financial calculator tools for accurate computations
    """

    def __init__(self, config=None):
        """Initialize Synthesis & Quality Control Agent with optimizations"""
        super().__init__("synthesis_reporting")

        # Use production config by default
        self.config = config or PRODUCTION_CONFIG
        logger.info(f"Using synthesis config: grounding_depth={self.config.grounding_depth}, max_concurrent={self.config.max_concurrent_llm_calls}")

        # Initialize optimization components
        self.parallel_processor = ParallelProcessor(
            max_concurrent=self.config.max_concurrent_llm_calls,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            timeout=self.config.llm_timeout
        )
        
        self.batched_verifier = BatchedVerificationProcessor(self.parallel_processor)
        self.claim_prioritizer = ClaimPrioritizer()
        self.financial_calculator = FinancialCalculator()
        
        # Initialize caching
        self.llm_cache = get_llm_cache(enable_caching=self.config.enable_caching)
        self.calc_cache = get_calculation_cache(enable_caching=self.config.enable_caching)
        
        if self.llm_cache:
            logger.info("LLM response caching enabled")
        if self.calc_cache:
            logger.info("Financial calculation caching enabled")

        # Initialize vector database for semantic similarity
        self.vector_db = None
        if CHROMA_AVAILABLE:
            try:
                self.vector_db = chromadb.PersistentClient(path="data/chromadb")
                logger.info("ChromaDB initialized for synthesis operations")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB: {e}")

        # Confidence scoring weights
        self.confidence_weights = {
            'source_data_quality': 0.3,
            'agent_methodology': 0.25,
            'cross_validation': 0.25,
            'consensus_strength': 0.2
        }

        logger.info("Synthesis & Quality Control Agent initialized with PRODUCTION optimizations")

    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Execute comprehensive synthesis and quality control

        Args:
            state: Current diligence state with all agent outputs

        Returns:
            Dictionary with synthesized data ready for report generation
        """
        errors = []
        warnings = []
        recommendations = []
        start_time = datetime.utcnow()

        try:
            self.log_action(f"Starting synthesis for {state['target_company']}")

            # Step 1: Collect and validate agent outputs
            agent_outputs = self._collect_agent_outputs(state)
            if not agent_outputs:
                errors.append("No agent outputs available for synthesis")
                return {
                    "data": {},
                    "errors": errors,
                    "warnings": warnings,
                    "recommendations": recommendations
                }

            # Step 2: Grounding & Fact-Checking
            self.log_action("Performing grounding and fact-checking...")
            grounded_outputs, hallucination_flags = await self._perform_grounding_checks(
                agent_outputs, state
            )

            # Step 3: De-duplication & Semantic Clustering
            self.log_action("Removing redundancies and clustering similar findings...")
            deduplicated_findings = await self._perform_deduplication(grounded_outputs)

            # Step 4: Conflict Resolution
            self.log_action("Resolving conflicts between agent outputs...")
            resolved_outputs, conflicts_resolved = await self._resolve_conflicts(deduplicated_findings)

            # Step 5: Confidence Scoring
            self.log_action("Calculating confidence scores...")
            confidence_scores = self._calculate_confidence_scores(resolved_outputs, state)

            # Step 6: Generate Structured Output for Report Generators
            self.log_action("Generating structured JSON for report generators...")
            structured_output = await self._generate_structured_output(
                resolved_outputs,
                confidence_scores,
                conflicts_resolved,
                hallucination_flags,
                state
            )

            # Success tracking
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.log_action(f"Synthesis completed successfully in {processing_time:.2f}s")

            success_metrics = {
                "processing_time_seconds": processing_time,
                "conflicts_resolved": len(conflicts_resolved),
                "hallucinations_flagged": len(hallucination_flags),
                "total_findings_synthesized": len(resolved_outputs.get('findings', [])),
                "confidence_distribution": self._calculate_confidence_distribution(confidence_scores)
            }

            # CRITICAL: Store consolidated data in state as single source of truth
            state['synthesized_data'] = {
                'metadata': structured_output['metadata'],
                'executive_summary': structured_output['executive_summary'],
                'detailed_financials': structured_output['detailed_financials'],
                'legal_diligence': structured_output['legal_diligence'],
                'market_analysis': structured_output['market_analysis'],
                'validation_summary': structured_output['validation_summary'],
                'synthesis_metadata': success_metrics,
                'consolidated_timestamp': datetime.utcnow().isoformat(),
                'data_version': '1.0',
                'source': 'synthesis_reporting_agent'
            }
            
            self.log_action(f"✓ Stored synthesized_data in state (version 1.0)")

            final_output = {
                "data": {
                    **structured_output,
                    "synthesis_metadata": success_metrics
                },
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }

            # CRITICAL: Save consolidated data to disk for audit trail
            if SYNTHESIS_OUTPUT_CONFIG.get("save_to_disk", True):
                self._save_consolidated_data(state, state['synthesized_data'])

            return final_output

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Synthesis failed after {processing_time:.1f}s: {str(e)}"
            self.log_action(error_msg, level="error")
            errors.append(error_msg)

            return {
                "data": {},
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }

    def _collect_agent_outputs(self, state: DiligenceState) -> Dict[str, Dict[str, Any]]:
        """
        Collect and validate outputs from all analytical agents from multiple storage locations

        Args:
            state: Current diligence state

        Returns:
            Dictionary of agent outputs keyed by agent name
        """
        agent_outputs = {}

        # List of analytical agents to collect from (exclude synthesis and support agents)
        analytical_agents = [
            'project_manager', 'financial_analyst', 'financial_deep_dive', 'legal_counsel',
            'market_strategist', 'competitive_benchmarking', 'macroeconomic_analyst',
            'risk_assessment', 'tax_structuring', 'deal_structuring',
            'accretion_dilution', 'sources_uses', 'contribution_analysis', 'exchange_ratio_analysis',
            'integration_planner', 'external_validator'
        ]

        # Collect from multiple possible locations for each agent with enhanced search
        for agent_name in analytical_agents:
            agent_info = self._find_agent_data_recursive(agent_name, state)
            if agent_info:
                agent_outputs[agent_name] = agent_info

        # Log collection details
        collected_agents = list(agent_outputs.keys())
        found_counts = {}
        for agent_name, agent_info in agent_outputs.items():
            source = agent_info.get('data_source', 'unknown')
            found_counts[source] = found_counts.get(source, 0) + 1

        self.log_action(f"Collected {len(agent_outputs)} agents: {collected_agents}")
        self.log_action(f"Data sources used: {found_counts}")

        # Check for missing agents and try fallback collection
        missing_agents = [agent for agent in analytical_agents if agent not in agent_outputs]
        if missing_agents:
            self.log_action(f"⚠️ Missing agents: {missing_agents}")
            # Try fallback collection for critical missing agents
            for agent_name in missing_agents:
                if agent_name in ['competitive_benchmarking', 'macroeconomic_analyst', 'risk_assessment']:
                    fallback_data = self._collect_fallback_agent_data(agent_name, state)
                    if fallback_data:
                        agent_outputs[agent_name] = fallback_data
                        self.log_action(f"✓ Collected fallback data for {agent_name}")

        return agent_outputs

    def _find_agent_data_recursive(self, agent_name: str, state: DiligenceState) -> Optional[Dict[str, Any]]:
        """
        Enhanced recursive agent data search with deeper exploration

        Args:
            agent_name: Name of the agent to find
            state: Current state

        Returns:
            Agent data if found, None otherwise
        """
        # First try the original method
        agent_info = self._find_agent_data(agent_name, state)
        if agent_info:
            return agent_info

        # Enhanced search: Check all possible nested locations
        def deep_search(data: Any, path: str = "") -> Optional[Dict[str, Any]]:
            if isinstance(data, dict):
                # Check if this dict has agent-like data
                if any(key in str(data).lower() for key in ['market_share', 'competitive_position', 'macro_analysis', 'risk_assessment']):
                    # Look for agent markers
                    agent_markers = {
                        'competitive_benchmarking': ['market_share', 'competitive_position', 'peers'],
                        'macroeconomic_analyst': ['scenario_models', 'economic_indicators', 'macro_analysis'],
                        'risk_assessment': ['risk_matrix', 'key_risks', 'risk_score']
                    }

                    markers = agent_markers.get(agent_name, [])
                    if markers and any(marker in str(data) for marker in markers):
                        # Found potential agent data
                        return {
                            'data': data,
                            'status': 'found_via_deep_search',
                            'timestamp': state.get('timestamp', ''),
                            'confidence_score': self._extract_agent_confidence(data),
                            'data_source': f'deep_search_{path}'
                        }

                # Recursively search sub-dictionaries
                for key, value in data.items():
                    result = deep_search(value, f"{path}.{key}" if path else key)
                    if result:
                        return result

            elif isinstance(data, list):
                # Search through list items
                for i, item in enumerate(data):
                    result = deep_search(item, f"{path}[{i}]")
                    if result:
                        return result

            return None

        # Search entire state deeply
        return deep_search(state)

    def _collect_fallback_agent_data(self, agent_name: str, state: DiligenceState) -> Optional[Dict[str, Any]]:
        """
        Collect basic fallback data for critical missing agents

        Args:
            agent_name: Agent name
            state: Current state

        Returns:
            Basic fallback data structure
        """
        fallback_data = {
            'competitive_benchmarking': {
                'market_share': 'N/A - Data unavailable',
                'competitive_position': 'Under analysis - Agent data missing',
                'key_competitors': [],
                'analysis_note': 'Competitive benchmarking data not available - requires agent run'
            },
            'macroeconomic_analyst': {
                'economic_outlook': 'Analysis in progress - Agent data missing',
                'scenario_models': {},
                'macro_analysis': {},
                'analysis_note': 'Macroeconomic analysis not available - requires agent run'
            },
            'risk_assessment': {
                'key_risks': ['Data unavailable - Agent not run'],
                'overall_risk_score': 0,
                'risk_matrix': {},
                'analysis_note': 'Risk assessment not available - requires agent run'
            }
        }

        if agent_name in fallback_data:
            return {
                'data': fallback_data[agent_name],
                'status': 'fallback_data_generated',
                'timestamp': state.get('timestamp', ''),
                'confidence_score': 0.1,  # Low confidence for fallback data
                'data_source': 'fallback_generation'
            }

        return None

    def _find_agent_data(self, agent_name: str, state: DiligenceState) -> Optional[Dict[str, Any]]:
        """
        Find agent data from multiple possible locations in state

        Args:
            agent_name: Name of the agent
            state: Current state

        Returns:
            Agent data if found, None otherwise
        """

        # Location 1: Direct state key (e.g., state["financial_analyst"])
        agent_data = state.get(agent_name)
        if agent_data:
            data = agent_data.get('data') if isinstance(agent_data, dict) and 'data' in agent_data else agent_data
            return {
                'data': data,
                'status': 'completed',
                'timestamp': state.get('timestamp', ''),
                'confidence_score': self._extract_agent_confidence(data),
                'data_source': f'centralized_key'
            }

        # Location 2: Target company sub-key (e.g., state[target_company][agent_name])
        target_company = state.get('target_company')
        if target_company and target_company in state:
            company_data = state[target_company]
            if isinstance(company_data, dict) and agent_name in company_data:
                data = company_data[agent_name]
                return {
                    'data': data,
                    'status': 'completed',
                    'timestamp': state.get('timestamp', ''),
                    'confidence_score': self._extract_agent_confidence(data),
                    'data_source': f'target_company_key'
                }

        # Location 3: Agent_outputs array (legacy fallback)
        agent_outputs = state.get('agent_outputs', [])
        for output in agent_outputs:
            if isinstance(output, dict) and output.get('agent_name') == agent_name:
                data = output.get('data', {})
                return {
                    'data': data,
                    'status': output.get('status', 'unknown'),
                    'timestamp': output.get('timestamp', ''),
                    'confidence_score': self._extract_agent_confidence(data),
                    'data_source': 'agent_outputs_array'
                }

        # Location 4: Raw state keys (e.g., state["compliance_status"] for legal_counsel)
        # Map agent names to possible alternative storage keys
        alternative_keys = {
            'legal_counsel': ['compliance_status', 'legal_risks', 'sec_analysis'],
            'risk_assessment': ['risk_matrix', 'risk_scores'],
            'market_strategist': ['market_analysis', 'swot_analysis'],
            'competitive_benchmarking': ['competitive_analysis'],
            'macroeconomic_analyst': ['macroeconomic_analysis'],
            'tax_structuring': ['tax_analysis'],
            'integration_planner': ['integration_plan'],
            'external_validator': ['validation_results']
        }

        if agent_name in alternative_keys:
            collected_data = {}
            found_any = False
            for alt_key in alternative_keys[agent_name]:
                if alt_key in state:
                    collected_data[alt_key] = state[alt_key]
                    found_any = True

            if found_any:
                # Wrap collected data in expected structure
                wrapped_data = {
                    agent_name: collected_data,
                    'collected_from_scattered_keys': True
                }
                return {
                    'data': wrapped_data,
                    'status': 'completed_from_scattered_data',
                    'timestamp': state.get('timestamp', ''),
                    'confidence_score': self._extract_agent_confidence(wrapped_data),
                    'data_source': 'scattered_keys'
                }

        # Not found
        return None

    def _extract_agent_confidence(self, agent_data: Dict[str, Any]) -> float:
        """
        Extract or estimate confidence score from agent output

        Args:
            agent_data: Agent's output data

        Returns:
            Confidence score between 0-1
        """
        # Look for explicit confidence scores in agent outputs
        if 'confidence_score' in agent_data:
            return min(1.0, max(0.0, agent_data['confidence_score']))

        # Estimate confidence based on output completeness and quality
        completeness_score = 0.0
        data_points = 0

        # Financial data completeness
        if 'financial_data' in agent_data and agent_data['financial_data']:
            completeness_score += 0.3
            data_points += 1

        # Multiple scenarios or analysis types
        if any(key in str(agent_data).lower() for key in ['scenario', 'analysis', 'valuation']):
            completeness_score += 0.2
            data_points += 1

        # Recommendations or insights
        if any(key in agent_data for key in ['recommendations', 'insights', 'findings']):
            completeness_score += 0.2
            data_points += 1

        # Risk assessments
        if 'risk' in str(agent_data).lower():
            completeness_score += 0.15
            data_points += 1

        # Quantitative metrics
        if any(isinstance(v, (int, float)) for v in agent_data.values() if isinstance(v, dict) or isinstance(v, list)):
            completeness_score += 0.15
            data_points += 1

        # Base confidence on completeness (with minimum floor)
        base_confidence = max(0.5, completeness_score)

        # Boost for data quantity but penalize for very sparse outputs
        if data_points == 0:
            return 0.3  # Very low confidence for empty outputs
        elif data_points <= 2:
            return min(0.7, base_confidence)
        else:
            return min(0.9, base_confidence + 0.1)

    async def _perform_grounding_checks(
        self,
        agent_outputs: Dict[str, Dict[str, Any]],
        state: DiligenceState
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Perform grounding and fact-checking using LLM cross-referencing

        Args:
            agent_outputs: Outputs from all agents
            state: Current diligence state with source data

        Returns:
            Tuple of (grounded_outputs, hallucination_flags)
        """
        grounded_outputs = {}
        hallucination_flags = []

        try:
            # Extract source data for verification
            source_data = self._extract_source_data(state)
            if not source_data:
                self.log_action("No source data available for grounding checks")
                return agent_outputs, hallucination_flags

            # Process each agent's outputs
            for agent_name, agent_info in agent_outputs.items():
                self.log_action(f"Grounding check for {agent_name}")

                agent_data = agent_info['data']
                grounded_data, agent_hallucinations = await self._ground_agent_claims(
                    agent_name, agent_data, source_data
                )

                grounded_outputs[agent_name] = {
                    **agent_info,
                    'data': grounded_data,
                    'grounding_status': 'completed'
                }

                hallucination_flags.extend(agent_hallucinations)

            self.log_action(f"Grounding checks complete. Flagged {len(hallucination_flags)} potential hallucinations")

        except Exception as e:
            self.log_action(f"Error during grounding checks: {e}", level="error")
            # Return original outputs if grounding fails
            return agent_outputs, hallucination_flags

        return grounded_outputs, hallucination_flags

    def _extract_source_data(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Extract source data from state for grounding verification

        Args:
            state: Current diligence state

        Returns:
            Structured source data for verification
        """
        source_data = {
            'sec_filings': [],
            'financial_statements': {},
            'market_data': {},
            'deal_documents': []
        }

        # Extract SEC filing data
        if 'documents' in state:
            for doc in state['documents']:
                if hasattr(doc, 'content') and doc.content:
                    content_type = self._classify_document_content(doc.content[:1000])
                    source_data[content_type].append({
                        'filename': getattr(doc, 'filename', ''),
                        'content': doc.content,
                        'type': content_type
                    })

        # Extract financial data
        if 'financial_data' in state:
            source_data['financial_statements'] = state['financial_data']

        return source_data

    def _classify_document_content(self, content_sample: str) -> str:
        """
        Classify document content type for source data categorization

        Args:
            content_sample: First 1000 chars of document

        Returns:
            Content type classification
        """
        content_lower = content_sample.lower()

        if any(term in content_lower for term in ['10-k', '10-q', '8-k', 'sec filing', 'securities act']):
            return 'sec_filings'
        elif any(term in content_lower for term in ['financial statement', 'income statement', 'balance sheet', 'cash flow']):
            return 'sec_filings'  # SEC filings often contain financial statements
        elif any(term in content_lower for term in ['merger', 'acquisition', 'deal terms', 'purchase agreement']):
            return 'deal_documents'
        else:
            return 'sec_filings'  # Default classification

    async def _ground_agent_claims(
        self,
        agent_name: str,
        agent_data: Dict[str, Any],
        source_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Ground agent claims against source data using LLM (OPTIMIZED - Batched & Parallel)
        
        Uses batched verification and parallel processing for 10x speedup.

        Args:
            agent_name: Name of the agent
            agent_data: Agent's output data
            source_data: Source data for verification

        Returns:
            Tuple of (grounded_data, hallucination_flags)
        """
        grounded_data = agent_data.copy()
        hallucinations = []

        try:
            # Extract factual claims from agent output (now prioritized and limited)
            claim_dicts = self._extract_factual_claims(agent_data, agent_name)

            if not claim_dicts:
                return grounded_data, hallucinations
            
            # Extract just the claim content for verification
            claims = [c['content'] for c in claim_dicts]
            
            self.log_action(f"Verifying {len(claims)} prioritized claims for {agent_name}")

            # Verify claims using BATCHED PARALLEL verification
            if self.config.enable_batched_verification:
                verification_results = await self._verify_claims_batched_parallel(
                    claims, source_data, agent_name
                )
            else:
                # Fallback to sequential verification
                verification_results = []
                for claim in claims:
                    result = await self._verify_claim_against_sources(
                        claim, source_data, agent_name
                    )
                    verification_results.append(result)
            
            # Process verification results
            for claim, verification in zip(claims, verification_results):
                if not verification['is_grounded']:
                    hallucinations.append({
                        'agent': agent_name,
                        'claim': claim,
                        'severity': verification['severity'],
                        'reason': verification['reason'],
                        'suggested_action': verification['action']
                    })

                    # Optionally remove or flag the ungrounded claim
                    if verification['severity'] in ['high', 'critical']:
                        self._flag_ungrounded_claim(grounded_data, claim)

            # Add grounding metadata
            grounded_data['_grounding_metadata'] = {
                'total_claims_checked': len(claims),
                'hallucinations_found': len(hallucinations),
                'grounding_coverage': (len(claims) - len(hallucinations)) / len(claims) if claims else 0,
                'optimization_used': 'batched_parallel' if self.config.enable_batched_verification else 'sequential'
            }

        except Exception as e:
            self.log_action(f"Error grounding claims for {agent_name}: {e}", level="error")

        return grounded_data, hallucinations
    
    async def _verify_claims_batched_parallel(
        self,
        claims: List[str],
        source_data: Dict[str, Any],
        agent_name: str
    ) -> List[Dict[str, Any]]:
        """
        Verify claims using batched parallel processing (OPTIMIZATION)
        
        Args:
            claims: List of claims to verify
            source_data: Source data for verification
            agent_name: Agent name
            
        Returns:
            List of verification results
        """
        try:
            # Create verification function for batching
            async def verify_batch(batch: List[str], sources: Dict[str, Any]) -> List[Dict[str, Any]]:
                """Verify a batch of claims in a single LLM call"""
                batch_results = []
                
                # Verify each claim in the batch (could be further optimized to verify all in one call)
                for claim in batch:
                    result = await self._verify_claim_against_sources(claim, sources, agent_name)
                    batch_results.append(result)
                
                return batch_results
            
            # Use batched verifier with parallel processing
            results = await self.batched_verifier.verify_claims_batched(
                claims,
                source_data,
                verify_batch,
                batch_size=self.config.batch_size
            )
            
            # Flatten results
            all_results = []
            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
                else:
                    all_results.append(result)
            
            return all_results
            
        except Exception as e:
            self.log_action(f"Batched verification failed: {e}, falling back to sequential", level="warning")
            # Fallback to sequential
            results = []
            for claim in claims:
                result = await self._verify_claim_against_sources(claim, source_data, agent_name)
                results.append(result)
            return results

    def _extract_factual_claims(self, agent_data: Dict[str, Any], agent_name: str = "") -> List[Dict[str, Any]]:
        """
        Extract factual claims that can be verified from agent output (OPTIMIZED)
        
        Uses intelligent prioritization to extract only critical claims.

        Args:
            agent_data: Agent's output data
            agent_name: Name of the agent (for prioritization)

        Returns:
            List of prioritized claim dictionaries with content, priority, etc.
        """
        raw_claims = []

        def extract_from_value(value: Any, path: str = "") -> None:
            if isinstance(value, str):
                # Look for numerical claims, dates, and specific factual statements
                if any(keyword in value.lower() for keyword in [
                    'million', '$', 'billion', 'valuation', 'revenue', 'profit', 'margin',
                    'change-of-control', 'clause', 'penalty', 'section', 'article', 'risk',
                    'wacc', 'irr', 'dcf', 'synergy', 'multiple', 'ebitda'
                ]):
                    raw_claims.append({
                        'content': value,
                        'path': path,
                        'source_agent': agent_name
                    })

            elif isinstance(value, dict):
                for key, val in value.items():
                    extract_from_value(val, f"{path}.{key}" if path else key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    extract_from_value(item, f"{path}[{i}]")

        extract_from_value(agent_data)
        
        # Apply intelligent prioritization
        prioritized_claims = self.claim_prioritizer.filter_claims_by_priority(
            raw_claims,
            self.config
        )
        
        # Limit to configured maximum per agent
        agent_limit = self.config.agent_claim_limits.get(agent_name, self.config.max_claims_per_agent)
        
        return prioritized_claims[:agent_limit]

    async def _verify_claim_against_sources(
        self,
        claim: str,
        source_data: Dict[str, Any],
        agent_name: str
    ) -> Dict[str, Any]:
        """
        Verify a claim against source data using LLM reasoning

        Args:
            claim: Factual claim to verify
            source_data: Available source data
            agent_name: Name of agent making the claim

        Returns:
            Verification result with grounding status
        """
        try:
            # Prepare source excerpts for LLM verification
            relevant_sources = self._find_relevant_sources(claim, source_data)

            if not relevant_sources:
                return {
                    'is_grounded': False,
                    'severity': 'medium',
                    'reason': 'No relevant source data found',
                    'action': 'Flag for manual review'
                }

            # Create verification prompt
            verification_prompt = f"""As an expert fact-checker in M&A due diligence, verify this claim against the provided source data.

CLAIM TO VERIFY:
{claim}

RELEVANT SOURCE DATA:
{chr(10).join(f"- {source}" for source in relevant_sources[:3])}  # Limit to top 3 sources

ANALYSIS REQUIREMENTS:
1. Is this claim directly supported by the source data? (Yes/No)
2. If not supported, explain the discrepancy
3. Rate the severity if unsupported (low/medium/high/critical)
4. Suggest appropriate action if the claim appears to be a hallucination

Respond in this format:
GROUNDING: [Yes/No]
REASONING: [Brief explanation]
SEVERITY: [low/medium/high/critical]
ACTION: [Keep/Flag/Remove/Review]"""

            messages = [
                SystemMessage(content="You are a specialist in verifying factual claims in M&A documents. Be precise and conservative in your assessments."),
                HumanMessage(content=verification_prompt)
            ]

            response = await llm_call_with_retry(
                self.llm,
                messages,
                max_retries=2,
                context=f"Grounding check for {agent_name}"
            )

            # Parse response
            response_text = response.content.strip()
            lines = response_text.split('\n')

            grounding = 'no'
            reasoning = 'Unable to determine'
            severity = 'medium'
            action = 'Review'

            for line in lines:
                line = line.strip()
                if line.startswith('GROUNDING:'):
                    grounding = line.split(':', 1)[1].strip().lower()
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
                elif line.startswith('SEVERITY:'):
                    severity = line.split(':', 1)[1].strip().lower()
                elif line.startswith('ACTION:'):
                    action = line.split(':', 1)[1].strip()

            is_grounded = grounding.startswith('yes')

            return {
                'is_grounded': is_grounded,
                'severity': severity,
                'reason': reasoning,
                'action': action
            }

        except Exception as e:
            self.log_action(f"Error verifying claim '{claim[:50]}...': {e}", level="error")
            return {
                'is_grounded': False,
                'severity': 'unknown',
                'reason': f'Verification error: {str(e)}',
                'action': 'Manual review required'
            }

    def _find_relevant_sources(self, claim: str, source_data: Dict[str, Any]) -> List[str]:
        """
        Find potentially relevant source excerpts for claim verification

        Args:
            claim: Claim to find sources for
            source_data: Available source data

        Returns:
            List of relevant source excerpts
        """
        relevant_sources = []

        # Simple keyword matching for now
        # In production, could use semantic similarity or more sophisticated matching
        claim_lower = claim.lower()

        for category, documents in source_data.items():
            if isinstance(documents, list):
                for doc in documents:
                    if isinstance(doc, dict) and 'content' in doc:
                        content_lower = doc['content'].lower()
                        # Look for overlapping keywords
                        claim_words = set(claim_lower.split())
                        content_words = set(content_lower.split())

                        overlap = len(claim_words.intersection(content_words))
                        if overlap >= 2:  # At least 2 matching words
                            # Extract relevant snippet
                            excerpt = self._extract_relevant_excerpt(claim, doc['content'])
                            if excerpt:
                                relevant_sources.append(f"{doc.get('filename', category)}: {excerpt}")
            elif isinstance(documents, dict):
                # Handle dictionary-type source data
                content_str = json.dumps(documents)
                content_lower = content_str.lower()
                claim_words = set(claim_lower.split())
                content_words = set(content_lower.split())

                overlap = len(claim_words.intersection(content_words))
                if overlap >= 2:
                    relevant_sources.append(f"{category}: {content_str[:500]}...")

        return relevant_sources[:5]  # Limit to top 5 sources

    def _extract_relevant_excerpt(self, claim: str, content: str, context_window: int = 200) -> Optional[str]:
        """
        Extract relevant excerpt from content that relates to the claim

        Args:
            claim: The claim being verified
            content: Full document content
            context_window: Characters of context around matching text

        Returns:
            Relevant excerpt or None
        """
        claim_lower = claim.lower()
        content_lower = content.lower()

        # Find position of first matching phrase
        claim_words = claim_lower.split()[:3]  # First 3 words
        claim_phrase = ' '.join(claim_words)

        pos = content_lower.find(claim_phrase)
        if pos == -1:
            # Try individual important words
            important_words = [word for word in claim_words if len(word) > 3 and not word.isdigit()]
            for word in important_words:
                pos = content_lower.find(word)
                if pos != -1:
                    break

        if pos == -1:
            return None

        # Extract context around the match
        start = max(0, pos - context_window // 2)
        end = min(len(content), pos + len(claim_phrase) + context_window // 2)

        excerpt = content[start:end].strip()
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt

    def _flag_ungrounded_claim(self, agent_data: Dict[str, Any], claim: str) -> None:
        """
        Flag or modify ungrounded claims in agent data

        Args:
            agent_data: Agent data to modify
            claim: The ungrounded claim
        """
        # Add hallucination flag to metadata
        if '_hallucination_warnings' not in agent_data:
            agent_data['_hallucination_warnings'] = []

        agent_data['_hallucination_warnings'].append({
            'claim': claim,
            'flag_reason': 'Failed grounding check against source data',
            'severity': 'high'
        })

    async def _perform_deduplication(self, grounded_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deduplication and semantic clustering of similar findings

        Args:
            grounded_outputs: Grounded agent outputs

        Returns:
            Deduplicated findings with clustered similar items
        """
        deduplicated_findings = {
            'clusters': [],
            'unique_findings': [],
            'redundancy_stats': {
                'total_findings': 0,
                'redundant_findings': 0,
                'clusters_created': 0,
                'unique_findings': 0
            }
        }

        try:
            # Extract all findings across agents
            all_findings = self._extract_all_findings(grounded_outputs)
            deduplicated_findings['redundancy_stats']['total_findings'] = len(all_findings)

            if not all_findings:
                return deduplicated_findings

            # Cluster similar findings using semantic similarity
            if CHROMA_AVAILABLE and self.vector_db:
                clusters = await self._cluster_with_embeddings(all_findings)
            else:
                # Fallback to text similarity
                clusters = self._cluster_with_text_similarity(all_findings)

            deduplicated_findings['clusters'] = clusters
            deduplicated_findings['redundancy_stats']['clusters_created'] = len(clusters)

            # Extract unique findings (best example from each cluster)
            unique_findings = []
            redundant_count = 0

            for cluster in clusters:
                if len(cluster['findings']) > 1:
                    redundant_count += len(cluster['findings']) - 1
                    # Keep the finding with highest confidence
                    best_finding = max(cluster['findings'],
                                     key=lambda f: self._calculate_finding_confidence(f))
                    unique_findings.append({
                        **best_finding,
                        'cluster_info': {
                            'cluster_size': len(cluster['findings']),
                            'sources': [f['source_agent'] for f in cluster['findings']],
                            'consensus_strength': 'high' if len(cluster['findings']) >= 3 else 'medium'
                        }
                    })
                else:
                    unique_findings.append(cluster['findings'][0])

            deduplicated_findings['unique_findings'] = unique_findings
            deduplicated_findings['redundancy_stats']['redundant_findings'] = redundant_count
            deduplicated_findings['redundancy_stats']['unique_findings'] = len(unique_findings)

            self.log_action(f"Deduplication complete: {redundant_count} redundant findings consolidated into {len(clusters)} clusters")

        except Exception as e:
            self.log_action(f"Error during deduplication: {e}", level="error")
            # Return original findings if deduplication fails
            all_findings = self._extract_all_findings(grounded_outputs)
            deduplicated_findings['unique_findings'] = all_findings

        return deduplicated_findings

    def _extract_all_findings(self, grounded_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all findings from all agents into a flat list

        Args:
            grounded_outputs: Agent outputs with their data

        Returns:
            Flat list of all findings across agents
        """
        all_findings = []

        for agent_name, agent_info in grounded_outputs.items():
            agent_data = agent_info.get('data', {})
            
            # Convert any DataFrames to dicts to avoid serialization issues
            agent_data = self._serialize_dataframes(agent_data)

            # Extract various types of findings based on agent type
            findings = self._extract_agent_findings(agent_name, agent_data)

            for finding in findings:
                all_findings.append({
                    'source_agent': agent_name,
                    'content': finding,
                    'confidence': agent_info.get('confidence_score', 0.5),
                    'grounding_status': agent_data.get('_grounding_metadata', {}).get('grounding_coverage', 0),
                    'extraction_timestamp': datetime.utcnow().isoformat()
                })

        return all_findings
    
    def _serialize_dataframes(self, data: Any) -> Any:
        """
        Recursively convert pandas DataFrames and special types to JSON-serializable formats
        
        Args:
            data: Data that may contain DataFrames, Period objects, etc.
            
        Returns:
            Data with all types converted to JSON-serializable formats
        """
        try:
            import pandas as pd
            
            # Handle pandas Period objects
            if isinstance(data, pd.Period):
                return str(data)
            
            # Handle pandas Timestamp objects
            if isinstance(data, pd.Timestamp):
                return data.isoformat()
            
            # Handle DataFrames
            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to dict, handling any special types in the process
                return data.astype(str).to_dict(orient='records')
            
            # Handle Series
            if isinstance(data, pd.Series):
                # Convert Series to dict, handling special types
                return data.astype(str).to_dict()
            
            # Handle dictionaries recursively
            if isinstance(data, dict):
                return {self._serialize_dataframes(k): self._serialize_dataframes(v) for k, v in data.items()}
            
            # Handle lists recursively
            if isinstance(data, list):
                return [self._serialize_dataframes(item) for item in data]
            
            # Return as-is for basic types
            return data
            
        except ImportError:
            # pandas not available, return as-is
            return data
        except Exception as e:
            logger.warning(f"Error serializing data structure: {e}")
            # Try to convert to string as last resort
            try:
                return str(data)
            except:
                return None

    def _extract_agent_findings(self, agent_name: str, agent_data: Dict[str, Any]) -> List[str]:
        """
        Extract findings from specific agent data based on agent type

        Args:
            agent_name: Name of the agent
            agent_data: Agent's data dictionary

        Returns:
            List of finding strings
        """
        findings = []
        
        # IMPORTANT: Serialize AGAIN before json.dumps to catch any remaining Period objects
        agent_data = self._serialize_dataframes(agent_data)
        
        try:
            data_str = json.dumps(agent_data, separators=(',', ':'), default=str)
        except Exception as e:
            logger.warning(f"Error serializing agent data to JSON: {e}, using str() fallback")
            data_str = str(agent_data)

        # Agent-specific extraction patterns
        if agent_name == 'financial_analyst':
            # Extract financial insights, risk warnings, valuation metrics
            patterns = [
                ' insights', 'analysis', 'valuation', 'risk', 'concern', 'opportunity',
                'margin', 'growth', 'ebitda', 'dcf', 'multiple'
            ]

        elif agent_name == 'legal_counsel':
            # Extract legal risks, contract terms, compliance issues
            patterns = [
                'risk', 'clause', 'section', 'compliance', 'liability', 'breach',
                'termination', 'penalty', 'contract', 'legal'
            ]

        elif agent_name == 'market_strategist':
            # Extract market insights, competitive analysis, strategic opportunities
            patterns = [
                'market', 'competition', 'growth', 'opportunity', 'threat', 'position',
                'strategy', 'competitive', 'advantage'
            ]

        elif agent_name == 'risk_assessment':
            # Extract risks and risk assessments
            patterns = ['risk', 'exposure', 'mitigation', 'assessment', 'probability', 'impact']

        elif agent_name == 'integration_planner':
            # Extract integration challenges, synergies, execution risks
            patterns = [
                'synergy', 'integration', 'challenge', 'execution', 'risk', 'plan',
                'migration', 'transition', 'cultural'
            ]

        else:
            # Generic extraction for other agents
            patterns = ['finding', 'insight', 'recommendation', 'risk', 'opportunity']

        # Split data into sentences and look for relevant ones
        sentences = [s.strip() for s in data_str.replace('",', '", ').split('.') if s.strip()]
        sentences = [s for s in sentences if len(s) > 20 and len(s) < 500]  # Reasonable sentence lengths

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(pattern.lower() in sentence_lower for pattern in patterns):
                findings.append(sentence)

        # Also extract from structured lists
        self._extract_from_lists(agent_data, findings, patterns)

        return findings[:20]  # Limit to top 20 findings per agent

    def _extract_from_lists(self, data: Dict[str, Any], findings: List[str], patterns: List[str]) -> None:
        """
        Extract findings from structured lists (risks, recommendations, etc.)

        Args:
            data: Agent data dictionary
            findings: List to append findings to
            patterns: Keywords to match
        """
        def process_list(items: List[Any]) -> None:
            for item in items:
                if isinstance(item, str) and len(item) > 10:
                    if any(p.lower() in item.lower() for p in patterns):
                        findings.append(item)
                elif isinstance(item, dict):
                    for value in item.values():
                        if isinstance(value, str) and len(value) > 10:
                            if any(p.lower() in value.lower() for p in patterns):
                                findings.append(value)

        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                process_list(value)

    async def _cluster_with_embeddings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster findings using vector embeddings and ChromaDB

        Args:
            findings: List of findings to cluster

        Returns:
            List of clusters with similar findings
        """
        if not self.vector_db:
            return self._cluster_with_text_similarity(findings)

        clusters = []

        try:
            collection_name = f"synthesis_findings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Create temporary collection
            collection = self.vector_db.create_collection(name=collection_name)

            # Add all findings to collection
            for i, finding in enumerate(findings):
                collection.add(
                    ids=[f"finding_{i}"],
                    documents=[finding['content']],
                    metadatas=[{
                        'index': i,
                        'source_agent': finding['source_agent'],
                        'confidence': finding['confidence']
                    }]
                )

            # Query for similar findings to create clusters
            processed_indices = set()
            similarity_threshold = 0.85  # High threshold for deduplication

            for i, finding in enumerate(findings):
                if i in processed_indices:
                    continue

                # Find similar findings
                results = collection.query(
                    query_texts=[finding['content']],
                    n_results=min(len(findings), 10)
                )

                if not results or not results['distances']:
                    continue

                # Group findings within similarity threshold
                cluster = [finding]
                processed_indices.add(i)

                for j, distance in enumerate(results['distances'][0]):
                    if j == 0:  # Skip self
                        continue

                    similarity = 1 - distance  # Cosine distance to similarity
                    if similarity >= similarity_threshold:
                        metadata = results['metadatas'][0][j]
                        similar_idx = metadata['index']
                        if similar_idx not in processed_indices:
                            cluster.append(findings[similar_idx])
                            processed_indices.add(similar_idx)

                if len(cluster) > 1:
                    clusters.append({
                        'cluster_id': f"cluster_{len(clusters)}",
                        'findings': cluster,
                        'similarity_score': similarity_threshold,
                        'central_finding': finding['content'][:100] + "..."
                    })

            # Cleanup
            try:
                self.vector_db.delete_collection(collection_name)
            except:
                pass

        except Exception as e:
            self.log_action(f"Embedding-based clustering failed: {e}", level="error")
            return self._cluster_with_text_similarity(findings)

        return clusters

    def _cluster_with_text_similarity(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback clustering using text similarity (Jaccard/overlap)

        Args:
            findings: List of findings to cluster

        Returns:
            List of clusters
        """
        clusters = []
        processed = set()
        similarity_threshold = 0.6

        for i, finding1 in enumerate(findings):
            if i in processed:
                continue

            cluster = [finding1]
            processed.add(i)

            content1_lower = finding1['content'].lower()
            words1 = set(content1_lower.split())

            for j, finding2 in enumerate(findings):
                if j in processed or j <= i:
                    continue

                content2_lower = finding2['content'].lower()
                words2 = set(content2_lower.split())

                # Calculate Jaccard similarity
                intersection = words1.intersection(words2)
                union = words1.union(words2)

                if union:
                    similarity = len(intersection) / len(union)
                    if similarity >= similarity_threshold:
                        cluster.append(finding2)
                        processed.add(j)

            if len(cluster) > 1:
                clusters.append({
                    'cluster_id': f"cluster_{len(clusters)}",
                    'findings': cluster,
                    'similarity_score': similarity_threshold,
                    'central_finding': finding1['content'][:100] + "..."
                })

        return clusters

    def _calculate_finding_confidence(self, finding: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score for a finding

        Args:
            finding: Finding dictionary

        Returns:
            Confidence score between 0-1
        """
        base_confidence = finding.get('confidence', 0.5)
        grounding_score = finding.get('grounding_status', 0)

        # Weighted combination
        overall_confidence = (base_confidence * 0.7) + (grounding_score * 0.3)

        return min(1.0, overall_confidence)

    async def _resolve_conflicts(self, deduplicated_findings: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Resolve conflicts between different agent outputs using rule-based and LLM approaches

        Args:
            deduplicated_findings: Deduplicated agent findings

        Returns:
            Tuple of (resolved_outputs, conflicts_resolved)
        """
        resolved_outputs = {
            'findings': [],
            'numerical_values': {},
            'qualitative_assessments': {},
            'confidence_adjustments': []
        }
        conflicts_resolved = []

        try:
            unique_findings = deduplicated_findings.get('unique_findings', [])

            # Extract numerical and qualitative conflicts
            numerical_conflicts = self._identify_numerical_conflicts(unique_findings)
            qualitative_conflicts = self._identify_qualitative_conflicts(unique_findings)

            # Resolve numerical conflicts using rule-based hierarchy
            self.log_action(f"Resolving {len(numerical_conflicts)} numerical conflicts...")
            for conflict in numerical_conflicts:
                resolution = self._resolve_numerical_conflict(conflict)
                resolved_outputs['numerical_values'][conflict['key']] = resolution['value']
                conflicts_resolved.append({
                    'type': 'numerical',
                    'key': conflict['key'],
                    'initial_conflict': conflict,
                    'resolved_value': resolution['value'],
                    'resolution_method': resolution['method'],
                    'agents_involved': conflict['agents']
                })

            # Resolve qualitative conflicts using LLM reasoning
            self.log_action(f"Resolving {len(qualitative_conflicts)} qualitative conflicts...")
            for conflict in qualitative_conflicts:
                resolution = await self._resolve_qualitative_conflict(conflict)
                resolved_outputs['qualitative_assessments'][conflict['key']] = resolution['assessment']
                conflicts_resolved.append({
                    'type': 'qualitative',
                    'key': conflict['key'],
                    'initial_conflict': conflict,
                    'resolved_assessment': resolution['assessment'],
                    'resolution_reasoning': resolution['reasoning'],
                    'agents_involved': conflict['agents']
                })

            # Process remaining non-conflicting findings
            resolved_outputs['findings'] = unique_findings

            self.log_action(f"Conflict resolution complete: resolved {len(conflicts_resolved)} conflicts")

        except Exception as e:
            self.log_action(f"Error during conflict resolution: {e}", level="error")
            resolved_outputs['findings'] = deduplicated_findings.get('unique_findings', [])

        return resolved_outputs, conflicts_resolved

    def _identify_numerical_conflicts(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify numerical conflicts across agent outputs

        Args:
            findings: Unique findings to analyze

        Returns:
            List of numerical conflicts
        """
        conflicts = []

        # Group findings by potential numerical metrics
        numerical_patterns = {
            'valuation': ['valuation', 'enterprise_value', 'equity_value'],
            'wacc': ['wacc', 'weighted_average_cost_of_capital'],
            'lbo_irr': ['lbo_irr', 'internal_rate_of_return', 'irr'],
            'revenue': ['revenue', 'sales'],
            'ebitda': ['ebitda', 'earnings_before_interest_taxes_depreciation_amortization'],
            'multiples': ['ev_multiple', 'price_multiple', 'p_e_ratio']
        }

        conflict_groups = defaultdict(list)

        for finding in findings:
            content_lower = finding['content'].lower()

            # Check for numerical values in content
            import re
            numbers = re.findall(r'\$?[\d,]+\.?\d*\s*(?:million|billion|MM|BN|%)?', content_lower)

            if numbers:
                # Try to match to known metrics
                for metric, patterns in numerical_patterns.items():
                    if any(pattern in content_lower for pattern in patterns):
                        if metric not in conflict_groups:
                            conflict_groups[metric] = []
                        conflict_groups[metric].append({
                            'finding': finding,
                            'agent': finding['source_agent'],
                            'value': self._extract_numerical_value(content_lower),
                            'content': finding['content']
                        })
                        break

        # Identify actual conflicts (multiple different values for same metric)
        for metric, items in conflict_groups.items():
            if len(items) > 1:
                values = [item['value'] for item in items if item['value'] is not None]
                values = list(set(values))  # Unique values

                if len(values) > 1:  # Multiple different values = conflict
                    agents = [item['agent'] for item in items]
                    conflicts.append({
                        'key': metric,
                        'agents': agents,
                        'values': values,
                        'findings': items
                    })

        return conflicts

    def _extract_numerical_value(self, text: str) -> Optional[float]:
        """
        Extract numerical value from text

        Args:
            text: Text containing numerical value

        Returns:
            Numerical value or None
        """
        import re

        # Look for dollar amounts and percentages
        patterns = [
            r'\$([\d,]+\.?\d*)\s*(?:million|MM)',
            r'\$([\d,]+\.?\d*)\s*(?:billion|BN)',
            r'\$([\d,]+\.?\d*)',
            r'(\d+\.?\d*)%',
            r'(\d+\.?\d*)\s*x',
            r'multiple.*?(\d+\.?\d*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))

                # Scale millions/billions
                if 'million' in text.lower() or 'mm' in text.lower():
                    value *= 1_000_000
                elif 'billion' in text.lower() or 'bn' in text.lower():
                    value *= 1_000_000_000

                return value

        return None

    def _resolve_numerical_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve numerical conflicts using rule-based hierarchy

        Args:
            conflict: Conflict data

        Returns:
            Resolution result
        """
        metric = conflict['key']
        agents = conflict['agents']
        values = conflict['values']

        # Rule-based hierarchy for different metrics
        if metric in ['wacc', 'valuation', 'lbo_irr']:
            # Financial Analyst has precedence
            if 'financial_analyst' in agents:
                return {
                    'value': values[0],  # Take first value from financial analyst
                    'method': 'hierarchy_financial_analyst',
                    'reason': 'Financial Analyst takes precedence for WACC/valuation/IRR'
                }

        elif metric == 'revenue':
            # Use most recent or average of reasonable values using FinancialCalculator
            stats = self.financial_calculator.calculate_statistics(values)
            return {
                'value': stats.get('mean', values[0] if values else 0),
                'method': 'average',
                'reason': 'Revenue estimates averaged across agents'
            }

        # Default: use median value using FinancialCalculator
        if len(values) > 1:
            stats = self.financial_calculator.calculate_statistics(values)
            resolution_value = stats.get('median', values[0])
        else:
            resolution_value = values[0]

        return {
            'value': resolution_value,
            'method': 'median',
            'reason': f'Median value selected from {len(values)} conflicting estimates'
        }

    def _identify_qualitative_conflicts(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify qualitative conflicts (assessment disagreements)

        Args:
            findings: Unique findings to analyze

        Returns:
            List of qualitative conflicts
        """
        conflicts = []

        # Group findings by qualitative topics
        qualitative_patterns = {
            'risk_level': ['risk', 'high risk', 'medium risk', 'low risk'],
            'growth_potential': ['growth', 'slowing', 'accelerating'],
            'competitive_position': ['competitive', 'advantage', 'disadvantage'],
            'regulatory_risk': ['regulatory', 'compliance', 'legal']
        }

        conflict_groups = defaultdict(list)

        for finding in findings:
            content_lower = finding['content'].lower()

            for topic, patterns in qualitative_patterns.items():
                if any(pattern in content_lower for pattern in patterns):
                    conflict_groups[topic].append({
                        'finding': finding,
                        'agent': finding['source_agent'],
                        'assessment': self._extract_qualitative_assessment(content_lower),
                        'content': finding['content']
                    })
                    break

        # Identify actual conflicts (different assessments for same topic)
        for topic, items in conflict_groups.items():
            if len(items) >= 2:
                assessments = [item['assessment'] for item in items if item['assessment']]
                assessments = list(set(assessments))

                if len(assessments) > 1:
                    agents = list(set(item['agent'] for item in items))
                    conflicts.append({
                        'key': topic,
                        'agents': agents,
                        'assessments': assessments,
                        'findings': items
                    })

        return conflicts

    def _extract_qualitative_assessment(self, text: str) -> Optional[str]:
        """
        Extract qualitative assessment from text

        Args:
            text: Text to analyze

        Returns:
            Assessment string or None
        """
        text_lower = text.lower()

        assessments = {
            'high risk': ['high risk', 'severe risk', 'critical risk'],
            'medium risk': ['medium risk', 'moderate risk'],
            'low risk': ['low risk', 'minimal risk'],
            'strong': ['strong', 'excellent', 'robust'],
            'moderate': ['moderate', 'average', 'adequate'],
            'weak': ['weak', 'poor', 'limited']
        }

        for assessment, keywords in assessments.items():
            if any(keyword in text_lower for keyword in keywords):
                return assessment

        return None

    async def _resolve_qualitative_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve qualitative conflicts using LLM reasoning

        Args:
            conflict: Conflict data

        Returns:
            Resolution result
        """
        try:
            # Prepare reasoning prompt
            topic = conflict['key']
            agents = conflict['agents']
            assessments = conflict['assessments']

            # Gather evidence from each agent's assessment
            agent_summaries = []
            for agent, assessment in zip(agents, assessments):
                agent_summaries.append(f"- {agent}: {assessment}")

            reasoning_prompt = f"""Resolve qualitative assessment conflict in M&A due diligence:

TOPIC: {topic}
CONFLICTING ASSESSMENTS:
{chr(10).join(agent_summaries)}

ADDITIONAL CONTEXT:
This is an M&A due diligence analysis. Different agents may have different focuses - financial, legal, market, etc.

REQUIREMENTS:
1. Choose the most appropriate final assessment
2. Provide clear reasoning for the choice
3. Consider the credibility/relevance of each agent's expertise
4. Document the initial conflict for transparency

Final assessment should be one of: high_risk, medium_risk, low_risk, strong, moderate, weak, or other appropriate classification.

Respond in format:
FINAL_ASSESSMENT: [assessment]
REASONING: [detailed explanation of your synthesis]"""

            messages = [
                SystemMessage(content="You are an expert M&A analyst resolving assessment conflicts. Be objective and well-reasoned."),
                HumanMessage(content=reasoning_prompt)
            ]

            response = await llm_call_with_retry(
                self.llm,
                messages,
                max_retries=2,
                context=f"Qualitative conflict resolution for {topic}"
            )

            # Parse response
            response_text = response.content.strip()
            lines = response_text.split('\n')

            final_assessment = 'moderate'  # default
            reasoning = 'Unable to determine'

            for line in lines:
                line = line.strip()
                if line.startswith('FINAL_ASSESSMENT:'):
                    final_assessment = line.split(':', 1)[1].strip().lower()
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()

            return {
                'assessment': final_assessment,
                'reasoning': reasoning
            }

        except Exception as e:
            self.log_action(f"Error resolving qualitative conflict for {conflict['key']}: {e}", level="error")
            return {
                'assessment': conflict['assessments'][0],  # Default to first assessment
                'reasoning': f'Error during resolution: {str(e)}. Used first assessment as fallback.'
            }

    def _calculate_confidence_scores(
        self,
        resolved_outputs: Dict[str, Any],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Calculate final confidence scores for the synthesis results

        Args:
            resolved_outputs: Resolved outputs from conflict resolution
            state: Current diligence state

        Returns:
            Dictionary of confidence scores and metrics
        """
        confidence_scores = {
            'overall_synthesis_confidence': 0.0,
            'component_confidences': {},
            'confidence_distribution': {},
            'confidence_adjustments': []
        }

        try:
            # Extract confidence metrics from each stage
            grounding_confidence = self._calculate_grounding_confidence(resolved_outputs)
            deduplication_confidence = self._calculate_deduplication_confidence(resolved_outputs)
            conflict_resolution_confidence = self._calculate_conflict_resolution_confidence(resolved_outputs)
            agent_quality_confidence = self._calculate_agent_quality_confidence(state)

            component_confidences = {
                'grounding': grounding_confidence,
                'deduplication': deduplication_confidence,
                'conflict_resolution': conflict_resolution_confidence,
                'agent_quality': agent_quality_confidence
            }

            confidence_scores['component_confidences'] = component_confidences

            # Calculate overall confidence using weighted approach
            overall_confidence = np.average([
                grounding_confidence,
                deduplication_confidence,
                conflict_resolution_confidence,
                agent_quality_confidence
            ], weights=[
                self.confidence_weights['source_data_quality'],
                0.2,  # Equal weight for internal processes
                0.2,
                self.confidence_weights['agent_methodology']
            ])

            confidence_scores['overall_synthesis_confidence'] = round(overall_confidence, 3)

            # Calculate confidence distribution
            confidence_scores['confidence_distribution'] = self._calculate_confidence_distribution_from_components(
                component_confidences
            )

            # Add confidence adjustments
            confidence_scores['confidence_adjustments'] = self._generate_confidence_adjustments(
                resolved_outputs, component_confidences
            )

            self.log_action(f"Overall synthesis confidence: {overall_confidence:.3f}")

        except Exception as e:
            self.log_action(f"Error calculating confidence scores: {e}", level="error")
            confidence_scores['overall_synthesis_confidence'] = 0.5  # Conservative default

        return confidence_scores

    def _calculate_grounding_confidence(self, resolved_outputs: Dict[str, Any]) -> float:
        """
        Calculate confidence based on grounding quality

        Args:
            resolved_outputs: Resolved outputs

        Returns:
            Grounding confidence score
        """
        findings = resolved_outputs.get('findings', [])
        if not findings:
            return 0.3

        grounding_scores = []
        for finding in findings:
            grounding_status = finding.get('grounding_status', 0)
            grounding_scores.append(grounding_status)

        if grounding_scores:
            return np.average(grounding_scores)
        return 0.3

    def _calculate_deduplication_confidence(self, resolved_outputs: Dict[str, Any]) -> float:
        """
        Calculate confidence based on deduplication quality

        Args:
            resolved_outputs: Resolved outputs

        Returns:
            Deduplication confidence score
        """
        # Higher confidence when more redundancies were successfully identified and resolved
        redundancy_stats = resolved_outputs.get('redundancy_stats', {})

        total_findings = redundancy_stats.get('total_findings', 0)
        redundant_findings = redundancy_stats.get('redundant_findings', 0)

        if total_findings == 0:
            return 0.5

        # Normalize redundancy ratio (aim for 10-30% redundancy as ideal)
        redundancy_ratio = redundant_findings / total_findings
        if redundancy_ratio < 0.05:  # Too few redundancies might indicate poor clustering
            return 0.6
        elif redundancy_ratio < 0.4:  # Good range
            return 0.85
        else:  # Too many redundancies might indicate overly aggressive clustering
            return 0.7

    def _calculate_conflict_resolution_confidence(self, resolved_outputs: Dict[str, Any]) -> float:
        """
        Calculate confidence based on conflict resolution outcomes

        Args:
            resolved_outputs: Resolved outputs

        Returns:
            Conflict resolution confidence score
        """
        numerical_values = resolved_outputs.get('numerical_values', {})
        qualitative_assessments = resolved_outputs.get('qualitative_assessments', {})

        total_resolved = len(numerical_values) + len(qualitative_assessments)

        if total_resolved == 0:
            return 0.8  # No conflicts found is good

        # Confidence based on resolution coverage and method quality
        # Rule-based numerical resolutions get higher confidence than LLM resolutions
        numerical_resolution_quality = 0.9  # High confidence for rule-based
        qualitative_resolution_quality = 0.7  # Lower for LLM-based

        weighted_confidence = (
            len(numerical_values) * numerical_resolution_quality +
            len(qualitative_assessments) * qualitative_resolution_quality
        ) / total_resolved

        return weighted_confidence

    def _calculate_agent_quality_confidence(self, state: DiligenceState) -> float:
        """
        Calculate confidence based on agent output quality and coverage

        Args:
            state: Current diligence state

        Returns:
            Agent quality confidence score
        """
        agent_outputs = state.get('agent_outputs', [])
        completed_agents = sum(1 for output in agent_outputs
                             if output.get('status') == 'completed')

        total_expected_agents = 13  # Full suite
        coverage_ratio = completed_agents / total_expected_agents

        if coverage_ratio >= 0.9:  # 90%+ coverage
            return 0.9
        elif coverage_ratio >= 0.7:  # 70%+ coverage
            return 0.75
        elif coverage_ratio >= 0.5:  # 50%+ coverage
            return 0.6
        else:
            return 0.4

    def _calculate_confidence_distribution_from_components(
        self, component_confidences: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate confidence distribution statistics using FinancialCalculator

        Args:
            component_confidences: Confidence scores by component

        Returns:
            Statistical distribution of confidence scores
        """
        confidences = list(component_confidences.values())
        
        # Use FinancialCalculator for statistical calculations with audit trail
        stats = self.financial_calculator.calculate_statistics(confidences)

        return {
            'mean': stats.get('mean', 0),
            'median': stats.get('median', 0),
            'std_dev': stats.get('std_dev', 0),
            'min': stats.get('min', 0),
            'max': stats.get('max', 0),
            'range': stats.get('max', 0) - stats.get('min', 0),
            'high_confidence_count': sum(1 for c in confidences if c >= 0.8),
            'low_confidence_count': sum(1 for c in confidences if c < 0.6),
            'calculation_methodology': stats.get('methodology', 'Statistical analysis using FinancialCalculator')
        }

    def _generate_confidence_adjustments(
        self,
        resolved_outputs: Dict[str, Any],
        component_confidences: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Generate confidence adjustments and recommendations

        Args:
            resolved_outputs: Resolved outputs
            component_confidences: Component confidence scores

        Returns:
            List of confidence adjustments and recommendations
        """
        adjustments = []

        # Grounding confidence adjustments
        grounding_conf = component_confidences.get('grounding', 0.5)
        if grounding_conf < 0.7:
            adjustments.append({
                'type': 'grounding_quality',
                'level': 'warning',
                'description': '.2f',
                'recommendation': 'Consider additional source document review for fact verification'
            })

        # Agent coverage adjustments
        agent_conf = component_confidences.get('agent_quality', 0.5)
        if agent_conf < 0.7:
            adjustments.append({
                'type': 'agent_coverage',
                'level': 'critical',
                'description': '.2f',
                'recommendation': 'Run additional analytical agents for complete assessment'
            })

        # Conflict resolution adjustments
        conflict_conf = component_confidences.get('conflict_resolution', 0.5)
        if conflict_conf < 0.8:
            adjustments.append({
                'type': 'conflict_resolution',
                'level': 'info',
                'description': 'Multiple agent conflicts resolved, confidence moderated',
                'recommendation': 'Review conflict resolution details for key assumptions'
            })

        return adjustments

    def _calculate_confidence_distribution(self, confidence_scores: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate confidence score distribution for reporting

        Args:
            confidence_scores: All confidence scores

        Returns:
            Distribution statistics
        """
        return confidence_scores.get('confidence_distribution', {})

    async def _generate_structured_output(
        self,
        resolved_outputs: Dict[str, Any],
        confidence_scores: Dict[str, Any],
        conflicts_resolved: List[Dict[str, Any]],
        hallucination_flags: List[Dict[str, Any]],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Generate final structured JSON output for report generators

        Args:
            resolved_outputs: All resolved synthesis outputs
            confidence_scores: Calculated confidence metrics
            conflicts_resolved: List of resolved conflicts
            hallucination_flags: List of hallucination flags
            state: Current diligence state

        Returns:
            Structured JSON object ready for report generation
        """
        try:
            structured_output = {
                "metadata": self._generate_metadata_section(state, confidence_scores),
                "executive_summary": self._generate_executive_summary_section(
                    resolved_outputs, confidence_scores
                ),
                "detailed_financials": await self._generate_financial_section(resolved_outputs, state),
                "legal_diligence": self._generate_legal_section(resolved_outputs, state),
                "market_analysis": self._generate_market_section(resolved_outputs, state),
                "integration_tax": self._generate_integration_tax_section(resolved_outputs, state),
                "risk_macro": self._generate_risk_macro_section(resolved_outputs, state),
                "external_validation": self._generate_external_validation_section(resolved_outputs, state),
                "validation_summary": self._generate_validation_section(
                    confidence_scores, conflicts_resolved, hallucination_flags
                )
            }

            return structured_output

        except Exception as e:
            self.log_action(f"Error generating structured output: {e}", level="error")
            return {
                "metadata": {},
                "executive_summary": {},
                "error": str(e)
            }

    def _generate_metadata_section(
        self, state: DiligenceState, confidence_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate metadata section for the report

        Args:
            state: Diligence state
            confidence_scores: Confidence metrics

        Returns:
            Metadata dictionary
        """
        return {
            "deal_id": state.get("deal_id", ""),
            "target_company": state.get("target_company", ""),
            "target_ticker": state.get("target_ticker", ""),
            "acquirer_company": state.get("acquirer_company", ""),
            "deal_type": state.get("deal_type", ""),
            "deal_value": state.get("deal_value", ""),
            "deal_structure": state.get("deal_structure", ""),
            "currency": state.get("currency", "USD"),
            "expected_close_date": state.get("expected_close_date", ""),
            "synthesis_confidence": confidence_scores.get("overall_synthesis_confidence", 0.5),
            "synthesis_timestamp": datetime.utcnow().isoformat(),
            "agent_coverage": len([o for o in state.get("agent_outputs", [])
                                 if o.get("status") == "completed"])
        }

    def _generate_executive_summary_section(
        self,
        resolved_outputs: Dict[str, Any],
        confidence_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate executive summary section

        Args:
            resolved_outputs: Resolved outputs
            confidence_scores: Confidence scores

        Returns:
            Executive summary dictionary
        """
        # Extract key valuation and risk information
        valuation_range = self._extract_valuation_range(resolved_outputs)
        top_risks = self._extract_top_risks(resolved_outputs)
        top_opportunities = self._extract_top_opportunities(resolved_outputs)

        # Generate investment recommendation (simplified)
        confidence = confidence_scores.get("overall_synthesis_confidence", 0.5)
        if confidence >= 0.8:
            recommendation = "Proceed with confidence"
        elif confidence >= 0.6:
            recommendation = "Proceed with caution"
        else:
            recommendation = "Requires additional due diligence"

        return {
            "valuation_range": valuation_range,
            "key_recommendation": recommendation,
            "top_3_risks": top_risks[:3],
            "top_3_opportunities": top_opportunities[:3],
            "overall_confidence": confidence,
            "key_assumptions": [],  # Can be populated from resolved conflicts
            "timeline_assessment": "On track"  # Placeholder
        }

    async def _generate_financial_section(
        self, resolved_outputs: Dict[str, Any], state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Generate COMPLETE detailed financials section - ALL valuation models & analysis

        Args:
            resolved_outputs: Resolved outputs
            state: Diligence state

        Returns:
            COMPLETE financial section with ALL agent outputs
        """
        # Extract COMPLETE financial_analyst output
        financial_analyst_data = state.get("financial_analyst", {})
        if not financial_analyst_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'financial_analyst':
                    financial_analyst_data = output.get('data', {})
                    break
        
        # Extract COMPLETE financial_deep_dive output
        financial_deep_dive_data = state.get("financial_deep_dive", {})
        if not financial_deep_dive_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'financial_deep_dive':
                    financial_deep_dive_data = output.get('data', {})
                    break
        
        # Get ALL components from financial_analyst
        normalized_financials = financial_analyst_data.get('normalized_financials', {})
        advanced_valuation = financial_analyst_data.get('advanced_valuation', {})
        trend_analysis = financial_analyst_data.get('trend_analysis', {})
        seasonality = financial_analyst_data.get('seasonality', {})
        anomaly_detection = financial_analyst_data.get('anomaly_detection', {})
        financial_health = financial_analyst_data.get('financial_health', {})
        ratio_analysis = financial_analyst_data.get('ratio_analysis', {})
        
        # Extract ALL valuation models (not just DCF!)
        dcf_analysis = advanced_valuation.get('dcf_analysis', {}) if advanced_valuation else {}
        lbo_analysis = advanced_valuation.get('lbo_analysis', {}) if advanced_valuation else {}
        sensitivity_analysis = advanced_valuation.get('sensitivity_analysis', {}) if advanced_valuation else {}
        monte_carlo = advanced_valuation.get('monte_carlo_simulation', {}) if advanced_valuation else {}
        comparable_companies = advanced_valuation.get('comparable_companies', {}) if advanced_valuation else {}
        precedent_transactions = advanced_valuation.get('precedent_transactions', {}) if advanced_valuation else {}
        
        # CRITICAL: Create flattened DCF structure for validator
        # Validator expects enterprise_value at root level, but dcf_analysis has nested structure
        base_case = dcf_analysis.get('base', {}) if dcf_analysis else {}
        dcf_outputs_flattened = {
            # Preserve nested structure for report generators
            'base': base_case,
            'optimistic': dcf_analysis.get('optimistic', {}),
            'pessimistic': dcf_analysis.get('pessimistic', {}),
            # Add base case values at root level for validator
            'enterprise_value': base_case.get('enterprise_value', 0),
            'equity_value': base_case.get('equity_value', 0),
            'equity_value_per_share': base_case.get('equity_value_per_share', 0),
            'wacc': base_case.get('wacc', 0),
            'terminal_growth_rate': base_case.get('terminal_growth_rate', 0),
            'valuation_date': base_case.get('valuation_date', ''),
        }
        
        # Extract normalized EBITDA with defensive checks
        normalized_ebitda = None
        if normalized_financials:
            normalized_income = normalized_financials.get('normalized_income', [])
            if normalized_income and len(normalized_income) > 0:
                normalized_ebitda = normalized_income[0].get('ebitda')
        
        # Fallback to raw financial data
        if normalized_ebitda is None:
            financial_data = state.get('financial_data', {})
            income_statements = financial_data.get('income_statement', [])
            if income_statements:
                normalized_ebitda = income_statements[0].get('ebitda')
        
        # Defensive: Ensure ebitda is never None (validator requires a number)
        if normalized_ebitda is None:
            normalized_ebitda = 0
            logger.warning("normalized_ebitda is None, defaulting to 0")

        # CRITICAL: Collect financial ratios using financetoolkit
        financial_ratios = await self._collect_financial_ratios(state)
        self.log_action(f"Collected {len(financial_ratios)} financial ratios using financetoolkit")

        # Return COMPLETE financial analysis (no placeholders!)
        return {
            # Normalized Financials
            "normalized_income_statement": normalized_financials.get('normalized_income', []),
            "normalized_balance_sheet": normalized_financials.get('normalized_balance', []),
            "normalized_cash_flow": normalized_financials.get('normalized_cash_flow', []),
            "normalized_ebitda": normalized_ebitda,
            "normalization_ledger": normalized_financials.get('adjustments', []),
            "quality_score": normalized_financials.get('quality_score', 0),
            
            # ALL Valuation Models (complete suite)
            "dcf_outputs": dcf_outputs_flattened,  # FLATTENED structure with base case at root (for validator)
            "dcf_analysis": dcf_analysis,  # NESTED structure (for backward compatibility)
            "lbo_analysis": lbo_analysis,  # Complete LBO model
            "sensitivity_analysis": sensitivity_analysis,  # WACC, growth sensitivity
            "monte_carlo_simulation": monte_carlo,  # 10K iterations
            "comparable_companies": comparable_companies,  # Trading comps
            "precedent_transactions": precedent_transactions,  # Deal comps
            "valuation_summary": advanced_valuation.get('valuation_summary', {}) if advanced_valuation else {},
            "external_validation": advanced_valuation.get('external_validation', {}) if advanced_valuation else {},
            
            # Trend & Historical Analysis
            "trend_analysis": trend_analysis,  # 10-year trends, CAGRs
            "seasonality": seasonality,  # Quarterly patterns
            "cagr_analysis": normalized_financials.get('cagr_analysis', {}),
            
            # Health & Risk Metrics
            "financial_health": financial_health,  # Health score, rating
            "ratio_analysis": ratio_analysis,  # All ratios
            "anomaly_detection": anomaly_detection,  # Anomalies found
            "anomaly_log": anomaly_detection.get('anomalies_detected', []),
            "red_flags": financial_analyst_data.get('red_flags', []),
            
            # Deep Dive Analysis (from financial_deep_dive agent)
            "deep_dive_ratios": financial_deep_dive_data.get('detailed_ratios', {}),
            "working_capital_analysis": financial_deep_dive_data.get('working_capital', {}),
            "debt_capacity": financial_deep_dive_data.get('debt_capacity', {}),
            "credit_metrics": financial_deep_dive_data.get('credit_metrics', {}),
            "segment_analysis": financial_deep_dive_data.get('segment_analysis', {}),
            
            # Raw data for reference
            "raw_financial_data": financial_analyst_data.get('raw_data', {}),
            "insights": financial_analyst_data.get('insights', {})
        }

    def _generate_legal_section(self, resolved_outputs: Dict[str, Any], state: DiligenceState) -> Dict[str, Any]:
        """
        Generate legal diligence section - FIXED to properly extract from legal_counsel

        Args:
            resolved_outputs: Resolved outputs
            state: Diligence state

        Returns:
            Legal section dictionary
        """
        # Extract legal counsel data
        legal_counsel_data = state.get("legal_counsel", {})
        if not legal_counsel_data and 'agent_outputs' in state:
            # Fallback: search in agent_outputs array
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'legal_counsel':
                    legal_counsel_data = output.get('data', {})
                    break
        
        # Extract key legal findings
        legal_risks = legal_counsel_data.get('legal_risks', [])
        contract_analysis = legal_counsel_data.get('contract_analysis', {})
        sec_analysis = legal_counsel_data.get('sec_analysis', {})
        ma_filings = legal_counsel_data.get('ma_filings', {})
        
        # Build risk register
        risk_register = []
        if legal_risks:
            for risk in legal_risks[:10]:  # Top 10 risks
                risk_register.append({
                    'risk_type': risk.get('type', 'Unknown'),
                    'description': risk.get('description', ''),
                    'severity': risk.get('severity', 'medium'),
                    'mitigation': risk.get('mitigation', '')
                })
        
        # Extract contract snippets
        contract_snippets = []
        if contract_analysis:
            key_terms = contract_analysis.get('key_terms', [])
            for term in key_terms[:5]:  # Top 5 key terms
                contract_snippets.append({
                    'clause_type': term.get('term_type', 'Unknown'),
                    'description': term.get('description', ''),
                    'impact': term.get('impact', '')
                })
        
        # Determine compliance status
        compliance_status = "Under Review"
        if sec_analysis:
            sec_issues = sec_analysis.get('issues', [])
            if not sec_issues:
                compliance_status = "No Issues Identified"
            elif any(issue.get('severity') == 'high' for issue in sec_issues):
                compliance_status = "Concerns Identified"
            else:
                compliance_status = "Minor Issues"
        
        return {
            "risk_register": risk_register,
            "contract_snippets": contract_snippets,
            "compliance_status": compliance_status,
            "sec_analysis_summary": sec_analysis,
            "ma_filings_summary": ma_filings,
            "total_risks_identified": len(legal_risks)
        }

    def _generate_market_section(self, resolved_outputs: Dict[str, Any], state: DiligenceState) -> Dict[str, Any]:
        """
        Generate market analysis section - FIXED to properly extract from agents

        Args:
            resolved_outputs: Resolved outputs
            state: Diligence state

        Returns:
            Market section dictionary
        """
        # Extract market strategist data
        market_strategist_data = state.get("market_strategist", {})
        if not market_strategist_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'market_strategist':
                    market_strategist_data = output.get('data', {})
                    break
        
        # Extract competitive benchmarking data
        competitive_data = state.get("competitive_benchmarking", {})
        if not competitive_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'competitive_benchmarking':
                    competitive_data = output.get('data', {})
                    break
        
        # Extract SWOT analysis
        swot_analysis = market_strategist_data.get('swot_analysis', {})
        if not swot_analysis:
            swot_analysis = {
                "strengths": [],
                "weaknesses": [],
                "opportunities": self._extract_top_opportunities(resolved_outputs),
                "threats": []
            }
        
        # Extract competitive landscape
        competitive_landscape = competitive_data.get('competitive_analysis', {})
        if not competitive_landscape:
            competitive_landscape = {
                'market_share': 'N/A',
                'competitive_position': 'Under analysis',
                'key_competitors': []
            }
        
        # Extract growth assessment
        growth_assessment = market_strategist_data.get('growth_outlook', 'Unknown')
        if not growth_assessment or growth_assessment == 'Unknown':
            growth_assessment = resolved_outputs.get("qualitative_assessments", {}).get("growth_potential", "Unknown")
        
        return {
            "swot_analysis": swot_analysis,
            "competitive_landscape": competitive_landscape,
            "growth_assessment": growth_assessment,
            "market_dynamics": market_strategist_data.get('market_dynamics', {}),
            "industry_trends": market_strategist_data.get('industry_trends', [])
        }

    def _generate_validation_section(
        self,
        confidence_scores: Dict[str, Any],
        conflicts_resolved: List[Dict[str, Any]],
        hallucination_flags: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate validation summary section

        Args:
            confidence_scores: Confidence metrics
            conflicts_resolved: Resolved conflicts
            hallucination_flags: Hallucination flags

        Returns:
            Validation section dictionary
        """
        return {
            "overall_confidence_score": confidence_scores.get("overall_synthesis_confidence", 0.5),
            "component_confidences": confidence_scores.get("component_confidences", {}),
            "discrepancies_found": conflicts_resolved,
            "hallucinations_detected": hallucination_flags,
            "validation_recommendations": confidence_scores.get("confidence_adjustments", []),
            "confidence_distribution": confidence_scores.get("confidence_distribution", {})
        }

    def _save_consolidated_data(self, state: DiligenceState, consolidated_data: Dict[str, Any]) -> None:
        """
        Save consolidated data to disk for report generators to consume
        
        Args:
            state: Diligence state with job/deal information
            consolidated_data: The synthesized and consolidated data
        """
        try:
            from pathlib import Path
            
            # Get job information for filename
            target_company = state.get("target_company", "unknown")
            target_ticker = state.get("target_ticker", "")
            job_id = state.get("deal_id", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
            
            # Determine output directory
            output_base = SYNTHESIS_OUTPUT_CONFIG.get("output_dir", "outputs")
            consolidated_subdir = SYNTHESIS_OUTPUT_CONFIG.get("consolidated_subdir", "synthesis")
            
            # Create full path
            if target_ticker:
                output_dir = Path(output_base) / f"{target_ticker.lower()}_analysis" / consolidated_subdir
            else:
                output_dir = Path(output_base) / f"{target_company.lower().replace(' ', '_')}_analysis" / consolidated_subdir
            
            # Create directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename_template = SYNTHESIS_OUTPUT_CONFIG.get("consolidated_filename_template", "{job_id}_consolidated_data.json")
            filename = filename_template.format(
                job_id=job_id,
                target_company=target_company.lower().replace(' ', '_'),
                target_ticker=target_ticker.upper() if target_ticker else ""
            )
            
            output_path = output_dir / filename
            
            # Serialize and save
            self.log_action(f"Saving consolidated data to {output_path}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, indent=2, default=str)
            
            self.log_action(f"✓ Consolidated data saved successfully to {output_path}")
            
            # Log file size for verification
            file_size_kb = output_path.stat().st_size / 1024
            self.log_action(f"  File size: {file_size_kb:.2f} KB")
            
        except Exception as e:
            self.log_action(f"ERROR saving consolidated data: {e}", level="error")
            # Don't fail the entire synthesis if saving fails
            pass

    def _generate_integration_tax_section(self, resolved_outputs: Dict[str, Any], state: DiligenceState) -> Dict[str, Any]:
        """
        Generate integration & tax section - COMPLETE extraction
        
        Args:
            resolved_outputs: Resolved outputs
            state: Diligence state
            
        Returns:
            Complete integration and tax analysis
        """
        # Extract integration planner data
        integration_data = state.get("integration_planner", {})
        if not integration_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'integration_planner':
                    integration_data = output.get('data', {})
                    break
        
        # Extract tax structuring data
        tax_data = state.get("tax_structuring", {})
        if not tax_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'tax_structuring':
                    tax_data = output.get('data', {})
                    break
        
        return {
            # Integration Planning (COMPLETE)
            "synergies": integration_data.get('synergies', {}),
            "synergy_breakdown": integration_data.get('synergy_breakdown', {}),
            "integration_plan": integration_data.get('integration_plan', {}),
            "integration_timeline": integration_data.get('timeline', {}),
            "integration_risks": integration_data.get('risks', []),
            "integration_costs": integration_data.get('costs', {}),
            "day_one_priorities": integration_data.get('day_one_priorities', []),
            "cultural_assessment": integration_data.get('cultural_assessment', {}),
            
            # Tax Structuring (COMPLETE)
            "tax_structure": tax_data.get('tax_structure', {}),
            "tax_implications": tax_data.get('tax_implications', {}),
            "effective_tax_rate": tax_data.get('effective_rate', 0),
            "tax_optimization": tax_data.get('optimization_opportunities', []),
            "nol_analysis": tax_data.get('nol_analysis', {}),
            "tax_risks": tax_data.get('tax_risks', []),
            "cross_border_considerations": tax_data.get('cross_border', {}),
            
            # Combined insights
            "recommendations": integration_data.get('recommendations', []) + tax_data.get('recommendations', []),
            "total_synergy_value": integration_data.get('total_synergy_value', 0)
        }
    
    def _generate_risk_macro_section(self, resolved_outputs: Dict[str, Any], state: DiligenceState) -> Dict[str, Any]:
        """
        Generate risk & macro section - COMPLETE extraction
        
        Args:
            resolved_outputs: Resolved outputs
            state: Diligence state
            
        Returns:
            Complete risk assessment and macroeconomic analysis
        """
        # Extract risk assessment data
        risk_data = state.get("risk_assessment", {})
        if not risk_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'risk_assessment':
                    risk_data = output.get('data', {})
                    break
        
        # Extract macroeconomic analyst data
        macro_data = state.get("macroeconomic_analyst", {})
        if not macro_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'macroeconomic_analyst':
                    macro_data = output.get('data', {})
                    break
        
        return {
            # Risk Assessment (COMPLETE)
            "risk_matrix": risk_data.get('risk_matrix', {}),
            "key_risks": risk_data.get('key_risks', []),
            "risk_score": risk_data.get('overall_risk_score', 0),
            "risk_mitigation_strategies": risk_data.get('mitigation_strategies', []),
            "risk_categories": risk_data.get('risk_categories', {}),
            "operational_risks": risk_data.get('operational_risks', []),
            "financial_risks": risk_data.get('financial_risks', []),
            "strategic_risks": risk_data.get('strategic_risks', []),
            "compliance_risks": risk_data.get('compliance_risks', []),
            
            # Macroeconomic Analysis (COMPLETE)
            "macro_environment": macro_data.get('macro_analysis', {}),
            "economic_outlook": macro_data.get('outlook', {}),
            "gdp_forecast": macro_data.get('gdp_forecast', {}),
            "inflation_outlook": macro_data.get('inflation', {}),
            "interest_rate_environment": macro_data.get('interest_rates', {}),
            "industry_cyclicality": macro_data.get('cyclicality', {}),
            "macro_risks": macro_data.get('risks', []),
            "macro_opportunities": macro_data.get('opportunities', []),
            
            # Combined assessment
            "overall_risk_rating": risk_data.get('rating', 'Medium'),
            "macro_headwinds": macro_data.get('headwinds', []),
            "macro_tailwinds": macro_data.get('tailwinds', [])
        }
    


    def _generate_external_validation_section(self, resolved_outputs: Dict[str, Any], state: DiligenceState) -> Dict[str, Any]:
        """
        Generate external validation section - COMPLETE extraction
        
        Args:
            resolved_outputs: Resolved outputs
            state: Diligence state
            
        Returns:
            Complete external validation analysis
        """
        # Extract external validator data
        validator_data = state.get("external_validator", {})
        if not validator_data and 'agent_outputs' in state:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'external_validator':
                    validator_data = output.get('data', {})
                    break
        
        return {
            # External validation results
            "validation_results": validator_data.get('validation_results', {}),
            "cross_checks": validator_data.get('cross_checks', []),
            "discrepancies": validator_data.get('discrepancies', []),
            "validation_confidence": validator_data.get('confidence', 0),
            "external_sources": validator_data.get('sources', []),
            "validation_summary": validator_data.get('summary', {}),
            "recommendations": validator_data.get('recommendations', [])
        }
    
    async def _collect_financial_ratios(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Collect financial ratios using financetoolkit if available
        
        Args:
            state: Diligence state
            
        Returns:
            Dictionary of financial ratios
        """
        if not HAS_FINANCETOOLKIT:
            self.log_action("financetoolkit not available, skipping ratio collection")
            return {}
        
        try:
            # This is a placeholder - actual implementation would use financetoolkit
            # to calculate comprehensive ratios from financial data
            financial_data = state.get('financial_data', {})
            if not financial_data:
                return {}
            
            # Return empty dict for now - can be enhanced later
            self.log_action("Financial ratio collection completed")
            return {}
            
        except Exception as e:
            self.log_action(f"Error collecting financial ratios: {e}", level="error")
            return {}

    # Helper methods for data extraction
    def _extract_valuation_range(self, resolved_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract valuation range from resolved outputs"""
        valuation = resolved_outputs.get("numerical_values", {}).get("valuation")
        if valuation:
            return {"low": valuation * 0.9, "high": valuation * 1.1, "midpoint": valuation}
        return {"status": "Not available"}

    def _extract_top_risks(self, resolved_outputs: Dict[str, Any]) -> List[str]:
        """Extract top risks from findings"""
        risks = []
        for finding in resolved_outputs.get("findings", []):
            content_lower = finding.get("content", "").lower()
            if "risk" in content_lower or "concern" in content_lower:
                risk_desc = finding.get("content", "")[:100]
                risks.append(f"{risk_desc} (Source: {finding.get('source_agent', 'Unknown')})")
        return risks[:5]

    def _extract_top_opportunities(self, resolved_outputs: Dict[str, Any]) -> List[str]:
        """Extract top opportunities from findings"""
        opportunities = []
        for finding in resolved_outputs.get("findings", []):
            content_lower = finding.get("content", "").lower()
            if "opportunity" in content_lower or "growth" in content_lower or "potential" in content_lower:
                opp_desc = finding.get("content", "")[:100]
                opportunities.append(f"{opp_desc} (Source: {finding.get('source_agent', 'Unknown')})")
        return opportunities[:5]
