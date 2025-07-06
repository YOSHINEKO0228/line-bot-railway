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

# ユーザー状態管理（ステップ進行用）
user_state = {}

# ChatGPTでレシピを生成

def generate_recipe_from_gpt(ingredients):
    prompt = f'''
あなたは節約上手な料理アドバイザーです。
以下の食材を使って、初心者でも簡単に作れるレシピを日本語で提案してください。

【材料】{ingredients}

🍽️【料理名】  
🧂【材料（2人分）】  
🔥【手順】STEP1〜STEP3で簡潔に  
💡【ワンポイント】

節約・簡単・おいしいがキーワードです。
'''
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ OpenAIエラー:", repr(e))
        return "申し訳ありません、レシピの取得に失敗しました。"

# 雑談対応

def generate_free_chat_response(user_text):
    prompt = f"あなたは親しみやすい会話アシスタントです。以下の内容に自然に返事してください：\n{user_text}"
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ 雑談応答エラー:", repr(e))
        return "うまく返せなかったみたい、ごめんね。"

# 3日分買い物提案
def suggest_shopping_plan():
    return """
🛒 3日分の節約メニューにおすすめの買い物リストだよ！

【食材リスト】
・鶏むね肉 2枚
・キャベツ 1玉
・卵 6個
・豆腐 2丁
・もやし 2袋
・にんじん 2本
・玉ねぎ 2個

🍽️ メニュー提案：
1日目：鶏キャベツ炒め  
2日目：豆腐と卵の中華風炒め  
3日目：もやしそば風炒め

📌 無駄なく使い切れてコスパも良いよ！
"""

# おかず追加提案
def suggest_extra_dish():
    return """
了解！今の食材に少し足すだけで、おかずを増やせるよ😊

🛒 追加するなら：
・ちくわ（100円で4本）
・冷凍ブロッコリー or わかめ

🍳 追加メニュー案：
・ちくわの甘辛炒め
・ブロッコリーと卵のごまマヨサラダ

副菜にちょうどいいし、コスパも最高だよ✨
"""

# ステップ進行
def continue_step(event, state):
    idx = state["step_index"] + 1
    if idx < len(state["steps"]):
        state["step_index"] = idx
        reply = f"STEP{idx}: {state['steps'][idx].strip()}\n👉 続けるには『次』と送ってね！"
    else:
        reply = "おつかれさま！これでレシピ完了だよ🍽️\nまた何か作りたくなったら教えてね！"
        del user_state[event.source.user_id]
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# LINEメッセージイベント
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.lower()

    if user_id in user_state and user_state[user_id].get("mode") == "step":
        return continue_step(event, user_state[user_id])

    if "買い物" in text or "3日分" in text:
        reply_text = suggest_shopping_plan()

    elif "おかず" in text and ("増やしたい" in text or "もう少し" in text):
        reply_text = suggest_extra_dish()

    elif "ステップで" in text:
        recipe = generate_recipe_from_gpt(text)
        steps = recipe.split("STEP")
        if len(steps) > 1:
            user_state[user_id] = {"mode": "step", "steps": steps, "step_index": 1}
            reply_text = f"STEP1: {steps[1].strip()}\n👉 続けるには『次』と送ってね！"
        else:
            reply_text = recipe

    elif "まとめて" in text:
        reply_text = generate_recipe_from_gpt(text)

    elif any(x in text for x in ["レシピ", "食材", "つくれる", "作れる", "料理", "献立", "つくる", "材料"]):
        reply_text = generate_recipe_from_gpt(text)

    else:
        reply_text = generate_free_chat_response(text)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

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

# 疎通確認用エンドポイント
@app.route("/test-openai", methods=["GET"])
def test_openai():
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        return jsonify({"status": "ok", "models": model_ids})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ルート確認エンドポイント
@app.route("/", methods=["GET"])
def home():
    return "✅ Flaskは起動しています"

# アプリ起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
