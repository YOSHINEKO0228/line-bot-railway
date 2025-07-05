from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
import os
import threading

# Railway以外の環境では .env を読み込む
if not os.getenv("RAILWAY_ENVIRONMENT"):
    from dotenv import load_dotenv
    load_dotenv()

app = Flask(__name__)

# 環境変数の取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")  # 任意

# OpenAIクライアント初期化
client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID if OPENAI_ORG_ID else None
)

# LINE BOT 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ChatGPTによる返信処理
def reply_with_chatgpt(event):
    user_text = event.message.text
    prompt = f"冷蔵庫の中にある材料で作れるレシピを教えてください。材料: {user_text}。レシピは簡潔に説明してください。"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        reply_text = response.choices[0].message.content.strip()
        print("✅ OpenAI応答:", reply_text)
    except Exception as e:
        print("❌ OpenAIエラー:", repr(e))
        reply_text = "申し訳ありません、レシピの取得に失敗しました。"

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print("❌ LINE返信エラー:", repr(e))

# LINE Webhookエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# LINEのメッセージイベント受信処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    thread = threading.Thread(target=reply_with_chatgpt, args=(event,))
    thread.start()

# 疎通確認用エンドポイント
@app.route("/test-openai", methods=["GET"])
def test_openai():
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        print("✅ OpenAIモデル取得成功:", model_ids)
        return jsonify({"status": "ok", "models": model_ids})
    except Exception as e:
        print("❌ OpenAIモデル取得エラー:", repr(e))
        return jsonify({"status": "error", "error": str(e)}), 500

# Railway or ローカル開発用の起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

