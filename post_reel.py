"""Publish a Reel via Instagram's official publishing API.

Three-step flow (Reels need processing time, unlike image posts):
  1. POST /{ig-user-id}/media            -> creates a REELS media container
  2. GET  /{container-id}?fields=status_code -> poll until FINISHED
  3. POST /{ig-user-id}/media_publish    -> publishes it
"""
import time

import requests

import config


def _base() -> str:
    return f"https://{config.GRAPH_HOST}/{config.GRAPH_VERSION}/{config.IG_USER_ID}"


def publish_reel(video_url: str, caption: str, max_wait_seconds: int = 600) -> str:
    if not (config.IG_USER_ID and config.IG_ACCESS_TOKEN):
        raise RuntimeError("IG_USER_ID / IG_ACCESS_TOKEN not set — see .env.example")

    print(f"Posting reel URL: {video_url}")
    r = requests.post(
        f"{_base()}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": config.IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    if not r.ok:
        print(f"Media container error {r.status_code}: {r.text}")
    r.raise_for_status()
    container_id = r.json()["id"]
    print(f"Container created: {container_id}")

    # Reels are transcoded server-side before they can be published — poll
    # until Instagram reports FINISHED (or bail out on ERROR/EXPIRED/timeout).
    waited = 0
    poll_interval = 10
    status = None
    while waited < max_wait_seconds:
        time.sleep(poll_interval)
        waited += poll_interval
        r_status = requests.get(
            f"https://{config.GRAPH_HOST}/{config.GRAPH_VERSION}/{container_id}",
            params={"fields": "status_code", "access_token": config.IG_ACCESS_TOKEN},
            timeout=30,
        )
        r_status.raise_for_status()
        status = r_status.json().get("status_code")
        print(f"Container status after {waited}s: {status}")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Reel processing failed: status_code={status}")
    else:
        raise RuntimeError("Timed out waiting for reel to finish processing")

    for attempt in range(5):
        r2 = requests.post(
            f"{_base()}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": config.IG_ACCESS_TOKEN,
            },
            timeout=60,
        )
        if r2.ok:
            media_id = r2.json()["id"]
            print(f"Published! media_id={media_id}")
            return media_id
        print(f"Publish attempt {attempt + 1} failed: {r2.text}")
        time.sleep(15)

    raise RuntimeError("Failed to publish after retries")
