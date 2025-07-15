import asyncio
from playwright.async_api import async_playwright
import os
from PIL import Image
import io
from ..ocr.engine import ocr_image_google_vision
from ..websocket.data_poster import post_data
import datetime
import base64
from PIL import Image
from io import BytesIO

LOGIN_URL = os.getenv('DASHBOARD_LOGIN_URL', 'https://dashboard.spyrix.com/login')
LIVE_VIEW_URL = os.getenv('DASHBOARD_LIVE_URL', 'https://dashboard.spyrix.com/live/')
USERNAME = os.getenv('DASHBOARD_USERNAME', 'iinfotech966@gmail.com')
PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'Khodal@111')
USERNAME_SELECTOR = 'input[type="email"], input[name="username"]'
PASSWORD_SELECTOR = 'input[type="password"]'
LOGIN_BUTTON_SELECTOR = 'button[type="submit"]'

async def login(page):
    try:
        await page.goto(LOGIN_URL)

        # Fill first input (username/email)
        await page.locator('input').nth(0).fill(USERNAME)

        # Fill second input (password)
        await page.locator('input').nth(1).fill(PASSWORD)

        # Click the button (assuming it's the next clickable element)
        await page.get_by_role("button").press('Enter')

        # Wait for navigation or success indicator
        await page.wait_for_load_state('networkidle')
    except Exception as e:
        print(f"Error during login: {e}")

async def watch_image_src():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        # Perform login first
        await login(page)
        print("[+] Login successful, current URL:", page.url)
        
        await capture_canvas_screenshot(page)
        
       

async def capture_canvas_screenshot(page, save_path="canvas_capture.png"):
    
    await page.goto(LIVE_VIEW_URL)
    print(f"[+] Navigated to live view page, current URL: {page.url}")
    await page.wait_for_load_state('networkidle')
    await page.wait_for_selector("#canvas", state="visible", timeout=10000)
    
    images_dir = "images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    for i in range(2000):
        # Get the canvas as a data URL (native resolution)
        canvas_data_url = await page.evaluate("""
            () => {
                const canvas = document.getElementById('canvas');
                return canvas ? canvas.toDataURL('image/png') : null;
            }
        """)
        if canvas_data_url:
            base64_data = canvas_data_url.split(',')[1]
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            unique_save_path = os.path.join(images_dir, f"canvas_capture_{timestamp}.png")
            image.save(unique_save_path)
            text = ocr_image_google_vision(unique_save_path)
            await post_data(text, unique_save_path)
        
            # print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OCR text: {text}")
            await asyncio.sleep(20)
        else:
            print(await page.content())  # Debug: print HTML if not found
            raise Exception("Canvas element with id 'canvas' not found or could not get data URL.")