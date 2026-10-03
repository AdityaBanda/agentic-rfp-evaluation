from __future__ import annotations

from datetime import date


def validate_supplier_forms(entries: list[dict]) -> list[str]:
    """Pure, UI-independent validation of supplier input rows before evaluation.

    Each entry is a dict with keys: supplier_name, submission_date,
    experience_rating, file_bytes. Returns a list of human-readable error
    strings (empty list means everything is valid).
    """
    errors: list[str] = []

    if not entries:
        errors.append("At least one supplier PDF must be uploaded.")
        return errors

    seen_names: set[str] = set()
    for i, entry in enumerate(entries, start=1):
        name = (entry.get("supplier_name") or "").strip()
        submission_date = entry.get("submission_date")
        experience_rating = entry.get("experience_rating")
        file_bytes = entry.get("file_bytes")
        label = name or f"supplier #{i}"

        if not name:
            errors.append(f"Supplier #{i}: name is required.")
        elif name.lower() in seen_names:
            errors.append(f"Duplicate supplier name '{name}'.")
        else:
            seen_names.add(name.lower())

        if not submission_date:
            errors.append(f"{label}: submission date is required.")
        elif not isinstance(submission_date, date):
            errors.append(f"{label}: submission date is invalid.")

        if experience_rating is None:
            errors.append(f"{label}: historical experience rating is required.")
        else:
            try:
                rating = float(experience_rating)
                if not (0 <= rating <= 10):
                    errors.append(f"{label}: experience rating must be between 0 and 10.")
            except (TypeError, ValueError):
                errors.append(f"{label}: experience rating must be numeric.")

        if not file_bytes:
            errors.append(f"{label}: a PDF file is required.")
        elif not file_bytes.startswith(b"%PDF"):
            errors.append(f"{label}: uploaded file does not look like a valid PDF.")

    return errors
