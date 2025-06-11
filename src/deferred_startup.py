"""
Deferred startup module for ProjectCatalog.

This module implements a startup strategy that prioritizes UI responsiveness
by starting background threads after the web server is ready to serve requests.
"""

import threading
import time
from bottle import run, default_app


class DeferredStartupManager:
    """Manages deferred startup of background threads for better UI responsiveness."""
    
    def __init__(self):
        self.background_threads_started = False
        self.startup_complete = False
        
    def start_web_server_first(self):
        """Start the web server immediately for instant UI availability."""
        print("Starting web server for immediate UI availability...")
        
        # Print the registered routes
        app = default_app()
        print("\\nRegistered routes:")
        for route in app.routes:
            print(f" - {route.method} {route.rule} -> {route.callback.__name__}")
        
        # Schedule background threads to start after a short delay
        startup_thread = threading.Thread(target=self._delayed_startup, daemon=True)
        startup_thread.name = "DeferredStartup"
        startup_thread.start()
        
        print("Web server starting on port 5001...")
        print("Background services will start automatically in a few seconds...")
        
        # Run the server
        run(host="0.0.0.0", port=5001, debug=True, reloader=True)
    
    def _delayed_startup(self):
        """Start background threads after a short delay to prioritize UI responsiveness."""
        # Wait a bit to ensure web server is responsive
        time.sleep(3)
        
        print("\\n" + "="*50)
        print("Starting background services...")
        print("="*50)
        
        self._start_background_threads()
        
        self.background_threads_started = True
        self.startup_complete = True
        
        print("Background services startup complete!")
        print("="*50 + "\\n")
    
    def _start_background_threads(self):
        """Start all background worker threads."""
        from src.projectcatalog import (
            analyze_projects_worker, 
            directory_watcher, 
            ANALYSIS_STATUS
        )
        
        # Initialize heartbeat
        ANALYSIS_STATUS['thread_heartbeat'] = time.time()
        
        # Start the analysis worker thread
        print("Creating analysis worker thread...")
        analysis_thread = threading.Thread(target=analyze_projects_worker, daemon=True)
        analysis_thread.name = "AnalysisWorker"
        analysis_thread.start()
        print(f"Analysis worker thread started: {analysis_thread.name}, is_alive={analysis_thread.is_alive()}")
        
        # Start the directory watcher thread
        print("Creating directory watcher thread...")
        watcher_thread = threading.Thread(target=directory_watcher, daemon=True)
        watcher_thread.name = "DirectoryWatcher"
        watcher_thread.start()
        print(f"Directory watcher thread started: {watcher_thread.name}, is_alive={watcher_thread.is_alive()}")
        
        # Start the heartbeat monitoring thread
        def monitor_heartbeat():
            """Monitor the analysis thread heartbeat and restart if needed."""
            while True:
                time.sleep(60)  # Check every minute
                from src.projectcatalog import is_analysis_thread_healthy, analyze_projects_worker
                
                if not is_analysis_thread_healthy():
                    print("Analysis thread appears to be stalled. Restarting...")
                    try:
                        # Create a new analysis thread
                        new_thread = threading.Thread(target=analyze_projects_worker, daemon=True)
                        new_thread.name = "AnalysisWorker"
                        new_thread.start()
                        print(f"Started new analysis thread: {new_thread.name}, is_alive={new_thread.is_alive()}")
                    except Exception as e:
                        print(f"Error starting new analysis thread: {e}")
        
        # Start the monitoring thread
        print("Creating heartbeat monitor thread...")
        monitor_thread = threading.Thread(target=monitor_heartbeat, daemon=True)
        monitor_thread.name = "HeartbeatMonitor"
        monitor_thread.start()
        print(f"Heartbeat monitor thread started: {monitor_thread.name}, is_alive={monitor_thread.is_alive()}")
    
    def get_startup_status(self):
        """Get the current startup status."""
        return {
            'background_threads_started': self.background_threads_started,
            'startup_complete': self.startup_complete
        }


def run_webserver_with_deferred_startup():
    """Run the web server with deferred background thread startup."""
    manager = DeferredStartupManager()
    manager.start_web_server_first()


# Global instance for startup status checking
startup_manager = DeferredStartupManager()
