import os
from pathlib import Path

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
