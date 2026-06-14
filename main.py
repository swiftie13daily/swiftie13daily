"""Daily orchestrator. Run once per day (GitHub Actions cron calls this).

Flow:
  1. Pick today's quiz: first approved item in the queue, or generate live
     if MODE=autogen and the queue is empty.
  2. Render the branded quiz card PNG into output/posts/.
  3. Build the caption (includes YESTERDAY's answer reveal + fun fact).
  4. Publish via the Instagram API using the public raw-repo image URL.
  5. Move the item from queue -> history and save state.

The GitHub Action commits the new PNG *before* this script publishes
(see workflow: render step, commit step, publish step are split via flags).
"""
import argparse
import datetime
import json
import sys

import config
from render_card import render_card


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
    queue = _load(config.QUEUE_PATH, [])
    for item in queue:
        if item.get("approved") and not item.get("posted"):
            return item, queue
    if config.MODE == "autogen":
        from generate_content import generate_one
        item = generate_one()
        queue.append(item)
        return item, queue
    print("ERROR: no approved items left in the queue. "
          "Run `python generate_content.py 30`, review, and commit.")
    sys.exit(1)


def build_caption(item, history) -> str:
    letters = ["A", "B", "C", "D"]
    parts = [f"🔮 Today's quiz — {item.get('difficulty', 'medium').title()} level",
             "",
             item["question"]]
    for i, opt in enumerate(item["options"]):
        parts.append(f"{letters[i]}. {opt}")
    parts += ["", "Drop your answer in the comments 👇",
              "Answer revealed in tomorrow's post!"]

    parts += ["", "Unofficial fan page 💜", config.POST_HASHTAGS]
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render-only", action="store_true",
                    help="pick item + render PNG + save state, but don't publish")
    ap.add_argument("--publish-only", action="store_true",
                    help="publish the already-rendered card from today's state")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    state_path = "output/today.json"

    if not args.publish_only:
        item, queue = pick_item()
        history = _load(config.HISTORY_PATH, [])
        img_path = render_card(item, f"{config.OUTPUT_DIR}/{today}.png")
        caption = build_caption(item, history)

        item["posted"] = today
        history.append(item)
        queue = [q for q in queue if q is not item]
        _save(config.QUEUE_PATH, queue)
        _save(config.HISTORY_PATH, history)
        _save(state_path, {"date": today, "image": img_path, "caption": caption})
        print(f"Rendered {img_path}")

    if not args.render_only:
        from post_instagram import publish_image
        state = _load(state_path, None)
        if not state or state["date"] != today:
            print("ERROR: no rendered post for today. Run render step first.")
            sys.exit(1)
        publish_image(state["image"], state["caption"])


if __name__ == "__main__":
    main()
