import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]
PACKAGE_DIR = REPOSITORY_ROOT / "repowhisper"

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
if str(PACKAGE_DIR) not in sys.path:
    sys.path.append(str(PACKAGE_DIR))
