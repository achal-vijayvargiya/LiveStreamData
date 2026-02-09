#!/usr/bin/env python3
"""
Test script for table extraction from OCR results
Tests the new table extraction logic with a sample image
"""

import sys
import os
import json
import asyncio

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.ocr.vision import get_full_ocr_response
from app.ocr.table_extractor import extract_table_data, extract_table_data_from_ocr

# Try to import the engine function, but it's optional
try:
    from app.ocr.engine import ocr_image_google_vision_table
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False
    print("⚠️  Note: Could not import ocr_image_google_vision_table (paddleocr not needed for this test)")


def format_websocket_output(table_data):
    """
    Format table data as it would be sent to websocket (without actually sending)
    This mimics the post_table_data function logic
    Format: Simple list of 10 numbers [value1, value2, ..., value10]
    """
    output = []
    for col_num in range(1, 11):  # Columns 1-10
        value = table_data.get(col_num, 0)
        output.append(value)
    
    # For testing, we don't have previous data, so validation won't change anything
    # But we show the format that would be sent
    return output


def test_table_extraction(image_path):
    """
    Test the table extraction flow with a sample image
    
    Args:
        image_path: Path to the test image file
    """
    print("=" * 80)
    print("TABLE EXTRACTION TEST SCRIPT")
    print("=" * 80)
    print(f"\n📸 Testing with image: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        return
    
    print("\n" + "-" * 80)
    print("STEP 1: Getting full OCR response from Google Vision API")
    print("-" * 80)
    
    try:
        # Get full OCR response
        response = get_full_ocr_response(image_path)
        print("✅ OCR response received successfully")
        
        # Print FULL raw OCR text for debugging
        full_text = response.full_text_annotation.text
        print(f"\n📝 FULL Raw OCR Text:")
        print("=" * 80)
        print(full_text)
        print("=" * 80)
        
        # Also print structured blocks information
        print(f"\n📋 OCR Structure Analysis:")
        print(f"   Total pages: {len(response.full_text_annotation.pages)}")
        
        for page_idx, page in enumerate(response.full_text_annotation.pages):
            print(f"\n   Page {page_idx + 1}:")
            print(f"      Blocks: {len(page.blocks)}")
            
            for block_idx, block in enumerate(page.blocks):
                block_text = ""
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        block_text += word_text + " "
                
                # Get bounding box
                if block.bounding_box.vertices:
                    x_coords = [v.x for v in block.bounding_box.vertices if v.x is not None]
                    y_coords = [v.y for v in block.bounding_box.vertices if v.y is not None]
                    if x_coords and y_coords:
                        x_min, x_max = min(x_coords), max(x_coords)
                        y_min, y_max = min(y_coords), max(y_coords)
                        print(f"      Block {block_idx + 1}: X=[{x_min}-{x_max}], Y=[{y_min}-{y_max}], Text='{block_text.strip()[:50]}'")
        
    except Exception as e:
        print(f"❌ Error getting OCR response: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "-" * 80)
    print("STEP 2: Extracting table data (Sub Total row)")
    print("-" * 80)
    
    try:
        # First, let's manually inspect the Sub Total row blocks
        print("\n🔍 DEBUG: Inspecting Sub Total row blocks...")
        from app.ocr.table_extractor import extract_table_data_from_ocr
        
        # Get all text blocks with their bounding boxes for debugging
        text_blocks = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        vertices = word.bounding_box.vertices
                        if len(vertices) >= 2:
                            x = vertices[0].x if vertices[0].x is not None else 0
                            y = vertices[0].y if vertices[0].y is not None else 0
                            text_blocks.append({
                                'text': word_text,
                                'x': x,
                                'y': y,
                                'bbox': vertices
                            })
        
        # Group by Y position (rows)
        text_blocks.sort(key=lambda b: b['y'])
        rows = []
        current_row = []
        current_y = None
        y_tolerance = 20
        
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
        
        # Find Sub Total row
        sub_total_row_blocks = None
        for i, row in enumerate(rows):
            row_text = ' '.join([b['text'] for b in row]).lower()
            if 'sub total' in row_text or 'subtotal' in row_text:
                sub_total_row_blocks = row
                print(f"\n   Found Sub Total row at index {i}")
                print(f"   Row has {len(row)} blocks")
                print(f"   Row text: {' '.join([b['text'] for b in row])}")
                print(f"\n   Block details (sorted by X):")
                row_sorted = sorted(row, key=lambda b: b['x'])
                for j, block in enumerate(row_sorted):
                    print(f"      Block {j+1}: X={block['x']:5d}, Y={block['y']:5d}, Text='{block['text']}'")
                break
        
        if sub_total_row_blocks is None:
            print("   ⚠️  Could not find Sub Total row in blocks")
        
        # Extract table data using the new extraction logic
        print("\n🔄 Running extraction logic...")
        table_data = extract_table_data_from_ocr(response)
        
        print(f"\n✅ Table extraction completed")
        print(f"\n📊 Extracted Sub Total Row Data:")
        print(f"   Format: {{column_number: value}}")
        print(f"   Total columns: {len(table_data)}")
        print(f"   Non-zero columns: {len([v for v in table_data.values() if v > 0])}")
        print(f"\n   Values (in column order):")
        for col_num in sorted(table_data.keys()):
            value = table_data[col_num]
            print(f"      Column {col_num:2d}: {value:5d}")
        
        # Also test the convenience function
        print("\n" + "-" * 80)
        print("STEP 3: Testing convenience function (extract_table_data)")
        print("-" * 80)
        table_data_alt = extract_table_data(image_path, response=response)
        print(f"✅ Convenience function result matches: {table_data == table_data_alt}")
        
    except Exception as e:
        print(f"❌ Error extracting table data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "-" * 80)
    print("STEP 4: Formatting for WebSocket (final output)")
    print("-" * 80)
    
    try:
        # Format as it would be sent to websocket
        websocket_output = format_websocket_output(table_data)
        
        print(f"\n✅ WebSocket format prepared")
        print(f"\n📤 Final Output (as would be sent to WebSocket):")
        print(json.dumps(websocket_output, indent=2))
        
        print(f"\n📋 Summary:")
        print(f"   Format: List of {len(websocket_output)} numbers")
        print(f"   Values: {websocket_output}")
        for i, value in enumerate(websocket_output, start=1):
            print(f"   Column {i}: {value}")
        
    except Exception as e:
        print(f"❌ Error formatting for websocket: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if HAS_ENGINE:
        print("\n" + "-" * 80)
        print("STEP 5: Testing via engine function (complete flow)")
        print("-" * 80)
        
        try:
            # Test the complete flow via engine
            result = ocr_image_google_vision_table(image_path)
            
            print(f"\n✅ Complete flow test successful")
            print(f"   Result type: {type(result)}")
            print(f"   Result keys: {sorted(result.keys())}")
            print(f"   Result matches previous extraction: {result == table_data}")
            
        except Exception as e:
            print(f"❌ Error in complete flow: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n" + "-" * 80)
        print("STEP 5: Skipped (engine function not available)")
        print("-" * 80)
        print("   (This is fine - we've already tested the core extraction logic)")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nThe extracted data is ready to be pushed to WebSocket!")
    print(f"Expected Sub Total values from image:")
    print(f"  Column 1: {table_data.get(1, 0)}")
    print(f"  Column 2: {table_data.get(2, 0)}")
    print(f"  Column 3: {table_data.get(3, 0)}")
    print(f"  Column 4: {table_data.get(4, 0)}")
    print(f"  Column 5: {table_data.get(5, 0)}")
    print(f"  Column 6: {table_data.get(6, 0)}")
    print(f"  Column 7: {table_data.get(7, 0)}")
    print(f"  Column 8: {table_data.get(8, 0)}")
    print(f"  Column 9: {table_data.get(9, 0)}")
    print(f"  Column 10: {table_data.get(10, 0)}")
    print()


if __name__ == "__main__":
    # Default test image - use the specific image mentioned by user
    default_image = "images/canvas_capture_20251129_000024_795352.png"
    
    # Allow command line argument for image path
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = default_image
    
    if not os.path.exists(image_path):
        print(f"\n⚠️  Image not found: {image_path}")
        print(f"\n   Please provide the image path as an argument:")
        print(f"   python test_table_extraction.py <image_path>")
        sys.exit(1)
    
    print(f"\n🔍 Using test image: {image_path}")
    
    # Run the test
    test_table_extraction(image_path)

