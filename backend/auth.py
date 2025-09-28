# backend/auth.py

# mapping simple : token → user_id
TOKENS = {
    "token_user1": "user1",
    "token_user2": "user2",
    "devtoken123": "dev"
}

def valid_token(token: str) -> str | None:
    """Retourne user_id si token valide, sinon None"""
    return TOKENS.get(token)
