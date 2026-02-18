#!/usr/bin/env python3
"""
Multi-User Dashboard Watcher
Handles multiple user credentials and runs them concurrently with persistent browser sessions
"""

import asyncio
import json
import os
import logging
import time
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image
from io import BytesIO
import base64
from ..ocr.engine import ocr_image_google_vision_table
from ..websocket.data_poster import post_table_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Browser configuration
BROWSER_CONFIG = {
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
    ]
}

class MultiUserWatcher:
    def __init__(self, config_file="app/config/users.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.active_tasks = []
        self.user_data_dir = "user_data"  # Base directory for user profiles
        
        # Ensure user data directory exists
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"✅ Loaded configuration for {len(config['users'])} users")
            return config
        except FileNotFoundError:
            logger.error(f"❌ Configuration file {self.config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in configuration file: {e}")
            raise
    
    def get_user_data_dir(self, user_index):
        """Get the persistent user data directory for a specific user"""
        user_dir = os.path.join(self.user_data_dir, f"user_{user_index}")
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        return user_dir

    async def login_user(self, page, user):
        """Login with specific user credentials"""
        try:
            logger.info(f"🔐 Logging in user: {user['name']} ({user['username']})")
            print(f"self.config['dashboard']['login_url']: {self.config['dashboard']['login_url']}")
            # Navigate to login page (no timeout limit for testing)
            await page.goto(self.config['dashboard']['login_url'], wait_until='domcontentloaded', timeout=0)
            await asyncio.sleep(3)  # Give time for page to load
            
            # Fill username using config selector
            username_selector = self.config['dashboard']['selectors']['username']
            await page.locator(username_selector).fill(user['username'])
            logger.info(f"📝 Filled username for {user['username']}")
            
            # Fill password using config selector
            password_selector = self.config['dashboard']['selectors']['password']
            await page.locator(password_selector).fill(user['password'])
            logger.info(f"🔒 Filled password for {user['username']}")
            
            # Submit login using config selector
            login_button_selector = self.config['dashboard']['selectors']['login_button']
            await page.locator(login_button_selector).click()
            await asyncio.sleep(5)  # Wait for login to process
            
            # Check if login was successful
            # current_url = page.url
            # if "login" not in current_url.lower():
            #     logger.info(f"✅ Login successful for {user['name']}, URL: {current_url}")
            #     return True
            # else:
            #     logger.error(f"❌ Login failed for {user['name']}, still on login page")
            #     return False
                
        except Exception as e:
            logger.error(f"❌ Login error for {user['name']}: {e}")
            return False
    
    async def wait_for_canvas_with_retry(self, page, max_retries=3, timeout=0):
        """Wait for canvas/video element with retry logic (no timeout limit for testing)"""
        canvas_selector = self.config['dashboard']['selectors']['canvas']
        for attempt in range(max_retries):
            try:
                logger.info(f"Waiting for video element (attempt {attempt + 1}/{max_retries})")
                await page.wait_for_selector(canvas_selector, state="visible", timeout=timeout)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Video element not found, retrying... ({e})")
                    await asyncio.sleep(10)  # Wait longer before retry
                else:
                    logger.warning(f"Video element not visible after {max_retries} attempts: {e}, continuing anyway...")
                    return False

    async def capture_and_process(self, page, user):
        """Capture canvas screenshots and process with OCR"""
        try:
            logger.info(f"📸 Starting capture process for {user['name']}")
            
            # Navigate to live view with retry (no timeout limit for testing)
            logger.info(f"🌐 Navigating to live view page (this may take time to load)...")
            await page.goto(self.config['dashboard']['live_view_url'], wait_until='domcontentloaded', timeout=0)
            logger.info("⏳ Waiting for page to fully load...")
            
            # Wait for play button to appear (this indicates page is fully loaded)
            play_button_selector = self.config['dashboard']['selectors'].get('play_button', '.play-btn')
            logger.info(f"⏳ Waiting for play button to appear: {play_button_selector}")
            logger.info("   (Play button indicates the page has fully loaded)")
            
            max_wait_attempts = 12  # Wait up to 6 minutes (12 × 30 seconds)
            play_button_found = False
            
            for attempt in range(max_wait_attempts):
                # Check for and hide dialog boxes if present
                dialog_selectors = [
                    '.dialog-content',
                    '.mask.global-guide-dialog',
                    '.dialog.guide-first'
                ]
                
                for dialog_selector in dialog_selectors:
                    try:
                        dialog = page.locator(dialog_selector)
                        dialog_count = await dialog.count()
                        if dialog_count > 0:
                            is_dialog_visible = await dialog.first.is_visible()
                            if is_dialog_visible:
                                logger.info(f"🔍 Dialog box found ({dialog_selector}), hiding it... (attempt {attempt + 1}/{max_wait_attempts})")
                                # Hide the dialog by setting display: none
                                await page.evaluate(f"""
                                    () => {{
                                        const dialog = document.querySelector('{dialog_selector}');
                                        if (dialog) {{
                                            dialog.style.display = 'none';
                                        }}
                                    }}
                                """)
                                logger.info(f"✅ Dialog box hidden ({dialog_selector})")
                    except Exception as dialog_error:
                        logger.debug(f"Dialog check for {dialog_selector}: {dialog_error}")
                
                # Wait a moment after checking/hiding all dialogs
                await asyncio.sleep(2)
                
                play_button = page.locator(play_button_selector)
                play_button_count = await play_button.count()
                
                if play_button_count > 0:
                    is_visible = await play_button.first.is_visible()
                    if is_visible:
                        logger.info(f"✅ Play button found and visible! (attempt {attempt + 1}/{max_wait_attempts})")
                        play_button_found = True
                        break
                    else:
                        logger.info(f"⏳ Play button found but not visible yet... (attempt {attempt + 1}/{max_wait_attempts})")
                else:
                    logger.info(f"⏳ Play button not found yet... (attempt {attempt + 1}/{max_wait_attempts})")
                
                if attempt < max_wait_attempts - 1:
                    logger.info(f"   Waiting 20 seconds before next check...")
                    await asyncio.sleep(20)
            
            # Click play button if found
            if play_button_found:
                try:
                    logger.info("🔘 Clicking play button...")
                    await play_button.first.click()
                    await asyncio.sleep(2)  # Wait for video/canvas to start
                    logger.info("✅ Play button clicked, video should be starting")
                except Exception as e:
                    logger.error(f"❌ Error clicking play button: {e}")
            else:
                logger.warning("⚠️ Play button not found after all attempts, trying alternative selectors...")
                # Try alternative selectors as fallback
                alt_selectors = [
                    'a.play-btn',
                    '.pc-new-video-box .play-btn',
                    'a[class*="play"]',
                    '[aria-label*="click"]'
                ]
                for alt_sel in alt_selectors:
                    try:
                        alt_button = page.locator(alt_sel)
                        alt_count = await alt_button.count()
                        if alt_count > 0:
                            logger.info(f"✅ Found play button with alternative selector: {alt_sel}")
                            await alt_button.first.click()
                            await asyncio.sleep(5)
                            logger.info("✅ Play button clicked")
                            break
                    except:
                        continue
            
            # Now wait for canvas element after play button is clicked
            canvas_selector = self.config['dashboard']['selectors']['canvas']
            logger.info(f"🔍 Waiting for canvas element: {canvas_selector}")
            await asyncio.sleep(5)  # Give time for canvas to appear after play button click

            # Create user-specific images directory
            user_images_dir = os.path.join(self.config['ocr']['images_dir'], user['id'])
            if not os.path.exists(user_images_dir):
                os.makedirs(user_images_dir)
            
            capture_count = 0
            max_captures = user.get('max_captures', 2000)
            interval = user.get('capture_interval', 2)
            
            # Find the element ONCE before entering the capture loop (with retries)
            canvas_selector = self.config['dashboard']['selectors']['canvas']
            element = page.locator(canvas_selector)
            element_found = False
            max_retries = 10
            for retry_attempt in range(max_retries):
                if await element.count() > 0 and await element.first.is_visible():
                    element_found = True
                    logger.info(f"✅ Canvas element (.pc-new-video-box) found and visible (attempt {retry_attempt + 1})")
                    break
                logger.info(f"⏳ Waiting for canvas element... (attempt {retry_attempt + 1}/{max_retries})")
                if retry_attempt < max_retries - 1:
                    await asyncio.sleep(30)
            
            if not element_found:
                logger.error("❌ Canvas element not found after all retries, aborting capture process")
                return
            
            # Inject html2canvas ONCE before the capture loop
            try:
                await page.add_script_tag(url='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js')
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"⚠️ Could not load html2canvas: {e}, will use screenshot fallback")
            
            logger.info(f"🔄 Starting capture loop for {user['name']} (max: {max_captures}, interval: {interval}s)")
            
            while capture_count < max_captures:
                try:
                    # Quick check: element should still be visible (no heavy retry per iteration)
                    element = page.locator(canvas_selector)
                    if await element.count() == 0 or not await element.first.is_visible():
                        logger.warning(f"⚠️ Canvas element not visible, waiting {interval}s before retry...")
                        await asyncio.sleep(interval)
                        continue
                    
                    # Capture the element using toDataURL method (following the sample pattern)
                    canvas_data_url = None
                    try:
                        # html2canvas was injected before the loop - get element and convert to image
                        canvas_data_url = await page.evaluate("""
                            async () => {
                                const container = document.getElementsByClassName('pc-new-video-box')[0];
                                if (!container) return null;
                                
                                // Use html2canvas to convert div to canvas
                                if (typeof html2canvas !== 'undefined') {
                                    try {
                                        const canvas = await html2canvas(container, {
                                            useCORS: true,
                                            allowTaint: true,
                                            scale: 1,
                                            logging: false
                                        });
                                        return canvas.toDataURL('image/png');
                                    } catch(e) {
                                        console.error('html2canvas error:', e);
                                        return null;
                                    }
                                }
                                
                                return null;
                            }
                        """)
                        
                        if canvas_data_url:
                            # Decode base64 image data
                            base64_data = canvas_data_url.split(',')[1]
                            image_data = base64.b64decode(base64_data)
                            image = Image.open(BytesIO(image_data))
                            logger.info(f"✅ Captured element using toDataURL (high quality)")
                        else:
                            # Fall back to screenshot if html2canvas failed
                            logger.info(f"⚠️ html2canvas conversion failed, using screenshot fallback")
                            screenshot_bytes = await element.screenshot(type='png')
                            image = Image.open(BytesIO(screenshot_bytes))
                            
                    except Exception as capture_error:
                        # Fall back to screenshot on any error
                        logger.warning(f"⚠️ toDataURL capture failed ({capture_error}), using screenshot fallback")
                        screenshot_bytes = await element.screenshot(type='png')
                        image = Image.open(BytesIO(screenshot_bytes))
                    
                    # Save with timestamp and user ID
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"canvas_capture_{user['id']}_{timestamp}.png"
                    save_path = os.path.join(user_images_dir, filename)
                    image.save(save_path)
                    
                    ocr_start = time.perf_counter()
                    # Run OCR in a worker thread so one slow API call does not block
                    # the event loop for other users/tasks.
                    table_data = await asyncio.to_thread(ocr_image_google_vision_table, save_path)
                    ocr_duration = time.perf_counter() - ocr_start
                    logger.info(f"⏱️ OCR duration for {filename}: {ocr_duration:.2f}s")
                    
                    # Send to WebSocket (1x10 format - Sub Total row only, no zero replacement)
                    request_key = user.get('request_key', 'machine1')
                    await post_table_data(table_data, save_path, user_info=user, request_key=request_key)
                    
                    capture_count += 1
                    logger.info(f"📊 {user['name']}: Capture #{capture_count}, OCR completed")
                    
                    # Clean up image if not saving
                    if not self.config['ocr']['save_images']:
                        os.remove(save_path)
                        
                except Exception as e:
                    logger.error(f"❌ Capture error for {user['name']}: {e}")
                    await asyncio.sleep(5)  # Short delay on error before retrying
                
                # Wait before next capture
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"❌ Fatal error in capture process for {user['name']}: {e}")
    
    async def run_user(self, user, user_index):
        """Run a complete session for one user with persistent browser context"""
        user_data_dir = self.get_user_data_dir(user_index)
        logger.info(f"🚀 Starting session for {user['name']} (User {user_index + 1}) with profile: {user_data_dir}")
        
        try:
            async with async_playwright() as p:
                # Launch persistent context for this user
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False  # Run headless for server deployment
                    
                )
                
                # Create a new page in the persistent context
                page = await context.new_page()
                
                try:
                    # Login
                    login_success = await self.login_user(page, user)
                    await asyncio.sleep(3)  # Wait after login
                    # if not login_success:
                    #     logger.error(f"❌ Failed to login {user['name']}, skipping session")
                    #     return
                    
                    # Start capture process
                    await self.capture_and_process(page, user)
                    
                finally:
                    # Ensure we always close the context properly
                    await context.close()
                    logger.info(f"🏁 Session completed for {user['name']}")
                    
        except Exception as e:
            logger.error(f"❌ Session error for {user['name']}: {e}")
    
    async def run_all_users(self):
        """Run sessions for all enabled users concurrently"""
        enabled_users = [user for user in self.config['users'] if user.get('enabled', True)]
        
        if not enabled_users:
            logger.warning("⚠️ No enabled users found in configuration")
            return
        
        logger.info(f"🎯 Starting sessions for {len(enabled_users)} enabled users")
        
        # Create tasks for all enabled users
        tasks = []
        for index, user in enumerate(enabled_users):
            task = asyncio.create_task(self.run_user(user, index))
            tasks.append(task)
            self.active_tasks.append(task)
        
        # Wait for all tasks to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal, stopping all sessions...")
            for task in self.active_tasks:
                task.cancel()
            await asyncio.gather(*self.active_tasks, return_exceptions=True)
        finally:
            logger.info("🏁 All user sessions completed")

async def main():
    """Main entry point"""
    try:
        watcher = MultiUserWatcher()
        await watcher.run_all_users()
    except KeyboardInterrupt:
        logger.info("🛑 Multi-user watcher stopped by user")
    except Exception as e:
        logger.error(f"❌ Multi-user watcher error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 