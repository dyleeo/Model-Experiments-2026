from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import io

from .sam_service import SAMService
from .video_service import VideoService

app = FastAPI(
    title="MLX SAM 3 Backend",
    description="Segment Anything Model 3 API for Apple Silicon - supports text and box prompts, images and videos",
    version="0.2.0",
)

# CORS configuration for SvelteKit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (lazy loading)
sam_service: Optional[SAMService] = None
video_service: Optional[VideoService] = None


def get_sam_service() -> SAMService:
    global sam_service
    if sam_service is None:
        sam_service = SAMService(confidence_threshold=0.5)
    return sam_service


def get_video_service() -> VideoService:
    global video_service
    if video_service is None:
        video_service = VideoService(max_frames=300)
    return video_service


class SegmentTextRequest(BaseModel):
    prompt: str  # e.g., "cat", "red car", "person"


class SegmentBoxRequest(BaseModel):
    box: list[float]  # [x1, y1, x2, y2]
    label: int = 1  # 1 = include (foreground), 0 = exclude (background)


class SetFrameRequest(BaseModel):
    frame_index: int


@app.get("/")
async def root():
    return {"status": "ok", "message": "MLX SAM 3 Backend is running (Apple Silicon)"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "platform": "Apple Silicon (MLX)"}


# ============== Image Endpoints ==============

@app.post("/api/set-image")
async def set_image(file: UploadFile = File(...)):
    """Upload an image to be segmented."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read()
        image_bytes = io.BytesIO(contents)

        service = get_sam_service()
        image_shape = service.set_image(image_bytes)

        return {
            "status": "ok",
            "message": "Image loaded successfully",
            "image_shape": image_shape,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/segment/text")
async def segment_with_text(request: SegmentTextRequest):
    """
    Generate segmentation masks from a text prompt.

    SAM 3's key feature: describe what you want to segment in natural language.
    Examples: "cat", "person", "red car", "laptop"
    """
    service = get_sam_service()

    if not service.has_image():
        raise HTTPException(status_code=400, detail="No image set. Upload an image first.")

    try:
        masks = service.predict_with_text(request.prompt)
        return {
            "status": "ok",
            "prompt": request.prompt,
            "count": len(masks),
            "masks": masks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/segment/box")
async def segment_with_box(request: SegmentBoxRequest):
    """Generate segmentation mask from a bounding box prompt."""
    service = get_sam_service()

    if not service.has_image():
        raise HTTPException(status_code=400, detail="No image set. Upload an image first.")

    if len(request.box) != 4:
        raise HTTPException(status_code=400, detail="Box must have 4 values: [x1, y1, x2, y2]")

    try:
        masks = service.predict_with_box(request.box, request.label)
        return {
            "status": "ok",
            "masks": masks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Video Endpoints ==============

@app.post("/api/video/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video and extract frames."""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    try:
        contents = await file.read()

        vs = get_video_service()
        metadata = vs.load_video(contents)

        return {
            "status": "ok",
            "message": "Video loaded successfully",
            **metadata,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/frame/{frame_index}")
async def get_video_frame(frame_index: int):
    """Get a specific frame as base64 JPEG."""
    vs = get_video_service()

    if not vs.has_video():
        raise HTTPException(status_code=400, detail="No video loaded")

    try:
        frame_base64 = vs.get_frame_as_base64(frame_index)
        return {
            "status": "ok",
            "frame_index": frame_index,
            "frame": frame_base64,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/video/thumbnails")
async def get_video_thumbnails(count: int = 10):
    """Get thumbnail strip for timeline preview."""
    vs = get_video_service()

    if not vs.has_video():
        raise HTTPException(status_code=400, detail="No video loaded")

    thumbnails = vs.get_thumbnail_strip(num_thumbnails=count)
    return {
        "status": "ok",
        "count": len(thumbnails),
        "thumbnails": thumbnails,
    }


@app.post("/api/video/set-frame")
async def set_video_frame_for_segmentation(request: SetFrameRequest):
    """Set a specific video frame as the current image for segmentation."""
    vs = get_video_service()
    sam = get_sam_service()

    if not vs.has_video():
        raise HTTPException(status_code=400, detail="No video loaded")

    try:
        # Get frame as PIL image
        pil_image = vs.get_frame_as_pil(request.frame_index)

        # Set it as the current image in SAM service
        image_shape = sam.set_image(pil_image)

        return {
            "status": "ok",
            "message": f"Frame {request.frame_index} set for segmentation",
            "frame_index": request.frame_index,
            "image_shape": image_shape,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/info")
async def get_video_info():
    """Get current video information."""
    vs = get_video_service()

    if not vs.has_video():
        return {
            "status": "ok",
            "has_video": False,
        }

    return {
        "status": "ok",
        "has_video": True,
        "frame_count": vs.get_frame_count(),
        "fps": vs.fps,
        "width": vs.width,
        "height": vs.height,
        "duration": vs.duration,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
