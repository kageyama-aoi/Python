import os


def ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def write_text(path, text, encoding="utf-8"):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding=encoding) as f:
        f.write(text)


def write_bytes(path, data):
    ensure_dir(os.path.dirname(path))
    with open(path, "wb") as f:
        f.write(data)
