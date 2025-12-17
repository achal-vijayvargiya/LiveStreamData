import asyncio
from playwright.async_api import async_playwright
import os
from PIL import Image
import io
from ..ocr.engine import ocr_image_google_vision, ocr_image_google_vision_table
from ..websocket.data_poster import post_data, post_table_data
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
        print(f"[+] Navigating to login page: {LOGIN_URL}")
        print(f"[+] Login credentials:")
        print(f"    Email: {USERNAME}")
        print(f"    Password: {'*' * len(PASSWORD)}")
        
        await page.goto(LOGIN_URL)
        await page.wait_for_load_state('networkidle')
        
        print(f"[+] Login page loaded, current URL: {page.url}")
        
        # Wait for login form to be ready
        await page.wait_for_selector('input[data-testid="app-input"]', timeout=30000)
        
        # Fill email input (first text input)
        print(f"[+] Filling email: {USERNAME}")
        email_input = page.locator('input[data-testid="app-input"][type="text"]')
        await email_input.fill(USERNAME)

        # Fill password input
        print("[+] Filling password")
        password_input = page.locator('input[data-testid="app-input"][type="password"]')
        await password_input.fill(PASSWORD)

        # Click the submit button
        print("[+] Clicking submit button")
        submit_button = page.locator('button[data-testid="submit-button"]')
        await submit_button.click()

        # Wait a moment for the form to be submitted
        await page.wait_for_timeout(30000)
        
        # Wait for navigation or success indicator
        await page.wait_for_load_state('networkidle')
        
        print(f"[+] Login completed, current URL: {page.url}")
        
        # Check if login was successful
        if "auth.spyrix.com" in page.url or "login" in page.url.lower():
            print("[ERROR] Still on login page - authentication may have failed")
            # Take screenshot for debugging
            await page.screenshot(path="debug_login_failed.png")
            print("[DEBUG] Login failure screenshot saved to debug_login_failed.png")
        else:
            print("[+] Login appears successful")
            
    except Exception as e:
        print(f"Error during login: {e}")
        # Take screenshot on error
        await page.screenshot(path="debug_login_error.png")
        print("[DEBUG] Login error screenshot saved to debug_login_error.png")

async def watch_image_src():
    async with async_playwright() as p:
        # Launch browser in visible mode (not headless) for debugging
        browser = await p.chromium.launch(headless=True)  # 1 second delay between actions
        # Set a large viewport to ensure full canvas is visible
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Set longer timeouts for page loading
        page.set_default_timeout(30000)  # 30 seconds timeout
        page.set_default_navigation_timeout(30000)  # 30 seconds for navigation
        
        # Perform login first
        await login(page)
        print("[+] Login successful, current URL:", page.url)
        
        await capture_canvas_screenshot(page)
        
       

