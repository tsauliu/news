"""
AI agent to read merged per-sector MD files and generate higher-level summaries.

This refactor introduces multi-processing so that all sector summaries are
generated in parallel.
"""

from __future__ import annotations

import os
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple

from models import OneAPI_request
from parameters import friday_date, errorkeywords, sector_list
from utils import archive_existing_in_target


OUTPUT_DIR = "data/4_combined_mds"
SUMMARY_DIR = "data/5_summary_mds"
RAW_SUMMARY_ROOT = "data/3_article_summary"


def merge_md_files() -> List[str]:
    """Merge article-level markdown files into per-sector files.

    Returns a list of generated per-sector file paths.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Archive previous combined outputs except those for the current date
    archive_existing_in_target(OUTPUT_DIR, exclude_contains=[friday_date])

    raw_mds_dir = RAW_SUMMARY_ROOT

    # Aggregate content by sector
    sector_contents: Dict[str, List[Tuple[str | None, str]]] = {sector: [] for sector in sector_list}
    md_files = glob.glob(f"{raw_mds_dir}/{friday_date}/*.md", recursive=True)

    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as infile:
                content = infile.read()

            if any(keyword in content for keyword in errorkeywords):
                continue

            file_sector: str | None = None
            relevant_score: int = 0
            date: str | None = None

            for line in content.split("\n"):
                if line.startswith("sector:"):
                    file_sector = line.replace("sector:", "").strip()
                elif line.startswith("relevant:"):
                    try:
                        relevant_score = int(line.replace("relevant:", "").strip())
                    except ValueError:
                        relevant_score = 0
                elif line.startswith("date:"):
                    date = line.replace("date:", "").strip()

            if file_sector in sector_list and relevant_score >= 3:
                sector_contents[file_sector].append((date, content))
        except Exception as e:
            print(f"Error reading {md_file}: {e}")

    # Write each sector's content to a separate file, sorted by date descending
    output_files: List[str] = []
    for sector, content_list in sector_contents.items():
        if not content_list:
            continue

        sorted_content = sorted(content_list, key=lambda x: x[0] if x[0] else "", reverse=True)
        combined_content = "\n\n---\n\n".join([content for _, content in sorted_content])

        sector_file = f"{OUTPUT_DIR}/{friday_date}_{sector}_merged_news.md"
        with open(sector_file, "w", encoding="utf-8") as outfile:
            outfile.write(combined_content)
        output_files.append(sector_file)

    # Also create an all-in-one combined file in sector order
    combined_summary_file = f"{OUTPUT_DIR}/{friday_date}_combined_news.md"
    with open(combined_summary_file, "w", encoding="utf-8") as combined_file:
        for sector in sector_list:
            sector_file = next((f for f in output_files if f"_{sector}_merged_news.md" in f), None)
            if not sector_file:
                continue
            with open(sector_file, "r", encoding="utf-8") as sector_content:
                combined_file.write(sector_content.read())
            combined_file.write("\n\n---\n\n")

    print(f"Combined news file created at: {combined_summary_file}")
    return output_files


def _generate_sector_summary(output_file: str, prompt_text: str) -> Tuple[str, str]:
    """Worker: generate a summary for a single sector file.

    Returns a tuple of (sector_name, md_summary).
    """
    try:
        sector_name = os.path.basename(output_file).split("_")[1]
        with open(output_file, "r", encoding="utf-8") as f:
            combined_md = f.read()

        print(f"Generating summary for sector: {sector_name}")
        md_summary = OneAPI_request(prompt_text, combined_md)
        return sector_name, md_summary
    except Exception as e:
        print(f"Error in worker for {output_file}: {e}")
        # Return empty summary so caller can skip
        return os.path.basename(output_file).split("_")[1], ""


def summarize_sectors_parallel(output_files: List[str]) -> Dict[str, str]:
    """Run sector summarization in parallel using multiple processes."""
    os.makedirs(SUMMARY_DIR, exist_ok=True)
    archive_existing_in_target(SUMMARY_DIR, exclude_contains=[friday_date])

    prompt_text = open("./prompt/auto_md_to_summary.md", "r", encoding="utf-8").read()

    sector_summaries: Dict[str, str] = {sector: "" for sector in sector_list}

    # Use one process per sector so all run at once
    max_procs = max(1, len(output_files))
    with ProcessPoolExecutor(max_workers=max_procs) as executor:
        future_map = {executor.submit(_generate_sector_summary, of, prompt_text): of for of in output_files}
        for future in as_completed(future_map):
            sector_name, md_summary = future.result()
            if md_summary:
                # Save individual sector summary as-is (prompt enforces format)
                sector_summary_file = os.path.join(SUMMARY_DIR, f"{friday_date}_{sector_name}_summary.md")
                try:
                    with open(sector_summary_file, "w", encoding="utf-8") as f:
                        f.write(md_summary)
                    print(f"Summary saved to {sector_summary_file}")
                except Exception as e:
                    print(f"Error saving {sector_summary_file}: {e}")
                sector_summaries[sector_name] = md_summary
            else:
                print(f"No summary generated for sector: {sector_name}")

    return sector_summaries


def write_combined_summary(sector_summaries: Dict[str, str]) -> None:
    ordered_summaries = [sector_summaries[s] for s in sector_list if sector_summaries.get(s)]
    combined_summary = "\n\n".join(ordered_summaries)
    combined_summary_file = os.path.join(SUMMARY_DIR, f"{friday_date}_summary.md")
    try:
        with open(combined_summary_file, "w", encoding="utf-8") as f:
            f.write(combined_summary)
        print(f"Combined summary saved to {combined_summary_file}")
    except Exception as e:
        print(f"Error saving combined summary: {e}")


def main() -> None:
    output_files = merge_md_files()
    if not output_files:
        print("No sector files to summarize.")
        return

    sector_summaries = summarize_sectors_parallel(output_files)
    write_combined_summary(sector_summaries)


if __name__ == "__main__":
    main()
