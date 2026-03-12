from translate import Translator


def translate(text: str, from_code: str, to_code: str) -> str:
    translator = Translator(from_lang=from_code, to_lang=to_code)
    return translator.translate(text)
