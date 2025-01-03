import bcrypt


def hash_secret(secret: str) -> str:
    return bcrypt.hashpw(secret.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
