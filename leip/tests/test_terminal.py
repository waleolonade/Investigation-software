"""
LEIP Terminal Execution Tests
Tests for terminal execution functions and API endpoint
"""

import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.api import app
from app.terminal_executor import execute_python_code, execute_shell_command

def test_execute_python_success():
    """Test successful Python code execution"""
    code = "x = 5\ny = 10\nprint(f'Sum: {x + y}')"
    result = execute_python_code(code)
    
    assert result["success"] is True
    assert "Sum: 15" in result["stdout"]
    assert result["stderr"] == ""
    assert result["execution_time"] > 0

def test_execute_python_failure():
    """Test Python code execution failure captures traceback"""
    code = "x = 1 / 0"
    result = execute_python_code(code)
    
    assert result["success"] is False
    assert "ZeroDivisionError" in result["stderr"]
    assert result["stdout"] == ""

def test_execute_python_db_access():
    """Test that db session is pre-loaded and accessible"""
    code = "print(db)\nassert db is not None"
    result = execute_python_code(code)
    
    assert result["success"] is True
    assert "sqlalchemy.orm.session.Session" in result["stdout"]

def test_execute_shell_success():
    """Test successful shell command execution"""
    # Use 'echo' command which is cross-platform
    result = execute_shell_command("echo terminal_test_run")
    
    assert result["success"] is True
    assert "terminal_test_run" in result["stdout"].strip()
    assert result["stderr"] == ""

def test_execute_shell_failure():
    """Test shell command execution failure"""
    # A command that doesn't exist to trigger error/non-zero status
    result = execute_shell_command("nonexistentcommand12345")
    
    assert result["success"] is False
    assert result["stdout"] == ""
    # On Windows, command interpreter tells that nonexistentcommand12345 is not recognized
    # Or in unix it says not found. Either way, stderr should contain it or explain execution failure.
    assert len(result["stderr"]) > 0

def test_audit_trail_logging():
    """Test that code execution is logged to audit trail log"""
    # Trigger execution
    code = "print('audit logging test')"
    execute_python_code(code)
    
    audit_log = Path(__file__).parent.parent / "logs" / "audit_trail.log"
    assert audit_log.exists()
    
    # Read last few lines and assert it contains our log entry
    with open(audit_log, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "MODE: PYTHON" in content
    assert "audit logging test" in content

def test_api_terminal_endpoint():
    """Test FastAPI /api/v1/investigation/terminal endpoint requires auth"""
    with TestClient(app) as client:
        # Unauthenticated request should fail with 401
        payload = {"code": "print('test')", "mode": "python"}
        response = client.post("/api/v1/investigation/terminal", json=payload)
        assert response.status_code == 401
        
        # Authenticated request
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "investigator", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/v1/investigation/terminal",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "test" in body["stdout"]
