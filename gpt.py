# gpt.py

from openai import OpenAI
import os
from utils import add_wan_suffix

# 環境変数からAPIキーを取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

# OpenAIクライアント初期化
client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID if OPENAI_ORG_ID else None
)

BOT_NAME = "オール"  # キャラ名（犬）

def generate_recipe_from_gpt(ingredients: str) -> str:
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
        return "ごめんなさいわん🐶💦 レシピの取得に失敗しちゃったワン…もう一度試してくれたらうれしいワン🐾"
