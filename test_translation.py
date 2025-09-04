#!/usr/bin/env python3
"""
Test the improved translation on a single file
"""

import os
import sys
from pathlib import Path

# Import the improved translation functions
from section_translate_podcasts import translate_podcast_by_sections

def test_single_file():
    """Test translation on a single podcast file"""
    
    # Test with the file that had issues
    input_file = Path('podcast/2025-08-29/V81.谁说不敢聊华为？余承东、鸿蒙智行一次聊透！.md')
    output_file = Path('podcast/2025-08-29_ENG_TEST/V81.谁说不敢聊华为？余承东、鸿蒙智行一次聊透！.md')
    
    if not input_file.exists():
        print(f"Input file not found: {input_file}")
        return False
    
    print(f"Testing translation improvement...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print("-" * 50)
    
    try:
        success = translate_podcast_by_sections(input_file, output_file)
        if success:
            print(f"\n✓ Test translation completed successfully!")
            print(f"Check output file: {output_file}")
        else:
            print(f"\n✗ Test translation failed")
        return success
    except Exception as e:
        print(f"\n✗ Test translation crashed: {e}")
        return False

if __name__ == '__main__':
    test_single_file()