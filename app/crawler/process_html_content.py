"""
Script to process HTML files and extract structured content.
"""

import os
import json
from extract_content import process_all_html_files


def main():
    """
    Process all HTML files in the data/html directory and output structured content.
    """
    # Directory containing HTML files
    # Use path relative to project root
    html_directory = "../../data/html"

    # Process all HTML files
    print(f"Processing HTML files in {html_directory}...")
    results = process_all_html_files(html_directory)

    # Create output directory if it doesn't exist
    output_directory = "../../data/processed"
    os.makedirs(output_directory, exist_ok=True)

    # Save results to JSON file for inspection
    json_output_path = os.path.join(output_directory, "extracted_content.json")
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved JSON output to {json_output_path}")

    # Create Python objects for each page
    all_chunks = []

    for file_path, content in results.items():
        page_title = content["title"]
        page_name = os.path.basename(file_path).replace(".html", "")

        # Process each section
        for section in content["sections"]:
            section_header = section["header"]

            # Process each chunk in the section
            for chunk in section["chunks"]:
                # Create a structured object for each chunk
                chunk_object = {
                    "page_title": page_title,
                    "page_name": page_name,
                    "section_header": section_header,
                    "content": chunk["content"],
                    "content_html": chunk["content_html"],
                }

                all_chunks.append(chunk_object)

    # Save all chunks to a Python file
    py_output_path = os.path.join(output_directory, "content_objects.py")
    with open(py_output_path, "w", encoding="utf-8") as f:
        f.write('"""Generated content objects from HTML files."""\n\n')
        f.write("# This file is auto-generated. Do not edit directly.\n\n")
        f.write("content_objects = [\n")

        # Remove duplicate chunks by tracking content we've seen
        seen_content = set()
        unique_chunks = []

        for chunk in all_chunks:
            # Create a key based on content to detect duplicates
            content_key = f"{chunk['page_name']}:{chunk['section_header']}:{chunk['content'][:100]}"

            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_chunks.append(chunk)

        # Write unique chunks to file
        for chunk in unique_chunks:
            f.write("    {\n")
            f.write(f"        'page_title': {json.dumps(chunk['page_title'])},\n")
            f.write(f"        'page_name': {json.dumps(chunk['page_name'])},\n")
            f.write(
                f"        'section_header': {json.dumps(chunk['section_header'])},\n"
            )
            f.write(f"        'content': {json.dumps(chunk['content'])},\n")
            f.write(f"        'content_html': {json.dumps(chunk['content_html'])}\n")
            f.write("    },\n")

        f.write("]\n")

        # Update the count for the summary
        all_chunks = unique_chunks

    print(f"Saved Python objects to {py_output_path}")
    print(f"Total chunks extracted: {len(all_chunks)}")

    # Print summary
    page_count = len(results)
    section_count = sum(len(content["sections"]) for content in results.values())

    print(f"\nSummary:")
    print(f"- Processed {page_count} HTML files")
    print(f"- Extracted {section_count} sections")
    print(f"- Created {len(all_chunks)} content chunks")


if __name__ == "__main__":
    main()
