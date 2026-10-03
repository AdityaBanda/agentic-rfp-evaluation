from datetime import date

from src.services.input_validation import validate_supplier_forms


def _valid_entry(name="Apex"):
    return {
        "supplier_name": name,
        "submission_date": date(2026, 1, 1),
        "experience_rating": 8,
        "file_bytes": b"%PDF-1.4 fake",
    }


def test_valid_entries_pass():
    assert validate_supplier_forms([_valid_entry("Apex"), _valid_entry("Nexa")]) == []


def test_duplicate_supplier_name_detected():
    errors = validate_supplier_forms([_valid_entry("Apex"), _valid_entry("apex")])
    assert any("Duplicate supplier name" in e for e in errors)


def test_no_entries_detected():
    errors = validate_supplier_forms([])
    assert errors


def test_invalid_pdf_bytes_detected():
    entry = _valid_entry()
    entry["file_bytes"] = b"not a pdf"
    errors = validate_supplier_forms([entry])
    assert any("does not look like a valid PDF" in e for e in errors)


def test_missing_name_detected():
    entry = _valid_entry()
    entry["supplier_name"] = ""
    errors = validate_supplier_forms([entry])
    assert any("name is required" in e for e in errors)


def test_experience_rating_out_of_range_detected():
    entry = _valid_entry()
    entry["experience_rating"] = 15
    errors = validate_supplier_forms([entry])
    assert any("between 0 and 10" in e for e in errors)
