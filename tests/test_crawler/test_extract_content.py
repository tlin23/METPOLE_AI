"""
Tests for the extract_content module.
"""

import os
import pytest
from bs4 import BeautifulSoup

from app.crawler.extract_content import (
    extract_structured_content,
    extract_page_title,
    extract_sections,
    find_main_content_area,
    should_skip_element,
    process_all_html_files,
)


@pytest.mark.unit
@pytest.mark.chunking
class TestExtractContentFunctions:
    """Test individual functions in the extract_content module."""

    def test_extract_page_title_from_meta(self):
        """Test extracting page title from meta tag."""
        soup = BeautifulSoup(
            """
        <html>
            <head>
                <meta property="og:title" content="Meta Title">
                <title>HTML Title</title>
            </head>
            <body>
                <h1>H1 Title</h1>
            </body>
        </html>
        """,
            "html.parser",
        )

        result = extract_page_title(soup)
        assert result == "Meta Title"

    def test_extract_page_title_from_title_tag(self):
        """Test extracting page title from title tag."""
        soup = BeautifulSoup(
            """
        <html>
            <head>
                <title>HTML Title</title>
            </head>
            <body>
                <h1>H1 Title</h1>
            </body>
        </html>
        """,
            "html.parser",
        )

        result = extract_page_title(soup)
        assert result == "HTML Title"

    def test_extract_page_title_from_h1(self):
        """Test extracting page title from h1 tag."""
        soup = BeautifulSoup(
            """
        <html>
            <head>
            </head>
            <body>
                <h1>H1 Title</h1>
            </body>
        </html>
        """,
            "html.parser",
        )

        result = extract_page_title(soup)
        assert result == "H1 Title"

    def test_find_main_content_area_with_role(self):
        """Test finding main content area with role attribute."""
        soup = BeautifulSoup(
            """
        <html>
            <body>
                <div role="main">Main content</div>
            </body>
        </html>
        """,
            "html.parser",
        )

        result = find_main_content_area(soup)
        assert result is not None
        assert result.get_text(strip=True) == "Main content"

    def test_find_main_content_area_with_main_tag(self):
        """Test finding main content area with main tag."""
        soup = BeautifulSoup(
            """
        <html>
            <body>
                <main>Main content</main>
            </body>
        </html>
        """,
            "html.parser",
        )

        result = find_main_content_area(soup)
        assert result is not None
        assert result.get_text(strip=True) == "Main content"

    def test_find_main_content_area_fallback(self):
        """Test finding main content area with fallback options."""
        soup = BeautifulSoup(
            """
        <html>
            <body>
                <article>Article content</article>
            </body>
        </html>
        """,
            "html.parser",
        )

        result = find_main_content_area(soup)
        assert result is not None
        assert result.get_text(strip=True) == "Article content"

    def test_should_skip_element_empty(self):
        """Test should_skip_element with empty element."""
        soup = BeautifulSoup("<p></p>", "html.parser")
        element = soup.p

        result = should_skip_element(element)
        assert result is True

    def test_should_skip_element_script(self):
        """Test should_skip_element with script element."""
        soup = BeautifulSoup("<script>var x = 5;</script>", "html.parser")
        element = soup.script

        result = should_skip_element(element)
        assert result is True

    def test_should_skip_element_navigation(self):
        """Test should_skip_element with navigation element."""
        soup = BeautifulSoup("<nav>Navigation</nav>", "html.parser")
        element = soup.nav

        result = should_skip_element(element)
        assert result is True

    def test_should_skip_element_content(self):
        """Test should_skip_element with content element."""
        soup = BeautifulSoup("<p>Valid content</p>", "html.parser")
        element = soup.p

        result = should_skip_element(element)
        assert result is False


