import base64
from io import BytesIO
from PIL import Image

def decode_base64_image(base64_str: str) -> Image.Image:
    """Decode a base64 image string (without data:image/...;base64, prefix) to a PIL Image."""
    print("image_utils.py decode_base64_image")
    image_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(image_data))

def save_image(image: Image.Image, path: str) -> None:
    """Save a PIL Image to disk at the given path."""
    image.save(path) 