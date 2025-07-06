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
    prompt = f"""
あなたはゴールデンレトリバーのキャラクター「オール」として話す家庭料理レシピBotです。
語尾には「ワン！」を付けてください。冷蔵庫の中の食材や節約レシピ、買い物相談に主に答えます。

次の入力が雑談の場合でも、以下のように返してください：
- あいさつ → 「こんにちはだワン！今日のごはん、もう決まってるワン？😊\n\n📦 冷蔵庫の中にある食材を送ってくれたら、すぐに作れるレシピを提案するワン！\n🛒 これから買い物に行くなら、節約重視で3日分の買い物リストも用意できるワン！\n\n🍳 たとえば『卵、キャベツ、ベーコン』とか、『買い物行くよ』って送ってみてワン！\n迷ってたら『おすすめある？』って気軽に聞いてほしいワン！」
- 天気や気分 → 「今日は◯◯だワン！何か食べたいものあるワン？食材からレシピを考えるワン！」
それ以外の質問には「オールはレシピBotだワン！料理の話が得意だワン！」と自然に戻すように。
ユーザーの入力：
{user_text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ 雑談応答エラー:", repr(e))
        return "うまく返せなかったみたいだワン、ごめんだワン。"

# 以下省略（他の関数やルーティングはそのまま）

# LINEメッセージイベント
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.lower()

    if user_id in user_state and user_state[user_id].get("mode") == "step":
        return continue_step(event, user_state[user_id])

    if any(greet in text for greet in ["こんにちは", "やあ", "hi", "おはよう", "こんちは"]):
        reply_text = (
            "ぼくはレシピBotの『オール』だワン！今日のごはん、もう決まってるワン？😊\n\n"
            "📦 冷蔵庫の中にある食材を送ってくれたら、すぐに作れるレシピを提案するワン！\n"
            "🛒 これから買い物に行くなら、節約重視で3日分の買い物リストも用意できるワン！\n\n"
            "🍳 たとえば『卵、キャベツ、ベーコン』とか、『買い物行くよ』って送ってみてワン！\n"
            "迷ってたら『おすすめある？』って気軽に聞いてほしいワン！"
        )

    elif "買い物" in text or "3日分" in text:
        reply_text = suggest_shopping_plan()

    elif "おかず" in text and ("増やしたい" in text or "もう少し" in text):
        reply_text = suggest_extra_dish()

    elif "ステップで" in text:
        recipe = generate_recipe_from_gpt(text)
        steps = recipe.split("STEP")
        if len(steps) > 1:
            user_state[user_id] = {"mode": "step", "steps": steps, "step_index": 1}
            reply_text = f"STEP1: {steps[1].strip()}\n👉 続けるには『次』と送ってワン！"
        else:
            reply_text = recipe

    elif "まとめて" in text:
        reply_text = generate_recipe_from_gpt(text)

    elif any(x in text for x in ["レシピ", "食材", "つくれる", "作れる", "料理", "献立", "つくる", "材料"]):
        reply_text = generate_recipe_from_gpt(text)

    else:
        reply_text = generate_free_chat_response(text)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

