"""
Orchestrator has ONLY 3 responsibilities:
1. Resolve DAG order
2. Execute agents
3. Aggregate outputs

"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import importlib
import logging
from .dag import get_dag_config, get_execution_order, get_node_by_id, get_dependencies
from .schemas import AgentExecutionResult, OrchestrationResult
from common.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator for executing agents in DAG order.
    Only handles execution orchestration - no business logic.
    """
    
    def __init__(self, dag_config: Optional[Dict] = None):
        """
        Initialize orchestrator.
        
        Args:
            dag_config: Optional custom DAG config (uses default if None)
        """
        logger.info("Initializing orchestrator...")
        # dag config not being passed in production, so using default
        if dag_config:
            from .dag import load_dag_config
            self.dag_config = load_dag_config(dag_config)
            logger.info(f"Using custom DAG config: {self.dag_config.name}")
        else:
            self.dag_config = get_dag_config()
            logger.info(f"Using default DAG config: {self.dag_config.name}")
        
        self.execution_order = get_execution_order(self.dag_config)
        logger.info(f"Resolved execution order: {self.execution_order}")
        self.execution_results: Dict[str, AgentExecutionResult] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}
        logger.info("Orchestrator initialized successfully")
    
    def _load_agent(self, agent_id: str) -> BaseAgent:
        """
        Dynamically load and instantiate an agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            BaseAgent instance
        """
        if agent_id in self.agent_instances:
            logger.debug(f"Agent {agent_id} already loaded, returning cached instance")
            return self.agent_instances[agent_id]
        
        logger.info(f"Loading agent: {agent_id}")
        node = get_node_by_id(self.dag_config, agent_id)
        if not node:
            logger.error(f"Agent node not found: {agent_id}")
            raise ValueError(f"Agent node not found: {agent_id}")
        
        logger.debug(f"Agent config - module: {node.agent_module}, class: {node.agent_class}, config: {node.config}")
        
        # Dynamically import agent module
        try:
            module = importlib.import_module(node.agent_module)
            agent_class = getattr(module, node.agent_class)
            logger.debug(f"Successfully imported {node.agent_class} from {node.agent_module}")
        except Exception as e:
            logger.error(f"Failed to import agent module {node.agent_module}: {str(e)}")
            raise
        
        # Instantiate agent with config using factory pattern if available
        config = node.config
        try:
            # Check if module has a create_agent factory function
            if hasattr(module, 'create_agent'):
                logger.debug(f"Using factory function create_agent for {agent_id}")
                # logger.debug(f"Config: {config}")
                agent = module.create_agent(config)
            else:
                # Fall back to direct instantiation
                logger.debug(f"Using direct instantiation for {agent_id}")
                agent = agent_class(**config)
            logger.info(f"Successfully instantiated agent: {agent_id}")
        except Exception as e:
            logger.error(f"Failed to instantiate agent {agent_id}: {str(e)}")
            raise
        
        self.agent_instances[agent_id] = agent
        return agent
    
    def _prepare_input(self, agent_id: str, execution_results: Dict[str, AgentExecutionResult]) -> Dict[str, Any]:
        """
        Prepare input for an agent based on its input_mapping and execution results.
        
        Args:
            agent_id: Agent ID
            execution_results: Dictionary of execution results
        
        Returns:
            Input dictionary for the agent
        """
        logger.debug(f"Preparing input for agent: {agent_id}")
        node = get_node_by_id(self.dag_config, agent_id)
        if not node or not node.input_mapping:
            logger.debug(f"Agent {agent_id} is root node or has no input mapping, returning empty input")
            return {}  # Root node or no input mapping
        
        input_data = {}
        logger.debug(f"Input mapping for {agent_id}: {node.input_mapping}")
        
        for input_key, source_path in node.input_mapping.items():
            # Parse source path: "parent_agent.data_key" or "parent_agent"
            parts = source_path.split('.', 1)
            source_agent_id = parts[0]
            
            if source_agent_id not in execution_results:
                raise ValueError(f"Source agent '{source_agent_id}' not found in execution results")
            
            source_result = execution_results[source_agent_id]
            
            if source_result.status != 'success':
                raise ValueError(f"Source agent '{source_agent_id}' failed: {source_result.error}")
            
            if len(parts) == 2:
                # Navigate nested data path
                data_key = parts[1]
                source_data = source_result.data
                logger.debug(f"Looking for key '{data_key}' in source agent '{source_agent_id}' data")
                logger.debug(f"Available keys in source data: {list(source_data.keys()) if source_data else 'None'}")
                
                # Simple path navigation (can be extended for nested paths)
                if data_key in source_data:
                    input_data[input_key] = source_data[data_key]
                    logger.debug(f"Mapped {source_agent_id}.{data_key} -> {input_key} (type: {type(source_data[data_key])}, length: {len(source_data[data_key]) if isinstance(source_data[data_key], (list, dict)) else 'N/A'})")
                else:
                    # Try to get from nested structure
                    logger.warning(f"Key '{data_key}' not found in source data, using entire data structure")
                    input_data[input_key] = source_data
            else:
                # Use entire data
                logger.debug(f"Using entire data from {source_agent_id} for {input_key}")
                input_data[input_key] = source_result.data
        
        return input_data
    
    def execute_agent(self, agent_id: str, input_data: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute a single agent.
        
        Args:
            agent_id: Agent ID
            input_data: Input data for the agent
        
        Returns:
            AgentExecutionResult
        """
        logger.info(f"Executing agent: {agent_id}")
        logger.debug(f"Input data keys for {agent_id}: {list(input_data.keys())}")
        
        try:
            agent = self._load_agent(agent_id)
            logger.debug(f"Starting execution of agent: {agent_id}")
            result = agent.execute(input_data)
            
            status = result['status']
            if status == 'success':
                logger.info(f"Agent {agent_id} executed successfully")
                if 'data' in result and result['data']:
                    logger.debug(f"Agent {agent_id} output data keys: {list(result['data'].keys())}")
            else:
                logger.warning(f"Agent {agent_id} execution failed: {result.get('error', 'Unknown error')}")
            
            return AgentExecutionResult(
                agent_id=agent_id,
                status=status,
                data=result.get('data'),
                error=result.get('error'),
                timestamp=result.get('timestamp')
            )
        except Exception as e:
            logger.error(f"Exception while executing agent {agent_id}: {str(e)}", exc_info=True)
            return AgentExecutionResult(
                agent_id=agent_id,
                status='error',
                data=None,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    def execute(self, initial_input: Optional[Dict[str, Any]] = None) -> OrchestrationResult:
        """
        Execute all agents in DAG order.
        
        Args:
            initial_input: Optional initial input (for root nodes)
        
        Returns:
            OrchestrationResult
        """
        logger.info("="*80)
        logger.info("Starting DAG execution")
        logger.info("="*80)
        logger.info(f"Execution order: {self.execution_order}")
        if initial_input:
            logger.info(f"Initial input: {initial_input}")
        
        execution_results = {}
        flat_execution_order = []
        
        try:
            # Execute agents level by level
            for level_idx, level in enumerate(self.execution_order):
                logger.info(f"\n--- Executing Level {level_idx + 1}: {level} ---")
                # Agents at same level can run in parallel (but we'll run sequentially for simplicity)
                for agent_id in level:
                    flat_execution_order.append(agent_id)
                    
                    # Prepare input
                    if agent_id in execution_results:
                        continue  # Already executed
                    
                    try:
                        # Check if this is a root node
                        dependencies = get_dependencies(self.dag_config, agent_id)
                        if not dependencies:
                            # Root node - use initial_input
                            logger.debug(f"Agent {agent_id} is a root node (no dependencies)")
                            input_data = initial_input or {}
                        else:
                            # Prepare input from dependencies
                            logger.debug(f"Agent {agent_id} depends on: {dependencies}")
                            input_data = self._prepare_input(agent_id, execution_results)
                        
                        # Execute agent
                        result = self.execute_agent(agent_id, input_data)
                        execution_results[agent_id] = result
                        
                        # Log scouting agent results specifically
                        if agent_id == 'scouting' and result.status == 'success' and result.data:
                            logger.info("\n" + "="*80)
                            logger.info("SCOUTING AGENT RESULTS")
                            logger.info("="*80)
                            data = result.data
                            logger.info(f"Total Screened: {data.get('total_screened', 0)}")
                            logger.info(f"Qualifying Stocks: {data.get('qualifying_count', 0)}")
                            shortlisted = data.get('shortlisted_stocks', [])
                            logger.info(f"Shortlisted Stocks: {len(shortlisted)}")
                            logger.info("-"*80)
                            for i, stock in enumerate(shortlisted[:10], 1):
                                logger.info(f"{i}. {stock.get('name', 'N/A')} ({stock.get('symbol', 'N/A')})")
                                logger.info(f"   Price: ₹{stock.get('current_price', 0):.2f}")
                                logger.info(f"   ATR: {stock.get('atr_percentage', 0):.2f}%" if stock.get('atr_percentage') else "   ATR: N/A")
                                logger.info(f"   Avg Volume: {stock.get('avg_volume', 0):,.0f}")
                                logger.info(f"   Meets Criteria: {'Yes' if stock.get('meets_criteria') else 'No'}")
                            logger.info("="*80 + "\n")
                        
                        # Stop if agent failed (unless configured to continue)
                        if result.status != 'success':
                            logger.error(f"Agent {agent_id} failed, stopping execution")
                            break
                        else:
                            logger.info(f"✓ Level {level_idx + 1} completed for {agent_id}")
                    
                    except Exception as e:
                        result = AgentExecutionResult(
                            agent_id=agent_id,
                            status='error',
                            data=None,
                            error=str(e),
                            timestamp=datetime.now().isoformat()
                        )
                        execution_results[agent_id] = result
                        break
            
            # Aggregate outputs
            logger.info("\nAggregating outputs...")
            aggregated_output = self._aggregate_outputs(execution_results)
            logger.debug(f"Aggregated output keys: {list(aggregated_output.keys())}")
            
            # Determine overall status
            overall_status = 'success' if all(
                r.status == 'success' for r in execution_results.values()
            ) else 'error'
            
            logger.info("="*80)
            logger.info(f"DAG execution completed with status: {overall_status}")
            logger.info(f"Executed {len(execution_results)} agents")
            logger.info("="*80)
            
            return OrchestrationResult(
                status=overall_status,
                execution_results=list(execution_results.values()),
                aggregated_output=aggregated_output,
                execution_order=flat_execution_order,
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            # Return partial results on error
            return OrchestrationResult(
                status='error',
                execution_results=list(execution_results.values()),
                aggregated_output={},
                execution_order=flat_execution_order,
                timestamp=datetime.now().isoformat()
            )
    
    def _aggregate_outputs(self, execution_results: Dict[str, AgentExecutionResult]) -> Dict[str, Any]:
        """
        Aggregate outputs from all agents.
        Simple aggregation - just combines all agent outputs.
        
        Args:
            execution_results: Dictionary of execution results
        
        Returns:
            Aggregated output dictionary
        """
        aggregated = {}
        
        for agent_id, result in execution_results.items():
            if result.status == 'success' and result.data:
                aggregated[agent_id] = result.data
            else:
                aggregated[agent_id] = {
                    'status': result.status,
                    'error': result.error
                }
        
        return aggregated


def create_orchestrator(dag_config: Optional[Dict] = None) -> Orchestrator:
    """
    Factory function to create an orchestrator instance.
    
    Args:
        dag_config: Optional custom DAG config
    
    Returns:
        Orchestrator instance
    """
    return Orchestrator(dag_config=dag_config)


# For direct execution/testing
if __name__ == "__main__":
    orchestrator = Orchestrator()
    result = orchestrator.execute()
    
    print("\n" + "="*80)
    print("ORCHESTRATION RESULTS")
    print("="*80)
    print(f"\nStatus: {result.status}")
    print(f"Execution Order: {' -> '.join(result.execution_order)}")
    print(f"\nExecution Results:")
    print("-"*80)
    
    for exec_result in result.execution_results:
        print(f"\n{exec_result.agent_id}:")
        print(f"  Status: {exec_result.status}")
        if exec_result.status == 'success':
            print(f"  Data keys: {list(exec_result.data.keys()) if exec_result.data else 'None'}")
        else:
            print(f"  Error: {exec_result.error}")
    
    print(f"\nAggregated Output Keys: {list(result.aggregated_output.keys())}")
