from translate import Translator


def strip_punctuation(text: str) -> list[str]:
    punctuation = set(' \t\n.,;:!?()[]{}"\'-')
    result = []
    current_word = []
    
    for char in text:
        if char in punctuation:
            if current_word:
                result.append(''.join(current_word))
                current_word = []
        else:
            current_word.append(char)
    
    if current_word:
        result.append(''.join(current_word))
    
    return result


def translate(text: str, from_code: str, to_code: str) -> str:
    translator = Translator(from_lang=from_code, to_lang=to_code)
    return translator.translate(text)
