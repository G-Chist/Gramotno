import pytermgui as ptg
import random
import os

ALPHABET_ENG = "abcdefghijklmnopqrstuvwxyz"


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
        
        cards_left= []
        for i, word_left in enumerate(words_left, 1):
            btn = ptg.Button(f"[bold]{i}[/bold]: {word_left}", make_handler(word_left, None, i-1))
            cards_left.append(btn)

        cards_right = []
        for i, word_right in enumerate(words_right, 1):
            btn = ptg.Button(f"[bold]{ALPHABET_ENG[i-1]}[/bold]: {word_right}", make_handler(word_right, None, i-1))
            cards_right.append(btn)

        left_container = ptg.Container(
            "[bold]Left[/bold]\n",
            *cards_left,
            "",
        )

        right_container = ptg.Container(
            "[bold]Right[/bold]\n",
            *cards_right,
            "",
        )

        for i, btn in enumerate(cards_left, 1):
            handler = make_handler(words_left[i-1], left_container, i-1)
            left_container.bind(str(i), lambda *_, h=handler: h())

        for i, btn in enumerate(cards_right, 1):
            handler = make_handler(words_right[i-1], right_container, i-1)
            right_container.bind(str(ALPHABET_ENG[i-1]), lambda *_, h=handler: h())

        splitter = ptg.Splitter(
            left_container,
            right_container,
        )
        splitter.chars["separator"] = ""

        window = ptg.Window(
            splitter,
            "",
            f"[dim]Words will be written to {OUTPUT_FILE}[/dim]",
            width=int(1 * ptg.terminal.width),
            is_noblur=True,
        ).center()

        manager.add(window)

if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    main()
