"""
LEIP - Quick Start & Installation Guide
Step-by-step setup for Windows, Mac, and Linux
"""

# ============================================================================
# LEIP QUICK START GUIDE
# ============================================================================

STEP_1_PREREQUISITES = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ STEP 1: PREREQUISITES & ENVIRONMENT SETUP                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

REQUIRED:
  - Python 3.11 or 3.12 (Download from python.org)
  - Git (Download from git-scm.com)
  - 8GB+ RAM (16GB recommended)
  - 10GB free disk space (for models)

OPTIONAL BUT RECOMMENDED:
  - Docker & Docker Compose (for containerized deployment)
  - PostgreSQL 15+ (for production database)
  - CUDA Toolkit (for GPU acceleration)

INSTALLATION:

  Windows:
    1. Download Python 3.12 from python.org
    2. Run installer, CHECK "Add Python to PATH"
    3. Download Git from git-scm.com
    4. Open Command Prompt or PowerShell

  Mac:
    brew install python@3.12
    brew install git

  Linux (Ubuntu/Debian):
    sudo apt update
    sudo apt install python3.12 python3.12-venv git

VERIFY INSTALLATION:
    python --version    # Should show 3.11+
    git --version       # Should show 2.0+
"""

STEP_2_PROJECT_SETUP = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ STEP 2: PROJECT SETUP                                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

1. CLONE PROJECT (if using Git):
    git clone <your-repo-url>
    cd leip

   OR Extract the project folder

2. CREATE VIRTUAL ENVIRONMENT:

    Windows (Command Prompt):
      python -m venv venv
      venv\\Scripts\\activate

    Windows (PowerShell):
      python -m venv venv
      .\\venv\\Scripts\\Activate.ps1

    Mac/Linux:
      python3.12 -m venv venv
      source venv/bin/activate

   You should see (venv) in your terminal prompt

3. UPGRADE PIP:
    python -m pip install --upgrade pip

4. INSTALL DEPENDENCIES:
    pip install -r requirements.txt

   ⏳ This takes 5-15 minutes (first time)
   ⚠ If CUDA issues appear, reinstall as:
      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

5. CONFIGURE ENVIRONMENT:
    cp .env.example .env

   Then edit .env file with your settings (important for database, API keys, etc.)
"""

STEP_3_VERIFY_INSTALLATION = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ STEP 3: VERIFY INSTALLATION                                              ║
╚═══════════════════════════════════════════════════════════════════════════╝

Run initialization script to verify all modules:

    python init.py

Expected output:
    ✓ Face Recognition module
    ✓ YOLO Detection module
    ✓ CCTV Processing module
    ✓ License Plate Recognition module
    ✓ FastAPI Backend

If all show "✓ PASS", proceed to Step 4.

If any fail:
    - Check error message
    - Ensure all packages installed: pip install -r requirements.txt
    - Check Python version: python --version
"""

STEP_4_START_API = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ STEP 4: START API SERVER                                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

Make sure you're in the leip directory and (venv) is active.

RUN API SERVER:
    python -m uvicorn app.api:app --reload

You should see:
    Uvicorn running on http://127.0.0.1:8000
    Reload enabled
    
The API is now running! Visit:
    http://localhost:8000/docs      (Interactive API documentation)
    http://localhost:8000/health    (Health check)

KEEP THIS TERMINAL OPEN. Do not close it.
"""

STEP_5_START_DASHBOARD = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ STEP 5: START DASHBOARD (NEW TERMINAL)                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

OPEN A NEW TERMINAL/COMMAND PROMPT IN THE LEIP FOLDER.

ACTIVATE VIRTUAL ENVIRONMENT:

    Windows:
      venv\\Scripts\\activate

    Mac/Linux:
      source venv/bin/activate

START STREAMLIT DASHBOARD:
    streamlit run frontend/app.py

You should see:
    You can now view your Streamlit app in your browser.
    Local URL: http://localhost:8501

OPEN IN BROWSER:
    Click the link or go to: http://localhost:8501
"""

STEP_6_FIRST_RUN = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ STEP 6: FIRST RUN - TEST THE SYSTEM                                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

Dashboard is now open at http://localhost:8501

1. EXPLORE THE DASHBOARD:
   - Click "Face Recognition" tab
   - Upload a test image to the gallery
   - Try the "Search Gallery" feature
   
2. TEST API DIRECTLY:
   - Go to http://localhost:8000/docs
   - Try POST /api/v1/faces/search
   - Upload a test image
   - See detections returned as JSON

3. CREATE A TEST CASE:
   - Go to "Case Management" tab
   - Click "New Case"
   - Create a test investigation case

NEXT STEPS:
   1. Prepare your CCTV video files or stream URLs
   2. Add suspect faces to the gallery
   3. Process CCTV footage
   4. Investigate detections and matches
"""

STEP_7_DEPLOYMENT = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ STEP 7: PRODUCTION DEPLOYMENT (Optional)                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

FOR LOCAL DEPLOYMENT (Current Setup):
    ✓ Already running with development settings
    ✓ API at http://localhost:8000
    ✓ Dashboard at http://localhost:8501

FOR DOCKER DEPLOYMENT:
    
    1. Install Docker Desktop
    2. Run: docker-compose up -d
    3. Services start on:
       - API: http://localhost:8000
       - Dashboard: http://localhost:8501
       - PostgreSQL: localhost:5432
       - Prometheus: http://localhost:9090

