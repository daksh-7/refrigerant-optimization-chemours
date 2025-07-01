import sys
from pathlib import Path

# `import src` didn't work since the root directory was not on the Python path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR)) 