#!/usr/bin/env python3
"""
Multi-User Dashboard Watcher - Fixed Version
Handles multiple user credentials with proper session isolation
"""

import asyncio
import json
import os
import logging
import random
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image
from io import BytesIO
import base64
from app.ocr.engine import ocr_image_google_vision
from app.websocket.data_poster import post_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiUserWatcherFixed:
    def __init__(self, config_file="app/config/users.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.active_tasks = []
        
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
    
    async def login_user(self, page, user, user_index):
        """Login with specific user credentials with proper delays"""
        try:
            logger.info(f"🔐 Logging in user {user_index + 1}: {user['name']} ({user['username']})")
            
            # Add random delay to prevent rate limiting
            delay = random.uniform(2, 5)
            logger.info(f"⏳ Waiting {delay:.1f}s before login attempt...")
            await asyncio.sleep(delay)
            
            # Navigate to login page
            await page.goto(self.config['dashboard']['login_url'])
            await page.wait_for_load_state('networkidle')
            
            # Wait for page to be fully loaded
            await page.wait_for_selector('input', timeout=10000)
            
            # Clear any existing data
            await page.evaluate("() => { document.querySelectorAll('input').forEach(input => input.value = ''); }")
            
            # Fill username with delay
            await page.locator('input').nth(0).fill(user['username'])
            await asyncio.sleep(0.5)
            logger.info(f"📝 Filled username for {user['username']}")
            
            # Fill password with delay
            await page.locator('input').nth(1).fill(user['password'])
            await asyncio.sleep(0.5)
            logger.info(f"🔒 Filled password for {user['username']}")
            
            # Submit login
            await page.get_by_role("button").press('Enter')
            await page.wait_for_load_state('networkidle')
            
            # Wait a bit more for any redirects
            await asyncio.sleep(2)
            
            # Check if login was successful
            current_url = page.url
            if "login" not in current_url.lower():
                logger.info(f"✅ Login successful for {user['name']}, URL: {current_url}")
                return True
            else:
                logger.error(f"❌ Login failed for {user['name']}, still on login page")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error for {user['name']}: {e}")
            return False
    
    async def capture_and_process(self, page, user):
        """Capture canvas screenshots and process with OCR"""
        try:
            logger.info(f"📸 Starting capture process for {user['name']}")
            
            # Navigate to live view
            await page.goto(self.config['dashboard']['live_view_url'])
            await page.wait_for_load_state('networkidle')
            await page.wait_for_selector(self.config['dashboard']['selectors']['canvas'], 
                                       state="visible", timeout=10000)
            
            # Create user-specific images directory
            user_images_dir = os.path.join(self.config['ocr']['images_dir'], user['id'])
            if not os.path.exists(user_images_dir):
                os.makedirs(user_images_dir)
            
            capture_count = 0
            max_captures = user.get('max_captures', 2000)
            interval = user.get('capture_interval', 20)
            
            logger.info(f"🔄 Starting capture loop for {user['name']} (max: {max_captures}, interval: {interval}s)")
            
            while capture_count < max_captures:
                try:
                    # Get canvas data URL
                    canvas_data_url = await page.evaluate("""
                        () => {
                            const canvas = document.getElementById('canvas');
                            return canvas ? canvas.toDataURL('image/png') : null;
                        }
                    """)
                    
                    if canvas_data_url:
                        # Decode base64 image
                        base64_data = canvas_data_url.split(',')[1]
                        image_data = base64.b64decode(base64_data)
                        image = Image.open(BytesIO(image_data))
                        
                        # Save with timestamp and user ID
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = f"canvas_capture_{user['id']}_{timestamp}.png"
                        save_path = os.path.join(user_images_dir, filename)
                        image.save(save_path)
                        
                        # Perform OCR
                        ocr_text = ocr_image_google_vision(save_path)
                        
                        # Send to WebSocket
                        await post_data(ocr_text, save_path, user_info=user)
                        
                        capture_count += 1
                        logger.info(f"📊 {user['name']}: Capture #{capture_count}, OCR completed")
                        
                        # Clean up image if not saving
                        if not self.config['ocr']['save_images']:
                            os.remove(save_path)
                            
                    else:
                        logger.warning(f"⚠️ Canvas not found for {user['name']}")
                        
                except Exception as e:
                    logger.error(f"❌ Capture error for {user['name']}: {e}")
                
                # Wait before next capture
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"❌ Fatal error in capture process for {user['name']}: {e}")
    
    async def run_user_session(self, user, user_index):
        """Run a complete session for one user with proper isolation"""
        try:
            logger.info(f"🚀 Starting session for {user['name']} (User {user_index + 1})")
            
            async with async_playwright() as p:
                # Use different browser contexts for each user
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                # Create isolated context for this user
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                # Login
                login_success = await self.login_user(page, user, user_index)
                if not login_success:
                    logger.error(f"❌ Failed to login {user['name']}, skipping session")
                    await browser.close()
                    return
                
                # Start capture process
                await self.capture_and_process(page, user)
                
                await browser.close()
                logger.info(f"🏁 Session completed for {user['name']}")
                
        except Exception as e:
            logger.error(f"❌ Session error for {user['name']}: {e}")
    
    async def run_all_users_sequential(self):
        """Run sessions sequentially to avoid conflicts"""
        enabled_users = [user for user in self.config['users'] if user.get('enabled', True)]
        
        if not enabled_users:
            logger.warning("⚠️ No enabled users found in configuration")
            return
        
        logger.info(f"🎯 Starting sequential sessions for {len(enabled_users)} enabled users")
        
        for i, user in enumerate(enabled_users):
            logger.info(f"🔄 Starting user {i + 1}/{len(enabled_users)}: {user['name']}")
            await self.run_user_session(user, i)
            
            # Add delay between users
            if i < len(enabled_users) - 1:
                delay = random.uniform(5, 10)
                logger.info(f"⏳ Waiting {delay:.1f}s before next user...")
                await asyncio.sleep(delay)
        
        logger.info("🏁 All user sessions completed")
    
    async def run_all_users_concurrent(self):
        """Run sessions concurrently with staggered starts"""
        enabled_users = [user for user in self.config['users'] if user.get('enabled', True)]
        
        if not enabled_users:
            logger.warning("⚠️ No enabled users found in configuration")
            return
        
        logger.info(f"🎯 Starting concurrent sessions for {len(enabled_users)} enabled users")
        
        # Create tasks with staggered starts
        tasks = []
        for i, user in enumerate(enabled_users):
            # Stagger the start times to avoid login conflicts
            start_delay = i * 10  # 10 seconds between each user start
            task = asyncio.create_task(self.run_user_session_with_delay(user, i, start_delay))
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
        
        logger.info("🏁 All user sessions completed")
    
    async def run_user_session_with_delay(self, user, user_index, start_delay):
        """Run user session with a delay"""
        if start_delay > 0:
            logger.info(f"⏳ Waiting {start_delay}s before starting {user['name']}...")
            await asyncio.sleep(start_delay)
        
        await self.run_user_session(user, user_index)

async def main():
    """Main entry point"""
    try:
        watcher = MultiUserWatcherFixed()
        
        # Choose your mode:
        # 1. Sequential (safer, no conflicts)
        await watcher.run_all_users_sequential()
        
        # 2. Concurrent with staggered starts (faster but more complex)
        # await watcher.run_all_users_concurrent()
        
    except KeyboardInterrupt:
        logger.info("🛑 Multi-user watcher stopped by user")
    except Exception as e:
        logger.error(f"❌ Multi-user watcher error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 