from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """
    Hashes a plain-text password.
    """
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """
    Verifies a plain-text password against a hashed password.
    """
    return check_password_hash(password_hash, password)

