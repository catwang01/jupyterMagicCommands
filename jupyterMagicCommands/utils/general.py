def removeprefix (s: str, prefix: str) -> str:
    return s[len(prefix):] if s.startswith(prefix) else s
