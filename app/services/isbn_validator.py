import re

def clean_isbn(val: str) -> str:
    return re.sub(r"[^0-9X]", "", val.upper().strip())

def validate_isbn13(isbn_raw: str) -> bool:
    digits = re.sub(r"[^0-9]", "", isbn_raw.strip())
    if len(digits) != 13:
        return False
    if not (digits.startswith("978") or digits.startswith("979")):
        return False
    total = 0
    for i in range(12):
        weight = 1 if i % 2 == 0 else 3
        total += int(digits[i]) * weight
    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(digits[12])

def format_isbn13(isbn_raw: str) -> str:
    digits = re.sub(r"[^0-9]", "", isbn_raw.strip())
    if len(digits) == 13:
        return f"{digits[0:3]}-{digits[3]}-{digits[4:7]}-{digits[7:12]}-{digits[12]}"
    return isbn_raw.strip()
