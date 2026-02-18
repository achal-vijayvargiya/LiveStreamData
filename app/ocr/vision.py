# ocr/vision_ocr.py

import os
import re
import logging
from google.cloud import vision

logger = logging.getLogger(__name__)
_vision_client = None
_credentials_initialized = False

def setup_vision_client():
    global _vision_client, _credentials_initialized

    if not _credentials_initialized:
        credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "credentials",
            "service_account.json",
        )
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Google Vision credentials not found at: {credentials_path}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        _credentials_initialized = True

    if _vision_client is None:
        _vision_client = vision.ImageAnnotatorClient()
        logger.info("[OCR] Initialized Google Vision client")

    return _vision_client

def extract_text_from_image(image_path, timeout=30.0):
    from PIL import Image as PILImage
    import io
    
    client = setup_vision_client()

    # Use same preprocessing as get_full_ocr_response for consistency
    pil_image = PILImage.open(image_path)
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # Save to bytes with PNG format (lossless) to preserve quality
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG', optimize=False)
    img_byte_arr.seek(0)
    content = img_byte_arr.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image, timeout=timeout, retry=None)
    return extract_kv_from_response(response)    
    # return response.full_text_annotation.text

def get_full_ocr_response(image_path, timeout=30.0):
    """
    Get the full OCR response with layout information for table parsing.
    Returns the raw Google Vision API response object.
    """
    from PIL import Image as PILImage
    import io
    
    client = setup_vision_client()

    # Preprocess image to ensure good quality for OCR
    # Read and optimize the image before sending to OCR
    pil_image = PILImage.open(image_path)
    
    # Convert to RGB if necessary (in case of RGBA or other modes)
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # Get image dimensions for debugging
    width, height = pil_image.size
    logger.info(f"[OCR] Processing image: {width}x{height} pixels")
    
    # Enhance image quality for better OCR
    # Save to bytes with high quality
    img_byte_arr = io.BytesIO()
    # Use PNG format for lossless compression, or high-quality JPEG
    pil_image.save(img_byte_arr, format='PNG', optimize=False)
    img_byte_arr.seek(0)
    content = img_byte_arr.read()
    
    logger.info(f"[OCR] Image size: {len(content)} bytes")
    
    # Create image object with content
    image = vision.Image(content=content)
    
    # Use document_text_detection for better table/layout detection
    # This is better than text_detection for structured documents
    response = client.document_text_detection(
        image=image,
        image_context={
            # Enable language hints if needed
            # 'language_hints': ['en']
        },
        timeout=timeout,
        retry=None,
    )
    
    # Check for errors in response
    if hasattr(response, 'error') and response.error.message:
        logger.error(f"[OCR ERROR] {response.error.message}")
    
    # Log OCR results summary for debugging
    if hasattr(response, 'full_text_annotation') and response.full_text_annotation:
        text_length = len(response.full_text_annotation.text) if response.full_text_annotation.text else 0
        pages_count = len(response.full_text_annotation.pages) if response.full_text_annotation.pages else 0
        blocks_count = sum(len(page.blocks) for page in response.full_text_annotation.pages) if response.full_text_annotation.pages else 0
        
        logger.info(f"[OCR DEBUG] OCR Results: {text_length} chars, {pages_count} page(s), {blocks_count} block(s)")
        
        # Check page dimensions from OCR response
        if response.full_text_annotation.pages:
            for i, page in enumerate(response.full_text_annotation.pages):
                if hasattr(page, 'width') and hasattr(page, 'height'):
                    logger.info(f"[OCR DEBUG] Page {i+1} dimensions from OCR: {page.width}x{page.height}")
                    # Compare with actual image dimensions
                    if page.width != width or page.height != height:
                        logger.warning(f"[OCR WARNING] OCR page dimensions ({page.width}x{page.height}) don't match image ({width}x{height})")
    
    return response



def normalize_delimiters(text):
    # Replace arrow-like and similar delimiters with a single dash
    return re.sub(r'\s*[→–—+>]\s*', '-', text)

def extract_kv_from_response(response):
    kv_pairs = {}

    def try_parse_line(line):
        line = normalize_delimiters(line)

        # 1. Standard cases like "156 - 1950"
        matches = re.findall(r'(\d{1,5})\s*-\s*(\d{1,5})', line)
        for m in matches:
            kv_pairs[int(m[0])] = int(m[1])

        # 2. Space-separated like "156 1950"
        if not matches:
            numbers = re.findall(r'\d{1,5}', line)
            if len(numbers) == 2:
                kv_pairs[int(numbers[0])] = int(numbers[1])

        # 3. Concatenated like "4563050" → 456 → 3050
        if not matches:
            concat_match = re.findall(r'\b(\d{7,8})\b', line)
            for val in concat_match:
                key = int(val[:3])
                value = int(val[3:])
                if 1 <= key <= 999 and value > 0:
                    kv_pairs[key] = value

    # 1. Layout-based text (structured blocks)
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            block_words = []
            for paragraph in block.paragraphs:
                words = [''.join([symbol.text for symbol in word.symbols]) for word in paragraph.words]
                block_words.extend(words)
            text_line = ' '.join(block_words)
            try_parse_line(text_line)

    # 2. Raw full-text lines (fallback)
    for line in response.full_text_annotation.text.splitlines():
        try_parse_line(line)

    return kv_pairs

def main():
    """
    Test the extract_text_from_image function with a default image.
    You can change 'test_image.png' to the path of your test image.
    """
    import sys
    import os

    # Default image path (change as needed)
    default_image_path = "test_image.png"

    # Allow user to specify image path as command line argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = default_image_path

    if not os.path.exists(image_path):
        print(f"Image file '{image_path}' not found.")
        return

    print(f"Extracting text from image: {image_path}")
    try:
        text = extract_text_from_image(image_path)
        print("Extracted text:")
        print(text)
    except Exception as e:
        print(f"Error extracting text: {e}")

if __name__ == "__main__":
    main()


