from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# 環境変数の読み込みと確認ログ
line_bot_api_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_secret = os.getenv("LINE_CHANNEL_SECRET")
print("LINE_CHANNEL_ACCESS_TOKEN:", line_bot_api_token)
print("LINE_CHANNEL_SECRET:", line_bot_secret)

# トークンが存在しない場合のエラー対策
if not line_bot_api_token or not line_bot_secret:
    raise EnvironmentError("環境変数 LINE_CHANNEL_ACCESS_TOKEN または LINE_CHANNEL_SECRET が見つかりません")

# LINE BOT設定
line_bot_api = LineBotApi(line_bot_api_token)
handler = WebhookHandler(line_bot_secret)

# Webhookエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    print("リクエストボディ:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("署名検証に失敗しました")
        abort(400)

    return 'OK'

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply = f"あなたは「{event.message.text}」と送りましたね！"
    print("送信メッセージ:", reply)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# アプリ起動（RailwayはPORT環境変数が自動で設定される）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

