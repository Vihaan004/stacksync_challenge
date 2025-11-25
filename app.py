import json
import subprocess
import tempfile
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

def run_script(script):
    # Create /tmp/nsjail directory if it doesn't exist
    nsjail_tmp = "/tmp/nsjail"
    os.makedirs(nsjail_tmp, exist_ok=True)
    
    # Temp files for script and result (in nsjail tmp)
    script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=nsjail_tmp)
    script_path = script_file.name
    result_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir=nsjail_tmp)
    result_path = result_file.name
    result_file.close()
    
    # Map the temp path to the jail path
    jail_script_path = script_path.replace(nsjail_tmp, "/tmp")
    jail_result_path = result_path.replace(nsjail_tmp, "/tmp")

    script_wrapper = f"""
import json
{script}
if __name__ == '__main__':
    result = main()
    with open('{jail_result_path}', 'w') as f:
        json.dump(result, f)
"""
    
    script_file.write(script_wrapper)
    script_file.close()
    
    # Run the script with nsjail
    try:
        process = subprocess.run(
            ['nsjail', '-C', '/nsjail.cfg', '--', 'python3', jail_script_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # get stdout
        stdout = process.stdout.strip()
        # read result
        with open(result_path, 'r') as f:
            result_data = json.load(f)
        return {
            "result": result_data,
            "stdout": stdout
        }
    
    except subprocess.TimeoutExpired:
        return {"error": "Script execution timed out (10s)"}
    except FileNotFoundError:
        return {"error": "Script did not produce a result"}
    except json.JSONDecodeError:
        return {"error": "main() must return a JSON-serializable object"}
    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}
    finally:
        # clean up
        if os.path.exists(script_path):
            os.remove(script_path)
        if os.path.exists(result_path):
            os.remove(result_path)

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
    if 'def main():' not in script:
        return jsonify({"error": "Script must contain a 'def main():' function"}), 400
    
    # execute the script
    output = run_script(script)
    
    # check if there was an error
    if "error" in output:
        return jsonify(output), 400
    return jsonify(output), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)