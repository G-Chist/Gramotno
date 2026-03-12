import pytermgui as ptg
import random
import os
import tomli as tomllib

ALPHABET_ENG = "abcdefghijklmnopqrstuvwxyz"

logo_string = """

    ▄▄▄▄                                                                        
  ██▀▀▀▀█                                            ██                         
 ██         ██▄████   ▄█████▄  ████▄██▄   ▄████▄   ███████   ██▄████▄   ▄████▄  
 ██  ▄▄▄▄   ██▀       ▀ ▄▄▄██  ██ ██ ██  ██▀  ▀██    ██      ██▀   ██  ██▀  ▀██ 
 ██  ▀▀██   ██       ▄██▀▀▀██  ██ ██ ██  ██    ██    ██      ██    ██  ██    ██ 
  ██▄▄▄██   ██       ██▄▄▄███  ██ ██ ██  ▀██▄▄██▀    ██▄▄▄   ██    ██  ▀██▄▄██▀ 
    ▀▀▀▀    ▀▀        ▀▀▀▀ ▀▀  ▀▀ ▀▀ ▀▀    ▀▀▀▀       ▀▀▀▀   ▀▀    ▀▀    ▀▀▀▀   
                                                                                

"""

with open("ui/settings.toml", "rb") as f:
    SETTINGS = tomllib.load(f)

COLORS = SETTINGS

GOOFY_WORDS = [
    "wobble", "bumbly", "splork", "noodle", "flurg",
    "blimp", "quack", "zorp", "glimp", "spork",
    "boop", "dingle", "wazzock", "goblin", "honk",
    "squelch", "flump", "boggle", "snark", "gurgle"
]

OUTPUT_FILE = "words.txt"

def pad_string_with_spaces(string: str, max_len: int = 20) -> str:
    return string + " " * (max_len - len(string)) 

def get_random_word() -> str:
    return random.choice(GOOFY_WORDS)

def write_word(word: str) -> None:
    with open(OUTPUT_FILE, "a") as f:
        f.write(word + "\n")

def make_handler(word: str, container: 'ptg.Container', index: int):
    def handler(*args):
        write_word(word)
        if container is not None:
            container.select(index)
    return handler

def main() -> None:
    with ptg.WindowManager() as manager:
        words_left = [pad_string_with_spaces(get_random_word()) for _ in range(5)]
        words_right = [pad_string_with_spaces(get_random_word()) for _ in range(5)]
        
        left_keys = [SETTINGS["left_keys"][f"key_{i}"] for i in range(1, 6)]
        right_keys = [SETTINGS["right_keys"][f"key_{i}"] for i in range(1, 6)]

        cards_left= []
        for i, word_left in enumerate(words_left):
            index_style = f'[{COLORS["left_index"]["foreground"]}]{COLORS["left_index"]["bold"] and "[bold]" or ""}{left_keys[i]}[/bold]'
            word_style = f'{word_left}'
            btn = ptg.Button(f"{index_style}: {word_style}", make_handler(word_left, None, i))
            cards_left.append(btn)

        cards_right = []
        for i, word_right in enumerate(words_right):
            index_style = f'[{COLORS["right_index"]["foreground"]}]{COLORS["right_index"]["bold"] and "[bold]" or ""}{right_keys[i]}[/bold]'
            word_style = f'{word_right}'
            btn = ptg.Button(f"{index_style}: {word_style}", make_handler(word_right, None, i))
            cards_right.append(btn)

        left_container = ptg.Container(
            f"[{COLORS['left_header']['foreground']}]{COLORS['left_header']['bold'] and '[bold]' or ''}Left[/bold]\n",
            *cards_left,
            "",
        )

        right_container = ptg.Container(
            f"[{COLORS['right_header']['foreground']}]{COLORS['right_header']['bold'] and '[bold]' or ''}Right[/bold]\n",
            *cards_right,
            "",
        )

        for i, btn in enumerate(cards_left):
            handler = make_handler(words_left[i], left_container, i)
            left_container.bind(left_keys[i], lambda *_, h=handler: h())

        for i, btn in enumerate(cards_right):
            handler = make_handler(words_right[i], right_container, i)
            right_container.bind(right_keys[i], lambda *_, h=handler: h())

        splitter = ptg.Splitter(
            left_container,
            right_container,
        )
        splitter.chars["separator"] = ""

        window = ptg.Window(
            logo_string,
            splitter,
            "",
            f"[dim]Words will be written to {OUTPUT_FILE}[/dim]",
            width=int(ptg.terminal.width),
            height=int(ptg.terminal.height*0.8),
            is_noblur=True,
        ).center()
        window.styles.fill = COLORS["background"]["foreground"]
        window.styles.border = ""

        manager.add(window)

if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    main()
