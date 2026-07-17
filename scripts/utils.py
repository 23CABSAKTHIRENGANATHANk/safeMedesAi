import os
import logging
import hashlib
from urllib.parse import urlparse

log = logging.getLogger("cdsco.utils")

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    name = os.path.basename(parsed.path) or parsed.netloc
    # append short hash to avoid collisions
    h = hashlib.sha1(url.encode('utf-8')).hexdigest()[:8]
    return f"{h}_{name}"
