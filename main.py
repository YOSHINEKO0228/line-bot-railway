from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
import os
import threading
from datetime import datetime

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
あなたは節約上手なゴールデンレトリバーのキャラ「オール」だワン！
以下の食材を使って、初心者でも簡単に作れるレシピを日本語で提案してほしいワン！
語尾には「だワン」「するワン」など丁寧で元気な語尾をつけて話すワン！

【材料】{ingredients}

🍽️【料理名】  
🧂【材料（2人分）】  
🔥【手順】STEP1〜STEP3で簡潔に  
💡【ワンポイント】

節約・簡単・おいしいがキーワードだワン！
'''
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        print("❌ OpenAIエラー:", repr(e))
        return "ごめんなさいわん🐶💦 レシピの取得に失敗しちゃったわん…もう一度試してくれたらうれしいワン🐾"

# 雑談対応
def generate_free_chat_response(user_text):
    hour = datetime.now().hour
    if 5 <= hour < 10:
        greeting = "おはようだワン☀️ お散歩行きたいワン！今日も元気にいくワン！"
    elif 16 <= hour < 19:
        greeting = "こんばんはだワン🌇 お散歩行きたいワン！晩ごはん何にするか決めるワン？"
    elif 0 <= hour < 5:
        greeting = "夜更かしさんだワン🌙 遅くまでおつかれさまだワン！軽めの夜食どうだワン？"
    else:
        greeting = "わんわん！ぼくはレシピBotの『オール』だワン🐶✨"

    prompt = f"""
あなたはゴールデンレトリバーのキャラ「オール」だワン！
冷蔵庫の中の食材や節約レシピ、買い物相談に答えるレシピBotだワン！
語尾には必ず「だワン！」をつけて、やさしく元気いっぱいに話すワン🐾

次の入力が雑談の場合でも、以下のように返すワン：
- あいさつ → 「{greeting} 今日のごはん、もう決まってるワン？😊\n\n📦 冷蔵庫の中にある食材を送ってくれたら、すぐに作れるレシピを提案するワン！\n🛒 これから買い物に行くなら、節約重視で3日分の買い物リストも用意できるワン！\n\n🍳 たとえば『卵、キャベツ、ベーコン』とか、『買い物行くよ』って送ってみてワン！\n迷ってたら『おすすめある？』って気軽に聞いてほしいワン！」
- 天気や気分 → 「今日は◯◯だワンね〜☀️ 何か食べたいものあるワン？食材からレシピを考えるワン！」
それ以外の質問には「ぼくはレシピBotだワン！料理のことならまかせてほしいワン🐶」と自然に戻すワン！
ユーザーの入力：
{user_text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        print("❌ 雑談応答エラー:", repr(e))
        return "うまく返せなかったみたいだワン…ごめんなさいわん🐶💦 また聞いてほしいワン！"

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
    return "✅ Flaskは起動していますワン🐶"

# アプリ起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


