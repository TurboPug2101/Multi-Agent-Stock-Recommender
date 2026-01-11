"""
Orchestrator Schemas
Defines schemas for DAG configuration, execution, and aggregation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AgentNode:
    """Schema for an agent node in the DAG."""
    agent_id: str
    agent_module: str  # e.g., "agents.scouting.agent"
    agent_class: str   # e.g., "ScoutingAgent"
    config: Optional[Dict[str, Any]] = None  # Agent-specific configuration
    input_mapping: Optional[Dict[str, str]] = None  # Maps parent outputs to inputs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DAGConfig:
    """Schema for declarative DAG configuration."""
    name: str
    description: str
    nodes: List[AgentNode]
    edges: List[Dict[str, str]]  # [{"from": "agent1", "to": "agent2"}, ...]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'nodes': [node.to_dict() for node in self.nodes],
            'edges': self.edges
        }


@dataclass
class AgentExecutionResult:
    """Schema for agent execution result."""
    agent_id: str
    status: str  # 'success' or 'error'
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_id': self.agent_id,
            'status': self.status,
            'data': self.data,
            'error': self.error,
            'timestamp': self.timestamp
        }


@dataclass
class OrchestrationResult:
    """Schema for final orchestration result."""
    status: str  # 'success' or 'error'
    execution_results: List[AgentExecutionResult]
    aggregated_output: Dict[str, Any]
    execution_order: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status,
            'execution_results': [result.to_dict() for result in self.execution_results],
            'aggregated_output': self.aggregated_output,
            'execution_order': self.execution_order,
            'timestamp': self.timestamp
        }
