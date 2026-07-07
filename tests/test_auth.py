import pytest
from auth import hash_password, verify_password


def test_hash_password_success():
    """
    Test successful password hashing and verification.
    """
    raw_password = "securepassword"
    hashed_password = hash_password(raw_password)

    # Verify correct password
    assert verify_password(hashed_password, raw_password), "Password verification failed"

    # Verify incorrect password
    assert not verify_password(hashed_password, "wrongpassword"), "Incorrect password should not verify"


def test_hash_password_empty_string():
    """
    Test password hashing and verification for an empty string.
    """
    raw_password = ""
    hashed_password = hash_password(raw_password)

    # Verify empty string
    assert verify_password(hashed_password, raw_password), "Empty password verification failed"
    assert not verify_password(hashed_password, "nonempty"), "Non-matching password should not verify"


def test_hash_password_special_characters():
    """
    Test password hashing and verification with special characters.
    """
    raw_password = "p@ssw0rd!#123"
    hashed_password = hash_password(raw_password)

    # Verify correct password
    assert verify_password(hashed_password, raw_password), "Password with special characters verification failed"

    # Verify incorrect password
    assert not verify_password(hashed_password,
                               "p@ssword!#123"), "Incorrect password with special characters should not verify"


def test_hash_password_unicode_characters():
    """
    Test password hashing and verification with Unicode characters.
    """
    raw_password = "pāsswørd😊"
    hashed_password = hash_password(raw_password)

    # Verify correct password
    assert verify_password(hashed_password, raw_password), "Password with Unicode characters verification failed"

    # Verify incorrect password
    assert not verify_password(hashed_password, "pāssword😞"), "Incorrect Unicode password should not verify"


def test_hash_password_consistency():
    """
    Test that hash_password generates different hashes for the same password.
    """
    raw_password = "securepassword"
    hash1 = hash_password(raw_password)
    hash2 = hash_password(raw_password)

    # Ensure that the hashes are not the same (salted hashing)
    assert hash1 != hash2, "Hashes should not match for the same password (salted hashing)"
