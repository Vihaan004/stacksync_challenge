# Python-Executor

Secure API service that executes arbitrary Python code in a sandboxed environment using Flask and nsjail.

**Note: nsjail disabled on Cloud Run for compatibility; Cloud Run provides container-level isolation.**

## Service URL

**Production:** `https://python-executor-310135046960.us-central1.run.app`

## API Usage

### Endpoint: `POST /execute`

Execute Python code that contains a `main()` function. The service returns the result of `main()` and any stdout output.

### Eg. Request

```bash
curl -X POST https://python-executor-310135046960.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import numpy as np\n    import pandas as pd\n    print(\"Processing data...\")\n    data = np.array([1, 2, 3, 4, 5])\n    return {\"mean\": float(np.mean(data)), \"sum\": int(np.sum(data))}"
  }'
```

### Eg. Response

```json
{
  "result": {
    "mean": 3.0,
    "sum": 15
  },
  "stdout": "Processing data..."
}
```

### Requirements & Limits

- Script must contain a `def main():` function
- `main()` must return a JSON-serializable object (dict, list, str, int, float, bool, None)
- Available libraries: `os`, `numpy`, `pandas`, `math`, standard library
- Execution timeout: 15 seconds
- Memory limit: 700MB
- Script size limit: 50KB

## Local Testing

Run the service locally with a single command:

```bash
docker run --privileged --rm -p 8080:8080 us-central1-docker.pkg.dev/scriptrunnerapi/cloud-run-source-deploy/python-executor:latest
```

> **Note:** The `--privileged` flag is required locally for nsjail to create security namespaces. This is not needed on Cloud Run.

Then test it:

```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    return {\"status\": \"ok\"}"}'
```

### Error Responses

```json
{
  "error": "Script must contain a 'def main():' function"
}
```

```json
{
  "error": "main() must return a JSON-serializable object"
}
```

## Architecture

- **app.py**: Flask app with `/execute` endpoint and nsjail integration
- **Dockerfile**: Multi-stage build for minimal image size
- **nsjail.cfg**: Sandboxing configuration with resource limits
- **requirements.txt**: Python dependencies (Flask, pandas, numpy, gunicorn)

## Security

**Local Execution (Docker with --privileged):**
- Scripts run in isolated nsjail sandbox with resource limits
- Execution timeout: 15 seconds
- Memory limit: 700MB

**Cloud Run Execution:**
- Cloud Run provides container-level isolation
- Each request runs in an isolated container instance
- Execution timeout: 15 seconds (enforced by Flask)
- Memory limit: 512MB (Cloud Run configuration)
- No persistent state between requests


## Brainstorm
- app.py
    - Flask app with a single endpoint /execute
    - parse incoming JSON request
    - input validation
    - nsjail subprocess to run script
    - return formatted JSON response
- Dockerfile 
    - base image (lightweight python)
    - required dependecies
    - nsjail dependencies and build
    - copy app.py and requirements.txt
    - expose port 8080
- requirements.txt
- nsjail.cfg
    - sandboxing config
    - decide resource limits
