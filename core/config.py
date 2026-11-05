import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_local_env():
    env_file = PROJECT_ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_local_env()
MAX_UPLOAD_MB = 50
QUANTUM_DEFAULT_ROWS = 100
QUANTUM_MAX_ROWS = 300
MAX_QUBITS = 8
DEFAULT_SEED = 0
DATA_DIR = Path(os.getenv("QMLFORGE_DATA_DIR", "data"))
