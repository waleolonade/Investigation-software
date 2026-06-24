# LEIP YOLO Detector Backend Integration

## Overview

The LEIP YOLO Detector supports two backends for object detection:
1. **Rust ONNX** - Fast, efficient, minimal dependencies
2. **PyTorch/ultralytics** - Full YOLOv8 support with GPU acceleration

The system will automatically fall back to ultralytics if:
- Rust binary is not found
- Rust initialization fails
- Rust detection process crashes

## Configuration

### Option 1: PyTorch/ultralytics (Default)

```env
YOLO_BACKEND=ultralytics
YOLO_MODEL_SIZE=medium
YOLO_DEVICE=cpu
```

### Option 2: Rust ONNX (Requires Build)

```env
YOLO_BACKEND=rust
YOLO_ONNX_PATH=yolov8m.onnx
YOLO_CLASS_NAMES=coco.names
YOLO_ONNX_INPUT_SIZE=640
YOLO_RUST_PERSISTENT=true
```

## Building the Rust Backend

### Prerequisites
- Rust toolchain (install from https://rustup.rs/)
- OpenCV development libraries
- ONNX Runtime

### Build Steps

```bash
cd yolo_detector-main
cargo build --release
```

The binary will be at: `target/release/yolo_detector` (or `.exe` on Windows)

### Setup ONNX Model

```bash
# Convert YOLOv8 to ONNX
pip install ultralytics
yolo export model=yolov8m.pt format=onnx opset=12 dynamic=True

# Download class names
wget https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names
```

## Rust Detector Modes

### Single-Shot Mode
- Spawn process for each detection
- Simpler, more isolated
- Use when: occasional detections, low throughput

```python
detector = YOLODetector()  # YOLO_RUST_PERSISTENT=false
annotated_frame, detections = detector.detect_frame(frame)
```

### Persistent Mode (Recommended)
- Keep model loaded, reuse process
- Lower per-frame overhead (~50% faster)
- Auto-restart on crash
- Use when: video/stream processing, high throughput

```python
detector = YOLODetector()  # YOLO_RUST_PERSISTENT=true
annotated_frame, detections = detector.detect_frame(frame)  # 2nd+ call reuses process
```

## Error Handling & Fallback

If Rust initialization fails:

```
⚠ Rust YOLO binary not found, falling back to ultralytics: [FileNotFoundError details]
```

The detector will automatically initialize the ultralytics backend instead.

If a detection fails during Rust mode:

```
⚠ Rust detector failed (RuntimeError): [error details]. Falling back to ultralytics.
```

The detector will reinitialize ultralytics and continue working.

## Performance

Rough benchmarks (on a 640x480 frame):

| Backend | Mode | Time | GPU Memory |
|---------|------|------|-----------|
| ultralytics | - | 50-100ms | 2-4GB |
| Rust | Single-shot | 100-150ms* | <500MB |
| Rust | Persistent | 20-30ms | <500MB |

*includes process spawn overhead

## Debugging

### Check which backend is active

```python
detector = YOLODetector()
print(f"Backend: {detector.backend}")
print(f"Using Rust: {detector.use_rust}")
```

### Check Rust process health

```python
if detector.use_rust and hasattr(detector, 'rust_detector'):
    print(f"Process alive: {detector.rust_detector.is_alive()}")
    # Force restart if needed:
    detector.rust_detector.restart()
```

### Enable verbose logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Troubleshooting

### "Rust YOLO binary not found"

- Ensure you ran `cargo build --release` in `yolo_detector-main/`
- Check that the binary exists at: `yolo_detector-main/target/release/yolo_detector`

### "Failed to read image" or detection hangs

- Ensure `YOLO_ONNX_PATH` and `YOLO_CLASS_NAMES` point to valid files
- Check file permissions
- Verify ONNX model is properly converted (opset 12)

### Persistent process crashes frequently

- Check system memory availability
- Try single-shot mode: `YOLO_RUST_PERSISTENT=false`
- Enable debug logging to see process stderr

### ONNX Runtime errors

- Reinstall ONNX Runtime: `pip install --upgrade onnx onnxruntime`
- Verify CUDA availability if using GPU