@pytest.mark.integration
@pytest.mark.chunking
class TestExtractStructuredContent:
    """Test the extract_structured_content function."""

    def test_extract_structured_content(self, sample_html_file):
        """Test extracting structured content from an HTML file."""
        result = extract_structured_content(sample_html_file)

        # Check the structure of the result
        assert "title" in result
        assert "sections" in result

        # Check the title
        assert result["title"] == "Test Page Meta Title"

        # Check the sections
        sections = result["sections"]
        assert len(sections) >= 2  # Should have at least 2 sections

        # Check the first section
        first_section = sections[0]
        assert "header" in first_section
        assert "chunks" in first_section
        assert len(first_section["chunks"]) > 0

        # Check a chunk
        chunk = first_section["chunks"][0]
        assert "content" in chunk
        assert "content_html" in chunk
        assert "section_header" in chunk

    def test_extract_sections(self, sample_html):
        """Test extracting sections from HTML."""
        soup = BeautifulSoup(sample_html, "html.parser")
        result = extract_sections(soup)

        # Should have at least 2 sections
        assert len(result) >= 2

        # Check section headers
        headers = [section["header"] for section in result]
        assert "Section 1" in headers
        assert "Section 2" in headers

        # Check section content
        section1 = next(
            section for section in result if section["header"] == "Section 1"
        )
        assert len(section1["chunks"]) >= 2  # Should have at least 2 chunks

        # Check chunk content
        chunk_contents = [chunk["content"] for chunk in section1["chunks"]]
        assert "This is the first paragraph of section 1." in chunk_contents
        assert "This is the second paragraph of section 1." in chunk_contents


@pytest.mark.integration
@pytest.mark.chunking
class TestProcessAllHtmlFiles:
    """Test the process_all_html_files function."""

    def test_process_all_html_files(self, temp_dir, sample_html):
        """Test processing all HTML files in a directory."""
        # Create multiple HTML files
        for i in range(3):
            file_path = os.path.join(temp_dir, f"test_page_{i}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(sample_html)

        # Process the files
        result = process_all_html_files(temp_dir)

        # Should have 3 files
        assert len(result) == 3

        # Check the structure of each result
        for file_path, content in result.items():
            assert "title" in content
            assert "sections" in content
            assert len(content["sections"]) >= 2


@pytest.mark.unit
@pytest.mark.chunking
@pytest.mark.edge_case
class TestExtractContentEdgeCases:
    """Test edge cases for the extract_content module."""

    def test_extract_page_title_no_title(self):
        """Test extracting page title with no title elements."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        # Should default to "Untitled Page"
        result = extract_page_title(soup)
        assert "Untitled" in result

    def test_extract_sections_no_content(self):
        """Test extracting sections with no content."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        result = extract_sections(soup)
        assert len(result) == 0

    def test_extract_sections_no_headers(self):
        """Test extracting sections with no headers."""
        soup = BeautifulSoup(
            """
        <html>
            <body>
                <main>
                    <p>Paragraph 1</p>
                    <p>Paragraph 2</p>
                </main>
            </body>
        </html>
        """,
            "html.parser",
        )

        result = extract_sections(soup)

        # Should create a default "Introduction" section
        assert len(result) == 1
        assert result[0]["header"] == "Introduction"
        assert len(result[0]["chunks"]) == 2

    def test_find_main_content_area_none(self):
        """Test finding main content area when none exists."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        result = find_main_content_area(soup)
        assert result is None

    def test_process_all_html_files_empty_dir(self, temp_dir):
        """Test processing an empty directory."""
        result = process_all_html_files(temp_dir)
        assert len(result) == 0

    def test_process_all_html_files_non_html(self, temp_dir):
        """Test processing a directory with non-HTML files."""
        # Create a non-HTML file
        file_path = os.path.join(temp_dir, "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("This is not HTML")

        result = process_all_html_files(temp_dir)
        assert len(result) == 0


@pytest.mark.integration
@pytest.mark.chunking
@pytest.mark.edge_case
class TestExtractContentIntegrationEdgeCases:
    """Test edge cases for the extract_content integration."""

    def test_extract_structured_content_missing_tags(
        self, sample_html_file_with_missing_tags
    ):
        """Test extracting structured content from HTML with missing tags."""
        result = extract_structured_content(sample_html_file_with_missing_tags)

        # Should still have a title and sections
        assert "title" in result
        assert "sections" in result

        # Title should be derived from filename
        assert "Untitled" in result["title"] or result["title"].endswith(".html")

        # Should have at least one section (Introduction)
        assert len(result["sections"]) >= 1

        # Check the content
        first_section = result["sections"][0]
        assert len(first_section["chunks"]) > 0

    def test_extract_structured_content_empty_content(
        self, sample_html_file_with_empty_content
    ):
        """Test extracting structured content from HTML with empty content."""
        result = extract_structured_content(sample_html_file_with_empty_content)

        # Should have a title and sections
        assert "title" in result
        assert "sections" in result
        assert result["title"] == "Empty Page"

        # Should have at least one section
        assert len(result["sections"]) >= 1

        # The section might have no chunks or empty chunks
        first_section = result["sections"][0]
        if first_section["chunks"]:
            for chunk in first_section["chunks"]:
                assert "content" in chunk
                # Content might be empty
