#!/usr/bin/env python3
"""
Script to check for and optionally kill processes using port 8081.
"""

import os
import argparse
import subprocess

def find_processes_using_port(port):
    """Find processes using the specified port."""
    try:
        # Using lsof to find processes using the port
        cmd = f"lsof -i :{port} -t"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            return []
        
        pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
        return pids
    except Exception as e:
        print(f"Error finding processes: {e}")
        return []

def get_process_info(pid):
    """Get information about a process."""
    try:
        cmd = f"ps -p {pid} -o pid,ppid,cmd,etime"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            return None
        
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return None
        
        return lines[1]
    except Exception as e:
        print(f"Error getting process info: {e}")
        return None

def kill_process(pid):
    """Kill a process by PID."""
    try:
        # First try a graceful termination with SIGTERM
        os.kill(pid, 15)  # SIGTERM
        print(f"Sent SIGTERM to process {pid}")
        
        # Check if process still exists after a short delay
        import time
        time.sleep(1)
        
        try:
            os.kill(pid, 0)  # Check if process exists
            # Process still exists, use SIGKILL
            os.kill(pid, 9)  # SIGKILL
            print(f"Sent SIGKILL to process {pid}")
        except OSError:
            # Process no longer exists
            pass
        
        return True
    except Exception as e:
        print(f"Error killing process {pid}: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check for and optionally kill processes using port 8081")
    parser.add_argument("--port", type=int, default=8081, help="Port to check")
    parser.add_argument("--kill", action="store_true", help="Kill processes using the port")
    parser.add_argument("--force", action="store_true", help="Force kill processes without confirmation")
    
    args = parser.parse_args()
    
    port = args.port
    print(f"Checking for processes using port {port}...")
    
    pids = find_processes_using_port(port)
    
    if not pids:
        print(f"No processes found using port {port}")
        return
    
    print(f"Found {len(pids)} process(es) using port {port}:")
    
    for pid in pids:
        info = get_process_info(pid)
        print(f"  PID {pid}: {info}")
    
    if args.kill:
        if not args.force:
            confirm = input("Do you want to kill these processes? (y/N): ")
            if confirm.lower() != 'y':
                print("Aborted.")
                return
        
        for pid in pids:
            print(f"Killing process {pid}...")
            success = kill_process(pid)
            if success:
                print(f"Successfully killed process {pid}")
            else:
                print(f"Failed to kill process {pid}")
    
    # Check if any processes are still using the port
    if args.kill:
        remaining_pids = find_processes_using_port(port)
        if not remaining_pids:
            print(f"All processes using port {port} have been killed.")
        else:
            print(f"Warning: {len(remaining_pids)} process(es) still using port {port}.")
            for pid in remaining_pids:
                info = get_process_info(pid)
                print(f"  PID {pid}: {info}")

if __name__ == "__main__":
    main()
