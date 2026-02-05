# SAM 3 Segmentation App

A web application for image segmentation using Meta's **Segment Anything Model 3 (SAM 3)**, running natively on Apple Silicon.

- **Frontend**: SvelteKit
- **Backend**: FastAPI + MLX SAM3
- **Platform**: Apple Silicon (M1/M2/M3/M4)

## Features

- Upload any image
- Segment objects using natural language text prompts (e.g., "cat", "person", "red car")
- View segmentation masks overlaid on the original image
- Switch between multiple detected objects
- See confidence scores for each detection

## Prerequisites

- **macOS 13.0+** (Ventura or later)
- **Apple Silicon Mac** (M1/M2/M3/M4)
- **Python 3.13+**
- **Node.js 18+**
- **pnpm** (or npm/yarn)

## Quick Start

### 1. Clone and setup

```bash
git clone <repo-url>
cd sam-test
```

### 2. Setup Python backend

```bash
cd python

# Install Python 3.13 (using mise, pyenv, or similar)
mise install python@3.13
mise use python@3.13

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install MLX SAM3
git clone https://github.com/Deekshith-Dade/mlx_sam3.git
cd mlx_sam3
pip install -e .
cd ..

# Install other dependencies
pip install -r requirements.txt
```

### 3. Setup frontend

```bash
cd ..  # back to project root
pnpm install
```

### 4. Run the app

**Terminal 1 - Backend:**
```bash
cd python
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
pnpm dev
```

Open **http://localhost:5173** in your browser.

> **Note:** The first segmentation request will download the SAM3 model weights (~3.5GB). Subsequent runs use cached weights.

## Usage

1. Click **"Choose Image"** to upload an image
2. Enter a text prompt describing what to segment (e.g., "dog", "laptop", "person in red")
3. Click **"Segment"** or press Enter
4. View the mask overlay on detected objects
5. If multiple objects are found, click the numbered buttons to switch between them

## Project Structure

```
sam-test/
├── src/                    # SvelteKit frontend
│   └── routes/
│       └── +page.svelte    # Main UI
├── python/                 # Python backend
│   ├── src/
│   │   ├── main.py         # FastAPI app
│   │   └── sam_service.py  # MLX SAM3 wrapper
│   ├── requirements.txt
│   └── README.md           # Backend-specific docs
├── package.json
└── README.md               # This file
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Health check |
| `POST /api/set-image` | POST | Upload image for segmentation |
| `POST /api/segment/text` | POST | Segment with text prompt |
| `POST /api/segment/box` | POST | Segment with bounding box |

API documentation available at http://localhost:8000/docs when backend is running.

## Tech Stack

- **Frontend**: SvelteKit 2, Svelte 5
- **Backend**: FastAPI, Uvicorn
- **ML**: MLX SAM3 (Apple's MLX framework)
- **Deployment**: Cloudflare Workers (frontend)

## Troubleshooting

### Backend won't start
- Ensure Python 3.13+ is active: `python --version`
- Ensure virtual environment is activated: `source .venv/bin/activate`
- Ensure MLX SAM3 is installed: `pip list | grep mlx`

### "No module named 'sam3'"
Install MLX SAM3:
```bash
cd python/mlx_sam3
pip install -e .
```

### CORS errors in browser
Make sure the backend is running on port 8000:
```bash
uvicorn src.main:app --reload --port 8000
```

### Model download slow/fails
The model (~3.5GB) downloads from Hugging Face on first use. Check your internet connection.

## License

MIT
