#!/usr/bin/env python3
"""Test runner for the Deanta Reference vs Commentary Parser"""

import json
import sys
import re
from lxml import etree
from app.main import classify_paragraph


# -------------------------
# Helpers
# -------------------------

def remove_wrappers(text: str) -> str:
    """Remove reference/commentary tags only"""
    return re.sub(r"</?(reference|commentary)>", "", text)


def is_valid_xml(text: str) -> tuple[bool, str]:
    """Validate XML by wrapping in a root element"""
    try:
        etree.fromstring(f"<root>{text}</root>")
        return True, ""
    except Exception as e:
        return False, str(e)


# -------------------------
# Test Cases
# -------------------------

TEST_CASES = [
    # --- Core rules ---
    {
        "id": 1,
        "name": "See Author → reference",
        "input": "See John Smith, 'Title' (2020) 10.",
        "expected": "<reference>See John Smith, 'Title' (2020) 10.</reference>",
    },
    {
        "id": 2,
        "name": "See also → commentary + reference",
        "input": "See also: J. C. Davis, 'The Pursuit of Knowledge' (2015) 25.",
        "expected": "<commentary>See also: </commentary><reference>J. C. Davis, 'The Pursuit of Knowledge' (2015) 25.</reference>",
    },
    {
        "id": 3,
        "name": "For X, see → full reference",
        "input": "For further analysis, see Peter Clark, 'The Dynamics of Change' (1998) 45.",
        "expected": "<reference>For further analysis, see Peter Clark, 'The Dynamics of Change' (1998) 45.</reference>",
    },

    # --- Mixed segmentation ---
    {
        "id": 4,
        "name": "Commentary → reference",
        "input": "This topic is debated, see John Brewer, 'The Sinews of Power' (2001) 12.",
        "expected": "<commentary>This topic is debated, </commentary><reference>see John Brewer, 'The Sinews of Power' (2001) 12.</reference>",
    },
    {
        "id": 5,
        "name": "Reference → commentary",
        "input": "John Smith, 'Analysis' (2010) 33, for further details.",
        "expected": "<reference>John Smith, 'Analysis' (2010) 33, </reference><commentary>for further details.</commentary>",
    },

    # --- Multiple references ---
    {
        "id": 6,
        "name": "Multiple references with semicolon",
        "input": "Peter Clark, 'The Dynamics' (1998) 45; Paul Slack, 'English Society' (2001) 78.",
        "expected": "<reference>Peter Clark, 'The Dynamics' (1998) 45;</reference> <reference>Paul Slack, 'English Society' (2001) 78.</reference>",
    },
    {
        "id": 7,
        "name": "See also with multiple references",
        "input": "See also: Peter Clark, 'The Dynamics of Change' (1998) 45; Paul Slack, 'English Society, 1580–1680' (2001) 78.",
        "expected": "<commentary>See also: </commentary><reference>Peter Clark, 'The Dynamics of Change' (1998) 45;</reference> <reference>Paul Slack, 'English Society, 1580–1680' (2001) 78.</reference>",
    },

    # --- XML + track changes ---
    {
        "id": 8,
        "name": "Plain reference",
        "input": "John Smith, 'The Rise of England' (2010) 45.",
        "expected": "<reference>John Smith, 'The Rise of England' (2010) 45.</reference>",
    },
    {
        "id": 9,
        "name": "Preserve XML tags",
        "input": "John Smith, <span class=\"emphasis\">noted author</span>, 'Title' (2010) 25.",
        "expected": "<reference>John Smith, <span class=\"emphasis\">noted author</span>, 'Title' (2010) 25.</reference>",
    },
    {
        "id": 10,
        "name": "Track changes (ins)",
        "input": "John Smith, <span class=\"ins\">author</span> 'Title' (2010) 25.",
        "expected": "<reference>John Smith, <span class=\"ins\">author</span> 'Title' (2010) 25.</reference>",
    },
    {
        "id": 11,
        "name": "Track changes (del preserved)",
        "input": "John Smith, <span class=\"del\">old</span> 'Title' (2010) 25.",
        "expected": "<reference>John Smith, <span class=\"del\">old</span> 'Title' (2010) 25.</reference>",
    },
    {
        "id": 12,
        "name": "Mixed ins/del",
        "input": "<span class=\"del\">Old</span><span class=\"ins\">New</span> Smith, 'Title' (2010) 25.",
        "expected": "<reference><span class=\"del\">Old</span><span class=\"ins\">New</span> Smith, 'Title' (2010) 25.</reference>",
    },

    # --- Structural guarantees ---
    {
        "id": 13,
        "name": "Whitespace preservation",
        "input": "<para>Text\n\t<i>italic</i></para>",
        "expected": "<para><commentary>Text\n\t<i>italic</i></commentary></para>",
    },
    {
        "id": 14,
        "name": "XML structure valid",
        "input": "<para>See John Smith, <i>Book</i> (2020).</para>",
        "expected": "<para><reference>See John Smith, <i>Book</i> (2020).</reference></para>",
    },

    # --- Edge cases ---
    {
        "id": 15,
        "name": "Implicit reference",
        "input": "Peter Clark, 'The Dynamics' (1998) 45; Paul Slack, 'English Society' (2001) 78.",
        "expected": "<reference>Peter Clark, 'The Dynamics' (1998) 45;</reference> <reference>Paul Slack, 'English Society' (2001) 78.</reference>",
    },
    {
        "id": 16,
        "name": "Mixed full flow",
        "input": "This is known. See John Smith, 'Book' (2020), for details.",
        "expected": "<commentary>This is known. </commentary><reference>See John Smith, 'Book' (2020), </reference><commentary>for details.</commentary>",
    },
    {
        "id": 17,
        "name": "Initials handling",
        "input": "See J. C. Davis, 'Title' (2010) 25.",
        "expected": "<reference>See J. C. Davis, 'Title' (2010) 25.</reference>",
    },
    {
        "id": 18,
        "name": "See inside XML tag",
        "input": "<i>See</i> John Smith, 'Title' (2020).",
        "expected": "<reference><i>See</i> John Smith, 'Title' (2020).</reference>",
    },
    {
        "id": 19,
        "name": "Trailing commentary",
        "input": "John Smith, 'Book' (2020), for more info.",
        "expected": "<reference>John Smith, 'Book' (2020), </reference><commentary>for more info.</commentary>",
    },
]


