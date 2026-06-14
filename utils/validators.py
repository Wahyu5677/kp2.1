from datetime import datetime


def require_text(value: str, field_label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_label} wajib diisi.")
    return text


def parse_int_non_negative(value: str, field_label: str) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{field_label} harus berupa angka bulat.")
    if parsed < 0:
        raise ValueError(f"{field_label} tidak boleh negatif.")
    return parsed


def parse_float_non_negative(value: str, field_label: str) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{field_label} harus berupa angka.")
    if parsed < 0:
        raise ValueError(f"{field_label} tidak boleh negatif.")
    return parsed


def validate_date_yyyy_mm_dd(value: str, field_label: str) -> str:
    text = require_text(value, field_label)
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_label} harus berformat YYYY-MM-DD.")
    return text


def parse_allowed_choice(value: str, field_label: str, allowed_values: set[str]) -> str:
    text = require_text(value, field_label)
    if text not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(f"{field_label} tidak valid. Pilihan: {allowed}.")
    return text
