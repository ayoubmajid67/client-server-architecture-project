from flask import Flask, request, jsonify
import requests
from threading import Lock
from utils import generate_task_id, current_time, validate_expression
import uuid
import time
from threading import Lock, Thread

app = Flask(__name__)
tasks = []
slaves = {}
lock = Lock()
port =5000

@app.route("/register-slave", methods=["POST"])
def register_slave():
    data = request.json
    webhook_url = data.get("webhook_url")
    
    if not webhook_url:
        return jsonify({"error": "Missing webhook_url"}), 400
    webhook_url = webhook_url.strip().lower()
    
    # Check slave health before registration
    try:
        for slave_id, slave_info in slaves.items():
         if slave_info["webhook"] == webhook_url:
                return jsonify({
                    "error": "Slave with this webhook URL is already registered",
                    "slave_id": slave_id
                }), 400
    
        health_response = requests.get(f"{webhook_url}/health", timeout=5)
        if health_response.status_code != 200:
            return jsonify({
                "error": "Slave health check failed",
                "status_code": health_response.status_code
            }), 503
    except requests.RequestException as e:
        return jsonify({
            "error": "Slave is not reachable",
            "details": str(e)
        }), 503
    
    with lock:
        # Generate a unique slave ID
        slave_id = f"slave-{str(uuid.uuid4())[:8]}"
        slaves[slave_id] = {
            "id":slave_id,
            "webhook": webhook_url,
            "status": "free"
        }
            # Notify the slave of its ID
    try:
        set_id_response = requests.post(f"{webhook_url}/register-slave-api/{slave_id}", timeout=5)
        if set_id_response.status_code != 200:
            return jsonify({
                "error": "Failed to assign ID to slave",
                "slave_id": slave_id,
                "details": set_id_response.text
            }), 500
    except requests.RequestException as e:
        return jsonify({
            "error": "Failed to contact slave to set ID",
            "slave_id": slave_id,
            "details": str(e)
        }), 500

    return jsonify({
        "message": "Slave registered successfully",
        "slave_id": slave_id
    }), 200

@app.route('/submit-task', methods=['POST'])
def submit_task():
    data = request.json
    payload = data.get('payload')
    if not payload or not validate_expression(payload):
        return jsonify({"error": "Invalid expression"}), 400

    task = {
        "id": generate_task_id(),
        "payload": payload,
        "status": "pending",
        "assigned_to": None,
        "created_at": current_time(),
        "updated_at": current_time(),
        "result": None
    }


    idle_slave = None
    for slave_id, slave_info in slaves.items():
       try:
        res = requests.get(f"{slave_info['webhook']}/status/{slave_id}", timeout=3)

        if res.status_code == 200 and res.json().get("status") == "idle":
            idle_slave = {"id": slave_id, "url": slave_info['webhook']}
            break
       except Exception as e:
         print(f"Slave {slave_id} unreachable: {e}")

    if not idle_slave:
            return jsonify({"error": "No idle slave available"}), 503

    task["status"] = "assigned"
    task["assigned_to"] = idle_slave["id"]
    tasks.append(task)

    try:
        requests.post(f"{idle_slave['url']}/receive-task", json=task, timeout=3)
        slaves[slave_id]["status"]="busy"
        return jsonify({"message": f"Task assigned to slave {idle_slave['id']}","taskId":task['id']}), 201
    except Exception as e:
        print(f"Failed to send task to slave {idle_slave['id']}: {e}")
        return jsonify({"error": "Failed to assign task"}), 500

@app.route('/complete-task/<task_id>', methods=['POST'])
def complete_task(task_id):
    data = request.json
    result = data.get("result")

    with lock:
        
        # Mark the task as done
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "done"
                task["result"] = result
                task["updated_at"] = current_time()
                slaves[task['assigned_to']]['status']='free'
                return jsonify({"message": "Task marked as done"}), 200

    return jsonify({"error": "Task not found"}), 404


@app.route('/slaves', methods=['GET'])
def get_slaves():
    return jsonify(slaves), 200

@app.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(tasks), 200

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    with lock:
        for task in tasks:
            if task["id"] == task_id:
                return jsonify(task), 200
    return jsonify({"error": "Task not found"}), 404


def check_slave_health():
    """Function to periodically check the health of slaves."""
    while True:
        with lock:           
            for slave_id, slave in list(slaves.items()):  # Use list to allow modifying dict while iterating
                try:
                    # Perform health check on each slave
                    health_response = requests.get(f"{slave['webhook']}/health", timeout=5)
                    health_data = health_response.json()

                    # print("Slave reported ID:", health_data.get('id'))

                    if health_response.status_code != 200 or health_data.get('id') != slave_id:
                        print(f"Slave {slave_id} is unhealthy or mismatched. Removing...")
                        del slaves[slave_id]
                except requests.RequestException as e:
                    print(f"Slave {slave_id} is unreachable. Removing... Error: {e}")
                    del slaves[slave_id]

        # Wait 5 seconds before checking again
        time.sleep(5)
        
if __name__ == '__main__':
    health_check_thread = Thread(target=check_slave_health, daemon=True)
    health_check_thread.start()
    app.run(host='0.0.0.0', port=port,debug=True)
