#!/usr/bin/env python3
"""Test script to process sample paragraphs and generate output.json"""

import json
import traceback
from pathlib import Path

from main import classify_paragraph


INPUT_FILE = "correct.json"
OUTPUT_FILE = "output.json"


def load_samples(path: str):
    if not Path(path).exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def test_samples():
    """Process all sample paragraphs from correct.json and compare with expected output"""

    test_cases = load_samples(INPUT_FILE)

    results = []
    success_count = 0
    failed_count = 0

    print(f"\nRunning {len(test_cases)} test cases from {INPUT_FILE}\n")
    print("=" * 60)

    for test_case in test_cases:
        para_id = test_case.get("id")
        original_text = test_case.get("text")
        expected_output = test_case.get("classified_paragraph")

        print(f"\nProcessing paragraph {para_id}...")

        try:
            classified_text, segment_classifications = classify_paragraph(original_text)

            # Check if output matches expected
            matches = classified_text == expected_output
            match_status = "✓ MATCHES" if matches else "✗ MISMATCH"

            result = {
                "id": para_id,
                "original_text": original_text,
                "classified_text": classified_text,
                "expected_output": expected_output,
                "matches": matches,
                "classifications": [
                    {
                        "text": text,
                        "start": start,
                        "end": end,
                        "type": classification,
                    }
                    for text, start, end, classification in segment_classifications
                ],
            }

            results.append(result)
            if matches:
                success_count += 1
            else:
                failed_count += 1

            print(f"✓ Success | segments: {len(segment_classifications)} | {match_status}")

        except Exception as e:
            print(f"✗ Error in paragraph {para_id}: {str(e)}")
            traceback.print_exc()
            failed_count += 1

    output = {"paragraphs": results}
    save_results(OUTPUT_FILE, output)

    print("\n" + "=" * 60)
    print(f"Results: {success_count} matched, {failed_count} mismatched out of {len(test_cases)}")
    print(f"Output written to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    test_samples()