# LEIP USAGE GUIDE
## Real-World Investigation Scenarios

This guide walks through common law enforcement investigation workflows using LEIP.

---

## 📋 Scenario 1: Bank Robbery Investigation

**Case:** Robbery at Downtown Bank on January 17, 2024
**Objective:** Identify and locate suspect using CCTV footage

### Step 1: Create Investigation Case

```
Dashboard → Case Management → New Case

Case ID:     CASE-2024-001
Title:       Downtown Bank Robbery
Description: Robbery at 123 Main St. Suspect fled north on 5th Ave
Priority:    Critical
Assigned To: Detective Smith
```

### Step 2: Upload Suspect Photo to Gallery

```
Dashboard → Face Recognition → Upload & Index

Person ID:   SUSPECT-001
Name:        Unknown Suspect
Source:      Bank surveillance screenshot
Upload:      Clear photo of suspect's face
```

The system extracts the face embedding and stores it in the searchable FAISS index.

### Step 3: Process CCTV Footage

```
Dashboard → CCTV Analysis → Process Video

Select video file from intersection camera footage
Frame Skip:  5 (process every 5th frame)
Extract Faces: YES

Expected results:
- 450 frames processed
- 87 persons detected
- 23 vehicle plates recognized
```

### Step 4: Search for Matches

Facial recognition automatically searches all extracted faces against the suspect gallery:

```
Matches Found:
  1. SUSPECT-001 - Similarity: 94% ✓ MATCH CONFIRMED
     Location: 5th Ave & Main St
     Time: 14:32:15
     
  2. PERSON-045  - Similarity: 71%
     Location: Downtown CCTV-42
     Time: 14:35:42
```

### Step 5: Vehicle Tracking

```
Dashboard → Vehicle Tracking

Search plate: LIC-1234 (vehicle seen leaving bank)

Results:
- Downtown CCTV-42:  14:30 (North direction)
- Highway CCTV-15:   14:35 (East direction)  
- Airport Road:      14:45 (Heading towards airport)

Predicted location: Northern suburbs
```

### Step 6: Generate Case Report

```
Dashboard → Reports → Generate Report

Case: CASE-2024-001
Type: Detailed

Report includes:
- Suspect identification (94% match)
- Timeline of movements
- Vehicle tracking data
- Location map
- Export as PDF
```

---

## 📋 Scenario 2: Missing Person Case

**Case:** Missing juvenile reported by parents
**Objective:** Search public locations and correlate with sightings

### Step 1: Upload Missing Person Photo

```
Face Recognition → Upload & Index

Person ID:   MISSING-JUV-001
Name:        Jane Doe, 14 years old
Source:      Family photo
```

### Step 2: Batch Process Multiple CCTV Locations

```
CCTV Analysis → Process Videos

Process feeds from:
- Shopping mall
- Transit stations
- Highways
- Downtown area
```

### Step 3: Automatic Matching

System automatically matches missing person's face against all processed footage:

```
MATCHES FOUND:

Location: Shopping Mall Food Court
  Time: 13:15 UTC
  Confidence: 91%
  Video: Mall-Camera-42
  
Location: Transit Station
  Time: 13:45 UTC
  Confidence: 87%
  Video: Transit-North
  
Location: Downtown Street
  Time: 14:20 UTC
  Confidence: 93%
  Video: Downtown-CCTV-15
```

### Step 4: Track Movement Pattern

```
Timeline View:
  13:15 - Shopping Mall (Food court area)
  13:45 - Transit Station (Platform 3)
  14:20 - Downtown (5th and Main)
  
Direction: Southeast movement pattern
Predicted: Heading towards residential area
```

### Step 5: Alert Law Enforcement

```
Automated Alert Generated:
- Missing person spotted at Downtown location
- Recent sighting: 14:20 UTC
- Direction: Southeast
- Dispatch units to area
- Coordinate with local departments
```

---

## 📋 Scenario 3: Organized Crime Investigation

**Case:** Human trafficking network investigation
**Objective:** Identify network members and correlate locations

### Step 1: Build Suspect Network

```
Face Recognition Gallery:

SUSPECT-A (Leader)    - High priority
SUSPECT-B (Driver)    - Medium priority
SUSPECT-C (Associate) - Medium priority
PERSON-D (Witness)    - Low priority
...
(Total: 45 known associates)
```

### Step 2: Multi-Location CCTV Analysis

Process footage from suspicious locations:
- Hotels in downtown
- Known trafficking hotspots
- Border crossing areas
- Transportation hubs

### Step 3: Co-Occurrence Analysis

```
System detects:
- SUSPECT-A spotted at Hotel X on Jan 15
- SUSPECT-B spotted at Hotel X on Jan 15 (same day)
- SUSPECT-C spotted at Hotel Y on Jan 16
- SUSPECT-A spotted at Hotel Y on Jan 17

Correlation: High probability same organization
```

### Step 4: Vehicle Network

```
Vehicle Tracking reveals:
- SUSPECT-A's vehicle: License ABC-1234
  Frequent visits to: Hotels, border crossing
  
- SUSPECT-B's vehicle: License XYZ-5678
  Frequent visits to: Staging areas, motels

Network map generated showing connections
```

### Step 5: Investigative Report

```
Report Contents:
- Network map (persons and vehicles)
- Timeline of movements
- Location correlation analysis
- Risk assessment
- Recommended next steps
```

---

## 🔌 API Integration Examples

### Integrate with External Systems

#### 1. **Automated CCTV Monitoring**

