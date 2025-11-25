# Python-Executor

Secure API service that executes arbitrary Python code in a sandboxed environment using Flask and nsjail.

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
docker run --cap-add=SYS_ADMIN --security-opt seccomp=unconfined --rm -p 8080:8080 us-central1-docker.pkg.dev/scriptrunnerapi/cloud-run-source-deploy/python-executor:latest
```

> **Optionally:** Use `--privileged` flag for more relaxed security for nsjail to create security namespaces. (not needed on Cloud Run)

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

Scripts run in an isolated nsjail sandbox with:
- **Seccomp filter**: Blocks socket, ptrace, kill, mount, and other dangerous syscalls
- **Namespace isolation**: User namespace with UID/GID mapping
- **Resource limits**: 
  - Execution timeout: 15 seconds
  - Memory limit: 700MB
  - CPU limit: 10 seconds
  - File size limit: 1024KB
- **Read-only mounts**: System directories mounted read-only
- **Network blocked**: Socket syscall returns ERRNO 13 (Permission denied)


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
