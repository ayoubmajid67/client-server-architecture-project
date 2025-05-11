from flask import Flask, request, jsonify
import requests
import sys
import socket
from utils import evaluate_expression
import time
import threading
from threading import Thread

MASTER_URL = "http://localhost:5000"
SLAVE_ID = None  # Will be set after registration
status = {"state": "idle"}

app = Flask(__name__)

def get_my_ip():
    try:
        # Create a socket connection to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "localhost"  # Fallback to localhost if IP detection fails


@app.route('/register-slave-api/<slave_id>', methods=["POST"])
def register_slave_api(slave_id):
    global SLAVE_ID
    SLAVE_ID = slave_id.strip()
    print(f"[INFO] Slave ID has been set to: {SLAVE_ID}")
    return jsonify({"message": f"Slave ID set to {SLAVE_ID}"}), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "state": status["state"],
        "id":SLAVE_ID
    }), 200

@app.route('/receive-task', methods=['POST'])
def receive_task():
    global status
    task = request.json
    print(f"[{SLAVE_ID}] Received task: {task['payload']}")

    if status["state"] != "idle":
        return jsonify({"error": "Slave is busy"}), 503

    status["state"] = "busy"

    def process_task():
        global status
        try:
            result = evaluate_expression(task["payload"])
            time.sleep(7)  # Simulate processing delay
            requests.post(f"{MASTER_URL}/complete-task/{task['id']}", json={"result": result})
            status["state"] = "idle"
            print(f"[{SLAVE_ID}] Completed task with result: {result}")
        except Exception as e:
            print(f"[{SLAVE_ID}] Error processing task: {e}")


    # Start task processing in a separate thread
    Thread(target=process_task).start()

    return jsonify({"message": "Task accepted and is being processed"}), 200

@app.route('/status/<slave_id>', methods=['GET'])
def get_status(slave_id):
    if slave_id != SLAVE_ID:
        return jsonify({"error": "Wrong slave id"}), 400
    return jsonify({"id": SLAVE_ID, "status": status["state"]}), 200





def register(webhook_port):
    global SLAVE_ID
    url = f"http://{get_my_ip()}:{webhook_port}"
    print("url :" , url)
    try:
        res = requests.post(f"{MASTER_URL}/register-slave", json={
            "webhook_url": url
        })
        if res.status_code == 200:
            data = res.json()
            SLAVE_ID = data["slave_id"]

            print("the salve is running on ", get_my_ip())
            print(f"[{SLAVE_ID}] Registered to master successfully")
        else:
            raise Exception(f"Registration failed: {res.json().get('error', 'Unknown error')}")
    except Exception as e:
        print("Registration failed")
        raise Exception(f"Registration failed: {e}")
        
def run_temp_server(port):
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python slave.py <port>")
        sys.exit(1)
    
    port = int(sys.argv[1])

    try:
        # Start the Flask server in the main thread
        print(f"Starting slave server on port {port}...")
        server_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False))
        server_thread.daemon = True
        server_thread.start()

        # Wait for 2 seconds to give the server time to start
        time.sleep(2)

        # Attempt to register after waiting
        try:
            register(port)
        except Exception as e:
            print(f"Registration failed: {e}")
            sys.exit(1)

        # If registration is successful, continue the server
        print("Registration successful. Slave is ready.")
        server_thread.join()  # Wait for the server thread to finish

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
