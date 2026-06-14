"""Generate quiz items with the Claude API.

Two uses:
  1. Batch mode (recommended): `python generate_content.py 30` creates 30 new
     items appended to content/queue.json with approved=false. You review the
     JSON, flip approved to true (or delete bad ones), commit, and the daily
     workflow posts them one per day.
  2. Live mode: main.py calls generate_one() when MODE=autogen and the queue
     is empty.
"""
import json
import sys

import anthropic

import config

SYSTEM_PROMPT = """You write daily Instagram quiz questions for an unofficial
Taylor Swift fan page called Swiftie13Daily.

Hard rules:
- NEVER quote song lyrics. Refer to songs by title or paraphrase loosely.
- Facts only: albums, eras, release dates, track numbers, music-video details,
  awards, well-documented fan lore. No rumors, no speculation about her
  personal life, no recent news (your knowledge may be stale).
- Respectful tone. Nothing about relationships, body, or controversies.
- Output ONLY a JSON array, no prose, no markdown fences.

Each item:
{
  "question": "string, max 140 chars",
  "options": ["A", "B", "C", "D"],   // exactly 4, short
  "answer_index": 0,                  // 0-3
  "era": "debut|fearless|speak_now|red|1989|reputation|lover|folklore|evermore|midnights|ttpd",
  "difficulty": "easy|medium|hard",
  "fun_fact": "one-sentence fact revealed with the answer, max 160 chars"
}

Mix difficulties roughly 40% easy, 40% medium, 20% hard, and vary the eras."""


def _client() -> anthropic.Anthropic:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _load(path: str, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _past_questions() -> list[str]:
    history = _load(config.HISTORY_PATH, [])
    queue = _load(config.QUEUE_PATH, [])
    return [i["question"] for i in history + queue if "question" in i]


def _ask_claude(n: int) -> list[dict]:
    avoid = _past_questions()[-200:]
    user_msg = (
        f"Generate {n} new quiz items. Do NOT repeat or closely rephrase any "
        f"of these already-used questions:\n{json.dumps(avoid)}"
    )
    resp = _client().messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    text = text.replace("```json", "").replace("```", "").strip()
    items = json.loads(text)
    valid = []
    for it in items:
        if (
            isinstance(it.get("question"), str)
            and isinstance(it.get("options"), list)
            and len(it["options"]) == 4
            and it.get("answer_index") in (0, 1, 2, 3)
        ):
            it.setdefault("difficulty", "medium")
            it.setdefault("era", "1989")
            it.setdefault("fun_fact", "")
            it["approved"] = False
            valid.append(it)
    return valid


def generate_batch(n: int = 30) -> None:
    queue = _load(config.QUEUE_PATH, [])
    new_items = _ask_claude(n)
    queue.extend(new_items)
    with open(config.QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2)
    print(f"Added {len(new_items)} items to {config.QUEUE_PATH} "
          f"(approved=false — review them, set approved=true, commit).")


def generate_one() -> dict:
    items = _ask_claude(1)
    if not items:
        raise RuntimeError("Claude returned no valid quiz item")
    item = items[0]
    item["approved"] = True  # autogen mode skips review by design
    return item


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    generate_batch(count)
