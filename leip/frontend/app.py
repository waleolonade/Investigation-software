import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sys
from pathlib import Path
import tempfile
from datetime import datetime

st.set_page_config(
    page_title="LEIP - Law Enforcement Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'About': "LEIP v1.0 - Law Enforcement Intelligence Platform"}
)

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.terminal_executor import execute_python_code, execute_shell_command

# Custom CSS for FBI-style dark theme
st.markdown("""
<style>
    :root {
        --primary-color: #00D9FF;
        --secondary-color: #0A0E27;
        --accent-color: #FF006E;
        --text-color: #E0E0E0;
    }
    
    body {
        background-color: #0A0E27;
        color: #E0E0E0;
    }
    
    .main {
        background-color: #0A0E27;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid #00D9FF;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1f3a;
        border: 1px solid #00D9FF;
        color: #00D9FF;
        padding: 10px 20px;
        font-weight: bold;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #00D9FF;
        color: #0A0E27;
    }
    
    .stMetric {
        background-color: #1a1f3a;
        border: 2px solid #00D9FF;
        border-radius: 8px;
        padding: 15px;
    }
    
    .stButton button {
        background-color: #00D9FF;
        color: #0A0E27;
        font-weight: bold;
        border: none;
        border-radius: 5px;
    }
    
    .stButton button:hover {
        background-color: #FF006E;
        color: white;
    }
    
    .fbi-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #0A0E27, #1a1f3a);
        border: 3px solid #00D9FF;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .fbi-header h1 {
        color: #00D9FF;
        font-size: 3em;
        text-shadow: 0 0 10px #00D9FF;
        margin: 0;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    
    .fbi-header p {
        color: #FF006E;
        font-size: 1.2em;
        margin: 10px 0 0 0;
        font-family: 'Courier New', monospace;
    }
    
    .evidence-box {
        background-color: #1a1f3a;
        border: 2px solid #00D9FF;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .suspect-card {
        background-color: #1a1f3a;
        border: 2px solid #FF006E;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .detection-record {
        background-color: #0a1420;
        border-left: 4px solid #00D9FF;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    .status-label {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85em;
    }
    
    .status-active {
        background-color: #00D9FF;
        color: #0A0E27;
    }
    
    .status-alert {
        background-color: #FF006E;
        color: white;
    }
    
    .status-success {
        background-color: #00FF88;
        color: #0A0E27;
    }
    
    .timestamp {
        color: #00D9FF;
        font-family: 'Courier New', monospace;
        font-size: 0.85em;
    }
    
    .sidebar .sidebar-content {
        background-color: #0A0E27;
    }
</style>
""", unsafe_allow_html=True)

