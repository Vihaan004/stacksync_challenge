# StackSync Challenge

## Overview

Build an API service that executes arbitrary Python code on a cloud server. Users send a Python script, and the service returns the execution result of the `main()` function.

## Business Context

You are building a service that enables customers to execute arbitrary Python code on a cloud server. The user sends a python script and the execution result of the `main()` function gets returned.

## Requirements

### API Specification

**Endpoint:** `POST /execute`

**Request Body:**
```json
{"script": "def main(): ..."}
```

**Response:**
```json
{
    "result": "...",
    "stdout": "..."
}
```

### Technical Requirements

1. Docker image should be lightweight
2. Run with a single `docker run` command locally
3. README with example cURL request to Cloud Run URL
4. Basic input validation
5. Safe execution (robust against malicious scripts)
6. Support basic libraries: `os`, `pandas`, `numpy`
7. Use Flask and nsjail

### Behavior

- Execute the Python script and capture the return value of `main()`
- Print statements go to `stdout`, not the result
- The `main()` function must exist and return JSON
- Throw an error if no `main()` function or invalid JSON return

## Deployment

- Docker image exposing port 8080
- Deployed on Google Cloud Run

## References

- https://nsjail.dev/
- https://github.com/google/nsjail
- https://github.com/windmill-labs/windmill/blob/main/backend/windmill-worker/nsjail/download.py.config.proto

## Submission Checklist

- [ ] GitHub repository URL (public or shared with RubenB1)
- [ ] Google Cloud Run service URL
- [ ] Time estimate to complete