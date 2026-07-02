"""Daily reel orchestrator - separate track from the quiz-card pipeline in
main.py (different queue, no render step, videos are already pre-made).

Flow:
  1. Pick the next un-posted reel from content/reel_queue.json (first entry
     without a "posted" date).
  2. Build its public video URL from config.REPO_RAW_BASE + reel/<file>
     (same raw-GitHub trick main.py uses for images - repo must stay public).
  3. Publish it to Instagram as a Reel via post_reel.publish_reel().
  4. Move the item to content/reel_history.json and save state.

Run manually to check what would post next: python main_reel.py --dry-run
"""
import argparse
import datetime
import json
import sys
import urllib.parse

import config
from post_reel import publish_reel

REEL_QUEUE_PATH = "content/reel_queue.json"
REEL_HISTORY_PATH = "content/reel_history.json"
REEL_DIR = "reel"


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def pick_item():
    queue = _load(REEL_QUEUE_PATH, [])
    for item in queue:
        if not item.get("posted"):
            return item, queue
    print("ERROR: no un-posted reels left in content/reel_queue.json. "
          "Add more entries (and video files in reel/) to keep the schedule going.")
    sys.exit(1)


def already_posted_today(today: str) -> bool:
    history = _load(REEL_HISTORY_PATH, [])
    return any(h.get("posted") == today for h in history)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                     help="print what would be posted, but don't call Instagram "
                          "or touch queue/history files")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()

    # One reel per day, no matter how many times this workflow gets
    # triggered today (e.g. a manual test run earlier, then the 8pm cron).
    if already_posted_today(today):
        print(f"A reel was already posted today ({today}) - skipping.")
        return

    item, queue = pick_item()

    if args.dry_run:
        print(f"Would post: {item['file']} (day={item['day']})")
        print(f"Caption:\n{item['caption']}")
        return

    if not config.REPO_RAW_BASE:
        print("ERROR: REPO_RAW_BASE not set - needed to build a public video URL.")
        sys.exit(1)

    encoded_name = urllib.parse.quote(item["file"])
    video_url = f"{config.REPO_RAW_BASE}/{REEL_DIR}/{encoded_name}"

    publish_reel(video_url, item["caption"])

    history = _load(REEL_HISTORY_PATH, [])
    item["posted"] = today
    history.append(item)
    queue = [q for q in queue if q is not item]
    _save(REEL_QUEUE_PATH, queue)
    _save(REEL_HISTORY_PATH, history)
    print(f"Posted reel: {item['file']}")


if __name__ == "__main__":
    main()
