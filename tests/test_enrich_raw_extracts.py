import pytest
from src.enrich import (
    extract_abstract_from_raw_details,
    extract_bio_from_raw_details,
    enrich_raw_extracts,
    RawExtractEnrichmentStats,
)


class TestExtractAbstractFromRawDetails:
    def test_extract_abstract_with_colon_marker(self):
        html = """
        <div class="events-detail-main">
            <p>Some intro text</p>
            <p>Abstract: This is the abstract content that should be extracted.</p>
            <p>More content here</p>
        </div>
        """
        result = extract_abstract_from_raw_details(html)
        assert "This is the abstract content that should be extracted" in result

    def test_extract_abstract_with_header_marker(self):
        html = """
        <div class="events-detail-main">
            <h2>Abstract</h2>
            <p>This is the abstract content under a header.</p>
            <p>More abstract text here.</p>
            <h2>Bio</h2>
            <p>Bio content</p>
        </div>
        """
        result = extract_abstract_from_raw_details(html)
        assert "This is the abstract content under a header" in result
        assert "Bio content" not in result  # Should stop at next header

    def test_extract_abstract_no_marker(self):
        html = """
        <div class="events-detail-main">
            <p>Just some regular content without abstract markers.</p>
        </div>
        """
        result = extract_abstract_from_raw_details(html)
        assert result == ""

    def test_extract_abstract_empty_input(self):
        result = extract_abstract_from_raw_details("")
        assert result == ""

    def test_extract_abstract_whitespace_only(self):
        result = extract_abstract_from_raw_details("   \n\t   ")
        assert result == ""


class TestExtractBioFromRawDetails:
    def test_extract_bio_with_colon_marker(self):
        html = """
        <div class="events-detail-main">
            <p>Some intro text</p>
            <p>Bio: This is the bio content that should be extracted.</p>
            <p>More content here</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert "This is the bio content that should be extracted" in result

    def test_extract_bio_with_header_marker(self):
        html = """
        <div class="events-detail-main">
            <h2>Abstract</h2>
            <p>Abstract content</p>
            <h2>Bio</h2>
            <p>This is the bio content under a header.</p>
            <p>More bio text here.</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert "This is the bio content under a header" in result
        assert "Abstract content" not in result  # Should not include content before bio

    def test_extract_bio_no_marker(self):
        html = """
        <div class="events-detail-main">
            <p>Just some regular content without bio markers.</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert result == ""

    def test_extract_bio_empty_input(self):
        result = extract_bio_from_raw_details("")
        assert result == ""

    def test_extract_bio_whitespace_only(self):
        result = extract_bio_from_raw_details("   \n\t   ")
        assert result == ""

    def test_bio_with_html_tags_around_marker(self):
        html = """
        <div class="events-detail-main">
            <p>Some intro text</p>
            <p><b>Bio</b>: This is the bio content with HTML tags around the marker.</p>
            <p>More content here</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert "This is the bio content with HTML tags around the marker" in result
        assert "More content here" not in result