# -------------------------
# Test Runner
# -------------------------

def run_tests():
    """Run all tests with strict + structural validation"""
    passed = 0
    failed = 0
    results = []

    print("\n" + "=" * 80)
    print("DEANTA REFERENCE VS COMMENTARY PARSER - TEST SUITE")
    print("=" * 80 + "\n")

    for test in TEST_CASES:
        test_id = test["id"]
        name = test["name"]
        input_text = test["input"]
        expected = test["expected"]

        errors = []
        passed_test = True

        try:
            result, _ = classify_paragraph(input_text)

            # 1. Exact match
            if result != expected:
                passed_test = False
                errors.append("Output mismatch")

            # 2. XML validity
            valid_xml, xml_error = is_valid_xml(result)
            if not valid_xml:
                passed_test = False
                errors.append(f"Invalid XML: {xml_error}")

            # 3. Ensure no text mutation (only wrappers added)
            try:
                cleaned = remove_wrappers(result)
                if cleaned != input_text:
                    passed_test = False
                    errors.append("Text modified (whitespace/structure changed)")
            except Exception as e:
                passed_test = False
                errors.append(f"Wrapper removal failed: {e}")

            # Results
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{status} | Test {test_id}: {name}")

            if not passed_test:
                print(f"   Input:    {input_text}")
                print(f"   Expected: {expected}")
                print(f"   Got:      {result}")
                print("   Issues:")
                for err in errors:
                    print(f"     - {err}")

            results.append({
                "id": test_id,
                "name": name,
                "passed": passed_test,
                "errors": errors,
            })

            passed += int(passed_test)
            failed += int(not passed_test)

            print()

        except Exception as e:
            print(f"❌ ERROR | Test {test_id}: {name}")
            print(f"   Exception: {e}\n")

            failed += 1
            results.append({
                "id": test_id,
                "name": name,
                "passed": False,
                "error": str(e),
            })

    total = passed + failed
    pct = (passed / total * 100) if total else 0

    print("=" * 80)
    print(f"RESULTS: {passed}/{total} tests passed ({pct:.1f}%)")
    print("=" * 80 + "\n")

    return passed, failed, results


if __name__ == "__main__":
    p, f, results = run_tests()

    with open("test_results.json", "w") as f_out:
        json.dump({
            "summary": {
                "total": p + f,
                "passed": p,
                "failed": f,
                "percentage": (p / (p + f) * 100) if (p + f) else 0,
            },
            "results": results,
        }, f_out, indent=2)

    sys.exit(0 if f == 0 else 1)