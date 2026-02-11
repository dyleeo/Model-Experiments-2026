#!/usr/bin/env python3
"""
Export YOLOv8 to ONNX and save to the app's static/models/ for the browser demo.

Run from the python/ directory:
  python3 scripts/export_yolov8_onnx.py           # exports yolov8n (default)
  python3 scripts/export_yolov8_onnx.py l         # exports yolov8l
  python3 scripts/export_yolov8_onnx.py s         # exports yolov8s
  python3 scripts/export_yolov8_onnx.py m        # exports yolov8m
  python3 scripts/export_yolov8_onnx.py n s m l  # exports all four

Uses yolov8<size>.pt from this directory if present, otherwise downloads it.
Requires: pip install ultralytics
"""
import os
import shutil
import sys
from pathlib import Path

VALID_SIZES = ("n", "s", "m", "l")
MODEL_IDS = [f"yolov8{s}" for s in VALID_SIZES]


def export_one(python_dir, repo_root, size: str) -> None:
    static_models = repo_root / "static" / "models"
    static_models.mkdir(parents=True, exist_ok=True)
    model_id = f"yolov8{size}"
    dest = static_models / f"{model_id}.onnx"

    from ultralytics import YOLO

    os.chdir(python_dir)
    pt_path = python_dir / f"{model_id}.pt"
    model_arg = str(pt_path) if pt_path.exists() else f"{model_id}.pt"
    print("Loading", model_arg, "(downloads automatically if needed)...")
    model = YOLO(model_arg)
    print("Exporting to ONNX (imgsz=640)...")
    exported = model.export(format="onnx", imgsz=640)
    exported_path = Path(exported).resolve()
    if not exported_path.exists():
        exported_path = python_dir / f"{model_id}.onnx"
    if exported_path.exists():
        shutil.copy2(exported_path, dest)
        print(f"Saved to {dest}")
        if exported_path != dest:
            try:
                exported_path.unlink()
            except OSError:
                pass
    else:
        raise SystemExit(f"Export did not create {model_id}.onnx")


def main():
    python_dir = Path(__file__).resolve().parent.parent
    repo_root = python_dir.parent

    try:
        from ultralytics import YOLO  # noqa: F401
    except ImportError:
        print("Install ultralytics first: pip install ultralytics")
        raise SystemExit(1)

    args = [a.strip().lower().replace("yolov8", "") or "n" for a in sys.argv[1:]]
    if not args:
        args = ["n"]
    sizes = []
    for a in args:
        if a == "all":
            sizes = list(VALID_SIZES)
            break
        if a in VALID_SIZES and a not in sizes:
            sizes.append(a)
    if not sizes:
        sizes = ["n"]

    for size in sizes:
        export_one(python_dir, repo_root, size)


if __name__ == "__main__":
    main()
