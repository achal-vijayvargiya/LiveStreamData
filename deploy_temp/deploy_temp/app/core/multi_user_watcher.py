#!/usr/bin/env python3
"""
Multi-User Dashboard Watcher
Handles multiple user credentials and runs them concurrently with persistent browser sessions
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image
from io import BytesIO
import base64
from ..ocr.engine import ocr_image_google_vision
from ..websocket.data_poster import post_data

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
            
            # Navigate to login page
            await page.goto(self.config['dashboard']['login_url'])
            await page.wait_for_load_state('networkidle')
            
            # Fill username
            await page.locator('input').nth(0).fill(user['username'])
            logger.info(f"📝 Filled username for {user['username']}")
            
            # Fill password
            await page.locator('input').nth(1).fill(user['password'])
            logger.info(f"🔒 Filled password for {user['username']}")
            
            # Submit login
            await page.get_by_role("button").press('Enter')
            await page.wait_for_load_state('networkidle')
            
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
                    headless=True,  # Run headless for server deployment
                    viewport=BROWSER_CONFIG['viewport'],
                    user_agent=BROWSER_CONFIG['user_agent']
                )
                
                # Create a new page in the persistent context
                page = await context.new_page()
                
                try:
                    # Login
                    login_success = await self.login_user(page, user)
                    if not login_success:
                        logger.error(f"❌ Failed to login {user['name']}, skipping session")
                        return
                    
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