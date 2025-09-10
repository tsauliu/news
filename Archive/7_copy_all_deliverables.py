#!/usr/bin/env python3
"""
Copy all deliverables to organized output directory structure

Copies finalized files to output/YY-MM-DD/CN and output/YY-MM-DD/ENG:
1. Email files (.mht)
2. News summary PDF files  
3. Podcast PDF files

Usage:
    python 7_copy_all_deliverables.py
    python 7_copy_all_deliverables.py --date 2025-09-05
    python 7_copy_all_deliverables.py --cn-only
    python 7_copy_all_deliverables.py --eng-only
"""

import os
import shutil
import argparse
from pathlib import Path
from parameters import friday_date

def copy_file_safe(src, dst, description=""):
    """Safely copy a file with error handling"""
    try:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ✓ {description}: {src.name}")
            return True
        else:
            print(f"  ⚠ {description}: Not found - {src}")
            return False
    except Exception as e:
        print(f"  ✗ {description}: Failed to copy - {e}")
        return False

def copy_deliverables(date_str, lang="both"):
    """Copy all deliverables for the specified date and language"""
    
    # Convert date format: 2025-09-05 -> 25-09-05
    date_parts = date_str.split('-')
    short_date = f"{date_parts[0][2:]}-{date_parts[1]}-{date_parts[2]}"
    
    # Convert date for PDF filename: 2025-09-05 -> "2025 09 05"
    pdf_date = date_str.replace('-', ' ')
    
    base_output = Path("output") / short_date
    
    success_count = {"CN": 0, "ENG": 0}
    total_count = {"CN": 0, "ENG": 0}
    
    # Process Chinese version
    if lang in ["both", "cn"]:
        print(f"\n📁 Processing Chinese deliverables...")
        cn_output = base_output / "CN"
        cn_output.mkdir(parents=True, exist_ok=True)
        
        # 1. Email file
        email_src = Path(f"data/7_emails/{date_str}_email.mht")
        email_dst = cn_output / f"{date_str}_email.mht"
        total_count["CN"] += 1
        if copy_file_safe(email_src, email_dst, "Email (CN)"):
            success_count["CN"] += 1
        
        # 2. PDF summary
        pdf_src = Path(f"data/7_pdfs/Autonomous Driving AI News Summary {pdf_date}.pdf")
        pdf_dst = cn_output / f"Autonomous Driving AI News Summary {pdf_date}.pdf"
        total_count["CN"] += 1
        if copy_file_safe(pdf_src, pdf_dst, "News Summary PDF (CN)"):
            success_count["CN"] += 1
        
        # 3. Podcast PDFs
        podcast_dir = Path(f"podcast/{date_str}")
        if podcast_dir.exists():
            podcast_pdfs = list(podcast_dir.glob("*.pdf"))
            print(f"  Found {len(podcast_pdfs)} Chinese podcast PDF(s)")
            for i, pdf_file in enumerate(podcast_pdfs, 1):
                # Use original filename but add podcast_ prefix
                dst_file = cn_output / f"podcast_{pdf_file.name}"
                total_count["CN"] += 1
                if copy_file_safe(pdf_file, dst_file, f"Podcast PDF #{i} (CN)"):
                    success_count["CN"] += 1
        else:
            print(f"  ⚠ Chinese podcast directory not found: {podcast_dir}")
    
    # Process English version
    if lang in ["both", "eng"]:
        print(f"\n📁 Processing English deliverables...")
        eng_output = base_output / "ENG"
        eng_output.mkdir(parents=True, exist_ok=True)
        
        # 1. Email file
        email_src = Path(f"data/7_emails/{date_str}_email_english.mht")
        email_dst = eng_output / f"{date_str}_email_english.mht"
        total_count["ENG"] += 1
        if copy_file_safe(email_src, email_dst, "Email (ENG)"):
            success_count["ENG"] += 1
        
        # 2. PDF summary
        pdf_src = Path(f"data/7_pdfs/Autonomous Driving AI News Summary {pdf_date}_ENG.pdf")
        pdf_dst = eng_output / f"Autonomous Driving AI News Summary {pdf_date}_ENG.pdf"
        total_count["ENG"] += 1
        if copy_file_safe(pdf_src, pdf_dst, "News Summary PDF (ENG)"):
            success_count["ENG"] += 1
        
        # 3. Podcast PDFs (English)
        podcast_dir = Path(f"podcast/{date_str}_ENG")
        if podcast_dir.exists():
            podcast_pdfs = list(podcast_dir.glob("*.pdf"))
            print(f"  Found {len(podcast_pdfs)} English podcast PDF(s)")
            for i, pdf_file in enumerate(podcast_pdfs, 1):
                # Use original filename but add podcast_ prefix
                dst_file = eng_output / f"podcast_{pdf_file.name}"
                total_count["ENG"] += 1
                if copy_file_safe(pdf_file, dst_file, f"Podcast PDF #{i} (ENG)"):
                    success_count["ENG"] += 1
        else:
            print(f"  ⚠ English podcast directory not found: {podcast_dir}")
    
    return success_count, total_count, short_date

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Copy all deliverables to organized output directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Structure:
  output/
    YY-MM-DD/
      CN/
        - {date}_email.mht
        - Autonomous Driving AI News Summary {date}.pdf
        - podcast_*.pdf (with original names)
      ENG/
        - {date}_email_english.mht
        - Autonomous Driving AI News Summary {date}_ENG.pdf
        - podcast_*.pdf (with original names)

Examples:
  python 7_copy_all_deliverables.py                    # Copy both CN and ENG
  python 7_copy_all_deliverables.py --date 2025-09-05  # Specify date
  python 7_copy_all_deliverables.py --cn-only          # Chinese only
  python 7_copy_all_deliverables.py --eng-only         # English only
        """
    )
    
    parser.add_argument('--date', type=str, default=friday_date,
                        help=f'Date for deliverables (default: {friday_date})')
    parser.add_argument('--cn-only', action='store_true',
                        help='Copy only Chinese deliverables')
    parser.add_argument('--eng-only', action='store_true',
                        help='Copy only English deliverables')
    
    args = parser.parse_args()
    
    # Determine language to process
    if args.cn_only:
        lang = "cn"
    elif args.eng_only:
        lang = "eng"
    else:
        lang = "both"
    
    print("\n" + "=" * 60)
    print("📦 Deliverables Copy Utility")
    print("=" * 60)
    print(f"📅 Date: {args.date}")
    print(f"🌐 Language: {lang.upper()}")
    
    # Copy deliverables
    success_count, total_count, short_date = copy_deliverables(args.date, lang)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Copy Summary:")
    if lang in ["both", "cn"]:
        print(f"  🇨🇳 Chinese: {success_count['CN']}/{total_count['CN']} files copied")
    if lang in ["both", "eng"]:
        print(f"  🇺🇸 English: {success_count['ENG']}/{total_count['ENG']} files copied")
    
    print(f"📁 Output directory: output/{short_date}/")
    
    total_success = success_count.get('CN', 0) + success_count.get('ENG', 0)
    total_files = total_count.get('CN', 0) + total_count.get('ENG', 0)
    
    if total_success == total_files and total_files > 0:
        print("✅ All deliverables copied successfully!")
    elif total_success > 0:
        print("⚠️  Some files copied, but some were missing or failed.")
    else:
        print("❌ No files were copied. Please check file paths and availability.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()