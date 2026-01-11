# Backend Setup and Running Instructions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or if you're using a virtual environment (recommended):
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Running the Backend

### Option 1: Using Python directly (Recommended)
```bash
cd backend
python main.py
```

### Option 2: Using the run script
```bash
cd backend
chmod +x run.sh  # Make script executable (first time only)
./run.sh
```

### Option 3: Using uvicorn directly
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Server Endpoints

Once the server is running, it will be available at:

- **API Server:** http://localhost:8000
- **Interactive API Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/redoc

## Key Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /dag/info` - Get DAG configuration
- `POST /dag/execute` - Execute DAG workflow (synchronous)
- `POST /dag/execute/async` - Execute DAG workflow (asynchronous)
- `GET /executions` - Get execution history
- `GET /executions/{execution_id}` - Get specific execution result
- `GET /agents` - Get list of all agents

## Example: Execute the DAG

Using curl:
```bash
curl -X POST http://localhost:8000/dag/execute \
  -H "Content-Type: application/json" \
  -d '{"initial_input": {"top_n": 10}}'
```

Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/dag/execute",
    json={"initial_input": {"top_n": 10}}
)
print(response.json())
```

## Logging

The backend includes detailed logging that will show:
- Server startup information
- DAG execution progress
- Agent execution details
- **Scouting agent results** (automatically printed to terminal)

## Troubleshooting

1. **Port already in use:**
   - Change the port in `main.py` or use `--port` flag with uvicorn

2. **Import errors:**
   - Make sure you're in the `backend` directory
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

3. **Module not found errors:**
   - Make sure Python can find the modules (run from `backend` directory)
   - Check that all agent files exist
