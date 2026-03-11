import pytermgui as ptg
import random
import os



GOOFY_WORDS = [
    "wobble", "bumbly", "splork", "noodle", "flurg",
    "blimp", "quack", "zorp", "glimp", "spork",
    "boop", "dingle", "wazzock", "goblin", "honk",
    "squelch", "flump", "boggle", "snark", "gurgle"
]

OUTPUT_FILE = "words.txt"

def get_random_word() -> str:
    return random.choice(GOOFY_WORDS)

def write_word(word: str) -> None:
    with open(OUTPUT_FILE, "a") as f:
        f.write(word + "\n")

def make_handler(word: str):
    def handler(*args):
        write_word(word)
    return handler

def main() -> None:
    with ptg.WindowManager() as manager:
        words = [get_random_word() for _ in range(5)]
        
        cards = []
        for i, word in enumerate(words, 1):
            btn = ptg.Button(f"[bold]{i}[/bold]: {word}", make_handler(word))
            cards.append(btn)

        window = ptg.Window(
            "[bold]Goofy Card Clicker![/bold]\n",
            *cards,
            "",
            f"[dim]Words will be written to {OUTPUT_FILE}[/dim]"
        ).center()

        for i, btn in enumerate(cards, 1):
            handler = make_handler(words[i-1])
            window.bind(str(i), lambda *_, h=handler: h())

        manager.add(window)

if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    main()
