"""
Comparison of infoboxes between data/infoboxes/ and data/infoboxes_old_data/

This script:
- Counts the number of data/infoboxes in each folder
- Extracts page titles ("--- Title ---" part)
- Compares titles to find similarities/differences
- Displays a detailed report
"""

import os
import re


def extract_page_title(infobox_file):
    """
    Extract page title from infobox file content.
    Format: --- Page Title ---
    """
    try:
        with open(infobox_file, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            match = re.match(r"^---\s+(.+?)\s+---$", first_line)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error reading {infobox_file}: {e}")
    return None


def get_infoboxes_from_directory(directory):
    """
    Fetches all infobox files from a directory.
    Returns a dictionary {filename: page_title}
    """
    infoboxes = {}

    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return infoboxes

    for filename in os.listdir(directory):
        if filename.startswith("infobox_") and filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            title = extract_page_title(filepath)
            if title:
                infoboxes[filename] = title

    return infoboxes


def compare_infoboxes():
    """
    Compare data/infoboxes between the two folders.
    """
    print("=" * 80)
    print("INFOBOX COMPARISON")
    print("=" * 80)

    current_dir = "data/infoboxes"
    old_dir = "data/infoboxes_old_data"

    current_infoboxes = get_infoboxes_from_directory(current_dir)
    old_infoboxes = get_infoboxes_from_directory(old_dir)

    print("\nSTATISTICS:")
    print(f"  - Current data/infoboxes ({current_dir}): {len(current_infoboxes)}")
    print(f"  - Old data/infoboxes ({old_dir}): {len(old_infoboxes)}")

    current_titles = set(current_infoboxes.values())
    old_titles = set(old_infoboxes.values())

    common_titles = current_titles & old_titles
    only_current = current_titles - old_titles
    only_old = old_titles - current_titles

    print("\nCOMPARISON:")
    print(f"  - Common titles: {len(common_titles)}")
    print(f"  - Only in {current_dir}: {len(only_current)}")
    print(f"  - Only in {old_dir}: {len(only_old)}")

    total = max(len(current_titles), len(old_titles))
    if total > 0:
        similarity = (len(common_titles) / total) * 100
        print(f"  - Similarity rate: {similarity:.1f}%")

    if only_current:
        print(f"\nNEW PAGES IN {current_dir.upper()} ({len(only_current)}):")
        for title in sorted(only_current)[:20]:
            print(f"  - {title}")
        if len(only_current) > 20:
            print(f"  ... and {len(only_current) - 20} others")

    if only_old:
        print(f"\nPAGES ONLY IN {old_dir.upper()} ({len(only_old)}):")
        for title in sorted(only_old)[:20]:
            print(f"  - {title}")
        if len(only_old) > 20:
            print(f"  ... and {len(only_old) - 20} others")

    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"  - Pages to fetch (not present): {len(only_current)}")
    print(f"  - Total coverage: {len(current_titles | old_titles)} pages")
    print("=" * 80 + "\n")

    report_file = "infobox_comparison_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("DETAILED COMPARISON REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"NEW PAGES ({len(only_current)}):\n")
        for title in sorted(only_current):
            f.write(f"  {title}\n")

        f.write(f"\n\nDELETED PAGES ({len(only_old)}):\n")
        for title in sorted(only_old):
            f.write(f"  {title}\n")

        f.write(f"\n\nCOMMON PAGES ({len(common_titles)}):\n")
        for title in sorted(common_titles):
            f.write(f"  {title}\n")

    print(f"OK. Detailed report saved: {report_file}\n")


if __name__ == "__main__":
    compare_infoboxes()


