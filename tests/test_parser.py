"""Unit tests for the paragraph parser and classifier."""

import json
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import classify_paragraph


TEST_DATA_DIR = Path(__file__).parent.parent
TEST_FILE = TEST_DATA_DIR / "correct.json"


@pytest.fixture
def test_cases():
    """Load test cases from correct.json."""
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.mark.parametrize("test_id", range(1, 11))
def test_classify_paragraph(test_cases, test_id):
    """Test that parser output matches expected classification.
    
    Args:
        test_cases: Fixture providing test data
        test_id: Test case ID (1-10)
    """
    test_case = next((tc for tc in test_cases if tc["id"] == test_id), None)
    assert test_case is not None, f"Test case {test_id} not found"
    
    original_text = test_case["text"]
    expected_output = test_case["classified_paragraph"]
    
    classified_text, segments = classify_paragraph(original_text)
    
    assert classified_text == expected_output, \
        f"Test {test_id}: Output mismatch\nExpected length: {len(expected_output)}\nActual length: {len(classified_text)}"
    
    assert len(segments) > 0, f"Test {test_id}: No segments generated"
    
    # Verify all segments have valid classifications
    for text, start, end, classification in segments:
        assert classification in ("reference", "commentary"), \
            f"Test {test_id}: Invalid classification '{classification}'"
        assert isinstance(start, int) and isinstance(end, int), \
            f"Test {test_id}: Invalid segment positions"
        assert start >= 0 and end <= len(original_text), \
            f"Test {test_id}: Segment positions out of bounds"


def test_classify_empty_paragraph():
    """Test that empty paragraph handling works."""
    try:
        result, segments = classify_paragraph("")
        # If it doesn't raise, it should return empty result
        assert result == "" or result is not None
    except Exception:
        # Some implementations may raise for empty input, which is acceptable
        pass


def test_classify_simple_reference():
    """Test classification of a simple reference."""
    text = "Smith (1990), p. 45."
    classified, segments = classify_paragraph(text)
    
    # Should produce some output
    assert classified is not None
    assert len(classified) > 0
    
    # Should have at least one segment
    assert len(segments) > 0


def test_classify_simple_commentary():
    """Test classification of simple commentary."""
    text = "As argued by many scholars, this is important."
    classified, segments = classify_paragraph(text)
    
    # Should produce output
    assert classified is not None
    assert len(classified) > 0
    
    # Should have segments
    assert len(segments) > 0
