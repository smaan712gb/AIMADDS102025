"""
Knowledge Graph Utilities for M&A Copilot

Provides graph-based querying capabilities for relationship-based questions
about the analysis data.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
import json
from loguru import logger


class KnowledgeGraph:
    """
    Knowledge Graph for M&A Analysis.
    
    Represents entities and relationships from the analysis to enable
    complex relationship-based queries.
    """
    
    def __init__(self):
        self.nodes = {}  # id -> {type, data, metadata}
        self.edges = []  # [(source, target, relationship, metadata)]
        self.relationships = defaultdict(list)  # source_id -> [(target_id, relationship)]
        
    def add_node(self, node_id: str, node_type: str, data: Dict[str, Any], metadata: Optional[Dict] = None):
        """Add a node to the graph."""
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'data': data,
            'metadata': metadata or {}
        }
        
    def add_edge(self, source_id: str, target_id: str, relationship: str, metadata: Optional[Dict] = None):
        """Add an edge (relationship) to the graph."""
        self.edges.append((source_id, target_id, relationship, metadata or {}))
        self.relationships[source_id].append((target_id, relationship))
        
    def find_related_nodes(self, node_id: str, relationship_type: Optional[str] = None, max_depth: int = 2) -> List[Dict]:
        """
        Find all nodes related to a given node.
        
        Args:
            node_id: Starting node ID
            relationship_type: Optional filter for relationship type
            max_depth: Maximum traversal depth
            
        Returns:
            List of related nodes with their relationships
        """
        visited = set()
        results = []
        
        def traverse(current_id: str, depth: int, path: List[Tuple[str, str]]):
            if depth > max_depth or current_id in visited:
                return
                
            visited.add(current_id)
            
            for target_id, rel_type in self.relationships.get(current_id, []):
                if relationship_type and rel_type != relationship_type:
                    continue
                    
                if target_id in self.nodes:
                    results.append({
                        'node': self.nodes[target_id],
                        'relationship': rel_type,
                        'path': path + [(current_id, rel_type)],
                        'depth': depth + 1
                    })
                    
                    traverse(target_id, depth + 1, path + [(current_id, rel_type)])
        
        traverse(node_id, 0, [])
        return results
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[Tuple[str, str, str]]]:
        """
        Find shortest path between two nodes.
        
        Returns:
            List of (node_id, relationship, next_node_id) tuples
        """
        from collections import deque
        
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
            
        queue = deque([(source_id, [])])
        visited = set()
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == target_id:
                return path
                
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            for next_id, relationship in self.relationships.get(current_id, []):
                new_path = path + [(current_id, relationship, next_id)]
                queue.append((next_id, new_path))
        
        return None
    
    def query_by_type(self, node_type: str) -> List[Dict]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node['type'] == node_type]
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get a specific node by ID."""
        return self.nodes.get(node_id)
    
    def get_connections(self, node_id: str) -> List[Tuple[str, str, Dict]]:
        """
        Get all direct connections for a node.
        
        Returns:
            List of (target_id, relationship, target_node) tuples
        """
        connections = []
        for target_id, relationship in self.relationships.get(node_id, []):
            if target_id in self.nodes:
                connections.append((target_id, relationship, self.nodes[target_id]))
        return connections


