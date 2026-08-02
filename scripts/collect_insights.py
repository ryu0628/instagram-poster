"""
投稿済みメディアのインサイトを収集し、data/insights/insights.csv に追記するスクリプト。

収集する指標は Graph API が実際に返す値のみ(reach, saved, likes, comments, shares)。
「ホーム率」など発信元別の内訳はAPIから直接取得できないため含まない。
insta-analystはこのCSVを元に保存率・フォロー率等を計算すること。

必須環境変数:
  IG_USER_ID
  IG_ACCESS_TOKEN
"""
import csv
import os
from datetime import datetime, timezone

import requests

GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v26.0")
GRAPH_API_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"
MEDIA_FETCH_LIMIT = int(os.environ.get("MEDIA_FETCH_LIMIT", "25"))
INSIGHT_METRICS = os.environ.get("INSIGHT_METRICS", "reach,saved,likes,comments,shares")
OUTPUT_CSV = os.path.join("data", "insights", "insights.csv")
CSV_FIELDS = [
    "collected_at",
    "media_id",
    "timestamp",
    "permalink",
    "caption_snippet",
    "reach",
    "saved",
    "likes",
    "comments",
    "shares",
    "followers_count_snapshot",
]


def call_graph_api(path, params):
    url = f"{GRAPH_API_BASE}/{path}"
    response = requests.get(url, params=params, timeout=30)
    if not response.ok:
        raise RuntimeError(f"Graph APIエラー ({response.status_code}): {response.text}")
    return response.json()


def get_followers_count(ig_user_id, access_token):
    result = call_graph_api(ig_user_id, {"fields": "followers_count", "access_token": access_token})
    return result.get("followers_count")


def get_recent_media(ig_user_id, access_token):
    result = call_graph_api(
        f"{ig_user_id}/media",
        {
            "fields": "id,caption,timestamp,permalink,media_type",
            "limit": MEDIA_FETCH_LIMIT,
            "access_token": access_token,
        },
    )
    return result.get("data", [])


def get_media_insights(media_id, access_token):
    result = call_graph_api(
        f"{media_id}/insights",
        {"metric": INSIGHT_METRICS, "access_token": access_token},
    )
    values = {}
    for entry in result.get("data", []):
        metric_values = entry.get("values", [])
        values[entry["name"]] = metric_values[0]["value"] if metric_values else None
    return values


def load_already_collected_media_ids():
    if not os.path.isfile(OUTPUT_CSV):
        return set()
    with open(OUTPUT_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {row["media_id"] for row in reader}


def append_rows(rows):
    file_exists = os.path.isfile(OUTPUT_CSV)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main():
    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    followers_count = get_followers_count(ig_user_id, access_token)
    media_list = get_recent_media(ig_user_id, access_token)
    already_collected = load_already_collected_media_ids()

    collected_at = datetime.now(timezone.utc).isoformat()
    new_rows = []
    for media in media_list:
        if media["id"] in already_collected:
            continue
        try:
            insights = get_media_insights(media["id"], access_token)
        except RuntimeError as e:
            print(f"[WARN] インサイト取得に失敗しました media_id={media['id']}: {e}")
            continue

        caption = (media.get("caption") or "").replace("\n", " ")
        new_rows.append(
            {
                "collected_at": collected_at,
                "media_id": media["id"],
                "timestamp": media.get("timestamp"),
                "permalink": media.get("permalink"),
                "caption_snippet": caption[:50],
                "reach": insights.get("reach"),
                "saved": insights.get("saved"),
                "likes": insights.get("likes"),
                "comments": insights.get("comments"),
                "shares": insights.get("shares"),
                "followers_count_snapshot": followers_count,
            }
        )

    if not new_rows:
        print("[INFO] 新規に収集すべきメディアはありませんでした。")
        return

    append_rows(new_rows)
    print(f"[SUCCESS] {len(new_rows)}件のインサイトを {OUTPUT_CSV} に追記しました。")


if __name__ == "__main__":
    main()
