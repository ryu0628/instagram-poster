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
- push後、GitHub Actionsの「Publish Instagram Post」をworkflow_dispatchで実行し、`post_id`(フォルダ名)を入力してください。
- 公開が成功すると、ワークフローが自動で `queue/<post_id>/` を `published/<post_id>/` に移動してコミットします。
