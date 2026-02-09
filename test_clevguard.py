#!/usr/bin/env python3
"""
Test script for Clevguard website
Tests login, navigation to live view, and canvas element selection
"""

import asyncio
import json
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_file="app/config/users.json"):
    """Load configuration from JSON file"""
    with open(config_file, 'r') as f:
        return json.load(f)

async def test_clevguard():
    """Test login, navigation, and canvas element selection"""
    config = load_config()
    
    if not config['users']:
        logger.error("❌ No users found in configuration")
        return
    
    user = config['users'][0]
    selectors = config['dashboard']['selectors']
    
    logger.info(f"🧪 Testing with user: {user['name']}")
    logger.info(f"🔗 Login URL: {config['dashboard']['login_url']}")
    logger.info(f"🔗 Live View URL: {config['dashboard']['live_view_url']}")
    
    try:
        async with async_playwright() as p:
            # Launch browser (headless=False for testing)
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Step 1: Login
                logger.info("=" * 60)
                logger.info("STEP 1: Testing Login")
                logger.info("=" * 60)
                
                login_url = config['dashboard']['login_url']
                logger.info(f"🌐 Navigating to login page: {login_url}")
                await page.goto(login_url, wait_until='domcontentloaded', timeout=0)
                await asyncio.sleep(3)  # Wait for page to load
                
                # Fill username
                logger.info(f"📝 Filling username: {user['username']}")
                logger.info(f"   Using selector: {selectors['username']}")
                await page.locator(selectors['username']).fill(user['username'])
                await asyncio.sleep(1)
                
                # Fill password
                logger.info(f"🔒 Filling password")
                logger.info(f"   Using selector: {selectors['password']}")
                await page.locator(selectors['password']).fill(user['password'])
                await asyncio.sleep(1)
                
                # Click login button
                logger.info(f"🔘 Clicking login button")
                logger.info(f"   Using selector: {selectors['login_button']}")
                await page.locator(selectors['login_button']).click()
                await asyncio.sleep(5)  # Wait for login to complete
                try:
                    await page.wait_for_load_state('domcontentloaded', timeout=10000)
                except:
                    pass  # Continue even if timeout
                
                current_url = page.url
                logger.info(f"📍 Current URL after login: {current_url}")
                
                # Step 2: Navigate to live view with refresh if needed
                logger.info("=" * 60)
                logger.info("STEP 2: Navigating to Live View Page")
                logger.info("=" * 60)
                
                live_view_url = config['dashboard']['live_view_url']
                logger.info(f"🌐 Navigating to: {live_view_url}")
                
                # First attempt to load (no timeout limit for testing)
                logger.info("⏳ Navigating to live view page (this may take time to load)...")
                await page.goto(live_view_url, wait_until='domcontentloaded', timeout=0)
                logger.info(f"📍 Current URL after navigation: {page.url}")
                
                # Wait for play button to appear (this indicates page is fully loaded)
                # Note: We don't wait for network idle because the page streams data continuously
                play_button_selector = selectors.get('play_button', '.play-btn')
                logger.info(f"⏳ Waiting for play button to appear: {play_button_selector}")
                logger.info("   (Play button indicates the page has fully loaded)")
                
                max_wait_attempts = 12  # Wait up to 6 minutes (12 × 30 seconds)
                play_button_found = False
                
                for attempt in range(max_wait_attempts):
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
                        logger.info(f"   Waiting 30 seconds before next check...")
                        await asyncio.sleep(30)
                
                # Click play button if found
                if play_button_found:
                    logger.info("=" * 60)
                    logger.info("STEP 2.5: Clicking Play Button")
                    logger.info("=" * 60)
                    
                    try:
                        play_button = page.locator(play_button_selector)
                        logger.info("🔘 Clicking play button...")
                        await play_button.first.click()
                        await asyncio.sleep(5)  # Wait for video/canvas to start
                        logger.info("✅ Play button clicked successfully, video should be starting")
                    except Exception as e:
                        logger.error(f"❌ Error clicking play button: {e}")
                else:
                    logger.warning("⚠️ Play button not found after all attempts, trying to continue anyway...")
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
                
                # Now check for canvas element after play button is clicked
                canvas_selector = selectors['canvas']
                logger.info("=" * 60)
                logger.info("STEP 3: Checking Canvas Element")
                logger.info("=" * 60)
                logger.info(f"🔍 Looking for canvas element: {canvas_selector}")
                
                element_count = await page.locator(canvas_selector).count()
                
                # If element not found, refresh the page
                if element_count == 0:
                    logger.warning("⚠️ Canvas element not found on first load, refreshing page...")
                    await page.reload(wait_until='domcontentloaded', timeout=0)
                    await asyncio.sleep(10)  # Wait after refresh
                    logger.info(f"📍 Current URL after refresh: {page.url}")
                    
                    # Check again after refresh
                    element_count = await page.locator(canvas_selector).count()
                    if element_count == 0:
                        logger.warning("⚠️ Canvas element still not found after refresh, waiting additional 30 seconds...")
                        await asyncio.sleep(30)
                else:
                    logger.info("✅ Canvas element found on first load")
                
                logger.info(f"📍 Final URL: {page.url}")
                
                # Step 3: Check canvas element
                logger.info("=" * 60)
                logger.info("STEP 3: Checking Canvas Element")
                logger.info("=" * 60)
                
                canvas_selector = selectors['canvas']
                logger.info(f"🔍 Looking for element with selector: {canvas_selector}")
                
                # Check if element exists (even if not visible)
                element_count = await page.locator(canvas_selector).count()
                element_exists = element_count > 0
                logger.info(f"✅ Element exists: {element_exists} (found {element_count} element(s))")
                
                if element_exists:
                    # Check visibility
                    is_visible = await page.locator(canvas_selector).first.is_visible()
                    logger.info(f"👁️  Element visible: {is_visible}")
                    
                    # Get element info
                    try:
                        element_info = await page.locator(canvas_selector).first.evaluate("""
                            (el) => {
                                return {
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    display: window.getComputedStyle(el).display,
                                    visibility: window.getComputedStyle(el).visibility,
                                    width: el.offsetWidth,
                                    height: el.offsetHeight,
                                    innerHTML: el.innerHTML.substring(0, 100)
                                };
                            }
                        """)
                        
                        logger.info(f"📊 Element Info:")
                        logger.info(f"   Tag: {element_info.get('tagName')}")
                        logger.info(f"   Class: {element_info.get('className')}")
                        logger.info(f"   ID: {element_info.get('id')}")
                        logger.info(f"   Display: {element_info.get('display')}")
                        logger.info(f"   Visibility: {element_info.get('visibility')}")
                        logger.info(f"   Dimensions: {element_info.get('width')}x{element_info.get('height')}")
                        logger.info(f"   InnerHTML preview: {element_info.get('innerHTML', '')[:50]}...")
                    except Exception as e:
                        logger.warning(f"⚠️  Could not get element details: {e}")
                    
                    logger.info("=" * 60)
                    logger.info("✅ TEST COMPLETED SUCCESSFULLY")
                    logger.info("=" * 60)
                    logger.info("Summary:")
                    logger.info(f"  ✓ Login: Completed")
                    logger.info(f"  ✓ Navigation: Completed")
                    logger.info(f"  ✓ Element Found: Yes ({element_count} element(s))")
                    logger.info(f"  ✓ Element Visible: {is_visible}")
                else:
                    logger.error("=" * 60)
                    logger.error("❌ TEST FAILED: Canvas element not found")
                    logger.error("=" * 60)
                    logger.error("Trying to find any elements with similar classes...")
                    
                    # Try to find similar elements
                    try:
                        similar_elements = await page.evaluate("""
                            () => {
                                const elements = document.querySelectorAll('[class*="video"], [class*="canvas"], [class*="pc-new"]');
                                return Array.from(elements).slice(0, 5).map(el => ({
                                    tag: el.tagName,
                                    class: el.className,
                                    id: el.id,
                                    display: window.getComputedStyle(el).display
                                }));
                            }
                        """)
                        if similar_elements:
                            logger.info("Found similar elements:")
                            for el in similar_elements:
                                logger.info(f"  - {el['tag']}: class='{el['class']}', id='{el['id']}', display='{el['display']}'")
                    except Exception as e:
                        logger.warning(f"Could not search for similar elements: {e}")
                
                # Keep browser open for manual inspection
                logger.info("=" * 60)
                logger.info("⏸️  Keeping browser open for 30 seconds for manual inspection...")
                logger.info("   You can manually check the page in the browser window")
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Test error: {e}", exc_info=True)
                logger.info("⏸️  Keeping browser open for 30 seconds for debugging...")
                await asyncio.sleep(30)
            finally:
                await browser.close()
                
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_clevguard())
