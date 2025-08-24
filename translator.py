import requests
import json
import re

from typing import List
from logger import build_logger
from googletrans import Translator

logger = build_logger("ocr_trans", "ollama.log")

GOOGLE_TRANSLATE_SOURCE_LANG = "ja"
GOOGLE_TRANSLATE_TARGET_LANG = "zh-TW"

OLLAMA_TRANSLATE_SYSTEM_PROMPT = """請將使用者提供的每一段日文分別翻譯成中文。
輸出時保持相同的行數與順序。
禁止輸出日文。
禁止輸出任何解釋、markdown 格式。
只輸出中文翻譯結果，每一行只包含一段翻譯文字。"""

OLLAMA_TRANSLATE_USER_PROMPT_PREFIX = """"""


OLLAMA_MODEL = "gemma2:2b"
OLLAMA_HOST = "http://192.168.50.19:11434"
OLLAMA_TRANSLATE_TITLE = [
    "text",
    "文本",
]


def google_translate(text: str, src_lang=GOOGLE_TRANSLATE_SOURCE_LANG, dest_lang=GOOGLE_TRANSLATE_TARGET_LANG):
    translator = Translator()
    try:
        translation = translator.translate(text, src=src_lang, dest=dest_lang)
        translated_text = translation.text
        return translated_text
    except Exception as e:
        logger.error(
            f"""Failed to translate with text: "{text}", the error is: {e}""")
        return text


def google_translate_texts(texts: List[str]) -> List[str]:
    formatted_texts = f"""<!--{"--><!--".join(texts)}-->"""
    logger.info(f"{formatted_texts=}")

    translation_string = google_translate(text=formatted_texts)
    logger.info(f"{translation_string=}")

    # < ！? -+   : left brackets, and allow mark in half-width or full-width following
    # \s*        : allow spaces
    # (.*?)      : get the content we need
    # \s* -+ >   : allow spaces and multiple dashes and ending mark
    pattern = r"<\s*[!！]?\s*-+\s*(.*?)\s*-+\s*>"
    matches = re.findall(pattern, translation_string)
    logger.info(f"{matches=}")

    return matches


def ollama_translate_text(text: str, model_name: str = OLLAMA_MODEL, ollama_url: str = OLLAMA_HOST) -> str:
    if not text:
        return ""

    request_body = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": OLLAMA_TRANSLATE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": OLLAMA_TRANSLATE_USER_PROMPT_PREFIX + text,
            }
        ],
        "stream": False,
        "think": False,
    }

    logger.info(f"{request_body=}")

    api_url = f"{ollama_url}/api/chat"
    try:
        response = requests.post(api_url, json=request_body, timeout=60)
        response.raise_for_status()

        llm_response = response.json()
        translated_text = llm_response.get("message", {}).get("content", "")

        return translated_text

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call ollama, error={e}")
        return ""


def ollama_translate_texts(texts: List[str]) -> List[str]:
    formatted_texts = "\n".join(
        [f"『{text}』" for text in texts])
    logger.info(f"{formatted_texts=}")

    translation_string = ollama_translate_text(text=formatted_texts)
    logger.info(f"{translation_string=}")

    # split by one new line or multiple new lines
    matches = re.split(r"\n+", translation_string.strip())
    logger.info(f"{matches=}")

    matches = [strip_quotes(text) for text in matches]
    logger.info(f"{matches=}")

    return matches


def strip_quotes(text: str) -> str:
    text = text.strip()

    quotes = [
        ("『", "』"),
        ("‘", "’"),
        ('"', '"'),
        ("'", "'"),
        ("「", "」"),
        ("“", "”"),
    ]
    
    for ql, qr in quotes:
        if text.startswith(ql) and text.endswith(qr) and len(text) >= 2:
            return text[len(ql):-len(qr)]
    return text


if __name__ == "__main__":
    texts = [
        "こんにちは",
        "お名前を伺えますか",
    ]
    # texts = [
    #     "お爺さんとおばあさんはなんだかそれが面白くて体のあちこちをこすっては、前のものと一緒にしてぎゅっと丸め、またこすってあかをだしてはさっき丸めたものに、さらにくっつけて・・とやっていたら、しまいには一かたまりになったので、ちょっといたずら心を起こしたおじいさんは、それを小さな人の形にしてみました。",
    #     "できあがった小さな人形をみているうちに、なんとなくそれが可愛くなってきたおじいさんとおばあさんは、そのまま捨てるにはかわいそうな気がして、あかで作った小さな人形をとりあえず神棚において、特に何を拝むでもなくぱんぱんと手を打ちました。 すると不思議なことに神棚に上がった人形がとつぜんむくむくと体をゆすったと思ったら、大きく伸びをして周りをきょろきょろ見回したのです！",
    #     "ふたりは夢でも見ているのかと思ってぽかんとそれを見ていましたが、すぐに神棚の人形とおじいさんとおばあさんの目が合い、人形はぴょんっと下に飛び降りたかとおもうと、ふたりの前にすっくと立ちました。",
    # ]

    logger.info("-----Test for google translate----")
    logger.info(f"{texts=}")
    response = google_translate_texts(texts)
    logger.info(f"{response=}")

    exit(0)

    logger.info("-----Test for LLM translation-----")
    logger.info(f"{texts=}")
    response = ollama_translate_texts(texts=texts)
    logger.info(f"{response=}")
