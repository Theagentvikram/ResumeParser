#!/usr/bin/env python3
"""
Script to run the ResuMatch backend server with proper path setup
"""
import os
import sys
import subprocess
import signal
import time

def kill_existing_servers():
    """Kill any existing uvicorn servers"""
    print("Checking for existing backend servers...")
    try:
        # Find any running uvicorn processes
        ps_output = subprocess.check_output(["ps", "aux"]).decode("utf-8")
        for line in ps_output.split("\n"):
            if "uvicorn" in line and "main:app" in line:
                # Extract the PID
                pid = int(line.split()[1])
                print(f"Killing existing uvicorn process with PID {pid}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)  # Give it time to shut down
    except Exception as e:
        print(f"Error checking for existing servers: {e}")

def main():
    """Run the backend server"""
    # Kill any existing servers
    kill_existing_servers()
    
    # Get the absolute path to the backend directory
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    
    # Set environment variables
    env = os.environ.copy()
    env["ANALYZER_MODE"] = "api"
    env["PYTHONPATH"] = backend_dir + ":" + env.get("PYTHONPATH", "")
    
    # Change to the backend directory
    os.chdir(backend_dir)
    
    # Start the server
    print(f"Starting backend server from {backend_dir}")
    cmd = ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    
    try:
        # Run the server
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
