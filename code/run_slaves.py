import subprocess
import sys
import time
import os
import signal

def run_slave(port):
    try:
        # Start slave as a subprocess and get its PID
        slave_process = subprocess.Popen([sys.executable, 'slave.py', str(port)])
        print(f"Started slave on port {port}, PID: {slave_process.pid}")
        return slave_process  # Return the process to track it
    except Exception as e:
        print(f"Failed to start slave on port {port}: {e}")
        return None

if __name__ == "__main__":
    # Define ports for different slaves
    ports = [6001, 6002, 6003]  # You can add more ports as needed
    
    # Start each slave and store their process objects
    slave_processes = []
    for port in ports:
        slave_process = run_slave(port)
        if slave_process:
            slave_processes.append(slave_process)
        time.sleep(1)  # Wait a bit between starting slaves
    
    print("All slaves started. Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all slaves...")
        
        # Stop all slave processes by sending a SIGTERM signal
        for slave_process in slave_processes:
            try:
                print(f"Stopping slave with PID {slave_process.pid}...")
                slave_process.terminate()  # Gracefully terminate slave process
                slave_process.wait()  # Wait for the process to terminate
            except Exception as e:
                print(f"Failed to stop slave: {e}")