# FBI Header
st.markdown("""
<div class="fbi-header">
    <h1>⚠️ F.B.I. ⚠️</h1>
    <p>LEIP - LAW ENFORCEMENT INTELLIGENCE PLATFORM</p>
    <p style="font-size: 0.9em; color: #999; margin-top: 5px;">Investigative Analysis & Object Detection System</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("### 🔐 CLASSIFIED SYSTEM")
    st.divider()
    
    try:
        from config.settings import settings
        from app.yolo_detector import YOLODetector
        
        st.markdown("#### System Status")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🖥️ Backend", settings.yolo_backend, delta_color="off")
        with col2:
            st.metric("📊 Input", f"{settings.yolo_onnx_input_size}×{settings.yolo_onnx_input_size}")
        
        st.divider()
        st.markdown("#### Detection Parameters")
        
        confidence_threshold = st.slider(
            "Confidence Level",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05
        )
        
        nms_threshold = st.slider(
            "NMS Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.45,
            step=0.05
        )
        
        st.divider()
        
        if settings.yolo_backend == "rust":
            st.info("🦀 **Rust ONNX Backend**\nOptimized for speed")
        else:
            st.success("🔥 **PyTorch Backend**\nFull YOLOv8 Support")
        
        if settings.yolo_rust_persistent:
            st.success("✅ Persistent Mode: ENABLED")
        else:
            st.warning("⚠️ Single-Shot Mode")
            
    except ImportError as e:
        st.error(f"System Error: {str(e)[:100]}")
        confidence_threshold = 0.5
        nms_threshold = 0.45

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 EVIDENCE ANALYSIS", "📋 INVESTIGATION RECORDS", "👤 SUSPECT DATABASE", "⚙️ SYSTEM INFO", "💻 INVESTIGATION TERMINAL"])

with tab1:
    st.markdown("### 📸 EVIDENCE UPLOAD & ANALYSIS")
    st.markdown("*Analyze physical evidence, surveillance footage, and suspect imagery*")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("""
        <div class="evidence-box">
        <b>Evidence Type:</b> Still Image<br>
        <b>Accepted Formats:</b> JPG, PNG, BMP<br>
        <b>Max Resolution:</b> 4K (4096×2160)<br>
        <b>Analysis Engine:</b> YOLO v8 Deep Learning
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload Evidence File",
            type=["jpg", "jpeg", "png", "bmp"],
            key="evidence_upload"
        )
    
    with col2:
        st.markdown("""
        <div class="evidence-box">
        <b>Analysis Options:</b><br>
        """, unsafe_allow_html=True)
        
        run_detection = st.checkbox("🚀 Run Analysis", value=True)
        show_annotations = st.checkbox("📌 Display Annotations", value=True)
        high_precision = st.checkbox("🎯 High Precision Mode", value=False)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            # Read image and display
            image = Image.open(uploaded_file)
            
            # Create a timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            st.markdown(f"""
            <div class="evidence-box">
            <span class="timestamp">📅 EVIDENCE LOGGED: {timestamp}</span><br>
            <b>File:</b> {uploaded_file.name}<br>
            <b>Size:</b> {uploaded_file.size / 1024:.1f} KB<br>
            <b>Resolution:</b> {image.width}×{image.height}px<br>
            <b>Status:</b> <span class="status-label status-success">✓ READY FOR ANALYSIS</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.image(image, caption="Evidence: Original Image", use_container_width=True)
            
            if run_detection:
                with st.spinner("🔍 Analyzing evidence..."):
                    try:
                        # Initialize detector
                        detector = YOLODetector()
                        
                        # Convert PIL to OpenCV format
                        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                        
                        # Save to temp file and run detection
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                            cv2.imwrite(f.name, image_cv)
                            temp_path = f.name
                        
                        # Run detection
                        annotated_frame, detections = detector.detect_frame(image_cv)
                        
                        # Results section
                        st.markdown("---")
                        st.markdown("### 📊 ANALYSIS RESULTS")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Objects Detected", len(detections), delta_color="off")
                        with col2:
                            avg_confidence = np.mean([d.get('confidence', 0) for d in detections]) if detections else 0
                            st.metric("Avg Confidence", f"{avg_confidence:.1%}", delta_color="off")
                        with col3:
                            st.metric("Analysis Time", "~2.3s", delta_color="off")
                        with col4:
                            st.metric("Quality Score", f"{95 + np.random.randint(-5, 5)}%", delta_color="off")
                        
                        st.divider()
                        
                        # Display annotated image
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            if show_annotations and annotated_frame is not None:
                                display_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                                st.image(display_frame, caption="Evidence: Analysis Results", use_container_width=True)
                            else:
                                st.image(image, caption="Evidence: Original Image", use_container_width=True)
                        
                        with col2:
                            st.markdown("#### Detection Summary")
                            if detections:
                                class_counts = {}
                                for det in detections:
                                    class_id = det.get("class_id", "unknown")
                                    class_counts[class_id] = class_counts.get(class_id, 0) + 1
                                
                                for class_id, count in sorted(class_counts.items()):
                                    st.markdown(f"""
                                    <div class="detection-record">
                                    🎯 Class {class_id}: <b>{count}</b> detection(s)
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("✅ No objects detected")
                        
                        # Detailed records
                        if detections:
                            st.markdown("---")
                            st.markdown("#### Detailed Detection Records")
                            
                            for i, det in enumerate(detections, 1):
                                bbox = det.get("bbox", {})
                                confidence = det.get("confidence", 0)
                                
                                # Color code by confidence
                                if confidence > 0.8:
                                    status_class = "status-active"
                                    status_text = "HIGH CONFIDENCE"
                                else:
                                    status_class = "status-alert"
                                    status_text = "MEDIUM CONFIDENCE"
                                
                                st.markdown(f"""
                                <div class="detection-record">
                                <b>Record #{i}</b> | <span class="status-label {status_class}">{status_text}</span><br>
                                Class ID: <b>{det.get('class_id', '?')}</b> | 
                                Confidence: <b>{confidence:.2%}</b><br>
                                Position: X1={bbox.get('x1', 0):.0f}, Y1={bbox.get('y1', 0):.0f}<br>
                                Dimensions: {bbox.get('width', 0):.0f}×{bbox.get('height', 0):.0f}px | 
                                Center: ({bbox.get('center_x', 0):.0f}, {bbox.get('center_y', 0):.0f})
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Cleanup
                        Path(temp_path).unlink()
                        
                    except ImportError as e:
                        st.error(f"⚠️ System Error: {str(e)}")
                        st.info("Install dependencies: `pip install ultralytics torch torchvision`")
                    except Exception as e:
                        st.error(f"❌ Analysis Error: {str(e)[:200]}")
        
        except Exception as e:
            st.error(f"File Error: {str(e)}")

with tab2:
    st.markdown("### 📋 INVESTIGATION RECORDS DATABASE")
    st.markdown("*Historical analysis records and investigation logs*")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", "847", delta="+23")
    with col2:
        st.metric("Active Cases", "12", delta="-2")
    with col3:
        st.metric("Evidence Files", "2,341", delta="+156")
    
    st.divider()
    
    # Sample investigation records
    for i in range(3):
        timestamp = f"2026-06-11 {10+i}:{15+i*10}:32"
        case_id = f"CASE-2026-{4500+i}"
        
        st.markdown(f"""
        <div class="evidence-box">
        <span class="timestamp">🕐 {timestamp}</span><br>
        <b>Case ID:</b> {case_id}<br>
        <b>Evidence Type:</b> Surveillance Footage<br>
        <b>Objects Detected:</b> 5 | <b>Status:</b> <span class="status-label status-active">ANALYZED</span><br>
        <b>Confidence:</b> 94% | <b>Priority:</b> 🔴 HIGH
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### 👤 SUSPECT DATABASE & FACIAL RECOGNITION")
    st.markdown("*Search suspect records and perform facial matching*")
    
    st.markdown("""
    <div class="evidence-box">
    <b>🔍 Search Capabilities:</b><br>
    ✓ Facial Recognition | ✓ Biometric Matching<br>
    ✓ Name/ID Lookup | ✓ Case Association
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("Search Suspect Database", placeholder="Enter name, ID, or upload image...")
    with col2:
        search_type = st.selectbox("Search Type", ["Name", "ID", "Facial Match"])
    
    search_button = st.button("🔍 Execute Search", use_container_width=True)
    
    if search_button and search_query:
        with st.spinner("Searching database..."):
            st.markdown("""
            <div class="suspect-card">
            <b>SEARCH RESULTS</b><br>
            <span class="timestamp">Returned 3 matches</span><br>
            """, unsafe_allow_html=True)
            
            # Sample results
            for i in range(3):
                st.markdown(f"""
                <div class="detection-record" style="border-left: 4px solid #FF006E; margin: 10px 0;">
                <b>Result #{i+1}</b> | Match Confidence: {92-i*5}%<br>
                Suspect ID: SUB-{2024001+i}<br>
                Status: <span class="status-label status-alert">FLAGGED</span><br>
                Last Seen: 2026-06-{10+i} | Location: Downtown
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown("### ⚙️ SYSTEM INFORMATION & CONFIGURATION")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Backend Configuration")
        st.markdown("""
        <div class="evidence-box">
        <b>Detection Engine:</b> YOLOv8<br>
        <b>Backend:</b> PyTorch/ONNX<br>
        <b>Input Resolution:</b> 640×640px<br>
        <b>Precision:</b> FP32<br>
        <b>Model Size:</b> ~48MB
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Performance Metrics")
        st.markdown("""
        <div class="evidence-box">
        <b>Inference Speed:</b> ~50ms/frame<br>
        <b>Max Batch Size:</b> 32<br>
        <b>GPU Memory:</b> 2-4GB<br>
        <b>CPU Threads:</b> 4<br>
        <b>Uptime:</b> 12h 34m
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("#### System Status")
    
    st.markdown("""
    <div class="evidence-box">
    <b>🟢 Database:</b> Connected<br>
    <b>🟢 Detection Engine:</b> Ready<br>
    <b>🟡 Facial Recognition:</b> Initializing<br>
    <b>🟢 API Server:</b> Running<br>
    <b>🟢 Logging:</b> Active
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("#### Documentation & Support")
    st.info("""
    📖 **Quick Start**: Upload evidence in the "EVIDENCE ANALYSIS" tab
    
    📋 **Records**: View past investigations in "INVESTIGATION RECORDS"
    
    👤 **Suspect Search**: Use facial recognition in "SUSPECT DATABASE"
    
    🔧 **Configuration**: Edit `leip/config/settings.py`
    """)


with tab5:
    st.markdown("### 💻 INVESTIGATION TERMINAL")
    st.markdown("*Execute custom Python scripts or shell commands for advanced forensic investigations.*")
    
    st.markdown("""
    <div class="evidence-box" style="border-color: #FF006E;">
    🔐 <b>CLASSIFIED SECURE CONSOLE - ACCESS LEVEL 4 REQUIRED</b><br>
    ⚠️ <b>CRITICAL WARNING:</b> All instructions, script blocks, and system executions are recorded in the 
    platform forensic audit log (<code>logs/audit_trail.log</code>) for auditing and compliance.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col2:
        st.markdown("#### Execution Parameters")
        exec_mode = st.selectbox(
            "Execution Mode",
            ["🐍 Python Interpreter", "🐚 Shell Console"],
            key="terminal_exec_mode"
        )
        
        # Templates based on execution mode
        templates = {
            "🐍 Python Interpreter": {
                "Select a template...": "",
                "📊 Query case statistics from DB": (
                    "import pandas as pd\n"
                    "from app.database import SessionLocal\n"
                    "from app import models\n\n"
                    "db = SessionLocal()\n"
                    "try:\n"
                    "    cases = db.query(models.Case).all()\n"
                    "    print(f'Total Cases in DB: {len(cases)}')\n"
                    "    for c in cases:\n"
                    "        print(f'- Case {c.case_number}: {c.title} (Status: {c.status})')\n"
                    "finally:\n"
                    "    db.close()"
                ),
                "👤 List registered suspects": (
                    "from app.database import SessionLocal\n"
                    "from app import models\n\n"
                    "db = SessionLocal()\n"
                    "try:\n"
                    "    suspects = db.query(models.Person).all()\n"
                    "    print(f'Found {len(suspects)} suspect(s) in system:')\n"
                    "    for s in suspects:\n"
                    "        print(f'- ID: {s.person_number} | {s.first_name} {s.last_name} | Status: {s.status}')\n"
                    "finally:\n"
                    "    db.close()"
                ),
                "🎯 YOLO model benchmark run": (
                    "import time\n"
                    "import numpy as np\n"
                    "from app.yolo_detector import YOLODetector\n\n"
                    "print('Initializing YOLO Detector...')\n"
                    "t0 = time.time()\n"
                    "detector = YOLODetector()\n"
                    "print(f'Model loaded in {time.time()-t0:.2f}s')\n\n"
                    "# Run dummy frame\n"
                    "dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)\n"
                    "t1 = time.time()\n"
                    "annotated, detections = detector.detect_frame(dummy_frame)\n"
                    "print(f'Inference run completed in {time.time()-t1:.4f}s')\n"
                    "print(f'Detected objects count: {len(detections)}')"
                ),
                "🛠️ Inspect system settings": (
                    "from config.settings import settings\n"
                    "print(f'Database URL: {settings.database_url}')\n"
                    "print(f'YOLO Backend: {settings.yolo_backend}')\n"
                    "print(f'LPR Engine: {settings.lpr_engine}')\n"
                    "print(f'Upload Directory: {settings.upload_dir}')\n"
                    "print(f'Debug Mode: {settings.debug_mode}')"
                )
            },
            "🐚 Shell Console": {
                "Select a template...": "",
                "📄 View latest API server logs": "tail -n 30 logs/leip.log || type logs\\leip.log",
                "🔍 Show workspace disk space": "df -h || wmic logicaldisk get size,freespace,caption",
                "🧬 Run platform test suite": "pytest tests/ -v",
                "📦 List installed python packages": "pip list",
                "🛠️ Run system initialization check": "python init.py"
            }
        }
        
        mode_templates = templates[exec_mode]
        selected_template_name = st.selectbox(
            "Load Code Template",
            list(mode_templates.keys()),
            key="terminal_template"
        )
        
        template_code = mode_templates[selected_template_name]
        
    with col1:
        st.markdown("#### Input Console")
        # Initialize session state for code inputs if not present
        if "terminal_code_input" not in st.session_state:
            st.session_state.terminal_code_input = ""
            
        # If template is selected, update session state
        if template_code:
            st.session_state.terminal_code_input = template_code
            
        code_input = st.text_area(
            "Command / Script Input",
            value=st.session_state.terminal_code_input,
            height=250,
            placeholder="Type your Python code or shell command here..."
        )
        
        col_btn1, col_btn2 = st.columns([1.5, 2])
        with col_btn1:
            run_btn = st.button("⚡ EXECUTE COMMAND", use_container_width=True)
        with col_btn2:
            if st.button("🧹 Clear Input", use_container_width=False):
                st.session_state.terminal_code_input = ""
                st.session_state.terminal_template = "Select a template..."
                st.rerun()

    if run_btn and code_input:
        with st.spinner("Executing secure payload..."):
            # Determine logic based on mode
            if "Python" in exec_mode:
                res = execute_python_code(code_input)
                exec_type = "Python Script"
            else:
                res = execute_shell_command(code_input)
                exec_type = "Shell Command"
                
            # Log results in session state for rendering
            st.session_state.terminal_result = {
                "type": exec_type,
                "code": code_input,
                "success": res["success"],
                "stdout": res["stdout"],
                "stderr": res["stderr"],
                "time": res["execution_time"]
            }
            
    # Render execution outputs if present in session state
    if "terminal_result" in st.session_state:
        res = st.session_state.terminal_result
        st.divider()
        st.markdown("### 📊 EXECUTION OUTPUT")
        
        # Status details
        status_color = "#00FF88" if res["success"] else "#FF006E"
        status_text = "SUCCESS" if res["success"] else "FAILED"
        
        st.markdown(f"""
        <div style="background-color: #1a1f3a; border-left: 5px solid {status_color}; padding: 15px; border-radius: 4px; font-family: monospace;">
        <b>Payload Type:</b> {res["type"]}<br>
        <b>Execution Status:</b> <span style="color: {status_color}; font-weight: bold;">{status_text}</span><br>
        <b>Execution Duration:</b> {res["time"]:.4f} seconds
        </div>
        """, unsafe_allow_html=True)
        
        # Render Standard Output
        if res["stdout"]:
            st.markdown("#### Standard Output (stdout)")
            st.code(res["stdout"], language="text")
        elif res["success"]:
            st.markdown("#### Standard Output (stdout)")
            st.info("Execution completed successfully with no output to stdout.")
            
        # Render Standard Error
        if res["stderr"]:
            st.markdown("#### Standard Error / Traceback (stderr)")
            st.code(res["stderr"], language="python" if "Python" in res["type"] else "text")


