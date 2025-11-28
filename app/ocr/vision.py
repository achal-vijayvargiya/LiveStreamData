# ocr/vision_ocr.py

from google.cloud import vision
import os
import re

def setup_vision_client():
    # Get the absolute path to the credentials file
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(base_dir)
    credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credentials", "service_account.json")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    return vision.ImageAnnotatorClient()

def extract_text_from_image(image_path):
    client = setup_vision_client()

    with open(image_path, "rb") as img_file:
        content = img_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    return extract_kv_from_response(response)    
    # return response.full_text_annotation.text



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


