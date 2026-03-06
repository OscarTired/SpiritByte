"""
SpiritByte - Password Generator
Cryptographically secure password generation using the secrets module.
"""
import secrets
import string

def generate_password(
    length: int = 16,
    uppercase: bool = True,
    lowercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """Generate a cryptographically secure random password.

    Args:
        length: Password length (minimum 4).
        uppercase: Include A-Z.
        lowercase: Include a-z.
        digits: Include 0-9.
        symbols: Include special characters.
        exclude_ambiguous: Remove visually similar chars (0O, 1lI).

    Returns:
        A random password string.
    """
    if length < 4:
        length = 4

    pool = ""
    required: list[str] = []

    upper_chars = string.ascii_uppercase
    lower_chars = string.ascii_lowercase
    digit_chars = string.digits
    symbol_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    if exclude_ambiguous:
        upper_chars = upper_chars.replace("O", "").replace("I", "")
        lower_chars = lower_chars.replace("l", "")
        digit_chars = digit_chars.replace("0", "").replace("1", "")

    if uppercase:
        pool += upper_chars
        required.append(secrets.choice(upper_chars))
    if lowercase:
        pool += lower_chars
        required.append(secrets.choice(lower_chars))
    if digits:
        pool += digit_chars
        required.append(secrets.choice(digit_chars))
    if symbols:
        pool += symbol_chars
        required.append(secrets.choice(symbol_chars))

    if not pool:
        pool = string.ascii_lowercase
        required.append(secrets.choice(pool))

    remaining = length - len(required)
    password_chars = required + [secrets.choice(pool) for _ in range(remaining)]

    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)
