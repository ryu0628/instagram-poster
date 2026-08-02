"""
queue/配下の投稿のうち、schedule.txt に指定された時刻を過ぎているものだけを自動公開するスクリプト。
schedule.txt が無いフォルダ(手動投稿用)はスキップする。

schedule.txt の中身の例(1行のみ、タイムゾーン付きISO8601):
  2026-08-05T09:00:00+09:00

公開に成功した投稿フォルダは published/<post_id>/ に移動する(git addでの記録は呼び出し元のワークフローで行う)。

必須環境変数:
  IG_USER_ID
  IG_ACCESS_TOKEN
  GITHUB_REPOSITORY
  GITHUB_SHA
"""
import os
import shutil
from datetime import datetime, timezone

from post_to_instagram import publish_post

QUEUE_DIR = "queue"
PUBLISHED_DIR = "published"
SCHEDULE_FILENAME = "schedule.txt"


def load_scheduled_at(post_dir):
    path = os.path.join(post_dir, SCHEDULE_FILENAME)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        value = f.read().strip()
    scheduled_at = datetime.fromisoformat(value)
    if scheduled_at.tzinfo is None:
        raise ValueError(f"{path} にタイムゾーンが指定されていません(例: +09:00): {value}")
    return scheduled_at


def main():
    if not os.path.isdir(QUEUE_DIR):
        print("[INFO] queueフォルダが存在しません。")
        return

    now = datetime.now(timezone.utc)
    published_post_ids = []

    for post_id in sorted(os.listdir(QUEUE_DIR)):
        post_dir = os.path.join(QUEUE_DIR, post_id)
        if not os.path.isdir(post_dir):
            continue

        try:
            scheduled_at = load_scheduled_at(post_dir)
        except ValueError as e:
            print(f"[WARN] {post_id}: {e}")
            continue

        if scheduled_at is None:
            continue  # 手動投稿用(スケジュール未指定)

        if scheduled_at > now:
            print(f"[SKIP] {post_id}: 予定時刻 {scheduled_at.isoformat()} はまだ先です。")
            continue

        print(f"[INFO] {post_id}: 予定時刻 {scheduled_at.isoformat()} を過ぎているため公開します。")
        try:
            media_id = publish_post(post_id)
        except Exception as e:
            print(f"[ERROR] {post_id}: 公開に失敗しました: {e}")
            continue

        print(f"[SUCCESS] {post_id}: media_id={media_id}")
        os.makedirs(PUBLISHED_DIR, exist_ok=True)
        shutil.move(post_dir, os.path.join(PUBLISHED_DIR, post_id))
        published_post_ids.append(post_id)

    if not published_post_ids:
        print("[INFO] 今回公開すべき予定投稿はありませんでした。")
    else:
        print(f"[SUCCESS] {len(published_post_ids)}件を公開しました: {', '.join(published_post_ids)}")


if __name__ == "__main__":
    main()
