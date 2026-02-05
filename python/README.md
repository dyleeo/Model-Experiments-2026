# MLX SAM 3 Backend (Apple Silicon)

Python backend for running **Segment Anything Model 3 (SAM 3)** natively on Apple Silicon using the MLX framework.

This uses the [MLX SAM3 port](https://github.com/Deekshith-Dade/mlx_sam3) which is optimized for M1/M2/M3/M4 Macs.

## Requirements

- **macOS 13.0+** (Ventura or later)
- **Apple Silicon** (M1/M2/M3/M4)
- **Python 3.13+**

## Setup

### 1. Install Python 3.13 with pyenv

```bash
cd python
pyenv install 3.13
pyenv local 3.13
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install MLX SAM3

```bash
# Clone the MLX SAM3 repository
git clone https://github.com/Deekshith-Dade/mlx_sam3.git
cd mlx_sam3
pip install -e .
cd ..
```

### 4. Install remaining dependencies

```bash
pip install -r requirements.txt
```

## Running the server

```bash
# Development with auto-reload
uvicorn src.main:app --reload --port 8000

# Or run directly
python -m src.main
```

The API will be available at `http://localhost:8000`

**Note:** The first request will download the model weights (~3.5GB). Subsequent runs use cached weights.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Health status |
| `/api/set-image` | POST | Upload image for segmentation |
| `/api/segment/text` | POST | **Segment with text prompt** |
| `/api/segment/box` | POST | Segment with bounding box |

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Text-based segmentation

```javascript
// Upload image first
const formData = new FormData();
formData.append('file', imageFile);
await fetch('http://localhost:8000/api/set-image', {
  method: 'POST',
  body: formData,
});

// Segment with text prompt
const response = await fetch('http://localhost:8000/api/segment/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: "cat"
  }),
});

const { masks, count } = await response.json();
// masks[].mask = base64-encoded PNG
// masks[].bbox = [x1, y1, x2, y2]
// masks[].score = confidence score
```

### Box-based segmentation

```javascript
const response = await fetch('http://localhost:8000/api/segment/box', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    box: [50, 50, 200, 300],  // [x1, y1, x2, y2]
    label: 1  // 1 = include, 0 = exclude
  }),
});
```

## Frontend Integration

CORS is configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:4173` (Vite preview)

## MLX SAM 3 Features

- **Text prompts**: Segment objects by description ("cat", "person", "car")
- **Box prompts**: Draw bounding box to include/exclude regions
- **Native Apple Silicon**: Runs directly on M-series chips via MLX
- **~3.5GB model**: Auto-downloads on first use

## Performance Notes

- First inference is slower (model compilation)
- Subsequent inferences are faster
- Performance scales with Apple Silicon chip tier (M1 < M2 < M3 < M4)
- 16GB+ unified memory recommended for smooth operation

## Troubleshooting

### Model download fails
Check your internet connection. The model (~3.5GB) downloads from Hugging Face on first run.

### Out of memory
Close other applications. SAM 3 benefits from available unified memory.

### Python version issues
MLX requires Python 3.13+. Verify with:
```bash
python --version
```

### MLX not found
Ensure you're on Apple Silicon Mac:
```bash
uname -m  # Should show "arm64"
```
