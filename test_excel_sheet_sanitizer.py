"""
Test script for Excel sheet name sanitization
"""
from src.outputs.excel_sheet_sanitizer import ExcelSheetSanitizer


def test_sanitizer():
    """Test the Excel sheet name sanitizer"""
    
    print("Testing Excel Sheet Name Sanitizer")
    print("=" * 60)
    
    test_cases = [
        # (input, expected_output)
        ("Accretion/Dilution", "Accretion-Dilution"),
        ("CapEx & Depreciation", "CapEx & Depreciation"),  # & is valid
        ("Test:Sheet", "Test-Sheet"),
        ("Test\\Sheet", "Test-Sheet"),
        ("Test?Sheet", "Test-Sheet"),
        ("Test*Sheet", "Test-Sheet"),
        ("Test[Sheet]", "Test-Sheet-"),
        ("Normal Sheet", "Normal Sheet"),
        ("Sheet with / and \\ and :", "Sheet with - and - and -"),
        ("A" * 40, "A" * 31),  # Test length truncation
        ("'Leading apostrophe", "Leading apostrophe"),
        ("Trailing apostrophe'", "Trailing apostrophe"),
    ]
    
    all_passed = True
    
    for original, expected in test_cases:
        sanitized = ExcelSheetSanitizer.sanitize(original)
        status = "✓" if sanitized == expected else "✗"
        
        if sanitized != expected:
            all_passed = False
            print(f"{status} FAILED:")
            print(f"  Input:    '{original}'")
            print(f"  Expected: '{expected}'")
            print(f"  Got:      '{sanitized}'")
        else:
            print(f"{status} '{original}' -> '{sanitized}'")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(test_sanitizer())
