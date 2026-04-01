#!/usr/bin/env python3
"""
Test runner using REAL XML cases

Focus:
- XML safety
- Structural integrity (no mutation)
- Semantic transformation presence
- Golden test validation (strict)
"""

import json
import sys
import re
from lxml import etree
from app.main import classify_paragraph


# -------------------------
# Load fixtures
# -------------------------

with open("fixture.json") as f:
    TEST_CASES = json.load(f)

with open("response-sample.json") as f:
    TRUTH_CASES = json.load(f)


# -------------------------
# Helpers
# -------------------------

def remove_wrappers(text: str) -> str:
    return re.sub(r"</?reference>|</?commentary>", "", text)


def is_valid_xml(text: str):
    try:
        etree.fromstring(f"<root>{text}</root>")
        return True, ""
    except Exception as e:
        return False, str(e)


# -------------------------
# Core Tests (Structural)
# -------------------------

def run_tests():
    passed = 0
    failed = 0
    results = []

    print("\n" + "=" * 80)
    print("STRUCTURAL TESTS (REAL DATA)")
    print("=" * 80 + "\n")

    for test in TEST_CASES:
        test_id = test["id"]
        input_text = test["text"]

        errors = []
        passed_test = True

        try:
            result, _ = classify_paragraph(input_text)

            # -------------------------
            # 1. XML VALIDATION
            # -------------------------
            valid_xml, xml_error = is_valid_xml(result)
            if not valid_xml:
                passed_test = False
                errors.append(f"Invalid XML: {xml_error}")

            # -------------------------
            # 2. STRUCTURE PRESERVATION
            # -------------------------
            cleaned = remove_wrappers(result)
            if cleaned != input_text:
                passed_test = False
                errors.append("Text modified (whitespace/structure changed)")

            # -------------------------
            # 3. TAG PRESENCE (must add something)
            # -------------------------
            if result.count("<reference>") + result.count("<commentary>") == 0:
                passed_test = False
                errors.append("No semantic tags added")

            # -------------------------
            # 4. NO-OP DETECTION
            # -------------------------
            if result == input_text:
                passed_test = False
                errors.append("Output identical to input")

            # -------------------------
            # 5. BALANCED TAGS
            # -------------------------
            if result.count("<reference>") != result.count("</reference>"):
                passed_test = False
                errors.append("Unbalanced <reference> tags")

            if result.count("<commentary>") != result.count("</commentary>"):
                passed_test = False
                errors.append("Unbalanced <commentary> tags")

            # -------------------------
            # RESULT
            # -------------------------
            status = "PASS" if passed_test else "FAIL"
            print(f"{status} | Test {test_id}")

            if not passed_test:
                print("   Input:")
                print(input_text)
                print("\n   Got:")
                print(result)
                print("\n   Issues:")
                for err in errors:
                    print(f"     - {err}")

            results.append({
                "id": test_id,
                "passed": passed_test,
                "errors": errors,
            })

            passed += int(passed_test)
            failed += int(not passed_test)

            print()

        except Exception as e:
            print(f"ERROR | Test {test_id}")
            print(f"   Exception: {e}\n")

            failed += 1
            results.append({
                "id": test_id,
                "passed": False,
                "error": str(e),
            })

    total = passed + failed
    pct = (passed / total * 100) if total else 0

    print("=" * 80)
    print(f"STRUCTURAL RESULTS: {passed}/{total} ({pct:.1f}%)")
    print("=" * 80 + "\n")

    return passed, failed, results



def run_truth_result_test():
    print("\n" + "=" * 80)
    print("Tests based on a previously validated result")
    print("=" * 80 + "\n")

    passed = 0
    failed = 0

    for i, test in enumerate(TRUTH_CASES, start=1):
        # JSON strings contain escaped XML, unescape them
        input_text = test["input_text"]
        expected = test["expected"]

        errors = []
        passed_test = True

        try:
            result, _ = classify_paragraph(input_text)

            # Structural check: same semantic tags in same order
            result_tags = re.findall(r'</?(?:reference|commentary)>', result)
            expected_tags = re.findall(r'</?(?:reference|commentary)>', expected)
            if result_tags != expected_tags:
                passed_test = False
                errors.append(f"Tag structure mismatch")
            
            # Check that input content is preserved (text without tags should be identical)
            result_text = remove_wrappers(result)
            expected_text = remove_wrappers(expected)
            if result_text != expected_text:
                passed_test = False
                errors.append("Content mismatch (text outside tags differs)")
            
            # Check that semantic tags are balanced
            if result.count("<reference>") != result.count("</reference>"):
                passed_test = False
                errors.append("Unbalanced <reference> tags")
            if result.count("<commentary>") != result.count("</commentary>"):
                passed_test = False
                errors.append("Unbalanced <commentary> tags")

            status = "PASS" if passed_test else "FAIL"
            print(f"{status} | Golden Test {i}")

            if not passed_test:
                print("   Input:")
                print(input_text)
                print("\n   Expected:")
                print(expected)
                print("\n   Got:")
                print(result)
                print("\n   Issues:")
                for err in errors:
                    print(f"     - {err}")

            passed += int(passed_test)
            failed += int(not passed_test)

            print()

        except Exception as e:
            print(f"ERROR | Golden Test {i}")
            print(f"   Exception: {e}\n")
            failed += 1

    total = passed + failed
    pct = (passed / total * 100) if total else 0

    print("=" * 80)
    print(f"GOLDEN RESULTS: {passed}/{total} ({pct:.1f}%)")
    print("=" * 80 + "\n")

    return passed, failed


# -------------------------
# Main
# -------------------------

if __name__ == "__main__":
    p, f, results = run_tests()
    gp, gf = run_truth_result_test()

    with open("test_results.json", "w") as f_out:
        json.dump({
            "summary": {
                "total": p + f + gp + gf,
                "passed": p + gp,
                "failed": f + gf,
                "percentage": ((p + gp) / (p + f + gp + gf) * 100) if (p + f + gp + gf) else 0,
            }
        }, f_out, indent=2)

    sys.exit(0 if f == 0 and gf == 0 else 1)