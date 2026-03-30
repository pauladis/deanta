#!/usr/bin/env python3
"""
Test script for validating paragraph classification endpoint.
Reads texts from correct.json, sends them to localhost:8000/parse-paragraph,
and compares results with expected classified_paragraph.
"""

import json
import requests
import sys
from pathlib import Path


def load_test_cases(json_file):
    """Load test cases from JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_endpoint(endpoint_url="http://localhost:8000/parse-paragraph"):
    """Test the endpoint with all cases from correct.json."""
    test_file = Path(__file__).parent / "correct.json"
    
    try:
        test_cases = load_test_cases(test_file)
    except FileNotFoundError:
        print(f"Error: {test_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    passed = 0
    failed = 0
    failures = []
    
    print(f"\nRunning {len(test_cases)} test cases against {endpoint_url}\n")
    print("=" * 80)
    
    for test_case in test_cases:
        test_id = test_case["id"]
        text = test_case["text"]
        expected_output = test_case["classified_paragraph"]
        
        try:
            # Send request to endpoint
            response = requests.post(
                endpoint_url,
                json={"text": text},
                timeout=10
            )
            
            if response.status_code != 200:
                failed += 1
                failures.append({
                    "id": test_id,
                    "reason": f"HTTP {response.status_code}: {response.text}"
                })
                print(f"Test {test_id}: FAILED (HTTP {response.status_code})")
                continue
            
            result = response.json()
            actual_output = result.get("classified_paragraph")
            
            # Compare results
            if actual_output == expected_output:
                passed += 1
                print(f"Test {test_id}: PASSED ✓")
            else:
                failed += 1
                failures.append({
                    "id": test_id,
                    "reason": "Output mismatch",
                    "expected_length": len(expected_output),
                    "actual_length": len(actual_output) if actual_output else 0
                })
                print(f"Test {test_id}: FAILED (output mismatch)")
                
        except requests.exceptions.ConnectionError:
            failed += 1
            failures.append({
                "id": test_id,
                "reason": f"Connection error - cannot reach {endpoint_url}"
            })
            print(f"Test {test_id}: FAILED (connection error)")
        except requests.exceptions.Timeout:
            failed += 1
            failures.append({
                "id": test_id,
                "reason": "Request timeout"
            })
            print(f"Test {test_id}: FAILED (timeout)")
        except Exception as e:
            failed += 1
            failures.append({
                "id": test_id,
                "reason": str(e)
            })
            print(f"Test {test_id}: FAILED ({str(e)})")
    
    # Print summary
    print("=" * 80)
    print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    if failures:
        print("\nFailed Tests:")
        for failure in failures:
            print(f"  - Test {failure['id']}: {failure['reason']}")
    
    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(test_endpoint())
