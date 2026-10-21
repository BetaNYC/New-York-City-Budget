"""Per-year configuration (PLAN §7): config/schedule_c/fyNNNN.toml, read with stdlib tomllib."""
import hashlib
import os
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(ROOT, "config", "schedule_c")


def load(fy):
    path = os.path.join(CONFIG_DIR, f"fy{fy}.toml")
    with open(path, "rb") as f:
        raw = f.read()
    cfg = tomllib.loads(raw.decode("utf-8"))
    cfg["_path"] = os.path.relpath(path, ROOT)
    cfg["_sha256"] = hashlib.sha256(raw).hexdigest()
    cfg["_pdf_abs"] = os.path.join(ROOT, cfg["pdf"])
    return cfg


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()
