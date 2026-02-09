#!/usr/bin/env python3
"""
End-to-end test script for Clevguard website
Tests complete flow: login -> live view -> capture -> OCR -> WebSocket
"""

import asyncio
import logging
from app.core.multi_user_watcher import MultiUserWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_end_to_end():
    """Run end-to-end test"""
    logger.info("=" * 80)
    logger.info("🧪 END-TO-END TEST - Clevguard Website")
    logger.info("=" * 80)
    logger.info("Testing complete flow:")
    logger.info("  1. Login to clevguard")
    logger.info("  2. Navigate to live view page")
    logger.info("  3. Wait for canvas element (.pc-new-video-box)")
    logger.info("  4. Capture screenshot")
    logger.info("  5. Extract 10 values using table extractor")
    logger.info("  6. Send via WebSocket")
    logger.info("=" * 80)
    
    try:
        watcher = MultiUserWatcher("app/config/users.json")
        await watcher.run_all_users()
    except KeyboardInterrupt:
        logger.info("🛑 Test stopped by user")
    except Exception as e:
        logger.error(f"❌ Test error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_end_to_end())