class TestEnrichRawExtracts:
    def test_enrich_raw_extracts_basic(self):
        events = [
            {
                "guid": "1",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <h2>Abstract</h2>
                    <p>This is the abstract content.</p>
                    <h2>Bio</h2>
                    <p>This is the bio content.</p>
                </div>
                """
            }
        ]

        stats = enrich_raw_extracts(events, enable=True, overwrite=False)

        assert stats.attempted == 1
        assert stats.updated_abstract == 1
        assert stats.updated_bio == 1
        assert stats.errors == 0
        assert "rawExtractAbstract" in events[0]
        assert "rawExtractBio" in events[0]
        assert "This is the abstract content" in events[0]["rawExtractAbstract"]
        assert "This is the bio content" in events[0]["rawExtractBio"]

    def test_enrich_raw_extracts_no_raw_details(self):
        events = [
            {"guid": "1"},  # No rawEventDetails
            {"guid": "2", "rawEventDetails": ""},  # Empty rawEventDetails
        ]

        stats = enrich_raw_extracts(events, enable=True, overwrite=False)

        assert stats.attempted == 0
        assert stats.skipped_missing_details == 2
        assert stats.updated_abstract == 0
        assert stats.updated_bio == 0

    def test_enrich_raw_extracts_no_overwrite(self):
        events = [
            {
                "guid": "1",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <h2>Abstract</h2>
                    <p>New abstract content.</p>
                    <h2>Bio</h2>
                    <p>New bio content.</p>
                </div>
                """,
                "rawExtractAbstract": "Existing abstract",
                "rawExtractBio": "Existing bio"
            }
        ]

        stats = enrich_raw_extracts(events, enable=True, overwrite=False)

        assert stats.attempted == 1
        assert stats.updated_abstract == 0  # Should not overwrite
        assert stats.updated_bio == 0  # Should not overwrite
        assert events[0]["rawExtractAbstract"] == "Existing abstract"
        assert events[0]["rawExtractBio"] == "Existing bio"

    def test_enrich_raw_extracts_with_overwrite(self):
        events = [
            {
                "guid": "1",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <h2>Abstract</h2>
                    <p>New abstract content.</p>
                    <h2>Bio</h2>
                    <p>New bio content.</p>
                </div>
                """,
                "rawExtractAbstract": "Existing abstract",
                "rawExtractBio": "Existing bio"
            }
        ]

        stats = enrich_raw_extracts(events, enable=True, overwrite=True)

        assert stats.attempted == 1
        assert stats.updated_abstract == 1  # Should overwrite
        assert stats.updated_bio == 1  # Should overwrite
        assert "New abstract content" in events[0]["rawExtractAbstract"]
        assert "New bio content" in events[0]["rawExtractBio"]

    def test_enrich_raw_extracts_partial_extraction(self):
        events = [
            {
                "guid": "1",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <h2>Abstract</h2>
                    <p>This abstract has content.</p>
                    <!-- No bio section -->
                </div>
                """
            }
        ]

        stats = enrich_raw_extracts(events, enable=True, overwrite=False)

        assert stats.attempted == 1
        assert stats.updated_abstract == 1
        assert stats.updated_bio == 0  # No bio found
        assert "rawExtractAbstract" in events[0]
        assert "rawExtractBio" not in events[0]

    def test_enrich_raw_extracts_disabled(self):
        events = [
            {
                "guid": "1",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <h2>Abstract</h2>
                    <p>Abstract content.</p>
                </div>
                """
            }
        ]

        stats = enrich_raw_extracts(events, enable=False, overwrite=False)

        assert stats.attempted == 0
        assert stats.updated_abstract == 0
        assert stats.updated_bio == 0
        assert "rawExtractAbstract" not in events[0]

    def test_enrich_raw_extracts_mixed_events(self):
        events = [
            {
                "guid": "1",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <h2>Abstract</h2>
                    <p>Abstract 1.</p>
                    <h2>Bio</h2>
                    <p>Bio 1.</p>
                </div>
                """
            },
            {
                "guid": "2",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <p>No headers here.</p>
                </div>
                """
            },
            {
                "guid": "3",
                "rawEventDetails": "",
            }
        ]

        stats = enrich_raw_extracts(events, enable=True, overwrite=False)

        assert stats.attempted == 2  # Events 1 and 2 have raw details
        assert stats.skipped_missing_details == 1  # Event 3
        assert stats.updated_abstract == 1  # Only event 1 has abstract
        assert stats.updated_bio == 1  # Only event 1 has bio

        # Check event 1
        assert "rawExtractAbstract" in events[0]
        assert "rawExtractBio" in events[0]

        # Check event 2 (no extraction)
        assert "rawExtractAbstract" not in events[1]
        assert "rawExtractBio" not in events[1]

        # Check event 3 (skipped)
        assert "rawExtractAbstract" not in events[2]
        assert "rawExtractBio" not in events[2]

    def test_enrich_raw_extracts_error_handling(self):
        events = [
            {
                "guid": "1",
                "rawEventDetails": """
                <div class="events-detail-main">
                    <h2>Abstract</h2>
                    <p>Valid abstract.</p>
                    <h2>Bio</h2>
                    <p>Valid bio.</p>
                </div>
                """
            }
        ]

        # Mock an error in extraction by passing malformed HTML that causes issues
        # For this test, we'll simulate by temporarily breaking the function
        original_extract_abstract = extract_abstract_from_raw_details

        def failing_extract_abstract(html):
            if "Valid abstract" in html:
                raise ValueError("Simulated extraction error")
            return original_extract_abstract(html)

        # Monkey patch for this test
        import src.enrich
        src.enrich.extract_abstract_from_raw_details = failing_extract_abstract

        try:
            stats = enrich_raw_extracts(events, enable=True, overwrite=False)

            assert stats.attempted == 1
            assert stats.errors == 1
            assert stats.updated_abstract == 0
            assert stats.updated_bio == 1  # Bio extraction should still work
        finally:
            # Restore original function
            src.enrich.extract_abstract_from_raw_details = original_extract_abstract


class TestExtractAbstractEdgeCases:
    def test_abstract_with_multiple_headers(self):
        html = """
        <div class="events-detail-main">
            <h1>Event Title</h1>
            <h2>Abstract</h2>
            <p>Abstract paragraph 1.</p>
            <p>Abstract paragraph 2.</p>
            <h2>Bio</h2>
            <p>Bio content.</p>
            <h2>Additional Info</h2>
            <p>More content.</p>
        </div>
        """
        result = extract_abstract_from_raw_details(html)
        assert "Abstract paragraph 1" in result
        assert "Abstract paragraph 2" in result
        assert "Bio content" not in result
        assert "More content" not in result

    def test_abstract_colon_in_middle_of_text(self):
        html = """
        <div class="events-detail-main">
            <p>This is some text: with a colon, but not the marker.</p>
            <p>Abstract: This is the actual abstract.</p>
        </div>
        """
        result = extract_abstract_from_raw_details(html)
        assert "This is the actual abstract" in result
        assert "with a colon, but not the marker" not in result

    def test_abstract_case_insensitive_header(self):
        html = """
        <div class="events-detail-main">
            <h3>ABSTRACT</h3>
            <p>Uppercase header abstract.</p>
        </div>
        """
        result = extract_abstract_from_raw_details(html)
        assert "Uppercase header abstract" in result

    def test_abstract_with_html_tags_around_marker(self):
        html = """
        <div class="events-detail-main">
            <p>Some intro text</p>
            <p><strong>Abstract</strong>: This is the abstract content with HTML tags around the marker.</p>
            <p>More content here</p>
        </div>
        """
        result = extract_abstract_from_raw_details(html)
        assert "This is the abstract content with HTML tags around the marker" in result
        assert "More content here" not in result


class TestExtractBioEdgeCases:
    def test_bio_with_multiple_headers(self):
        html = """
        <div class="events-detail-main">
            <h2>Abstract</h2>
            <p>Abstract content.</p>
            <h2>Bio</h2>
            <p>Bio paragraph 1.</p>
            <p>Bio paragraph 2.</p>
            <h2>Additional Info</h2>
            <p>More content.</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert "Bio paragraph 1" in result
        assert "Bio paragraph 2" in result
        assert "Abstract content" not in result
        assert "More content" not in result

    def test_bio_case_insensitive_header(self):
        html = """
        <div class="events-detail-main">
            <h3>BIO</h3>
            <p>Uppercase header bio.</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert "Uppercase header bio" in result

    def test_bio_colon_in_middle_of_text(self):
        html = """
        <div class="events-detail-main">
            <p>This is some text: with a colon, but not the marker.</p>
            <p>Bio: This is the actual bio.</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert "This is the actual bio" in result
        assert "with a colon, but not the marker" not in result

    def test_bio_with_html_tags_around_marker(self):
        html = """
        <div class="events-detail-main">
            <p>Some intro text</p>
            <p><b>Bio</b>: This is the bio content with HTML tags around the marker.</p>
            <p>More content here</p>
        </div>
        """
        result = extract_bio_from_raw_details(html)
        assert "This is the bio content with HTML tags around the marker" in result
        assert "More content here" not in result


class TestRaceConditionAndRobustness:
    """Tests for out-of-order operations and parsing robustness."""

    def test_extraction_order_independence(self):
        """Test that extraction works regardless of abstract/bio order."""
        # Bio before abstract
        html1 = """
        <div class="events-detail-main">
            <h2>Bio</h2>
            <p>Bio content first.</p>
            <h2>Abstract</h2>
            <p>Abstract content second.</p>
        </div>
        """

        # Abstract before bio
        html2 = """
        <div class="events-detail-main">
            <h2>Abstract</h2>
            <p>Abstract content first.</p>
            <h2>Bio</h2>
            <p>Bio content second.</p>
        </div>
        """

        result1_abstract = extract_abstract_from_raw_details(html1)
        result1_bio = extract_bio_from_raw_details(html1)
        result2_abstract = extract_abstract_from_raw_details(html2)
        result2_bio = extract_bio_from_raw_details(html2)

        assert "Abstract content second" in result1_abstract
        assert "Bio content first" in result1_bio
        assert "Abstract content first" in result2_abstract
        assert "Bio content second" in result2_bio

    def test_malformed_html_robustness(self):
        """Test extraction handles malformed HTML gracefully."""
        malformed_html = """
        <div class="events-detail-main">
            <h2>Abstract</h2>
            <p>Unclosed paragraph
            <h2>Bio</h2>
            <p>Bio content</p>
            <unclosed_tag>
        </div>
        """

        # Should not crash
        abstract_result = extract_abstract_from_raw_details(malformed_html)
        bio_result = extract_bio_from_raw_details(malformed_html)

        assert isinstance(abstract_result, str)
        assert isinstance(bio_result, str)

    def test_empty_and_whitespace_content(self):
        """Test handling of empty or whitespace-only content after markers."""
        html = """
        <div class="events-detail-main">
            <h2>Abstract</h2>
            <p></p>
            <p>   </p>
            <h2>Bio</h2>
            <p>Valid bio content</p>
        </div>
        """

        abstract_result = extract_abstract_from_raw_details(html)
        bio_result = extract_bio_from_raw_details(html)

        # Abstract should be empty due to whitespace-only content
        assert abstract_result.strip() == ""
        # Bio should have content
        assert "Valid bio content" in bio_result

    def test_nested_elements_and_complex_html(self):
        """Test extraction with nested elements and complex HTML structure."""
        html = """
        <div class="events-detail-main">
            <h2>Abstract</h2>
            <div class="content-wrapper">
                <p>Abstract paragraph with <strong>bold text</strong>.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
            </div>
            <h2>Bio</h2>
            <p>Bio content with <em>emphasis</em>.</p>
        </div>
        """

        abstract_result = extract_abstract_from_raw_details(html)
        bio_result = extract_bio_from_raw_details(html)

        assert "Abstract paragraph with" in abstract_result
        assert "bold text" in abstract_result
        assert "List item 1" in abstract_result
        assert "Bio content with" in bio_result
        assert "emphasis" in bio_result

    def test_multiple_marker_occurrences(self):
        """Test behavior when markers appear multiple times."""
        html = """
        <div class="events-detail-main">
            <h3>Abstract</h3>
            <p>First abstract mention.</p>
            <h3>Abstract</h3>
            <p>Second abstract mention - should be ignored.</p>
            <h3>Bio</h3>
            <p>First bio mention.</p>
            <h3>Bio</h3>
            <p>Second bio mention - should be ignored.</p>
        </div>
        """

        abstract_result = extract_abstract_from_raw_details(html)
        bio_result = extract_bio_from_raw_details(html)

        # Should extract from first occurrence only
        assert "First abstract mention" in abstract_result
        assert "Second abstract mention" not in abstract_result
        assert "First bio mention" in bio_result
        assert "Second bio mention" not in bio_result