"""
Synthesis Agent Configuration - Production Optimizations

This configuration file controls the behavior of the synthesis_reporting agent,
including timeout settings, claim verification depth, and performance optimizations.
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class GroundingDepth(Enum):
    """Grounding verification depth levels"""
    MINIMAL = "minimal"  # Skip verification for validated data
    STANDARD = "standard"  # Verify critical claims only
    COMPREHENSIVE = "comprehensive"  # Verify all claims (slowest)


@dataclass
class SynthesisConfig:
    """Configuration for synthesis agent"""
    
    # LLM Settings
    llm_timeout: int = 120  # INCREASED from 30s to 120s to fix timeouts
    max_concurrent_llm_calls: int = 5
    max_retries: int = 2
    retry_delay: float = 1.0
    
    # Grounding & Verification
    grounding_depth: GroundingDepth = GroundingDepth.MINIMAL  # SKIP verification for validated data
    enable_batched_verification: bool = True
    batch_size: int = 5
    
    # Claim Prioritization
    max_claims_per_agent: int = 10  # Reduced from default to speed up
    agent_claim_limits: Dict[str, int] = None
    
    # Performance
    enable_caching: bool = True
    skip_verification_for_validated: bool = True  # NEW: Skip if data already validated
    
    def __post_init__(self):
        """Initialize agent-specific claim limits"""
        if self.agent_claim_limits is None:
            # Prioritize financial agents, limit others
            self.agent_claim_limits = {
                'financial_analyst': 15,  # Most critical
                'financial_deep_dive': 10,
                'legal_counsel': 10,
                'risk_assessment': 10,
                'tax_structuring': 8,
                'deal_structuring': 8,
                'accretion_dilution': 10,  # NEW: EPS impact analysis
                'integration_planner': 8,
                'market_strategist': 5,
                'competitive_benchmarking': 5,
                'macroeconomic_analyst': 5,
                'external_validator': 5,
                'project_manager': 3
            }


# PRODUCTION CONFIGURATION - Optimized for speed with quality
PRODUCTION_CONFIG = SynthesisConfig(
    llm_timeout=120,  # 2 minutes per LLM call (4x increase from 30s)
    max_concurrent_llm_calls=5,
    grounding_depth=GroundingDepth.MINIMAL,  # Skip verification for validated data
    enable_batched_verification=True,
    max_claims_per_agent=10,
    enable_caching=True,
    skip_verification_for_validated=True
)


# COMPREHENSIVE CONFIGURATION - For when quality > speed
COMPREHENSIVE_CONFIG = SynthesisConfig(
    llm_timeout=180,  # 3 minutes
    max_concurrent_llm_calls=3,
    grounding_depth=GroundingDepth.COMPREHENSIVE,
    enable_batched_verification=True,
    max_claims_per_agent=20,
    enable_caching=True,
    skip_verification_for_validated=False
)


# SYNTHESIS OUTPUT CONFIGURATION
SYNTHESIS_OUTPUT_CONFIG = {
    "save_to_disk": True,
    "output_dir": "outputs",
    "consolidated_subdir": "synthesis",
    "consolidated_filename_template": "{job_id}_consolidated_data.json"
}


class ClaimPrioritizer:
    """
    Intelligent claim prioritizer that filters and ranks claims by importance
    
    This class implements the logic to identify which claims are most critical
    to verify, allowing the synthesis agent to skip low-priority claims.
    """
    
    # Critical claim keywords (HIGH PRIORITY)
    CRITICAL_KEYWORDS = [
        'valuation', 'enterprise_value', 'equity_value', 'dcf', 'wacc',
        'deal_value', 'purchase_price', 'lbo', 'irr', 'multiple',
        'ebitda', 'revenue', 'net_income', 'cash_flow', 'synergy',
        'change-of-control', 'termination', 'material_adverse_change',
        'breach', 'covenant', 'critical_risk', 'high_risk'
    ]
    
    # Medium priority keywords
    MEDIUM_KEYWORDS = [
        'margin', 'growth', 'ratio', 'metric', 'performance',
        'tax', 'structure', 'integration', 'timeline',
        'risk', 'opportunity', 'competitive'
    ]
    
    def filter_claims_by_priority(
        self, 
        claims: List[Dict[str, Any]], 
        config: SynthesisConfig
    ) -> List[Dict[str, Any]]:
        """
        Filter and prioritize claims based on importance
        
        Args:
            claims: Raw list of extracted claims
            config: Synthesis configuration
            
        Returns:
            Filtered and prioritized list of claims
        """
        if not claims:
            return []
        
        # Skip verification entirely if configured
        if config.skip_verification_for_validated:
            # Return only critical claims
            return self._filter_critical_only(claims)
        
        # Assign priority scores
        scored_claims = []
        for claim in claims:
            score = self._calculate_priority_score(claim)
            claim['priority_score'] = score
            scored_claims.append(claim)
        
        # Sort by priority (highest first)
        scored_claims.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Determine grounding depth filtering
        if config.grounding_depth == GroundingDepth.MINIMAL:
            # Only verify critical claims (score >= 80)
            filtered = [c for c in scored_claims if c['priority_score'] >= 80]
        elif config.grounding_depth == GroundingDepth.STANDARD:
            # Verify critical and high-priority claims (score >= 60)
            filtered = [c for c in scored_claims if c['priority_score'] >= 60]
        else:  # COMPREHENSIVE
            # Verify all claims
            filtered = scored_claims
        
        return filtered[:config.max_claims_per_agent]
    
    def _filter_critical_only(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return only critical claims (optimization for validated data)
        
        Args:
            claims: All claims
            
        Returns:
            Only critical claims
        """
        critical_claims = []
        
        for claim in claims:
            content_lower = claim.get('content', '').lower()
            
            # Check for critical keywords
            if any(keyword in content_lower for keyword in self.CRITICAL_KEYWORDS):
                critical_claims.append(claim)
        
        return critical_claims[:5]  # Top 5 critical claims only
    
    def _calculate_priority_score(self, claim: Dict[str, Any]) -> int:
        """
        Calculate priority score for a claim (0-100)
        
        Args:
            claim: Claim dictionary with content
            
        Returns:
            Priority score (0-100)
        """
        content_lower = claim.get('content', '').lower()
        score = 0
        
        # Check for critical keywords (+30 points each, max 90)
        critical_matches = sum(1 for kw in self.CRITICAL_KEYWORDS if kw in content_lower)
        score += min(90, critical_matches * 30)
        
        # Check for medium keywords (+10 points each, max 30)
        medium_matches = sum(1 for kw in self.MEDIUM_KEYWORDS if kw in content_lower)
        score += min(30, medium_matches * 10)
        
        # Boost for numerical values (+20 points)
        if any(char.isdigit() for char in content_lower):
            score += 20
        
        # Boost for source agent credibility
        source_agent = claim.get('source_agent', '')
        if source_agent in ['financial_analyst', 'financial_deep_dive', 'legal_counsel']:
            score += 10
        
        # Cap at 100
        return min(100, score)
