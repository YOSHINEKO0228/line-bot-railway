# messages.py

from datetime import datetime
import pytz

BOT_NAME = "オール"

def generate_weekly_plan() -> str:
    return "1週間分の献立プランを作る準備中だワン！もうちょっと待っててほしいワン！"

def generate_shopping_list() -> str:
    return "買い物リストを作る準備中だワン！食材を教えてくれるとうれしいワン！"

def generate_free_chat_response(user_text: str) -> str:
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
