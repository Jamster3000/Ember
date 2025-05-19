#!/usr/bin/env python3
"""
File Watcher Script for ASM Flowchart Generator

This script monitors assembly files in the specified directory and automatically
runs the auto_flowchart_3000.py script whenever changes are detected.
"""

import time
import os
import sys
import subprocess
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Path to the auto_flowchart script
FLOWCHART_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_flowchart_3000.py')

# File extensions to monitor
EXTENSIONS_TO_WATCH = ['.asm', '.s', '.inc']

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path
        self.last_run_time = 0
        self.cooldown_period = 2  # seconds

    def on_any_event(self, event):
        # Skip directory events or non-create/modify events
        if event.is_directory or event.event_type not in ['created', 'modified']:
            return
        
        # Only process assembly files
        if not any(event.src_path.endswith(ext) for ext in EXTENSIONS_TO_WATCH):
            return
            
        # Implement cooldown to prevent multiple rapid executions
        current_time = time.time()
        if current_time - self.last_run_time < self.cooldown_period:
            return
            
        self.last_run_time = current_time
            
        # Log the change
        logger.info(f"Change detected in {event.src_path}")
        
        # Run the auto_flowchart script
        self.run_flowchart_generator()
        
    def run_flowchart_generator(self):
        """Run the auto_flowchart_3000.py script"""
        try:
            logger.info(f"Running flowchart generator: {self.script_path}")
            result = subprocess.run(
                [sys.executable, self.script_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Flowchart generation completed successfully")
                if result.stdout:
                    logger.info(f"Output: {result.stdout.strip()}")
            else:
                logger.error(f"Flowchart generation failed with code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr.strip()}")
                    
        except Exception as e:
            logger.error(f"Error running flowchart generator: {e}")

def watch_directory(path_to_watch, script_path):
    """Set up and start the file system observer"""
    event_handler = ChangeHandler(script_path)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()
    
    logger.info(f"Watching for changes in {path_to_watch}")
    logger.info(f"Will run {script_path} on changes")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Watcher stopped")
    
    observer.join()

if __name__ == "__main__":
    # Default to the current directory
    path_to_watch = os.path.dirname(os.path.abspath(__file__))
    
    # Allow command-line override of directory to watch
    if len(sys.argv) > 1:
        path_to_watch = sys.argv[1]
        
    # Verify that the flowchart script exists
    if not os.path.exists(FLOWCHART_SCRIPT):
        logger.error(f"Flowchart script not found at {FLOWCHART_SCRIPT}")
        sys.exit(1)
        
    watch_directory(path_to_watch, FLOWCHART_SCRIPT)