```python
import requests
import time

# Monitor city cameras 24/7
cameras = [
    "rtsp://downtown-camera-01",
    "rtsp://highway-camera-02",
    "rtsp://airport-camera-03"
]

for camera in cameras:
    response = requests.post(
        "http://localhost:8000/api/v1/cctv/process-video",
        json={
            "source": camera,
            "frame_skip": 10,
            "extract_faces": True
        }
    )
    job_id = response.json()["job_id"]
    
    # Check status periodically
    while True:
        status = requests.get(
            f"http://localhost:8000/api/v1/cctv/job/{job_id}"
        )
        if status.json()["status"] == "completed":
            results = status.json()["results"]
            print(f"Detections: {results['detections_summary']}")
            break
        time.sleep(5)
```

#### 2. **Automated Suspect Identification**

```python
# When new person is added to watch list
suspect_photo = "new_suspect.jpg"

# Upload to gallery
upload_response = requests.post(
    "http://localhost:8000/api/v1/faces/upload",
    files={"file": open(suspect_photo, "rb")},
    data={"person_id": "SUSPECT-NEW-001"}
)

# Search against all CCTV from last 24 hours
search_response = requests.post(
    "http://localhost:8000/api/v1/faces/search",
    files={"file": open(suspect_photo, "rb")},
    params={"top_k": 20, "threshold": 0.7}
)

matches = search_response.json()["matches"]
if matches:
    print(f"Found {len(matches)} potential matches")
    # Alert dispatch centers
```

#### 3. **Real-time Vehicle Tracking**

```python
# Continuous vehicle tracking across city
plates_of_interest = ["ABC-1234", "XYZ-5678"]

for plate in plates_of_interest:
    response = requests.post(
        "http://localhost:8000/api/v1/vehicles/track",
        json={"plate_number": plate}
    )
    
    trail = response.json()["trail"]
    predicted = response.json()["predicted_location"]
    
    # Alert if entering restricted area
    if predicted["distance_to_courthouse"] < 500:
        send_alert(f"Vehicle {plate} approaching courthouse")
```

#### 4. **Automated Case Updates**

```python
# Every 6 hours, scan all stored CCTV for case updates

case_id = "CASE-2024-001"
suspect_ids = ["SUSPECT-001", "SUSPECT-002"]

# Get all detections for case
response = requests.get(
    f"http://localhost:8000/api/v1/cases/{case_id}"
)

case_data = response.json()["case_data"]
detections = case_data["detections"]

# Generate updated report
report_response = requests.post(
    f"http://localhost:8000/api/v1/reports/case-summary",
    json={"case_id": case_id}
)

updated_report = report_response.json()["report"]
# Email to assigned detective
send_email(to=detective_email, content=updated_report)
```

---

## 🎯 Best Practices

### 1. **Quality Over Speed**
- Use higher-quality CCTV footage
- Adjust frame_skip based on quality (skip 10 for clear footage, 5 for poor)
- Set appropriate confidence thresholds (0.7+ for investigations)

### 2. **Gallery Management**
- Keep suspect gallery updated
- Remove confirmed non-suspects
- Maintain detailed metadata
- Regular duplicate checks

### 3. **Case Management**
- Document all detections with metadata
- Link vehicles to persons when possible
- Create detailed timelines
- Cross-reference with other cases

### 4. **Verification**
- Always manually verify high-confidence matches (>90%)
- Use multiple data points (face + vehicle + location)
- Get supervisor approval before arrests
- Maintain chain of custody

### 5. **Privacy & Ethics**
- Only search authorized footage
- Minimize false positives through threshold tuning
- Audit logs for compliance
- Regular bias assessment
- Transparent methodology

---

## 📊 Example: Impact Assessment

**Before LEIP:**
- Manual review: 100 hours per case
- Hit rate: ~30%
- Response time: 48-72 hours
- Coordination: Phone/email

**After LEIP:**
- Automated search: 30 minutes per case
- Hit rate: ~85%
- Response time: 1-2 hours
- Coordination: Real-time dashboard

**Case Resolution Time: Improved 75%**

---

## ✅ Checklist for Investigators

- [ ] Case created with all details
- [ ] Suspects added to gallery with metadata
- [ ] All CCTV footage uploaded
- [ ] Confidence thresholds appropriate
- [ ] Matches manually verified
- [ ] Supporting evidence documented
- [ ] Timeline created
- [ ] Report generated
- [ ] Case details shared with team
- [ ] Chain of custody maintained

---

## 🚨 Common Issues & Solutions

**Issue: High false positives**
- Solution: Increase threshold (0.7→0.8)
- Check lighting/angle similarity in matches

**Issue: Missing detections**
- Solution: Lower threshold slightly
- Check frame quality in that area
- Verify CCTV camera is operational

**Issue: Slow processing**
- Solution: Increase frame_skip
- Use smaller YOLO model
- Enable GPU acceleration

**Issue: Inconsistent vehicle detections**
- Solution: Adjust YOLO confidence threshold
- Check camera angle for plates

---

## 📞 Escalation & Support

**Technical Issues:**
- Check logs: `logs/leip.log`
- Run: `python init.py`
- Verify: `http://localhost:8000/health`

**Operational Questions:**
- Review documentation: README.md
- Check API docs: `/docs` endpoint
- Contact IT/supervisor

**Case-Related:**
- Verify suspect information
- Check metadata completeness
- Consult with detective team

---

**Last Updated:** January 2024

For authorized law enforcement use only.
