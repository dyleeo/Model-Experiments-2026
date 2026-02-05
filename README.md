# Model Experiments 2026

A collection of interactive demos exploring real-time segmentation and object detection models — both server-side and browser-based.

- **Frontend**: SvelteKit 2 + Svelte 5
- **Backend**: FastAPI + MLX (for server-side models)
- **Browser ML**: ONNX Runtime + WebGPU

## Models & Approaches

| Route | Model | Runtime | Description |
|-------|-------|---------|-------------|
| `/` | Home | - | Overview and comparison of all models |
| `/sam3` | SAM 3 | Server | Text-based concept segmentation |
| `/sam2` | SAM 2 | Server | Video segmentation with tracking |
| `/mobilesam` | MobileSAM | Browser | Lightweight SAM (9.66M params) |
| `/yolo` | YOLOv8 | Browser | Real-time detection + segmentation |
| `/fastsam` | FastSAM | Browser | CNN-based fast segmentation |

### Server-Side Models
- **SAM 3**: Open-vocabulary segmentation with text prompts ("yellow school bus", "person in red")
- **SAM 2**: Video segmentation with streaming memory, handles occlusion and reappearance

### Browser-Based Models (WebGPU)
- **MobileSAM**: 66× smaller than SAM, point/box prompting, runs on-device
- **YOLOv8**: Real-time detection + instance segmentation, webcam support
- **FastSAM**: 10-100× faster than SAM, all-instance segmentation

## Prerequisites

- **macOS 13.0+** / Linux / Windows (browser demos work everywhere)
- **Apple Silicon Mac** (M1/M2/M3/M4) for server-side MLX models
- **Python 3.13+** (for server-side demos)
- **Node.js 18+**
- **pnpm**

## Quick Start

### 1. Install dependencies

```bash
pnpm install
```

### 2. Run the frontend

```bash
pnpm dev
```

Open **http://localhost:5173** — browser-based demos (MobileSAM, YOLOv8, FastSAM) work immediately.

### 3. (Optional) Run Python backend for server-side models

```bash
cd python
uv run src/main.py
# or
source .venv/bin/activate && uvicorn src.main:app --reload --port 8000
```

> **Note:** First run downloads SAM3 model weights (~3.5GB) from Hugging Face.

## Project Structure

```
model-experiments-2026/
├── src/
│   ├── routes/
│   │   ├── +page.svelte        # Home - model overview & comparison
│   │   ├── sam3/               # SAM 3 server-side demo
│   │   ├── sam2/               # SAM 2 video segmentation
│   │   ├── mobilesam/          # MobileSAM browser demo
│   │   ├── yolo/               # YOLOv8 detection demo
│   │   └── fastsam/            # FastSAM browser demo
│   └── lib/
├── python/                     # Python backend
│   ├── src/
│   │   ├── main.py             # FastAPI app
│   │   ├── sam_service.py      # MLX SAM3 wrapper
│   │   └── video_service.py    # Video processing
│   └── requirements.txt
├── static/
├── package.json
└── README.md
```

## Model Comparison

| Model | Speed | Quality | Size | Best For |
|-------|-------|---------|------|----------|
| SAM 3 | ~30ms/img | Excellent | ~3.5GB | Text-based concept segmentation |
| SAM 2 | 44 FPS | Excellent | ~2GB | Video with tracking |
| MobileSAM | 5-15 FPS | Good | ~10MB | Browser point/box prompts |
| YOLOv8 | 30+ FPS | Good | 6-87MB | Real-time detection |
| FastSAM | 20+ FPS | Good | ~25MB | Fast all-instance segmentation |

## API Endpoints (Server-Side)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Health check |
| `POST /api/set-image` | POST | Upload image for segmentation |
| `POST /api/segment/text` | POST | Segment with text prompt |
| `POST /api/segment/box` | POST | Segment with bounding box |
| `POST /api/video/upload` | POST | Upload video for SAM2 |
| `POST /api/video/set-frame` | POST | Set frame for segmentation |
| `GET /api/video/frame/{index}` | GET | Get frame image |

API docs: http://localhost:8000/docs

## Browser Requirements

For WebGPU-accelerated browser demos:

| Browser | WebGPU Support |
|---------|----------------|
| Chrome/Edge (Win/Mac/Android) | ✅ Stable |
| Firefox | ⚠️ Behind flag |
| Safari | ⚠️ Technology Preview |
| iOS Safari | ❌ Not yet |

Falls back to WebAssembly (WASM) if WebGPU unavailable.

## Tech Stack

- **Frontend**: SvelteKit 2, Svelte 5, Vite
- **Backend**: FastAPI, Uvicorn, MLX
- **Browser ML**: ONNX Runtime Web, WebGPU
- **Deployment**: Cloudflare Workers (frontend)

## Adding Real Model Inference

The browser demos include UI scaffolding. To add actual inference:

### MobileSAM / FastSAM / YOLO

```bash
npm install onnxruntime-web
```

```javascript
import * as ort from 'onnxruntime-web/webgpu';

const session = await ort.InferenceSession.create('/models/model.onnx', {
  executionProviders: ['webgpu', 'wasm']
});

const results = await session.run({ input: tensor });
```

### Model Sources
- MobileSAM ONNX: [github.com/ChaoningZhang/MobileSAM](https://github.com/ChaoningZhang/MobileSAM)
- YOLOv8 ONNX: `yolo export model=yolov8n-seg.pt format=onnx`
- FastSAM ONNX: [github.com/CASIA-IVA-Lab/FastSAM](https://github.com/CASIA-IVA-Lab/FastSAM)

## Troubleshooting

### Backend won't start
```bash
# Ensure Python 3.13+ is active
python --version

# Ensure MLX SAM3 is installed
pip list | grep mlx
```

### "No module named 'sam3'"
```bash
cd python/mlx_sam3
pip install -e .
```

### CORS errors
Ensure backend is running on port 8000:
```bash
uvicorn src.main:app --reload --port 8000
```

### WebGPU not working
- Check browser compatibility (Chrome/Edge recommended)
- Falls back to WASM automatically (slower but works)

## License

MIT
