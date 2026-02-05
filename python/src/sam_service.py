"""
MLX SAM 3 (Segment Anything Model 3) Service for Apple Silicon

This module wraps the MLX port of SAM 3 for native Apple Silicon inference.
Supports text prompts and box prompts.
"""

import base64
import io
from typing import Optional, Any

import numpy as np
from PIL import Image

# MLX SAM3 imports
from sam3 import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor


def to_python(obj: Any) -> Any:
    """Convert MLX arrays and other objects to Python native types."""
    # Handle MLX arrays
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    # Handle numpy arrays
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle lists recursively
    if isinstance(obj, (list, tuple)):
        return [to_python(item) for item in obj]
    # Handle dicts recursively
    if isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    # Handle scalar types with .item()
    if hasattr(obj, 'item'):
        return obj.item()
    return obj


class SAMService:
    """Service class for MLX SAM 3 model inference on Apple Silicon."""

    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the SAM 3 service.

        Args:
            confidence_threshold: Minimum confidence score for detections (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.processor: Optional[Sam3Processor] = None
        self.inference_state = None
        self.current_image: Optional[Image.Image] = None
        self._model_loaded = False

    def _load_model(self):
        """Load the MLX SAM 3 model. Called lazily on first use."""
        if self._model_loaded:
            return

        print("Loading MLX SAM 3 model (this may take a moment on first run)...")
        self.model = build_sam3_image_model()
        self.processor = Sam3Processor(self.model, confidence_threshold=self.confidence_threshold)
        self._model_loaded = True
        print("MLX SAM 3 model loaded successfully.")

    def set_image(self, image_input) -> dict:
        """
        Set the image for segmentation.

        Args:
            image_input: PIL Image, numpy array, or file-like object

        Returns:
            dict with image shape info
        """
        self._load_model()

        # Load image
        if isinstance(image_input, np.ndarray):
            image = Image.fromarray(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")
        else:
            # Assume file-like object
            image = Image.open(image_input).convert("RGB")

        self.current_image = image
        self.inference_state = self.processor.set_image(image)

        width, height = image.size
        return {
            "height": height,
            "width": width,
            "channels": 3,
        }

    def has_image(self) -> bool:
        """Check if an image is currently set."""
        return self.current_image is not None and self.inference_state is not None

    def predict_with_text(self, text_prompt: str) -> list[dict]:
        """
        Generate segmentation masks from a text prompt.

        Args:
            text_prompt: Text description of what to segment (e.g., "cat", "red car", "person")

        Returns:
            List of mask dictionaries with base64 data and metadata
        """
        if not self.has_image():
            raise ValueError("No image set")

        # Run text prompt segmentation
        self.inference_state = self.processor.set_text_prompt(
            text_prompt,
            self.inference_state
        )

        # Get results and convert to Python types
        masks = self.inference_state.get("masks", [])
        boxes = self.inference_state.get("boxes", [])
        scores = self.inference_state.get("scores", [])

        # Convert to Python native types
        masks = to_python(masks)
        boxes = to_python(boxes)
        scores = to_python(scores)

        # Handle case where scores might be a single value or list
        if not isinstance(scores, list):
            scores = [scores] if scores is not None else []

        results = []
        for i in range(len(masks)):
            mask = masks[i] if i < len(masks) else None
            box = boxes[i] if i < len(boxes) else None
            score = scores[i] if i < len(scores) else 1.0

            if mask is None:
                continue

            # Convert mask to numpy array for encoding
            mask_np = np.array(mask)

            results.append({
                "mask": self._mask_to_base64(mask_np),
                "bbox": box,
                "score": float(score) if score is not None else 1.0,
            })

        return results

    def predict_with_box(self, box: list[float], label: int = 1) -> list[dict]:
        """
        Generate segmentation masks from a bounding box prompt.

        Args:
            box: Bounding box as [x1, y1, x2, y2]
            label: 1 for include (foreground), 0 for exclude (background)

        Returns:
            List of mask dictionaries with base64 data
        """
        if not self.has_image():
            raise ValueError("No image set")

        # Run box prompt segmentation
        self.inference_state = self.processor.set_box_prompt(
            boxes=[box],
            labels=[label],
            state=self.inference_state
        )

        masks = self.inference_state.get("masks", [])
        scores = self.inference_state.get("scores", [])

        # Convert to Python types
        masks = to_python(masks)
        scores = to_python(scores)

        if not isinstance(scores, list):
            scores = [scores] if scores is not None else [1.0]

        results = []
        for i, mask in enumerate(masks):
            mask_np = np.array(mask)
            score = scores[i] if i < len(scores) else 1.0

            results.append({
                "mask": self._mask_to_base64(mask_np),
                "bbox": box,
                "score": float(score) if score is not None else 1.0,
            })

        return results

    def _mask_to_base64(self, mask: np.ndarray) -> str:
        """Convert a numpy mask to base64-encoded PNG."""
        # Handle different mask shapes
        if len(mask.shape) > 2:
            mask = mask.squeeze()

        # Ensure mask is uint8
        if mask.dtype == bool:
            mask = (mask * 255).astype(np.uint8)
        elif mask.max() <= 1:
            mask = (mask * 255).astype(np.uint8)
        else:
            mask = mask.astype(np.uint8)

        # Convert to PIL and encode
        pil_mask = Image.fromarray(mask)
        buffer = io.BytesIO()
        pil_mask.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8")
