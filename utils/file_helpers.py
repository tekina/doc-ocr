"""
File helper utilities for image encoding and file operations.
"""
import base64


def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes as a base64 string.

    Args:
        image_bytes: Raw bytes of the image file

    Returns:
        Base64 encoded string of the image
    """
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    return base64_image
