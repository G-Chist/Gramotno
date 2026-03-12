import string
from translate import Translator


def strip_punctuation(text: str) -> list[str]:
    translator = str.maketrans("", "", string.punctuation)
    cleaned = text.translate(translator)
    return cleaned.split()


def translate(text: str, from_code: str, to_code: str) -> str:
    translator = Translator(from_lang=from_code, to_lang=to_code)
    return translator.translate(text)
