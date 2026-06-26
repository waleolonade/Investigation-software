"""
LEIP Terminal Execution Engine
Executes Python code and Shell commands with secure audit logging.
"""

import sys
import os
import io
import time
import subprocess
import traceback
import logging
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from datetime import datetime

# Import database & configuration
from config.settings import settings
from app.database import SessionLocal
from app import models, crud, schemas

logger = logging.getLogger(__name__)

def log_audit_action(mode: str, command: str, success: bool, duration: float):
    """Log terminal execution action to an audit trail file"""
    try:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        audit_file = log_dir / "audit_trail.log"
        
        timestamp = datetime.now().isoformat()
        status_str = "SUCCESS" if success else "FAILED"
        
        log_entry = f"[{timestamp}] MODE: {mode.upper()} | STATUS: {status_str} | DURATION: {duration:.4f}s\n"
        log_entry += f"COMMAND/CODE:\n{command}\n"
        log_entry += "=" * 80 + "\n"
        
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Failed to write to audit trail: {e}")

def execute_python_code(code: str) -> dict:
    """Executes Python code in a sandboxed context and redirects stdout/stderr"""
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    
    t0 = time.time()
    success = True
    
    # Create DB session for the duration of execution
    db = SessionLocal()
    
    # Pre-populate globals
    exec_globals = {
        "db": db,
        "models": models,
        "crud": crud,
        "schemas": schemas,
        "settings": settings,
        "SessionLocal": SessionLocal,
        "sys": sys,
        "os": os,
        "time": time,
    }
    
    # Attempt to import optional AI modules if present
    try:
        from app.yolo_detector import YOLODetector
        exec_globals["YOLODetector"] = YOLODetector
    except Exception:
        pass
    
    try:
        from app.face_utils import LEIPFaceMatcher
        exec_globals["LEIPFaceMatcher"] = LEIPFaceMatcher
    except Exception:
        pass
    
    try:
        from app.plate_recognition import LicensePlateRecognizer
        exec_globals["LicensePlateRecognizer"] = LicensePlateRecognizer
    except Exception:
        pass
    
    try:
        import numpy as np
        exec_globals["np"] = np
    except ImportError:
        pass
        
    try:
        import pandas as pd
        exec_globals["pd"] = pd
    except ImportError:
        pass
        
    try:
        import cv2
        exec_globals["cv2"] = cv2
    except ImportError:
        pass

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            # Execute the code
            exec(code, exec_globals)
    except Exception as e:
        success = False
        traceback.print_exc(file=stderr_buf)
    finally:
        db.close()
        
    execution_time = time.time() - t0
    
    # Log to audit trail
    log_audit_action("python", code, success, execution_time)
    
    return {
        "success": success,
        "stdout": stdout_buf.getvalue(),
        "stderr": stderr_buf.getvalue(),
        "execution_time": execution_time
    }

def execute_shell_command(command: str) -> dict:
    """Executes a system shell command inside the leip directory"""
    t0 = time.time()
    success = True
    stdout = ""
    stderr = ""
    
    try:
        # Run command in the leip directory (parent of app)
        leip_dir = Path(__file__).parent.parent
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=leip_dir,
            capture_output=True,
            text=True,
            timeout=30  # Timeout to prevent hanging terminal
        )
        stdout = result.stdout
        stderr = result.stderr
        if result.returncode != 0:
            success = False
            # If stderr is empty but return code is non-zero, indicate error in stderr
            if not stderr:
                stderr = f"Command failed with exit status {result.returncode}"
    except subprocess.TimeoutExpired as e:
        success = False
        stdout = e.stdout or ""
        stderr = f"Error: Command timed out after 30 seconds.\n{e.stderr or ''}"
    except Exception as e:
        success = False
        stderr = f"Execution error: {str(e)}\n{traceback.format_exc()}"
        
    execution_time = time.time() - t0
    log_audit_action("shell", command, success, execution_time)
    
    return {
        "success": success,
        "stdout": stdout,
        "stderr": stderr,
        "execution_time": execution_time
    }
