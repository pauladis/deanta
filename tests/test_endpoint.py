"""Integration tests for the paragraph classification HTTP endpoint."""

import json
import pytest
import requests
from pathlib import Path


ENDPOINT_URL = "http://localhost:8000/parse-paragraph"
TEST_DATA_DIR = Path(__file__).parent.parent
TEST_FILE = TEST_DATA_DIR / "correct.json"


@pytest.fixture
def test_cases():
    """Load test cases from correct.json."""
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_endpoint_reachable():
    """Verify endpoint is reachable."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Endpoint {ENDPOINT_URL} is not running")


@pytest.mark.parametrize("test_id", range(1, 11))
def test_parse_paragraph(test_cases, test_id):
    """Test paragraph parsing against endpoint.
    
    Args:
        test_cases: Fixture providing test data
        test_id: Test case ID (1-10)
    """
    test_case = next((tc for tc in test_cases if tc["id"] == test_id), None)
    assert test_case is not None, f"Test case {test_id} not found"
    
    text = test_case["text"]
    expected_output = test_case["classified_paragraph"]
    
    response = requests.post(
        ENDPOINT_URL,
        json={"text": text},
        timeout=10
    )
    
    assert response.status_code == 200, f"Endpoint returned {response.status_code}"
    result = response.json()
    actual_output = result.get("classified_paragraph")
    
    assert actual_output == expected_output, \
        f"Test {test_id}: Output mismatch\nExpected length: {len(expected_output)}\nActual length: {len(actual_output)}"


def test_empty_paragraph():
    """Test that empty paragraph is rejected."""
    response = requests.post(
        ENDPOINT_URL,
        json={"text": ""},
        timeout=10
    )
    assert response.status_code == 400


def test_whitespace_paragraph():
    """Test that whitespace-only paragraph is rejected."""
    response = requests.post(
        ENDPOINT_URL,
        json={"text": "   \n  \t  "},
        timeout=10
    )
    assert response.status_code == 400
