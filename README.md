# K-Notify MVP

中央競馬の当日レースを安全側に絞り込み、買う価値が比較的ありそうな候補だけをDiscordへ通知する個人用MVPです。

## 方針

- 9:00 JSTに土日だけ実行します。
- 9:00時点では馬体重が未発表のことが多いため、馬体重なしでも止めません。
- 過去5走はMVPでは任意です。取得できない場合は中立評価にします。
- 通知はDiscord Webhookです。
- 通知処理は `title/body` 型の抽象インターフェースにしてあり、後でPushoverを追加できます。
- SQLiteはローカル保存です。
- 「推奨確率」ではなく「推奨信頼度」と表示します。

## 初回セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 動作確認

まずはサンプルデータでdry-runします。

```bash
python scripts/run_daily.py --sample --dry-run
```

実データ取得では `beautifulsoup4` が必要です。未インストールの場合は先に以下を実行してください。

```bash
pip install -r requirements.txt
```

SQLiteに保存されます。

```bash
ls db/knotify.sqlite3
```

## Discord通知

DiscordのWebhook URLを環境変数に入れて実行します。

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python scripts/test_notify.py
python scripts/run_daily.py --sample
```

Webhook URLが未設定の場合は自動でdry-run表示に切り替わります。

`Webhook URLが無効、削除済み、または権限不足です` と出た場合は、Discord側でWebhookを作り直し、URLをコピーし直してください。

## Pushover対応の予定

当面はDiscordで運用します。Pushoverへ切り替える場合は、`app/notifier/base.py` の `NotificationProvider` に合わせて `PushoverNotifier` を追加します。

通知本文はすでに以下の形に分かれています。

```python
send(title, body)
```

そのため、予想ロジックやJRA取得部分を変更せずに通知先だけ追加できます。

## 実データ取得について

JRA公式HTMLは変更される可能性が高いため、MVPでは以下の順で安全に進めます。

1. サンプルデータでスコアリングと通知を検証
2. live取得で当日の出馬表と単勝オッズを取得
3. 失敗時は「本日の予想をスキップ」と通知
4. parser変更時は保存済みHTMLを `--source-dir` で読み込み、再検証

保存済みHTMLを使う例:

```bash
python scripts/run_daily.py --source-dir ./samples/jra_html --dry-run
```

## GitHub Actions

`.github/workflows/daily.yml` は土日 9:07 JSTに実行します。

GitHub ActionsのscheduleはUTC指定です。`7 0 * * 6,0` は日本時間の土日9:07です。GitHub Actionsは毎時0分付近で遅延・取りこぼしが起きる場合があるため、9:00ちょうどではなく9:07にしています。

Discord通知する場合は、GitHub Secretsに `DISCORD_WEBHOOK_URL` を登録してください。
