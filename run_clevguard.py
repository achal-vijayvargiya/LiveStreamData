#!/usr/bin/env python3
"""
Run Clevguard Multi-User Watcher
Full application flow: Login -> Navigate -> Play -> Capture -> OCR -> WebSocket
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

async def main():
    """Main entry point for Clevguard watcher"""
    logger.info("=" * 80)
    logger.info("🚀 Clevguard Multi-User Watcher - Starting Application")
    logger.info("=" * 80)
    logger.info("Flow:")
    logger.info("  1. Login to clevguard account")
    logger.info("  2. Navigate to live view page")
    logger.info("  3. Wait for play button and click it")
    logger.info("  4. Wait for canvas element")
    logger.info("  5. Capture screenshots")
    logger.info("  6. Extract 10 values using OCR table extractor")
    logger.info("  7. Send data via WebSocket")
    logger.info("=" * 80)
    
    try:
        watcher = MultiUserWatcher("app/config/users.json")
        await watcher.run_all_users()
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
