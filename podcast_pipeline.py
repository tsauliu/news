#!/usr/bin/env python3
"""
Complete podcast pipeline: Translate Chinese podcasts to English and generate PDFs
This script combines section-based translation and PDF generation
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess

# Import friday_date from parameters
from parameters import friday_date

def run_translation():
    """Run the section-based translation script"""
    print("\n" + "="*60)
    print("📝 STEP 1: Translating Podcasts")
    print("="*60)
    
    result = subprocess.run(
        [sys.executable, 'section_translate_podcasts.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Translation completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print("❌ Translation failed")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return False

def run_pdf_generation():
    """Run the PDF generation script"""
    print("\n" + "="*60)
    print("📄 STEP 2: Generating PDFs")
    print("="*60)
    
    result = subprocess.run(
        [sys.executable, 'podcast_to_pdf.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ PDF generation completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print("❌ PDF generation failed")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return False

def main():
    """Main pipeline function"""
    
    print("🎙️ " + "="*58 + " 🎙️")
    print("   PODCAST PROCESSING PIPELINE")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Friday Date: {friday_date}")
    print("="*60)
    
    # Check if source directory exists
    podcast_dir = Path('podcast') / friday_date
    if not podcast_dir.exists():
        print(f"\n⚠️ Warning: Source directory not found: {podcast_dir}")
        print("No podcasts to process for this week.")
        return False
    
    # Check for markdown files
    md_files = list(podcast_dir.glob('*.md'))
    if not md_files:
        print(f"\n⚠️ Warning: No markdown files found in {podcast_dir}")
        return False
    
    print(f"\n📋 Found {len(md_files)} podcast files to process:")
    for md_file in md_files:
        print(f"  • {md_file.name}")
    
    # Run translation
    translation_success = run_translation()
    
    if not translation_success:
        print("\n⚠️ Translation failed. Skipping PDF generation.")
        return False
    
    # Run PDF generation
    pdf_success = run_pdf_generation()
    
    # Final summary
    print("\n" + "="*60)
    print("📊 PIPELINE SUMMARY")
    print("="*60)
    
    if translation_success and pdf_success:
        print("✅ All steps completed successfully!")
        
        # Show output directories
        eng_dir = Path('podcast') / f'{friday_date}_ENG'
        pdf_dir = Path('podcast') / f'{friday_date}_ENG_PDFs'
        
        if eng_dir.exists():
            eng_files = list(eng_dir.glob('*.md'))
            print(f"\n📁 English translations: {eng_dir}")
            print(f"   {len(eng_files)} files generated")
        
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob('*.pdf'))
            print(f"\n📁 PDF documents: {pdf_dir}")
            print(f"   {len(pdf_files)} PDFs generated")
            
            # Show file sizes
            total_size = 0
            for pdf in pdf_files:
                size_mb = pdf.stat().st_size / (1024 * 1024)
                total_size += size_mb
                print(f"   • {pdf.name}: {size_mb:.2f} MB")
            print(f"   Total size: {total_size:.2f} MB")
    else:
        print("❌ Pipeline encountered errors")
        if not translation_success:
            print("  • Translation failed")
        if not pdf_success:
            print("  • PDF generation failed")
    
    print("\n" + "="*60)
    return translation_success and pdf_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)