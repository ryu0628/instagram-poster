"""
queue/配下にまとめて用意した投稿フォルダに対し、「1日1件・毎日20:00 JST」で
公開予定日時を連続して割り当て、各フォルダに schedule.txt を書き込むスクリプト。

使い方:
  python scripts/schedule_next_slots.py <post_id1> <post_id2> ... [--start-date YYYY-MM-DD]

--start-date を省略した場合、実行日の翌日(JST)から割り当てる。
既に schedule.txt があるフォルダは上書きする。
"""
import argparse
import os
from datetime import datetime, timedelta, timezone

QUEUE_DIR = "queue"
JST = timezone(timedelta(hours=9))
POST_TIME = "20:00:00"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("post_ids", nargs="+", help="queue/ 配下の投稿フォルダ名(複数可、公開したい順)")
    parser.add_argument("--start-date", help="YYYY-MM-DD (JST)。省略時は実行日の翌日から。")
    args = parser.parse_args()

    if args.start_date:
        current_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    else:
        current_date = (datetime.now(JST) + timedelta(days=1)).date()

    for post_id in args.post_ids:
        post_dir = os.path.join(QUEUE_DIR, post_id)
        if not os.path.isdir(post_dir):
            raise FileNotFoundError(f"投稿フォルダが見つかりません: {post_dir}")

        scheduled_at = f"{current_date.isoformat()}T{POST_TIME}+09:00"
        schedule_path = os.path.join(post_dir, "schedule.txt")
        with open(schedule_path, "w", encoding="utf-8") as f:
            f.write(scheduled_at + "\n")
        print(f"[INFO] {post_id}: {scheduled_at} を予約しました。")

        current_date += timedelta(days=1)


if __name__ == "__main__":
    main()
