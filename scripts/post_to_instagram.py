"""
Instagram API (Instagram Login方式) へキャロウセル/単体画像を投稿するスクリプト。

前提:
- 画像は queue/<post_id>/ に 01.png, 02.png ... の連番で置き、GitHubにpush済みであること
  (Instagram APIはローカルファイルを直接受け付けず、公開URLが必要なため raw.githubusercontent.com を利用する)
- caption.txt に投稿本文(ハッシュタグ含む)を書いておくこと

使い方:
  python scripts/post_to_instagram.py <post_id>

必須環境変数:
  IG_USER_ID       InstagramアカウントのユーザーID(Meta for Developersのトークン生成画面で確認したもの)
  IG_ACCESS_TOKEN  長期アクセストークン(Instagramテスター経由で生成したもの)
  GITHUB_REPOSITORY  例: owner/repo (GitHub Actions実行時は自動設定される)
  GITHUB_SHA         コミットSHA (GitHub Actions実行時は自動設定される)
"""
import os
import sys
import time
import requests

GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v26.0")
GRAPH_API_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 5
STATUS_POLL_INTERVAL_SECONDS = 3
STATUS_POLL_MAX_ATTEMPTS = 20


def call_graph_api(method, path, **kwargs):
    url = f"{GRAPH_API_BASE}/{path}"
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.request(method, url, timeout=30, **kwargs)
        if response.status_code < 500:
            break
        last_error = f"{response.status_code}: {response.text}"
        print(f"[WARN] サーバーエラー、リトライします ({attempt}/{MAX_RETRIES}): {last_error}")
        time.sleep(RETRY_WAIT_SECONDS)
    else:
        raise RuntimeError(f"Graph APIへのリクエストが{MAX_RETRIES}回失敗しました: {last_error}")

    if not response.ok:
        raise RuntimeError(f"Graph APIエラー ({response.status_code}): {response.text}")
    return response.json()


def build_public_image_url(post_id, filename):
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["GITHUB_SHA"]
    return f"https://raw.githubusercontent.com/{repo}/{sha}/queue/{post_id}/{filename}"


def wait_until_container_ready(creation_id, access_token):
    for _ in range(STATUS_POLL_MAX_ATTEMPTS):
        result = call_graph_api(
            "GET",
            creation_id,
            params={"fields": "status_code", "access_token": access_token},
        )
        status = result.get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"メディアコンテナの生成に失敗しました: {result}")
        time.sleep(STATUS_POLL_INTERVAL_SECONDS)
    raise RuntimeError(f"メディアコンテナの生成がタイムアウトしました: {creation_id}")


def create_single_image_container(ig_user_id, access_token, image_url, caption):
    result = call_graph_api(
        "POST",
        f"{ig_user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
    )
    return result["id"]


def create_carousel_item_container(ig_user_id, access_token, image_url):
    result = call_graph_api(
        "POST",
        f"{ig_user_id}/media",
        data={"image_url": image_url, "is_carousel_item": "true", "access_token": access_token},
    )
    return result["id"]


def create_carousel_container(ig_user_id, access_token, children_ids, caption):
    result = call_graph_api(
        "POST",
        f"{ig_user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": access_token,
        },
    )
    return result["id"]


def publish_container(ig_user_id, access_token, creation_id):
    result = call_graph_api(
        "POST",
        f"{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
    )
    return result["id"]


def publish_post(post_id):
    post_dir = os.path.join("queue", post_id)
    caption_path = os.path.join(post_dir, "caption.txt")

    if not os.path.isdir(post_dir):
        raise FileNotFoundError(f"投稿フォルダが見つかりません: {post_dir}")
    if not os.path.isfile(caption_path):
        raise FileNotFoundError(f"caption.txt が見つかりません: {caption_path}")

    with open(caption_path, encoding="utf-8") as f:
        caption = f.read().strip()

    image_files = sorted(
        f for f in os.listdir(post_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )
    if not image_files:
        raise FileNotFoundError(f"画像ファイルが見つかりません: {post_dir}")

    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    print(f"[INFO] 投稿ID: {post_id} / 画像枚数: {len(image_files)}")

    if len(image_files) == 1:
        image_url = build_public_image_url(post_id, image_files[0])
        creation_id = create_single_image_container(ig_user_id, access_token, image_url, caption)
    else:
        children_ids = []
        for filename in image_files[:10]:
            image_url = build_public_image_url(post_id, filename)
            child_id = create_carousel_item_container(ig_user_id, access_token, image_url)
            wait_until_container_ready(child_id, access_token)
            children_ids.append(child_id)
        creation_id = create_carousel_container(ig_user_id, access_token, children_ids, caption)

    wait_until_container_ready(creation_id, access_token)
    media_id = publish_container(ig_user_id, access_token, creation_id)
    print(f"[SUCCESS] 投稿完了。media_id={media_id}")
    return media_id


def main():
    if len(sys.argv) != 2:
        print("使い方: python scripts/post_to_instagram.py <post_id>")
        sys.exit(1)
    publish_post(sys.argv[1])


if __name__ == "__main__":
    main()
