# HTML Content Extraction

This module provides tools for extracting structured content from HTML files, specifically designed for the Metropole Ballard website.

## Overview

The extraction process:
1. Reads HTML files from the `data/html` directory
2. Extracts page titles, section headers (h1, h2, h3), and content (paragraphs, list items)
3. Groups content by section
4. Outputs structured Python objects with content, content_html, and section header

## Files

- `extract_content.py`: Core module for extracting structured content from HTML files
- `process_html_content.py`: Script to process all HTML files and output structured content

## Usage

To process all HTML files and generate structured content:

```bash
cd app/crawler
python process_html_content.py
```

This will:
1. Process all HTML files in the `data/html` directory
2. Save JSON output to `data/processed/extracted_content.json`
3. Save Python objects to `data/processed/content_objects.py`

## Output Format

The generated Python objects have the following structure:

```python
{
    'page_title': "Page title",
    'page_name': "Filename without extension",
    'section_header': "Section header (h1, h2, or h3)",
    'content': "Plain text content",
    'content_html': "HTML content"
}
```

## Example

```python
from data.processed.content_objects import content_objects

# Access the first content chunk
first_chunk = content_objects[0]
print(f"Page: {first_chunk['page_title']}")
print(f"Section: {first_chunk['section_header']}")
print(f"Content: {first_chunk['content'][:100]}...")

# Filter content by section
def get_content_by_section(section_header):
    return [chunk for chunk in content_objects if chunk['section_header'] == section_header]

# Get all content from a specific section
security_content = get_content_by_section("Security")
```

## Statistics

The extraction process results in:
- 11 processed HTML files
- 76 extracted sections
- 597 unique content chunks
