"""
Base Agent Contract
All agents must inherit from BaseAgent and implement the run method.
Agents should be stateless, deterministic, and have no side effects.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class that all agents must inherit from.
    Ensures all agents conform to a single contract.
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Unique identifier for this agent
        """
        self.agent_name = agent_name
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data against the agent's input schema.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            bool: True if input is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method. Must be:
        - Stateless (no instance state modification that affects behavior)
        - Deterministic (same input produces same output)
        - No side effects (no external state modification)
        
        Args:
            input_data: Validated input data conforming to input schema
        
        Returns:
            Output data conforming to output schema
        """
        pass
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Public execution method with validation and error handling.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            Dict with 'status', 'data', 'error', 'timestamp' keys
        """
        try:
            # Validate input
            if not self.validate_input(input_data):
                return {
                    'agent': self.agent_name,
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': 'Invalid input data',
                    'data': None
                }
            
            # Execute agent logic
            output_data = self.run(input_data)
            
            # Return standardized format
            return {
                'agent': self.agent_name,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'data': output_data,
                'error': None
            }
            
        except Exception as e:
            return {
                'agent': self.agent_name,
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'data': None
            }
