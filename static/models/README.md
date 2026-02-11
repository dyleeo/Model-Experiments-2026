# YOLOv8 ONNX models

Place your exported YOLOv8 ONNX model here so the browser can load it.

**Required file:** `yolov8n.onnx` (for the default model).

## Quick: run the export script (recommended)

From the **python/** directory (the Python project):

```bash
cd python
python3 -m pip install ultralytics
python3 scripts/export_yolov8_onnx.py
```

If you get “externally-managed-environment”, use a venv:

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install ultralytics
python scripts/export_yolov8_onnx.py
```

Exports `yolov8n.onnx` by default. To export other sizes (e.g. YOLOv8l):

```bash
cd python
python3 scripts/export_yolov8_onnx.py l    # yolov8l.onnx
python3 scripts/export_yolov8_onnx.py s    # yolov8s.onnx
python3 scripts/export_yolov8_onnx.py m    # yolov8m.onnx
python3 scripts/export_yolov8_onnx.py all  # n, s, m, l
```

Uses `yolov8<size>.pt` from `python/` if present, otherwise downloads it; saves the `.onnx` here.

## Manual export

From the **python/** directory (so `yolov8n.pt` is found):

```bash
cd python
python3 -m pip install ultralytics
python3 -m ultralytics export model=yolov8n.pt format=onnx
# Copy the created yolov8n.onnx to ../static/models/
```

Optional: export other sizes and name them `yolov8s.onnx`, `yolov8m.onnx`, `yolov8l.onnx` to use the model selector in the app.

**Note:** Use the **detection** model (`yolov8n.pt`), not the segmentation model (`yolov8n-seg.pt`), as the app expects output shape `[1, 84, 8400]` (4 box + 80 class scores).
