# queueフォルダの使い方

投稿したい内容を `queue/<post_id>/` フォルダに用意してから GitHub にpushしてください。

```
queue/
  2026-08-01_kampo-summer/
    caption.txt
    01.jpg
    02.jpg
    ...(最大10枚、カルーセルの並び順どおりに連番で命名)
```

- `caption.txt`: 投稿本文(ハッシュタグ含む)。1ファイル1テキスト。
- 画像は **JPEG形式(.jpg / .jpeg)** で用意してください。PNGは投稿時にAPIエラー(`Only photo or video can be accepted as media type`)になることが確認されています。スクリーンショット等PNGで作った画像は、pushする前にJPEGへ変換してください(Macなら `sips -s format jpeg 元ファイル.png --out 01.jpg`)。
- 画像が1枚なら通常投稿、2枚以上ならカルーセル投稿として扱われます。

## 公開方法(2通り)

### A. 手動ですぐ公開する
push後、GitHub Actionsの「Publish Instagram Post」をworkflow_dispatchで実行し、`post_id`(フォルダ名)を入力してください。

### B. 日時を指定して自動公開する(スケジュール投稿)
フォルダに `schedule.txt` を追加し、公開したい日時を1行だけ書いてください(タイムゾーン付きISO8601形式、必須)。

```
queue/2026-08-05_kampo-autumn/
  caption.txt
  01.jpg
  schedule.txt   ← 例: 2026-08-05T09:00:00+09:00
```

`schedule.txt` を置いてpushしておけば、「Publish Scheduled Instagram Posts」ワークフローが15分ごとに自動実行され、予定時刻を過ぎている投稿を自動で公開します。手動実行は不要です。
`schedule.txt` を置かないフォルダは自動公開の対象にならず、上記Aの手動実行でのみ公開されます。

#### 「1日1件・毎日20:00固定」でまとめて予約する場合

複数日分の投稿をまとめて用意したときは、以下のコマンドで公開したい順に `post_id` を並べて渡すと、翌日から1日ずつ・20:00 JST固定で自動的に `schedule.txt` を割り当てられる。

```bash
python scripts/schedule_next_slots.py post-id-1 post-id-2 post-id-3
```

開始日を指定したい場合は `--start-date 2026-08-10` のように渡す。

いずれの方法でも、公開が成功すると自動で `queue/<post_id>/` が `published/<post_id>/` に移動してコミットされます。
