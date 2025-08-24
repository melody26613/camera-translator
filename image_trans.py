import requests
import os

from PIL import Image, ImageDraw, ImageFont
from cachetools import LRUCache
from typing import List

from logger import build_logger
from translator import ollama_translate_texts, google_translate_texts

OCR_SERVICE_URL = "http://192.168.50.19:20000/ocr/dict"
TRANS_SOURCE_IMAGE_PATH = "pic/test.png"
TRANS_DEST_IMAGE_PATH = "pic/translated_text_overlay.png"

TRANS_METHOD_MAP = {
    "ollama": ollama_translate_texts,
    "google": google_translate_texts,
}

TRANS_METHOD = TRANS_METHOD_MAP.get("ollama")

# key: original OCR text
# value: translated text
translation_cache = LRUCache(maxsize=1000)

logger = build_logger("ocr_trans", "ocr_trans.log")


def run_ocr_service(image_path):
    """
    call OCR service to get text and coordinate
    """
    image_path_abs = os.path.abspath(image_path)
    if not os.path.exists(image_path_abs):
        logger.error(f"Failed to find image at path: {image_path_abs}")
        return None

    try:
        with open(image_path_abs, "rb") as f:
            files = {
                "file": (os.path.basename(image_path_abs), f, "image/png")
            }
            response = requests.post(OCR_SERVICE_URL, files=files)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed when calling OCR service: {e}")
        logger.error(
            f"Please make sure the OCR service is running at {OCR_SERVICE_URL}")
        return None


def translate_and_cache(texts: List[str]):
    """
    Read LRU cache before translation.
    """
    if not texts:
        return {}

    texts_to_translate = []
    all_translations = {}

    for text in texts:
        if text in translation_cache:
            all_translations[text] = translation_cache[text]
            print(
                f"""Get cache with key:"{text}", value: "{translation_cache[text]}" """)
        else:
            texts_to_translate.append(text)

    if texts_to_translate:
        try:
            translations = TRANS_METHOD(texts=texts_to_translate)

            # store into cache
            for original, translation in zip(texts_to_translate, translations):
                translation_cache[original] = translation
                all_translations[original] = translation
                print(f"New translation: {original} -> {translation}")

        except Exception as e:
            print(
                f"""Failed to translate: {texts_to_translate}, the error is: {e}""")

    return all_translations


def create_text_overlay(image_path, ocr_data, output_path):
    """
    Create a new PNG image, with only translated text and transparent background
    """
    if not ocr_data:
        logger.error("There is no valid ocr_data")
        return

    image_path_abs = os.path.abspath(image_path)
    if not os.path.exists(image_path_abs):
        logger.error(f"Original image not found at path: {image_path_abs}")
        return

    original_texts = [item["transcription"] for item in ocr_data]
    translations = translate_and_cache(original_texts)

    original_img = Image.open(image_path_abs)
    width, height = original_img.size

    overlay_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay_img)

    for item in ocr_data:
        original_text = item["transcription"]
        points = item["points"]

        translated_text = translations.get(original_text, original_text)

        box_width = abs(points[1][0] - points[0][0])
        box_height = abs(points[2][1] - points[1][1])

        font = find_best_font_size(translated_text, box_width, box_height)

        bbox = font.getbbox(translated_text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        start_x = points[0][0] + (box_width - text_width) / 2
        start_y = points[0][1] + (box_height - text_height) / 2

        draw.text(
            (start_x, start_y),
            translated_text,
            font=font,
            fill=(0, 0, 0),  # fill font with color black
            stroke_width=5,  # font stroke width
            stroke_fill=(255, 255, 255)  # set font stroke with color white
        )

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    overlay_img.save(output_path)
    logger.info(f"Output new image {output_path=}")


def find_best_font_size(text, max_width, max_height):
    font_path = find_font_file()

    font_size = 50
    while font_size > 1:
        try:
            font = ImageFont.truetype(font_path, font_size)
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            if text_width <= max_width and text_height <= max_height:
                return font
            font_size -= 1
        except Exception:
            font_size -= 1

    return ImageFont.load_default()


def find_font_file() -> str:
    font_path = None

    if os.name == "nt":
        font_paths = ["C:/Windows/Fonts/msjh.ttc",
                      "C:/Windows/Fonts/simsun.ttc"]
    elif os.name == "posix":
        if os.uname().sysname == "Darwin":
            font_paths = ["/System/Library/Fonts/PingFang.ttc",
                          "/Library/Fonts/Arial Unicode.ttf"]
        else:
            font_paths = ["/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                          "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]

    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    if not font_path:
        logger.warning("Warning, cannot find Chinese font.")

    return font_path


def image_translate(image_path: str):
    if not os.path.exists(image_path):
        logger.error(f"Invalid image path {image_path}")
        return

    logger.info("--- Step 1: calling OCR service ---")
    ocr_result = run_ocr_service(image_path)

    if ocr_result:
        logger.info("--- Step 2 & 3: translate and output to new image ---")
        create_text_overlay(image_path, ocr_result, TRANS_DEST_IMAGE_PATH)


if __name__ == "__main__":
    image_translate(TRANS_SOURCE_IMAGE_PATH)