def build_knowledge_graph_from_state(state: Dict[str, Any]) -> KnowledgeGraph:
    """
    Build a Knowledge Graph from the complete analysis state.
    
    Args:
        state: Complete analysis state dictionary
        
    Returns:
        Populated KnowledgeGraph instance
    """
    graph = KnowledgeGraph()
    
    try:
        # Add company node
        company_name = state.get('target_company', 'Target')
        graph.add_node(
            'company:main',
            'company',
            {
                'name': company_name,
                'ticker': state.get('target_ticker', '')
            }
        )
        
        # Add financial metrics nodes
        financial_data = state.get('financial_data', {})
        if financial_data:
            # Valuation node
            valuation = financial_data.get('valuation', {})
            if valuation:
                graph.add_node(
                    'metric:valuation',
                    'valuation',
                    valuation,
                    {'source': 'Financial Analysis'}
                )
                graph.add_edge('company:main', 'metric:valuation', 'has_valuation')
            
            # Ratio analysis
            ratios = financial_data.get('ratio_analysis', {})
            for category, metrics in ratios.items():
                node_id = f'metric:{category}'
                graph.add_node(node_id, 'financial_metric', metrics, {'category': category})
                graph.add_edge('company:main', node_id, 'has_metrics')
        
        # Add competitive analysis
        competitive = state.get('competitive_analysis', {})
        if competitive:
            graph.add_node(
                'analysis:competitive',
                'competitive_analysis',
                competitive,
                {'source': 'Competitive Benchmarking'}
            )
            graph.add_edge('company:main', 'analysis:competitive', 'analyzed_by')
            
            # Add peer companies
            peers = competitive.get('peer_companies', [])
            for i, peer in enumerate(peers[:5]):  # Top 5 peers
                peer_id = f"peer:{peer.get('ticker', i)}"
                graph.add_node(peer_id, 'competitor', peer)
                graph.add_edge('company:main', peer_id, 'competes_with')
                graph.add_edge(peer_id, 'analysis:competitive', 'included_in')
        
        # Add risks
        risks = state.get('critical_risks', [])
        for i, risk in enumerate(risks[:10]):  # Top 10 risks
            risk_id = f'risk:{i}'
            graph.add_node(
                risk_id,
                'risk',
                risk if isinstance(risk, dict) else {'description': str(risk)}
            )
            graph.add_edge('company:main', risk_id, 'has_risk')
        
        # Add opportunities
        opportunities = state.get('key_findings', [])
        for i, opp in enumerate(opportunities[:10]):
            opp_id = f'opportunity:{i}'
            graph.add_node(
                opp_id,
                'opportunity',
                {'description': str(opp)}
            )
            graph.add_edge('company:main', opp_id, 'has_opportunity')
        
        # Add macroeconomic factors
        macro = state.get('macroeconomic_analysis', {})
        if macro:
            graph.add_node(
                'analysis:macro',
                'macroeconomic_analysis',
                macro,
                {'source': 'Macroeconomic Analysis'}
            )
            graph.add_edge('company:main', 'analysis:macro', 'affected_by')
            
            # Add scenario models
            scenarios = macro.get('scenario_models', {})
            for scenario_name, scenario_data in scenarios.items():
                scenario_id = f'scenario:{scenario_name}'
                graph.add_node(scenario_id, 'scenario', scenario_data)
                graph.add_edge('analysis:macro', scenario_id, 'includes_scenario')
                graph.add_edge('company:main', scenario_id, 'modeled_in')
        
        # Add integration planning
        integration = state.get('integration_plan', {})
        if integration:
            graph.add_node(
                'plan:integration',
                'integration_plan',
                integration,
                {'source': 'Integration Planning'}
            )
            graph.add_edge('company:main', 'plan:integration', 'has_integration_plan')
        
        logger.info(f"Built knowledge graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        
    except Exception as e:
        logger.error(f"Error building knowledge graph: {e}")
    
    return graph


def query_knowledge_graph(graph: KnowledgeGraph, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query the knowledge graph based on natural language query.
    
    Args:
        graph: KnowledgeGraph instance
        query: Natural language query
        context: Additional context for query interpretation
        
    Returns:
        Query results with relevant nodes and relationships
    """
    query_lower = query.lower()
    results = {
        'nodes': [],
        'relationships': [],
        'insights': []
    }
    
    try:
        # Detect query type
        if 'connect' in query_lower or 'relationship' in query_lower or 'between' in query_lower:
            # Relationship query
            results['query_type'] = 'relationship'
            results['nodes'] = list(graph.nodes.values())[:10]
            
        elif 'risk' in query_lower:
            # Risk query
            results['query_type'] = 'risk'
            risks = graph.query_by_type('risk')
            results['nodes'] = risks
            results['insights'].append(f"Found {len(risks)} risks identified in the analysis")
            
        elif 'competitor' in query_lower or 'peer' in query_lower:
            # Competitor query
            results['query_type'] = 'competitor'
            peers = graph.query_by_type('competitor')
            results['nodes'] = peers
            
            # Get competitive analysis
            comp_analysis = graph.get_node('analysis:competitive')
            if comp_analysis:
                results['analysis'] = comp_analysis
            
        elif 'opportunity' in query_lower or 'growth' in query_lower:
            # Opportunity query
            results['query_type'] = 'opportunity'
            opportunities = graph.query_by_type('opportunity')
            results['nodes'] = opportunities
            
        elif 'scenario' in query_lower or 'bull' in query_lower or 'bear' in query_lower:
            # Scenario query
            results['query_type'] = 'scenario'
            scenarios = graph.query_by_type('scenario')
            results['nodes'] = scenarios
            
        else:
            # General query - return company node and its connections
            results['query_type'] = 'general'
            company_node = graph.get_node('company:main')
            if company_node:
                results['nodes'].append(company_node)
                connections = graph.get_connections('company:main')
                results['relationships'] = [
                    {
                        'target': target_node,
                        'relationship': rel
                    }
                    for _, rel, target_node in connections[:10]
                ]
        
    except Exception as e:
        logger.error(f"Error querying knowledge graph: {e}")
        results['error'] = str(e)
    
    return results
