import re
from wtforms.validators import ValidationError


def strong_password(form, field):
    password = field.data or ""

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit")

    if not re.search(r"[^\w\s]", password):
        raise ValidationError("Password must contain at least one special character")
