"""Central configuration. All secrets come from environment variables."""
import os

# Load .env file if present
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# --- Anthropic (content generation) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# --- Instagram ---
GRAPH_HOST = os.environ.get("GRAPH_HOST", "graph.instagram.com")
GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v23.0")
IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")

# --- Image hosting (imgbb) ---
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "")

# --- Legacy (not needed with imgbb approach) ---
REPO_RAW_BASE = os.environ.get("REPO_RAW_BASE", "")

# --- Behaviour ---
MODE = os.environ.get("MODE", "queue")
POST_HASHTAGS = os.environ.get(
    "POST_HASHTAGS",
    "#swiftie #swifties #taylorsversion #swiftietok #erastour #swiftiequiz",
)
PAGE_NAME = "Swiftie13Daily"

QUEUE_PATH = "content/queue.json"
HISTORY_PATH = "content/history.json"
THEMES_PATH = "content/themes.json"
OUTPUT_DIR = "output/posts"