FOR PRODUCTION SERVER:
    
    1. Set DEBUG_MODE=false in .env
    2. Use PostgreSQL instead of SQLite
    3. Configure real API keys
    4. Set SECRET_KEY to random string: python -c "import secrets; print(secrets.token_urlsafe(32))"
    5. Use proper reverse proxy (Nginx)
    6. Enable HTTPS/TLS
    7. Configure authentication (JWT tokens)
    8. Enable role-based access control (RBAC)
    9. Set up monitoring (Prometheus/Grafana)
    10. Configure audit logging

SECURITY CHECKLIST:
    ☐ Changed default passwords
    ☐ Set SECRET_KEY to random value
    ☐ Enabled RBAC
    ☐ Configured HTTPS/TLS
    ☐ Set up authentication
    ☐ Enabled audit logging
    ☐ Configured database backups
    ☐ Reviewed data retention policies
    ☐ Tested with authorized law enforcement only
"""

TROUBLESHOOTING = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ TROUBLESHOOTING GUIDE                                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

ISSUE: "python: command not found" or "python not in PATH"
SOLUTION:
    - Python not installed or not in PATH
    - Windows: Reinstall Python, CHECK "Add to PATH"
    - Linux: Try "python3" instead of "python"

ISSUE: "No module named 'face_utils'" or import errors
SOLUTION:
    - Not in the correct directory
    - Check: pwd (should end with /leip)
    - Missing imports: pip install -r requirements.txt
    - Restart terminal and reactivate venv

ISSUE: "CUDA out of memory" or GPU errors
SOLUTION:
    - Set in .env: YOLO_DEVICE=cpu
    - Reinstall PyTorch for CPU: pip install torch --index-url https://download.pytorch.org/whl/cpu

ISSUE: Dashboard or API not responding
SOLUTION:
    - Check if both are running (API and Streamlit)
    - API terminal should show "Uvicorn running on http://127.0.0.1:8000"
    - Streamlit terminal should show "Local URL: http://localhost:8501"
    - Try restarting both

ISSUE: "No space left on device"
SOLUTION:
    - Models require ~5GB
    - Check disk space: df -h (Mac/Linux) or disk management (Windows)
    - Delete unnecessary files or expand storage

ISSUE: Face detection/recognition not working
SOLUTION:
    - Model downloads on first use (takes 2-5 minutes)
    - Check internet connection
    - Check logs: tail -f logs/leip.log
    - Try with a different image

ISSUE: Video processing is slow
SOLUTION:
    - Set frame_skip to higher value (e.g., 10 instead of 5)
    - Use smaller YOLO model: YOLO_MODEL_SIZE=nano
    - Enable CUDA if available
    - Process multiple videos in parallel (batch processing)

GETTING HELP:
    1. Check logs: logs/leip.log
    2. Run: python init.py (to test modules)
    3. Check GitHub issues/documentation
    4. Contact system administrator
"""

QUICK_REFERENCE = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ QUICK REFERENCE - COMMON COMMANDS                                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

ACTIVATE ENVIRONMENT:
    Windows: venv\\Scripts\\activate
    Mac/Linux: source venv/bin/activate

START API:
    python -m uvicorn app.api:app --reload

START DASHBOARD:
    streamlit run frontend/app.py

RUN TESTS:
    pytest tests/ -v

CHECK LOGS:
    tail -f logs/leip.log        (Mac/Linux)
    type logs\\leip.log          (Windows)

VIEW API DOCS:
    http://localhost:8000/docs

VIEW DASHBOARD:
    http://localhost:8501

DEACTIVATE ENVIRONMENT:
    deactivate

INSTALL NEW PACKAGE:
    pip install package_name

SAVE REQUIREMENTS:
    pip freeze > requirements.txt

DATABASE:
    psql -U leip_user -d leip_db              (PostgreSQL)
    ALTER DATABASE leip_db OWNER TO leip_user;

DOCKER:
    docker-compose up -d                      (Start)
    docker-compose down                       (Stop)
    docker-compose logs -f api               (View logs)

CLEAN UP:
    rm -rf venv                              (Remove venv)
    find . -type d -name __pycache__ -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
"""

API_ENDPOINTS_QUICK = """
╔═══════════════════════════════════════════════════════════════════════════╗
║ KEY API ENDPOINTS                                                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

HEALTH & INFO:
    GET  /health                              System health check
    GET  /api/v1/info                         System information

FACE RECOGNITION:
    POST /api/v1/faces/upload                 Add face to gallery
    POST /api/v1/faces/search                 Search gallery (1:N)
    POST /api/v1/faces/verify                 Verify match (1:1)

CCTV & VIDEO:
    POST /api/v1/cctv/process-video          Process video file
    GET  /api/v1/cctv/job/{job_id}           Get processing status

CASES:
    POST /api/v1/cases                        Create new case
    GET  /api/v1/cases/{case_id}              Get case details
    GET  /api/v1/cases                        List all cases

VEHICLES:
    POST /api/v1/vehicles/track               Track vehicle by plate

REPORTS:
    POST /api/v1/reports/case-summary         Generate case report

Full API docs: http://localhost:8000/docs
"""

if __name__ == "__main__":
    print(STEP_1_PREREQUISITES)
    print("\n\n")
    print(STEP_2_PROJECT_SETUP)
    print("\n\n")
    print(STEP_3_VERIFY_INSTALLATION)
    print("\n\n")
    print(STEP_4_START_API)
    print("\n\n")
    print(STEP_5_START_DASHBOARD)
    print("\n\n")
    print(STEP_6_FIRST_RUN)
    print("\n\n")
    print(STEP_7_DEPLOYMENT)
    print("\n\n")
    print(TROUBLESHOOTING)
    print("\n\n")
    print(QUICK_REFERENCE)
    print("\n\n")
    print(API_ENDPOINTS_QUICK)
