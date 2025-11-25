import json
import subprocess
import tempfile
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

def run_script(script):
    # Create temp directory
    nsjail_tmp = "/tmp/nsjail"
    os.makedirs(nsjail_tmp, exist_ok=True)
    
    # Temp files for script and result
    script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=nsjail_tmp)
    script_path = script_file.name
    os.chmod(script_path, 0o644)
    
    result_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir=nsjail_tmp)
    result_path = result_file.name
    result_file.close()
    os.chmod(result_path, 0o666)

    # Check if nsjail should be used (disabled on Cloud Run via env var)
    # Cloud Run sets K_SERVICE environment variable
    is_cloud_run = os.environ.get('K_SERVICE') is not None
    use_nsjail = (not is_cloud_run) and os.path.exists('/usr/local/bin/nsjail') and os.path.exists('/app/nsjail.cfg')
    
    # Map paths for nsjail namespace (host:/tmp/nsjail -> jail:/tmp)
    if use_nsjail:
        jail_script_path = script_path.replace(nsjail_tmp, "/tmp")
        jail_result_path = result_path.replace(nsjail_tmp, "/tmp")
    else:
        jail_script_path = script_path
        jail_result_path = result_path

    script_wrapper = f"""
import json
import sys
{script}

if __name__ == '__main__':
    try:
        if not callable(main):
            print("Error: 'main' is not a function", file=sys.stderr)
            sys.exit(1)
        result = main()
        with open('{jail_result_path}', 'w') as f:
            json.dump(result, f)
    except Exception as e:
        print(f"Error in main(): {{e}}", file=sys.stderr)
        sys.exit(1)
"""
    
    script_file.write(script_wrapper)
    script_file.close()
    
    try:
        if use_nsjail:
            # Run with nsjail (local Docker)
            process = subprocess.run(
                [
                    '/usr/local/bin/nsjail',
                    '--config',
                    '/app/nsjail.cfg',
                    '--',
                    '/usr/local/bin/python3',
                    jail_script_path
                ],
                capture_output=True,
                text=True,
                timeout=15,
                cwd='/tmp/nsjail'
            )
        else:
            # Run directly without nsjail (Cloud Run provides isolation)
            process = subprocess.run(
                ['/usr/local/bin/python3', script_path],
                capture_output=True,
                text=True,
                timeout=15,
                cwd='/tmp/nsjail'
            )
        
        # debug
        # if process.returncode != 0:
        #     error_msg = process.stderr.strip() or "Script execution failed"
        #     return {
        #         "error": error_msg,
        #         "stdout": process.stdout.strip()
        #     }

        # get stdout
        stdout = process.stdout.strip()
        
        if not os.path.exists(result_path):
            return {"error": "Script did not produce a result. Ensure main() returns a value."}
            
        with open(result_path, 'r') as f:
            result_data = json.load(f)
            
        return {
            "result": result_data,
            "stdout": stdout
        }
    
    except subprocess.TimeoutExpired:
        return {"error": "Script execution timed out (15s)"}
    except json.JSONDecodeError:
        return {"error": "main() must return a JSON-serializable object"}
    except Exception as e:
        return {"error": f"Execution error: {str(e)}"}
    finally:
        for path in [script_path, result_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass

@app.route("/execute", methods=['POST'])
def execute_script():
    data = request.get_json()
    
    # Input validation
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    if 'script' not in data:
        return jsonify({"error": "Missing 'script' field"}), 400

    # extract script
    script = data['script']
    if not isinstance(script, str):
        return jsonify({"error": "Script must be a string"}), 400
    if len(script) > 50000:
        return jsonify({"error": "Script too large (max 50KB)"}), 400
    if 'def main():' not in script and 'def main(' not in script:
        return jsonify({"error": "Script must contain a 'def main():' function"}), 400
    
    output = run_script(script)
    
    if "error" in output:
        return jsonify(output), 400
    return jsonify(output), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)