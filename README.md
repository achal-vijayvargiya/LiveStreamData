# LiveStreamData OCR Dashboard Watcher
venv\Scripts\activate 
This app monitors a live streaming dashboard (e.g., Spyrix Live view), extracts images from <img> tags, performs OCR using PaddleOCR, and logs the results.

## Features
- Uses Playwright for browser automation
- Detects <img> tags with base64 src
- Decodes and saves images
- Runs OCR with PaddleOCR
- Async, modular, and ready for extension

## Setup

1. **Clone the repo and enter the directory**
2. **Install dependencies:**
   ```bash
   pip install playwright paddleocr pillow numpy
   playwright install
   ```
   (You may need to install Tesseract if you want to compare with pytesseract.)

3. **Download PaddleOCR models (first run will auto-download)**

## Usage

```bash
python main.py
```
- Enter the live dashboard URL when prompted.
- OCR results will be printed to the console.

## File Structure
- `main.py` - Entrypoint
- `watcher.py` - Playwright watcher for <img> tags
- `image_utils.py` - Base64 decode/save helpers
- `ocr_engine.py` - PaddleOCR integration

## Extending
- Add SQLite logging in `main.py` as needed
- For headless/cloud, set `headless=True` in watcher

## Requirements
- Python 3.8+
- Playwright
- PaddleOCR
- Pillow
- numpy 