async def capture_canvas_screenshot(page, save_path="canvas_capture.png"):
    
    # First, try to navigate to the base live view URL
    print(f"[+] Attempting to navigate to: {LIVE_VIEW_URL}")
    await page.goto(LIVE_VIEW_URL)
    print(f"[+] Navigated to live view page, current URL: {page.url}")
    
    # Check if we were redirected
    if "auth.spyrix.com" in page.url or "login" in page.url.lower():
        print("[ERROR] Page redirected to login/auth page. Authentication may have failed.")
        print(f"[DEBUG] Final URL: {page.url}")
        
        # Get the complete DOM to debug
        dom_content = await page.content()
        print(f"[DEBUG] Page title: {await page.title()}")
        print(f"[DEBUG] DOM length: {len(dom_content)} characters")
        
        # Save DOM to file for inspection
        with open("debug_dom.html", "w", encoding="utf-8") as f:
            f.write(dom_content)
        print("[DEBUG] Complete DOM saved to debug_dom.html")
        
        # Take a screenshot for visual debugging
        await page.screenshot(path="debug_redirect.png")
        print("[DEBUG] Screenshot saved to debug_redirect.png")
        
        return
    
    # Wait for initial page load
    await page.wait_for_load_state('networkidle')
    
    # Get the current URL (whatever it changed to)
    current_url = page.url
    print(f"[+] Current URL after initial load: {current_url}")
    
    # Ensure viewport is large enough to see full canvas
    await page.set_viewport_size({'width': 1920, 'height': 1080})
    await page.evaluate("window.scrollTo(0, 0)")
    
    # Wait a bit for any dynamic content to load
    print("[+] Waiting for dynamic content to load...")
    await page.wait_for_timeout(10000)
    
    # Check if URL has changed from the base URL
    if current_url != LIVE_VIEW_URL:
        print(f"[+] URL has changed from base URL to: {current_url}")
        print("[+] This indicates dynamic parameters were added")
    else:
        print("[+] URL hasn't changed, but will still refresh for faster loading")
    
    # Refresh the page to replicate manual refresh behavior (works with any URL)
    print("[+] Refreshing current page to load content quickly (replicating manual refresh)")
    await page.reload()
    print(f"[+] Page refreshed, current URL: {page.url}")
    
    # Wait for page to load after refresh
    await page.wait_for_load_state('networkidle')
    
    # Additional wait for dynamic content after refresh
    print("[+] Waiting for canvas content to load after refresh...")
    await page.wait_for_timeout(30000)
    
    # Debug: Check if canvas exists and its properties
    canvas_info = await page.evaluate("""
        () => {
            const canvas = document.getElementById('canvas');
            if (!canvas) {
                return { exists: false, message: "Canvas element not found" };
            }
            
            return {
                exists: true,
                tagName: canvas.tagName,
                id: canvas.id,
                className: canvas.className,
                width: canvas.width,
                height: canvas.height,
                offsetWidth: canvas.offsetWidth,
                offsetHeight: canvas.offsetHeight,
                style: {
                    display: canvas.style.display,
                    visibility: canvas.style.visibility,
                    opacity: canvas.style.opacity,
                    position: canvas.style.position,
                    zIndex: canvas.style.zIndex
                },
                computedStyle: {
                    display: window.getComputedStyle(canvas).display,
                    visibility: window.getComputedStyle(canvas).visibility,
                    opacity: window.getComputedStyle(canvas).opacity
                },
                isVisible: canvas.offsetWidth > 0 && canvas.offsetHeight > 0,
                boundingRect: canvas.getBoundingClientRect()
            };
        }
    """)
    
    print(f"[DEBUG] Canvas info: {canvas_info}")
    
    if not canvas_info.get('exists'):
        print("[ERROR] Canvas element not found in DOM")
        # Take a screenshot for debugging
        await page.screenshot(path="debug_no_canvas.png")
        return
    
    if not canvas_info.get('isVisible'):
        print("[WARNING] Canvas exists but has zero dimensions")
        print(f"Canvas dimensions: {canvas_info.get('offsetWidth')}x{canvas_info.get('offsetHeight')}")
    
    # Try different waiting strategies
    try:
        # Strategy 1: Wait for element to be attached (more reliable than visible)
        await page.wait_for_selector("#canvas", state="attached", timeout=30000)
        print("[+] Canvas element attached to DOM")
        
        # Strategy 2: Wait a bit for the canvas to be rendered
        await page.wait_for_timeout(30000)
        
        # Strategy 3: Check if canvas has content (better than waiting for "visible")
        canvas_ready = await page.evaluate("""
            () => {
                const canvas = document.getElementById('canvas');
                if (!canvas) return false;
                
                // Check if canvas has been drawn on by checking if it has any content
                try {
                    const ctx = canvas.getContext('2d');
                    const imageData = ctx.getImageData(0, 0, Math.min(canvas.width, 100), Math.min(canvas.height, 100));
                    const data = imageData.data;
                    
                    // Check if any pixel is not transparent (sample first 100x100 pixels for performance)
                    for (let i = 3; i < data.length; i += 4) {
                        if (data[i] !== 0) return true; // Found non-transparent pixel
                    }
                    return false;
                } catch (e) {
                    // Canvas might not be ready yet
                    return false;
                }
            }
        """)
        
        if canvas_ready:
            print("[+] Canvas has content and is ready")
        else:
            print("[INFO] Canvas attached but waiting for content...")
            # Wait a bit more for content to load
            await page.wait_for_timeout(30000)
            
            # Check again
            canvas_ready = await page.evaluate("""
                () => {
                    const canvas = document.getElementById('canvas');
                    if (!canvas) return false;
                    
                    try {
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, Math.min(canvas.width, 100), Math.min(canvas.height, 100));
                        const data = imageData.data;
                        
                        for (let i = 3; i < data.length; i += 4) {
                            if (data[i] !== 0) return true;
                        }
                        return false;
                    } catch (e) {
                        return false;
                    }
                }
            """)
            
            if canvas_ready:
                print("[+] Canvas content loaded after waiting")
            else:
                print("[WARNING] Canvas still appears empty, but proceeding anyway...")
        
    except Exception as e:
        print(f"[WARNING] Canvas check failed: {e}")
        print("[INFO] Proceeding anyway since canvas exists in DOM...")
    
    images_dir = "images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    # Variables for stuck detection
    consecutive_failures = 0
    max_consecutive_failures = 5  # Refresh after 5 consecutive failures
    consecutive_zero_data = 0
    max_consecutive_zero_data = 2  # Refresh after 2 consecutive zero-data captures
    last_successful_capture = datetime.datetime.now()
    last_valid_data_capture = datetime.datetime.now()
    refresh_interval = 180  # Refresh every 3 minutes (180 seconds) as preventive measure (reduced from 5 min)
    last_ocr_result = None
    
    for i in range(2000):
        # Multi-layered stuck detection system:
        # 1. Capture failure detection (consecutive_failures)
        # 2. Zero/empty data detection (consecutive_zero_data)
        # 3. Time-based refresh (refresh_interval)
        # 4. Valid data timeout (120 seconds)
        
        # Get the canvas as a data URL (native resolution) with better error handling
        # First, get canvas info and ensure it's fully visible
        canvas_info = await page.evaluate("""
            () => {
                const canvas = document.getElementById('canvas');
                if (!canvas) {
                    return { exists: false };
                }
                
                // Scroll canvas into view to ensure it's fully rendered
                canvas.scrollIntoView({ behavior: 'instant', block: 'center' });
                
                return {
                    exists: true,
                    width: canvas.width,
                    height: canvas.height,
                    offsetWidth: canvas.offsetWidth,
                    offsetHeight: canvas.offsetHeight,
                    scrollWidth: canvas.scrollWidth,
                    scrollHeight: canvas.scrollHeight,
                    boundingRect: canvas.getBoundingClientRect()
                };
            }
        """)
        
        if canvas_info and canvas_info.get('exists'):
            print(f"[DEBUG] Canvas dimensions: {canvas_info.get('width')}x{canvas_info.get('height')} (display: {canvas_info.get('offsetWidth')}x{canvas_info.get('offsetHeight')})")
        
        # Wait a moment for scroll to complete
        await page.wait_for_timeout(100)
        
        canvas_data_url = await page.evaluate("""
            () => {
                const canvas = document.getElementById('canvas');
                if (!canvas) {
                    console.log('Canvas not found');
                    return null;
                }
                
                try {
                    // Check if canvas has content before capturing
                    const ctx = canvas.getContext('2d');
                    const imageData = ctx.getImageData(0, 0, Math.min(canvas.width, 50), Math.min(canvas.height, 50));
                    const data = imageData.data;
                    
                    let hasContent = false;
                    for (let i = 3; i < data.length; i += 4) {
                        if (data[i] !== 0) {
                            hasContent = true;
                            break;
                        }
                    }
                    
                    if (!hasContent) {
                        console.log('Canvas has no content yet');
                        return null;
                    }
                    
                    // Capture the full canvas - toDataURL should capture entire canvas regardless of viewport
                    // But if there are size limits, we might need to check
                    const dataUrl = canvas.toDataURL('image/png');
                    
                    // Log canvas dimensions for debugging
                    console.log('Canvas captured:', canvas.width, 'x', canvas.height, 'DataURL length:', dataUrl.length);
                    
                    return dataUrl;
                } catch (e) {
                    console.log('Error capturing canvas:', e);
                    console.log('Error details:', e.message, e.stack);
                    return null;
                }
            }
        """)
        
        if canvas_data_url:
            # Successful capture - reset failure counter
            consecutive_failures = 0
            last_successful_capture = datetime.datetime.now()
            
            base64_data = canvas_data_url.split(',')[1]
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            
            # Log image dimensions for debugging
            print(f"[DEBUG] Captured image dimensions: {image.width}x{image.height}")
            
            # Verify image is not empty
            if image.width == 0 or image.height == 0:
                print("[WARNING] Captured image has zero dimensions!")
                continue
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            unique_save_path = os.path.join(images_dir, f"canvas_capture_{timestamp}.png")
            image.save(unique_save_path)
            print(f"[DEBUG] Image saved: {unique_save_path} ({image.width}x{image.height})")
            # Use table extraction for new solution - extracts Sub Total row
            text = ocr_image_google_vision_table(unique_save_path)
            
            # Check if OCR result is empty or all zeros (indicates stale/blank canvas)
            is_zero_data = False
            if not text or len(text) == 0:
                is_zero_data = True
                print(f"[WARNING] OCR returned empty data - canvas may be blank/stale")
            elif all(v == 0 for v in text.values()) and len(text) > 0:
                is_zero_data = True
                print(f"[WARNING] OCR returned all zero values - canvas may be stale")
            
            # Check if OCR result is identical to previous (canvas not updating)
            is_stale_data = False
            if last_ocr_result is not None and text == last_ocr_result:
                is_stale_data = True
                print(f"[WARNING] OCR result identical to previous capture - canvas may not be updating")
            
            last_ocr_result = text.copy() if text else {}
            
            # Handle zero/stale data detection
            if is_zero_data:
                consecutive_zero_data += 1
                print(f"[WARNING] Zero/empty data detected (consecutive count: {consecutive_zero_data})")
                
                if consecutive_zero_data >= max_consecutive_zero_data:
                    refresh_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"\n{'🔴'*35}")
                    print(f"[CRITICAL] {refresh_time} - {consecutive_zero_data} consecutive zero-data captures!")
                    print(f"[CRITICAL] Canvas is stuck. Forcing EMERGENCY REFRESH...")
                    print(f"{'🔴'*35}\n")
                    await page.reload()
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(10000)  # Wait for canvas to load after refresh
                    consecutive_zero_data = 0
                    last_ocr_result = None
                    print(f"[+] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Emergency refresh completed due to zero data, continuing capture...\n")
                    continue
            else:
                consecutive_zero_data = 0
                last_valid_data_capture = datetime.datetime.now()
            
            # Use new table data posting function for Sub Total row extraction
            await post_table_data(text, unique_save_path)
        
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Capture #{i+1} successful | Columns extracted: {len(text)}")
            
            # Periodic status report every 10 captures
            if (i + 1) % 10 == 0:
                print(f"\n{'='*70}")
                print(f"📊 STATUS REPORT - Capture #{i+1}")
                print(f"{'='*70}")
                print(f"⏰ Time since last valid data: {(datetime.datetime.now() - last_valid_data_capture).total_seconds():.1f}s")
                print(f"🔄 Consecutive zero data: {consecutive_zero_data}")
                print(f"❌ Consecutive failures: {consecutive_failures}")
                print(f"📈 Last OCR keys: {len(last_ocr_result) if last_ocr_result else 0}")
                print(f"{'='*70}\n")
            
            await asyncio.sleep(1)  # Capture every 1 second
        else:
            # Failed capture - increment failure counter
            consecutive_failures += 1
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Capture #{i+1} failed (consecutive failures: {consecutive_failures})")
            
            # Check if we need to refresh due to consecutive failures
            if consecutive_failures >= max_consecutive_failures:
                refresh_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n{'🟡'*35}")
                print(f"[WARNING] {refresh_time} - {consecutive_failures} consecutive failures detected.")
                print(f"[WARNING] Page may be stuck. Refreshing...")
                print(f"{'🟡'*35}\n")
                await page.reload()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(10000)  # Wait for canvas to load after refresh
                consecutive_failures = 0  # Reset counter after refresh
                print(f"[+] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Failure-based refresh completed, continuing capture...\n")
                continue
            
            # Check if we need preventive refresh (time-based)
            time_since_last_success = (datetime.datetime.now() - last_successful_capture).total_seconds()
            time_since_last_valid_data = (datetime.datetime.now() - last_valid_data_capture).total_seconds()
            
            if time_since_last_success > refresh_interval:
                refresh_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n{'🔵'*35}")
                print(f"[INFO] {refresh_time} - No successful capture for {time_since_last_success:.0f} seconds.")
                print(f"[INFO] Preventive refresh (every {refresh_interval}s)...")
                print(f"{'🔵'*35}\n")
                await page.reload()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(10000)  # Wait for canvas to load after refresh
                last_successful_capture = datetime.datetime.now()
                last_valid_data_capture = datetime.datetime.now()
                consecutive_zero_data = 0
                last_ocr_result = None
                print(f"[+] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Preventive refresh completed, continuing capture...\n")
                continue
            
            # Additional check: refresh if no valid data for extended period (even if captures succeed)
            if time_since_last_valid_data > 120:  # 2 minutes without valid data
                refresh_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n{'🟠'*35}")
                print(f"[WARNING] {refresh_time} - No valid data for {time_since_last_valid_data:.0f} seconds")
                print(f"[WARNING] Despite successful captures, canvas appears stuck. Refreshing...")
                print(f"{'🟠'*35}\n")
                await page.reload()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(10000)  # Wait for canvas to load after refresh
                last_successful_capture = datetime.datetime.now()
                last_valid_data_capture = datetime.datetime.now()
                consecutive_zero_data = 0
                last_ocr_result = None
                print(f"[+] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Data-timeout refresh completed, continuing capture...\n")
                continue
            
            # If not too many failures, just wait and try again
            print("[INFO] Waiting before next attempt...")
            await asyncio.sleep(1)  # Retry after 1 second