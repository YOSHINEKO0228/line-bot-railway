# utils.py

def add_wan_suffix(text: str) -> str:
    text = text.replace("です。", "だワン！").replace("ます。", "するワン！")
    text = text.replace("でした。", "だったワン！").replace("ました。", "したワン！")
    text = text.replace("ください。", "してほしいワン！")
    text = text.replace("だ。", "だワン！")
    text = text.replace("ね。", "だワンね！")
    return text
