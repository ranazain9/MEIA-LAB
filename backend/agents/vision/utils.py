"""
Vision Utilities
================

Helpers for image preprocessing, format detection, and slide handling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
SUPPORTED_DOC_FORMATS = {".pdf", ".pptx"}


def validate_slides_input(path: str) -> Path:
    """Validate slide file or directory exists and is a supported format."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Slides path not found: {path}")
    if p.is_file():
        allowed = SUPPORTED_IMAGE_FORMATS | SUPPORTED_DOC_FORMATS
        if p.suffix.lower() not in allowed:
            raise ValueError(f"Unsupported format '{p.suffix}'. Supported: {allowed}")
    return p


def collect_slide_images(directory: str) -> List[Path]:
    """Collect all image files from a directory, sorted by name."""
    d = Path(directory)
    images = sorted(
        f for f in d.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_FORMATS
    )
    return images


def resize_for_vlm(
    image_path: str,
    max_width: int = 1280,
    max_height: int = 960,
) -> str:
    """
    Resize an image to fit within VLM input constraints while
    preserving aspect ratio. Returns path to resized image.
    """
    # TODO: Implement with Pillow
    return image_path
