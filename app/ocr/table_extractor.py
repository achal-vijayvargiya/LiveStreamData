"""
Table Data Extractor for OCR Results
Extracts table data from Google Vision OCR response, specifically the "Sub Total" row.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from google.cloud import vision

# Configure logging
logger = logging.getLogger(__name__)


def extract_table_data_from_ocr(response) -> Dict[int, int]:
    """
    Extract table data from Google Vision OCR response.
    Specifically extracts the "Sub Total" row values.
    
    Args:
        response: Google Vision API response object
        
    Returns:
        Dictionary mapping column numbers (1-10) to their values from Sub Total row
    """
    # Get all text blocks with their bounding boxes
    text_blocks = []
    
    logger.info("=" * 80)
    logger.info("🔍 [TABLE EXTRACTOR] Starting OCR data extraction")
    logger.info("=" * 80)
    
    # Extract text with bounding box information
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    # Get bounding box
                    vertices = word.bounding_box.vertices
                    if len(vertices) >= 2:
                        # Use top-left corner for positioning
                        x = vertices[0].x if vertices[0].x is not None else 0
                        y = vertices[0].y if vertices[0].y is not None else 0
                        text_blocks.append({
                            'text': word_text,
                            'x': x,
                            'y': y,
                            'bbox': vertices
                        })
    
    logger.info(f"📊 [TABLE EXTRACTOR] Extracted {len(text_blocks)} text blocks from OCR")
    if text_blocks:
        logger.info(f"📝 [TABLE EXTRACTOR] First 20 text blocks: {[(b['text'], b['x'], b['y']) for b in text_blocks[:20]]}")
    
    # Log full OCR text for debugging
    if hasattr(response, 'full_text_annotation') and response.full_text_annotation:
        full_text = response.full_text_annotation.text
        logger.info(f"📄 [TABLE EXTRACTOR] Full OCR text (first 500 chars):\n{full_text[:500]}")
        logger.info(f"📄 [TABLE EXTRACTOR] Full OCR text length: {len(full_text)} characters")
    
    # If we don't have bounding boxes, fall back to text-based parsing
    if not text_blocks or len(text_blocks) < 10:
        logger.warning(f"⚠️ [TABLE EXTRACTOR] Insufficient text blocks ({len(text_blocks)}), falling back to text-based extraction")
        return extract_table_from_text(response)
    
    # Group text blocks by approximate Y position (rows)
    # Sort by Y coordinate
    text_blocks.sort(key=lambda b: b['y'])
    
    # Group into rows (tolerance for slight Y variations)
    rows = []
    current_row = []
    current_y = None
    y_tolerance = 20  # Pixels tolerance for same row
    
    for block in text_blocks:
        if current_y is None or abs(block['y'] - current_y) <= y_tolerance:
            current_row.append(block)
            if current_y is None:
                current_y = block['y']
        else:
            if current_row:
                rows.append(current_row)
            current_row = [block]
            current_y = block['y']
    
    if current_row:
        rows.append(current_row)
    
    logger.info(f"📋 [TABLE EXTRACTOR] Grouped into {len(rows)} rows")
    for i, row in enumerate(rows[:10]):  # Log first 10 rows
        row_text = ' '.join([b['text'] for b in row])
        logger.info(f"   Row {i}: Y={row[0]['y'] if row else 'N/A'}, Text: '{row_text[:100]}'")
    
    # Find the "Sub Total" row
    sub_total_row = None
    sub_total_row_index = None
    
    for i, row in enumerate(rows):
        row_text = ' '.join([b['text'] for b in row]).lower()
        if 'sub total' in row_text or 'subtotal' in row_text:
            sub_total_row = row
            sub_total_row_index = i
            logger.info(f"✅ [TABLE EXTRACTOR] Found 'Sub Total' row at index {i}")
            logger.info(f"   Row text: '{' '.join([b['text'] for b in row])}'")
            break
    
    if sub_total_row is None:
        logger.warning("⚠️ [TABLE EXTRACTOR] 'Sub Total' row not found by text search")
        # Fallback: try to find row by position (usually 2nd data row after headers)
        if len(rows) >= 3:
            # Skip header row, take second row (index 1)
            sub_total_row = rows[1]
            sub_total_row_index = 1
            logger.info(f"🔄 [TABLE EXTRACTOR] Using fallback: row at index 1")
            logger.info(f"   Row text: '{' '.join([b['text'] for b in sub_total_row])}'")
        else:
            # Last resort: use text-based extraction
            logger.warning(f"⚠️ [TABLE EXTRACTOR] Not enough rows ({len(rows)}), falling back to text-based extraction")
            return extract_table_from_text(response)
    
    # Extract numeric values from Sub Total row
    # Sort blocks in row by X coordinate (left to right) to ensure column order
    sub_total_row.sort(key=lambda b: b['x'])
    
    logger.info(f"🔢 [TABLE EXTRACTOR] Sub Total row has {len(sub_total_row)} blocks")
    logger.info(f"   All blocks in Sub Total row: {[(b['text'], b['x'], b['y']) for b in sub_total_row]}")
    
    # Filter out the "Sub Total" label blocks and other non-data blocks
    # First, determine the typical Y position for Sub Total row data blocks
    # Only use blocks that are clearly numeric data (not labels, not large numbers)
    data_y_positions = []
    for block in sub_total_row:
        block_text = block['text'].strip()
        block_text_lower = block_text.lower()
        
        # Skip label blocks
        if block_text_lower in ['sub', 'total', 'subtotal'] or 'sub total' in block_text_lower:
            logger.debug(f"   Skipping label block: '{block_text}'")
            continue
        
        # Only include blocks that are clearly numeric data values
        try:
            num_value = int(block_text)
            if num_value >= 0:
                data_y_positions.append(block['y'])
                logger.debug(f"   Found numeric block: '{block_text}' = {num_value} at Y={block['y']}")
        except ValueError:
            logger.debug(f"   Skipping non-numeric block: '{block_text}'")
            continue
    
    # Calculate median Y position for data blocks (more robust than mean)
    if data_y_positions:
        sorted_y = sorted(data_y_positions)
        median_y = sorted_y[len(sorted_y) // 2]
        # Use very tight tolerance - blocks should be almost exactly on the same line
        y_tolerance = 3  # Very tight - only 3 pixels difference allowed
    else:
        # Fallback: use the Y position of the first non-label block
        for block in sub_total_row:
            block_text_lower = block['text'].lower()
            if 'sub' not in block_text_lower and 'total' not in block_text_lower:
                median_y = block['y']
                break
        else:
            median_y = None
        y_tolerance = 3
    
    data_blocks = []
    logger.info(f"📐 [TABLE EXTRACTOR] Median Y position: {median_y}, Y tolerance: {y_tolerance}")
    
    for block in sub_total_row:
        block_text = block['text'].strip()
        block_text_lower = block_text.lower()
        
        # Skip label blocks
        if block_text_lower in ['sub', 'total', 'subtotal'] or 'sub total' in block_text_lower:
            logger.debug(f"   Filtering out label block: '{block_text}'")
            continue
        
        # Filter by Y position - must be close to median Y of data blocks
        if median_y is not None and abs(block['y'] - median_y) > y_tolerance:
            logger.debug(f"   Filtering out block '{block_text}' due to Y position mismatch: {block['y']} vs {median_y} (tolerance: {y_tolerance})")
            continue
        
        # Try to extract numeric value
        try:
            num_value = int(block_text)
            logger.info(f"   ✅ Keeping numeric block: '{block_text}' = {num_value} at (X={block['x']}, Y={block['y']})")
            data_blocks.append(block)
        except ValueError:
            # Not a number, might be other text - skip it
            logger.debug(f"   Filtering out non-numeric block: '{block_text}'")
            continue
    
    # Extract values from each block, preserving order
    # Since we've already filtered to only data blocks, extract the number directly
    block_values = []
    logger.info(f"💰 [TABLE EXTRACTOR] Extracting values from {len(data_blocks)} data blocks")
    
    for i, block in enumerate(data_blocks):
        block_text = block['text'].strip()
        
        # Try to extract the number directly from the block text
        # The block should contain a single number (the Sub Total value)
        try:
            # Direct conversion - block should be just a number
            value = int(block_text)
            block_values.append(value)
            logger.info(f"   Block {i+1}: '{block_text}' -> {value}")
        except ValueError:
            # If direct conversion fails, try to extract numbers
            nums = re.findall(r'\d+', block_text)
            if nums:
                # Take the first/largest number found
                all_nums = [int(n) for n in nums]
                # Use the largest number found
                if all_nums:
                    value = max(all_nums)
                    block_values.append(value)
                    logger.info(f"   Block {i+1}: '{block_text}' -> extracted {value} (from {all_nums})")
                else:
                    block_values.append(0)
                    logger.warning(f"   Block {i+1}: '{block_text}' -> 0 (no valid numbers)")
            else:
                # No numbers found - should be 0
                block_values.append(0)
                logger.warning(f"   Block {i+1}: '{block_text}' -> 0 (no numbers found)")
    
    logger.info(f"📊 [TABLE EXTRACTOR] Extracted {len(block_values)} values: {block_values}")
    
    # Now we need to map these block values to column positions 1-10
    # If we have exactly 10 blocks, map directly
    # If we have fewer, we need to infer missing positions
    # Strategy: Assume blocks are evenly spaced, and missing blocks are zeros
    
    if len(block_values) == 10:
        # Perfect - we have exactly 10 blocks, map directly
        result = {}
        for i, value in enumerate(block_values, start=1):
            result[i] = value
        logger.info(f"✅ [TABLE EXTRACTOR] Successfully extracted {len(result)} column values from Sub Total row: {result}")
        logger.info("=" * 80)
        return result
    elif len(block_values) > 10:
        # More than 10 blocks - take first 10
        result = {}
        for i, value in enumerate(block_values[:10], start=1):
            result[i] = value
        logger.warning(f"⚠️ [TABLE EXTRACTOR] Found {len(block_values)} blocks, taking first 10: {result}")
        logger.info("=" * 80)
        return result
    else:
        # Fewer than 10 blocks - need to infer positions
        logger.warning(f"⚠️ [TABLE EXTRACTOR] Only found {len(block_values)} blocks, need to infer positions")
        # Use X coordinates to estimate column positions
        # Calculate average spacing between blocks
        if len(data_blocks) > 1:
            x_positions = [b['x'] for b in data_blocks]
            spacings = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
            avg_spacing = sum(spacings) / len(spacings) if spacings else 100
            logger.info(f"📏 [TABLE EXTRACTOR] X positions: {x_positions}, avg spacing: {avg_spacing}")
            
            # Create a mapping: for each column 1-10, find the closest block
            result = {}
            for col_num in range(1, 11):
                # Estimate X position for this column (assuming columns start at first block's X)
                estimated_x = data_blocks[0]['x'] + (col_num - 1) * avg_spacing
                
                # Find the closest block to this estimated position
                closest_block_idx = None
                min_distance = float('inf')
                for i, block in enumerate(data_blocks):
                    distance = abs(block['x'] - estimated_x)
                    if distance < min_distance:
                        min_distance = distance
                        closest_block_idx = i
                
                # If the closest block is within reasonable distance, use its value
                # Otherwise, it's likely an empty cell (zero)
                if closest_block_idx is not None and min_distance < avg_spacing * 0.5:
                    # This block likely belongs to this column
                    result[col_num] = block_values[closest_block_idx]
                    logger.debug(f"   Column {col_num}: mapped to block {closest_block_idx+1} (distance: {min_distance:.1f})")
                else:
                    # No block close enough - empty cell
                    result[col_num] = 0
                    logger.debug(f"   Column {col_num}: no block found (min distance: {min_distance:.1f})")
        else:
            # Not enough blocks to estimate spacing - just map sequentially and fill with zeros
            logger.warning(f"⚠️ [TABLE EXTRACTOR] Not enough blocks ({len(data_blocks)}) to estimate spacing")
            result = {}
            for i, value in enumerate(block_values, start=1):
                if i <= 10:
                    result[i] = value
            for i in range(len(block_values) + 1, 11):
                result[i] = 0
        
        non_zero_count = len([v for v in result.values() if v > 0])
        logger.info(f"📊 [TABLE EXTRACTOR] Final result: {non_zero_count} non-zero values from {len(block_values)} blocks: {result}")
        logger.info("=" * 80)
        return result


def extract_table_from_text(response) -> Dict[int, int]:
    """
    Fallback method: Extract table data from plain text OCR result.
    Looks for "Sub Total" row in the text and extracts numeric values.
    
    Args:
        response: Google Vision API response object
        
    Returns:
        Dictionary mapping column numbers (1-10) to their values
    """
    full_text = response.full_text_annotation.text
    
    # Split into lines
    lines = full_text.split('\n')
    
    # Find the "Sub Total" line
    sub_total_line = None
    sub_total_index = None
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if 'sub total' in line_lower or 'subtotal' in line_lower:
            sub_total_line = line
            sub_total_index = i
            break
    
    if sub_total_line is None:
        # Try to find by position - usually 2nd data row
        # Look for lines with multiple numbers
        for i, line in enumerate(lines):
            numbers = re.findall(r'\d+', line)
            if len(numbers) >= 5:  # Likely a data row
                # Check if previous line might be "Input" or header
                if i > 0 and ('input' in lines[i-1].lower() or 'action' in lines[i-1].lower()):
                    sub_total_line = line
                    sub_total_index = i
                    break
    
    if sub_total_line is None:
        logger.warning("[TABLE EXTRACTOR] Could not find Sub Total row in OCR text")
        logger.warning(f"[TABLE EXTRACTOR] Available lines (first 20): {lines[:20]}")
        return {i: 0 for i in range(1, 11)}
    
    # Extract all numbers from the Sub Total line (preserving order and including 0)
    numbers = re.findall(r'\d+', sub_total_line)
    
    # Convert to integers, preserving all numbers including zeros
    all_numbers = [int(num_str) for num_str in numbers]
    
    # We need to identify which numbers are likely Sub Total values
    # Sub Total values are typically >= 10, but we also need to preserve zeros
    # Strategy: Keep all numbers >= 10, and also keep 0 if it appears
    # For numbers < 10 and > 0, they might be part of other text, so filter them
    valid_numbers = []
    for num in all_numbers:
        if num >= 10:
            valid_numbers.append(num)
        elif num == 0:
            # Preserve zeros - they're valid data values
            valid_numbers.append(0)
        # Skip numbers 1-9 as they're likely not Sub Total values
    
    # Create result dictionary - take first 10 values
    result = {}
    for i, value in enumerate(valid_numbers[:10], start=1):
        result[i] = value
    
    # Fill missing columns with 0 if we have fewer than 10 values
    for i in range(len(valid_numbers) + 1, 11):
        result[i] = 0
    
    non_zero_count = len([v for v in result.values() if v > 0])
    logger.info(f"[TABLE EXTRACTOR] Extracted {non_zero_count} non-zero column values from Sub Total row (text-based): {result}")
    return result


def extract_table_data(image_path, response=None) -> Dict[int, int]:
    """
    Main entry point for table data extraction.
    
    Args:
        image_path: Path to the image file
        response: Optional pre-computed OCR response (to avoid re-calling API)
        
    Returns:
        Dictionary mapping column numbers (1-10) to Sub Total values
    """
    if response is None:
        from .vision import get_full_ocr_response
        response = get_full_ocr_response(image_path)
    
    return extract_table_data_from_ocr(response)

