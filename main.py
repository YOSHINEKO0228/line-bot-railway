from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import threading
from openai import OpenAI

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ChatGPT処理を非同期で行う関数
def reply_with_chatgpt(event):
    user_text = event.message.text
    prompt = f"冷蔵庫の中にある材料で作れるレシピを教えてください。材料: {user_text}。レシピは簡潔に説明してください。"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as e:
        reply_text = "申し訳ありません、レシピの取得に失敗しました。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    thread = threading.Thread(target=reply_with_chatgpt, args=(event,))
    thread.start()



