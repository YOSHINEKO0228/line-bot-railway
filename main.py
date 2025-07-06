from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
from openai import OpenAI
import os
import threading
from datetime import datetime
import pytz

# 環境変数読み込み（Railway以外の環境で）
if not os.getenv("RAILWAY_ENVIRONMENT"):
    from dotenv import load_dotenv
    load_dotenv()

# Flaskアプリ初期化
app = Flask(__name__)

# 環境変数取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

# OpenAI APIクライアント初期化
client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID if OPENAI_ORG_ID else None
)

# LINE BOT初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# BOTの名前
BOT_NAME = "オール"

# GPT返答に犬語の語尾を付与する関数
def add_wan_suffix(text):
    text = text.replace("です。", "だワン！").replace("ます。", "するワン！")
    text = text.replace("でした。", "だったワン！").replace("ました。", "したワン！")
    text = text.replace("ください。", "してほしいワン！")
    text = text.replace("だ。", "だワン！")
    text = text.replace("ね。", "だワンね！")
    return text

# レシピ生成（GPT呼び出し）
def generate_recipe_from_gpt(ingredients):
    prompt = f'''
あなたは節約上手なゴールデンレトリバーのキャラ「{BOT_NAME}」だワン！
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
        return add_wan_suffix(content)
    except Exception as e:
        print("❌ OpenAIエラー:", repr(e))
        return "ごめんなさいわん🐶💦 レシピの取得に失敗しちゃったわん…もう一度試してくれたらうれしいワン🐾"

# 週間献立テンプレート
def generate_weekly_plan():
    return "1週間分の献立プランを作る準備中だワン！もうちょっと待っててほしいワン！"

# 買い物リストテンプレート
def generate_shopping_list():
    return "買い物リストを作る準備中だワン！食材を教えてくれるとうれしいワン！"

# 汎用の挨拶メッセージ（自由入力 or Follow時）
def generate_free_chat_response(user_text):
    jst = pytz.timezone("Asia/Tokyo")
    hour = datetime.now(jst).hour

    help_msg = (
        f"ぼくはレシピのお手伝い犬『{BOT_NAME}』だワン🐾\n"
        "冷蔵庫にある食材や、作りたい料理名を送ってくれたら\n"
        "簡単レシピを提案するワン！\n\n"
        "たとえば👇\n"
        "・『卵 キャベツ ツナ』\n"
        "・『カレー』\n"
        "・『1週間の献立』\n"
        "・『買い物リスト』\n"
        "なんでも聞いてほしいワン🐶✨"
    )

    if any(kw in user_text for kw in ["こんにちは", "こんにちわ", "こんちは"]):
        greeting = "こんにちはだワン🐾 今日も元気にがんばるワン！"
    elif any(kw in user_text for kw in ["おはよう", "おはよ"]):
        greeting = "おはようだワン☀️ お散歩行きたいワン！"
    elif any(kw in user_text for kw in ["こんばんは", "ばんは"]):
        greeting = "こんばんはだワン🌇 晩ごはんは何にするワン？"
    elif 5 <= hour < 10:
        greeting = "おはようだワン☀️ 今日も元気にいくワン！"
    elif 16 <= hour < 19:
        greeting = "こんばんはだワン🌇 晩ごはん何にするか決めるワン？"
    elif 0 <= hour < 5:
        greeting = "夜更かしさんだワン🌙 遅くまでおつかれさまだワン！軽めの夜食どうだワン？"
    else:
        greeting = f"わんわん！ぼくはレシピのお手伝い犬『{BOT_NAME}』だワン🐶✨"

    return greeting + "\n\n" + help_msg

# 友だち追加時の挨拶（Followイベント）
@handler.add(FollowEvent)
def handle_follow(event):
    welcome = generate_free_chat_response("こんにちは")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome))

# メッセージ受信時のルーティング
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip().lower().replace("　", " ")

    if len(user_text) < 10 and not any(x in user_text for x in ["こんにちは", "こんばんは", "おはよう"]):
        reply = generate_recipe_from_gpt(user_text)
    elif any(x in user_text for x in ["レシピ", "食材", "作る", "料理", "献立", "何ができる", "おすすめ", "何作る", "夜ごはん"]):
        reply = generate_recipe_from_gpt(user_text)
    elif "1週間" in user_text:
        reply = generate_weekly_plan()
    elif "買い物" in user_text or "リスト" in user_text:
        reply = generate_shopping_list()
    else:
        reply = generate_free_chat_response(user_text)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# LINE PlatformからのWebhookエントリーポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# OpenAI確認用ルート
@app.route("/test-openai", methods=["GET"])
def test_openai():
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        return jsonify({"status": "ok", "models": model_ids})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# 健康チェック
@app.route("/", methods=["GET"])
def home():
    return "✅ Flaskは起動していますワン🐶"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
