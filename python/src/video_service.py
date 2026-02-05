"""
Video processing service for frame extraction.
"""

import base64
import io
import tempfile
import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image


class VideoService:
    """Service for handling video uploads and frame extraction."""

    def __init__(self, max_frames: int = 300):
        """
        Initialize the video service.

        Args:
            max_frames: Maximum number of frames to extract (to limit memory usage)
        """
        self.max_frames = max_frames
        self.current_video_path: Optional[str] = None
        self.frames: list[np.ndarray] = []
        self.frame_count: int = 0
        self.fps: float = 0
        self.width: int = 0
        self.height: int = 0
        self.duration: float = 0

    def load_video(self, video_bytes: bytes) -> dict:
        """
        Load a video from bytes and extract frames.

        Args:
            video_bytes: Raw video file bytes

        Returns:
            dict with video metadata
        """
        # Save to temporary file (OpenCV needs a file path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(video_bytes)
            temp_path = f.name

        try:
            cap = cv2.VideoCapture(temp_path)

            if not cap.isOpened():
                raise ValueError("Could not open video file")

            # Get video properties
            self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.duration = self.frame_count / self.fps if self.fps > 0 else 0

            # Calculate frame sampling rate
            if self.frame_count > self.max_frames:
                # Sample frames evenly
                sample_interval = self.frame_count / self.max_frames
            else:
                sample_interval = 1

            # Extract frames
            self.frames = []
            frame_idx = 0
            next_sample = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx >= next_sample:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.frames.append(frame_rgb)
                    next_sample += sample_interval

                    if len(self.frames) >= self.max_frames:
                        break

                frame_idx += 1

            cap.release()
            self.current_video_path = temp_path

            return {
                "frame_count": len(self.frames),
                "original_frame_count": self.frame_count,
                "fps": self.fps,
                "width": self.width,
                "height": self.height,
                "duration": round(self.duration, 2),
            }

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e

    def has_video(self) -> bool:
        """Check if a video is loaded."""
        return len(self.frames) > 0

    def get_frame_count(self) -> int:
        """Get the number of extracted frames."""
        return len(self.frames)

    def get_frame(self, frame_index: int) -> np.ndarray:
        """
        Get a specific frame as numpy array.

        Args:
            frame_index: Index of the frame (0-based)

        Returns:
            Frame as RGB numpy array
        """
        if not self.has_video():
            raise ValueError("No video loaded")

        if frame_index < 0 or frame_index >= len(self.frames):
            raise ValueError(f"Frame index out of range: {frame_index}")

        return self.frames[frame_index]

    def get_frame_as_pil(self, frame_index: int) -> Image.Image:
        """
        Get a specific frame as PIL Image.

        Args:
            frame_index: Index of the frame (0-based)

        Returns:
            Frame as PIL Image
        """
        frame = self.get_frame(frame_index)
        return Image.fromarray(frame)

    def get_frame_as_base64(self, frame_index: int) -> str:
        """
        Get a specific frame as base64-encoded JPEG.

        Args:
            frame_index: Index of the frame (0-based)

        Returns:
            Base64-encoded JPEG string
        """
        frame = self.get_frame(frame_index)
        pil_image = Image.fromarray(frame)

        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8")

    def get_thumbnail_strip(self, num_thumbnails: int = 10, thumb_height: int = 60) -> list[str]:
        """
        Get a strip of thumbnail images for the timeline.

        Args:
            num_thumbnails: Number of thumbnails to generate
            thumb_height: Height of each thumbnail in pixels

        Returns:
            List of base64-encoded JPEG thumbnails
        """
        if not self.has_video():
            return []

        thumbnails = []
        step = max(1, len(self.frames) // num_thumbnails)

        for i in range(0, len(self.frames), step):
            if len(thumbnails) >= num_thumbnails:
                break

            frame = self.frames[i]
            pil_image = Image.fromarray(frame)

            # Calculate thumbnail width maintaining aspect ratio
            aspect = pil_image.width / pil_image.height
            thumb_width = int(thumb_height * aspect)

            # Resize
            thumbnail = pil_image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)

            # Encode
            buffer = io.BytesIO()
            thumbnail.save(buffer, format="JPEG", quality=70)
            buffer.seek(0)

            thumbnails.append(base64.b64encode(buffer.read()).decode("utf-8"))

        return thumbnails

    def cleanup(self):
        """Clean up temporary files and memory."""
        if self.current_video_path and os.path.exists(self.current_video_path):
            os.unlink(self.current_video_path)
            self.current_video_path = None

        self.frames = []
        self.frame_count = 0
