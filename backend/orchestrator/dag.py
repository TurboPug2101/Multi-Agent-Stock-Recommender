"""
Declarative DAG Configuration and Resolver
Defines the agent execution DAG declaratively and resolves execution order.
No business logic - only DAG structure and ordering.
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict, deque
from .schemas import DAGConfig, AgentNode


# Declarative DAG Configuration
# This is the ONLY place where agent order is defined
# Follows typical trading workflow:
# 1. Scouting (screens stocks)
# 2. Analysis Agents (Technical, Fundamental, Sentiment) - run in parallel
# 3. Strategist (aggregates and makes final decision)
TRADING_DAG_CONFIG = {
    'name': 'trading_agent_workflow',
    'description': 'Multi-agent trading system workflow: Scouting -> Analysis -> Strategist',
    'nodes': [
        {
            'agent_id': 'scouting',
            'agent_module': 'agents.scouting.agent',
            'agent_class': 'ScoutingAgent',
            'config': None,
            'input_mapping': None  # Root node, no inputs from other agents
        },
        {
            'agent_id': 'technical',
            'agent_module': 'agents.technical.technical_agent',
            'agent_class': 'TechnicalAgent',
            'config': None,
            'input_mapping': {
                'stocks': 'scouting.shortlisted_stocks'  # Maps scouting output to technical input
            }
        },
        # {
        #     'agent_id': 'fundamental',
        #     'agent_module': 'agents.fundamental.agent',
        #     'agent_class': 'FundamentalAgent',
        #     'config': None,
        #     'input_mapping': {
        #         'stocks': 'scouting.shortlisted_stocks'
        #     }
        # },
        {
            'agent_id': 'sentiment',
            'agent_module': 'agents.sentiment.sentiment_agent',
            'agent_class': 'SentimentAgent',
            'config': None,
            'input_mapping': {
                'stocks': 'scouting.shortlisted_stocks'
            }
        },
        # {
        #     'agent_id': 'strategist',
        #     'agent_module': 'agents.strategist.agent',
        #     'agent_class': 'StrategistAgent',
        #     'config': None,
        #     'input_mapping': {
        #         'scouting': 'scouting.data',
        #         'technical': 'technical.data',
        #         'fundamental': 'fundamental.data',
        #         'sentiment': 'sentiment.data'
        #     }
        # }
    ],
    'edges': [
        {'from': 'scouting', 'to': 'technical'},
        {'from': 'scouting', 'to': 'sentiment'},
    #     {'from': 'scouting', 'to': 'fundamental'},
    #     {'from': 'technical', 'to': 'strategist'},
    #     {'from': 'fundamental', 'to': 'strategist'},
    #     {'from': 'sentiment', 'to': 'strategist'}
    ]
}


# Before (dict):                           After (DAGConfig object):
# ─────────────                           ──────────────────────────

# {                                       DAGConfig
#   'name': 'trading...',       →           ├─ name: str = 'trading...'
#   'description': '...',       →           ├─ description: str = '...'
#   'nodes': [                  →           ├─ nodes: List[AgentNode]
#     {                         →           │   └─ [0] AgentNode
#       'agent_id': 'scouting', →           │         ├─ agent_id: str = 'scouting'
#       'agent_module': '...',  →           │         ├─ agent_module: str = 'agents.scouting.agent'
#       'agent_class': '...',   →           │         ├─ agent_class: str = 'ScoutingAgent'
#       'config': None,         →           │         ├─ config: Optional[Dict] = None
#       'input_mapping': None   →           │         └─ input_mapping: Optional[Dict] = None
#     }                         →           │
#   ],                          →           │
#   'edges': [...]              →           └─ edges: List[Dict] = [{'from': 'scouting


def load_dag_config(config: Dict) -> DAGConfig:
    """
    Load DAG configuration from dictionary.
    
    Args:
        config: DAG configuration dictionary
    
    Returns:
        DAGConfig object
    """
    nodes = [AgentNode(**node) for node in config['nodes']]
    return DAGConfig(
        name=config['name'],
        description=config['description'],
        nodes=nodes,
        edges=config['edges']
    )


def build_dependency_graph(edges: List[Dict[str, str]]) -> Dict[str, Set[str]]:
    """
    Build adjacency list representation of dependency graph.
    
    Args:
        edges: List of edges [{"from": "agent1", "to": "agent2"}, ...]
    
    Returns:
        Dict mapping agent_id to set of dependent agent_ids
    """
    graph = defaultdict(set)
    in_degree = defaultdict(int)
    node_ids = set()
    
    # Collect all node IDs
    for edge in edges:
        node_ids.add(edge['from'])
        node_ids.add(edge['to'])
    
    # Build graph and calculate in-degrees
    for edge in edges:
        from_node = edge['from']
        to_node = edge['to']
        graph[from_node].add(to_node)
        in_degree[to_node] += 1
        # Initialize in-degree for all nodes
        if from_node not in in_degree:
            in_degree[from_node] = 0
    
    return graph, in_degree, node_ids


def resolve_execution_order(edges: List[Dict[str, str]]) -> List[List[str]]:
    """
    Resolve DAG execution order using topological sort.
    Returns list of execution levels (agents at same level can run in parallel).
    
    Args:
        edges: List of edges defining dependencies
    
    Returns:
        List of lists, where each inner list contains agent_ids that can run in parallel
    """
    graph, in_degree, node_ids = build_dependency_graph(edges)
    
    # Find root nodes (nodes with no dependencies)
    queue = deque([node for node in node_ids if in_degree[node] == 0])
    execution_order = []
    remaining_in_degree = in_degree.copy()
    
    while queue:
        # Current level (can run in parallel)
        current_level = []
        level_size = len(queue)
        
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node)
            
            # Process dependents
            for dependent in graph[node]:
                remaining_in_degree[dependent] -= 1
                if remaining_in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if current_level:
            execution_order.append(current_level)
    
    # Check for cycles
    if sum(remaining_in_degree.values()) > 0:
        raise ValueError("DAG contains cycles - cannot resolve execution order")
    
    return execution_order


def get_dag_config() -> DAGConfig:
    """
    Get the default trading DAG configuration.
    
    Returns:
        DAGConfig object
    """
    return load_dag_config(TRADING_DAG_CONFIG)


def get_execution_order(dag_config: Optional[DAGConfig] = None) -> List[List[str]]:
    """
    Get execution order for the DAG.
    
    Args:
        dag_config: Optional DAG config (uses default if not provided)
    
    Returns:
        List of execution levels
    """
    if dag_config is None:
        dag_config = get_dag_config()
    
    return resolve_execution_order(dag_config.edges)


def get_node_by_id(dag_config: DAGConfig, agent_id: str) -> Optional[AgentNode]:
    """
    Get node configuration by agent ID.
    
    Args:
        dag_config: DAG configuration
        agent_id: Agent ID to find
    
    Returns:
        AgentNode if found, None otherwise
    """
    for node in dag_config.nodes:
        if node.agent_id == agent_id:
            return node
    return None


def get_dependencies(dag_config: DAGConfig, agent_id: str) -> List[str]:
    """
    Get list of agent IDs that this agent depends on.
    
    Args:
        dag_config: DAG configuration
        agent_id: Agent ID
    
    Returns:
        List of dependency agent IDs
    """
    dependencies = []
    for edge in dag_config.edges:
        if edge['to'] == agent_id:
            dependencies.append(edge['from'])
    return dependencies


def get_dependents(dag_config: DAGConfig, agent_id: str) -> List[str]:
    """
    Get list of agent IDs that depend on this agent.
    
    Args:
        dag_config: DAG configuration
        agent_id: Agent ID
    
    Returns:
        List of dependent agent IDs
    """
    dependents = []
    for edge in dag_config.edges:
        if edge['from'] == agent_id:
            dependents.append(edge['to'])
    return dependents
