import re
from fastapi import HTTPException, status


def validate_password(password: str):

    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if len(password) > 64:
        errors.append("Password must not exceed 64 characters.")

    if " " in password:
        errors.append("Password must not contain spaces.")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number.")

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        errors.append("Password must contain at least one special character.")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors
        )

    return True