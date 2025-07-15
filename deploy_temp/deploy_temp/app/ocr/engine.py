from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import io
from app.ocr.vision import  extract_text_from_image
_ocr_instance = None

def get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang='en')
    return _ocr_instance

def ocr_image(image: Image.Image) -> str:
    ocr = get_ocr()
    print("ocr_engine.py ocr_image")
    # Convert PIL Image to numpy array (BGR)
    img_np = np.array(image.convert('RGB'))[:, :, ::-1]
    result = ocr.ocr(img_np, cls=True)
    # Concatenate all detected text
    print("ocr_engine.py ocr_image result")
    lines = []
    for line in result:
        for seg in line:
            lines.append(seg[1][0])
    print("ocr_engine.py ocr_image result", lines)
    return '\n'.join(lines) 

def ocr_image_google_vision(image_path: str) -> str:
    """
    Perform OCR on a PIL Image using Google Cloud Vision API.
    Assumes that the GOOGLE_APPLICATION_CREDENTIALS environment variable is set.
    """

    # client = setup_vision_client()
    text = extract_text_from_image(image_path)
    return text
        

