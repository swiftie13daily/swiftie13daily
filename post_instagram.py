"""Publish an image post via Instagram's official publishing API.

Two-step flow:
  1. Upload image to imgbb to get a public URL
  2. POST /{ig-user-id}/media          -> creates a media container
  3. POST /{ig-user-id}/media_publish  -> publishes it
"""
import base64
import time

import requests

import config


def _upload_to_imgbb(image_path: str) -> str:
    """Upload local image to imgbb, return public URL."""
    if not config.IMGBB_API_KEY:
        raise RuntimeError("IMGBB_API_KEY not set — see .env.example")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": config.IMGBB_API_KEY, "image": b64},
        timeout=60,
    )
    r.raise_for_status()
    url = r.json()["data"]["url"]
    print(f"Uploaded to imgbb: {url}")
    return url


def _base() -> str:
    return f"https://{config.GRAPH_HOST}/{config.GRAPH_VERSION}/{config.IG_USER_ID}"


def publish_image(image_path_or_url: str, caption: str) -> str:
    if not (config.IG_USER_ID and config.IG_ACCESS_TOKEN):
        raise RuntimeError("IG_USER_ID / IG_ACCESS_TOKEN not set — see .env.example")

    # If it's a local file path, resolve to a public URL
    if not image_path_or_url.startswith("http"):
        if config.REPO_RAW_BASE:
            # Use raw GitHub URL (workflow commits PNG before calling this)
            image_url = f"{config.REPO_RAW_BASE}/{image_path_or_url}"
        else:
            image_url = _upload_to_imgbb(image_path_or_url)
    else:
        image_url = image_path_or_url

    print(f"Posting image URL: {image_url}")
    r = requests.post(
        f"{_base()}/media",
        data={
            "image_url": image_url,
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

    time.sleep(8)

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
