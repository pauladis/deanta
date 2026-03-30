#!/usr/bin/env python3
"""Test script to process sample paragraphs and generate output.json"""

import json
import traceback
from pathlib import Path

from main import classify_paragraph


INPUT_FILE = "paragraphs-samples.json"
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
    """Process all sample paragraphs"""

    samples = load_samples(INPUT_FILE)

    results = []
    success_count = 0

    for paragraph in samples.get("paragraphs", []):
        para_id = paragraph.get("id")
        original_text = paragraph.get("text")

        print(f"\nProcessing paragraph {para_id}...")

        try:
            classified_text, segment_classifications = classify_paragraph(original_text)

            result = {
                "id": para_id,
                "original_text": original_text,
                "classified_text": classified_text,
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
            success_count += 1

            print(f"✓ Success | segments: {len(segment_classifications)}")

        except Exception as e:
            print(f"✗ Error in paragraph {para_id}: {str(e)}")
            traceback.print_exc()

    output = {"paragraphs": results}
    save_results(OUTPUT_FILE, output)

    print("\n" + "=" * 60)
    print(f"Processed: {success_count}/{len(samples.get('paragraphs', []))}")
    print(f"Output written to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    test_samples()