"""
FastAPI Backend Main Entry Point
Starts the FastAPI server and provides endpoints to trigger DAG execution.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import uvicorn
import logging
from orchestrator.main import create_orchestrator
from common.logging_config import setup_logging

# Setup logging
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Swing Trader API",
    description="Multi-Agent Trading System Backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator on startup
logger.info("Initializing backend...")
orchestrator = create_orchestrator()
logger.info("Orchestrator initialized successfully")
execution_history: list[Dict[str, Any]] = []


class ExecutionRequest(BaseModel):
    """Request model for triggering DAG execution."""
    initial_input: Optional[Dict[str, Any]] = None
    dag_config: Optional[Dict[str, Any]] = None


class ExecutionResponse(BaseModel):
    """Response model for execution results."""
    execution_id: str
    status: str
    message: str
    timestamp: str


def _generate_execution_id() -> str:
    """Generate unique execution ID."""
    return f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def _store_execution(execution_id: str, result: Dict[str, Any], status: str = "completed", error: Optional[str] = None):
    """Store execution result in history."""
    execution_history.append({
        "execution_id": execution_id,
        "result": result,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "error": error
    })
    # Keep only last 100 executions
    if len(execution_history) > 100:
        execution_history.pop(0)


def _execute_dag(request: ExecutionRequest) -> Dict[str, Any]:
    """Execute DAG and return result."""
    logger.info("Executing DAG workflow...")
    exec_orchestrator = create_orchestrator(dag_config=request.dag_config) if request.dag_config else orchestrator
    result = exec_orchestrator.execute(initial_input=request.initial_input)
    logger.info(f"DAG execution completed with status: {result.status}")
    return result.to_dict()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Swing Trader API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/dag/info")
async def get_dag_info():
    """Get DAG configuration information."""
    return {
        "dag_name": orchestrator.dag_config.name,
        "description": orchestrator.dag_config.description,
        "execution_order": orchestrator.execution_order,
        "nodes": [
            {
                "agent_id": node.agent_id,
                "agent_module": node.agent_module,
                "agent_class": node.agent_class,
                "config": node.config
            }
            for node in orchestrator.dag_config.nodes
        ],
        "edges": orchestrator.dag_config.edges
    }


# @app.post("/dag/execute", response_model=ExecutionResponse)
# async def execute_dag(request: ExecutionRequest):
#     """Execute the DAG workflow synchronously."""
#     execution_id = _generate_execution_id()
#     logger.info(f"Received DAG execution request. Execution ID: {execution_id}")
    
#     try:
#         result_dict = _execute_dag(request)
#         _store_execution(execution_id, result_dict)
#         logger.info(f"DAG execution {execution_id} stored successfully")
        
#         return ExecutionResponse(
#             execution_id=execution_id,
#             status=result_dict.get("status", "success"),
#             message="DAG execution completed",
#             timestamp=result_dict.get("timestamp", datetime.now().isoformat())
#         )
#     except Exception as e:
#         logger.error(f"DAG execution {execution_id} failed: {str(e)}", exc_info=True)
#         _store_execution(execution_id, {}, status="failed", error=str(e))
#         raise HTTPException(status_code=500, detail=f"DAG execution failed: {str(e)}")


# @app.post("/dag/execute/async", response_model=ExecutionResponse)
# async def execute_dag_async(request: ExecutionRequest, background_tasks: BackgroundTasks):
#     """Execute the DAG workflow asynchronously in background."""
#     execution_id = _generate_execution_id()
    
#     def run_dag():
#         try:
#             result_dict = _execute_dag(request)
#             _store_execution(execution_id, result_dict)
#         except Exception as e:
#             _store_execution(execution_id, {}, status="failed", error=str(e))
    
#     background_tasks.add_task(run_dag)
    
#     return ExecutionResponse(
#         execution_id=execution_id,
#         status="pending",
#         message="DAG execution started in background",
#         timestamp=datetime.now().isoformat()
#     )


@app.get("/executions")
async def get_executions(limit: int = 10):
    """Get execution history."""
    return {
        "total": len(execution_history),
        "executions": execution_history[-limit:]
    }


@app.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get specific execution result."""
    for record in execution_history:
        if record["execution_id"] == execution_id:
            return record
    raise HTTPException(status_code=404, detail="Execution not found")


@app.get("/agents")
async def get_agents():
    """Get list of all agents in the DAG."""
    return {
        "agents": [
            {
                "agent_id": node.agent_id,
                "module": node.agent_module,
                "class": node.agent_class,
                "config": node.config,
                "input_mapping": node.input_mapping
            }
            for node in orchestrator.dag_config.nodes
        ]
    }

import os
from threading import Thread

def startup_dag_runner():
    logger.info("Startup DAG execution started (background)")
    try:
        result = orchestrator.execute(initial_input=None)
        logger.info(f"Startup DAG finished with status: {result.status}")
    except Exception:
        logger.error("Startup DAG failed", exc_info=True)

@app.on_event("startup")
def run_dag_on_startup():
    # Prevent double-run when using uvicorn --reload
    # if os.environ.get("RUN_MAIN") != "true":
    #     return
    logger.info("Running DAG on FastAPI startup...")
    Thread(target=startup_dag_runner, daemon=True).start()

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    logger.info("Server will be available at http://0.0.0.0:8000")
    logger.info("API docs available at http://localhost:8000/docs")
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
