import pytermgui as ptg
import random
import os
import tomli as tomllib
import tomli_w as tomlwrite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from language_logic.language_utils import strip_punctuation, translate 

from models.schema import Base, UserSettings, Language, Card, Progress

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

with open("settings/settings.toml", "rb") as f:
    SETTINGS = tomllib.load(f)

COLORS = SETTINGS

FILE_TO_LOAD = "enter .txt file path"

engine = create_engine('sqlite:///evolving_cards.db')
Session = sessionmaker(bind=engine)

OUTPUT_FILE = "words.txt"

def sync_settings_to_db():
    session = Session()
    settings = session.query(UserSettings).first()
    if not settings:
        settings = UserSettings(
            native_lang=SETTINGS.get('native_lang', {}).get('code', 'en'),
            learning_lang=SETTINGS.get('learning_lang', {}).get('code', 'tr')
        )
        session.add(settings)
    else:
        settings.native_lang = SETTINGS.get('native_lang', {}).get('code', 'en')
        settings.learning_lang = SETTINGS.get('learning_lang', {}).get('code', 'tr')
    session.commit()
    session.close()

def save_settings():
    with open("settings/settings.toml", "wb") as f:
        tomlwrite.dump(SETTINGS, f)
    sync_settings_to_db()

def reload_settings():
    global SETTINGS, COLORS
    with open("settings/settings.toml", "rb") as f:
        SETTINGS = tomllib.load(f)
    COLORS = SETTINGS

def get_words_from_db() -> list[str]:
    session = Session()
    cards = session.query(Card).all()
    session.close()
    return [card.word for card in cards]

def get_random_word() -> str:
    words = get_words_from_db()
    if not words:
        return "N/A"
    return random.choice(words)

def pad_string_with_spaces(string: str, max_len: int = 20) -> str:
    return string + " " * (max_len - len(string)) 

def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def invert_color(r: int, g: int, b: int):
    return (255 - r, 255 - g, 255 - b)

def color_preview(hex_color: str, text: str = "Preview") -> str:
    r, g, b = hex_to_rgb(hex_color)
    ir, ig, ib = invert_color(r, g, b)
    return f"[{ir};{ig};{ib} @{r};{g};{b}]{text}[/]"

def write_word(word: str) -> None:
    with open(OUTPUT_FILE, "a") as f:
        f.write(word + "\n")

class Game:

    def __init__(self):
        self.all_cards = []
        self.left_ids = []
        self.right_ids = []
        self.words_left = []
        self.words_right = []
        self.left_keys = []
        self.right_keys = []
        self.cards_left = []
        self.cards_right = []
        self.selected_left = None
        self.selected_right = None

        if len(self.all_cards) == 0:
            self.status = ptg.Label("[dim]Please load words![/dim]") 
        else:
            self.status = ptg.Label("[dim]Start matching![/dim]")

        self.clicks = 0
        self.clicks_label = ptg.Label(f"Clicks: {self.clicks}")
        self.button = ptg.Button(f"Click me!", lambda *_: self.button_handler()) 

        self.left_keys = [SETTINGS['left_keys'][f'key_{i}'] for i in range(1, 6)]
        self.right_keys = [SETTINGS['right_keys'][f'key_{i}'] for i in range(1, 6)]
        
        self.left_buttons = []
        for key in self.left_keys:
            btn = ptg.Button(pad_string_with_spaces(f"{key})"))
            self.left_buttons.append(btn)

        self.right_buttons = []
        for key in self.right_keys:
            btn = ptg.Button(pad_string_with_spaces(f"{key})"))
            self.right_buttons.append(btn)

        left_header = ptg.Label(f"[{COLORS['left_header']['foreground']}]{COLORS['left_header']['bold'] and '[bold]' or ''}Native[/bold]\n")
        right_header = ptg.Label(f"[{COLORS['right_header']['foreground']}]{COLORS['right_header']['bold'] and '[bold]' or ''}Learning[/bold]\n")
        
        left_container = ptg.Container(
            left_header,
            "",
            *self.left_buttons,
            "",
            get_random_word(),
        )
        right_container = ptg.Container(
            right_header,
            "",
            *self.right_buttons,
            "",
            self.clicks_label,
        )
        
        splitter = ptg.Splitter(
            left_container,
            right_container,
        )
        splitter.chars["separator"] = ""

        for i, btn in enumerate(self.left_buttons):
            left_container.bind(self.left_keys[i], lambda *_, idx=i: self.left_button_handler(idx))

        for i, btn in enumerate(self.right_buttons):
            right_container.bind(self.right_keys[i], lambda *_, idx=i: self.right_button_handler(idx))

        self.window = ptg.Window(
            logo_string,
            "",
            splitter,
            "",
            self.status,
            "",
            width=int(ptg.terminal.width),
            height=int(ptg.terminal.height*0.8),
            is_noblur=True,
        ).center()
        self.window.styles.border = ""

    def button_handler(self):
        self.clicks += 1
        self.button.label = f"Dude {self.clicks}"
        self.clicks_label.value = f"Clicks: {self.clicks}"

    def left_button_handler(self, index):
        print(f"Left button {index + 1} pressed")

    def right_button_handler(self, index):
        print(f"Right button {index + 1} pressed") 


class TextLoader:

    def __init__(self):
        self.file_input = ptg.InputField("enter .txt file path")
        self.status = ptg.Label("[dim]Ready[/dim]")

        self.save_btn = ptg.Button("[bold]Save[/bold]", lambda *_: self.save_handler())

        ptg.Splitter.set_char("separator", "")

        self.window = ptg.Window(
            "[bold]Load text into flashcards[/bold]",
            "",
            ptg.Splitter(
                ptg.Label(pad_string_with_spaces("File to load", 20)),
                self.file_input,
            ),
            "",
            ptg.Splitter(self.save_btn),
            "",
            self.status,
            "",
            "[dim]S: Save | Ctrl-c: Close[/dim]",
            width=70,
            is_noblur=True,
        ).center()
        self.window.styles.border = ""

        self.window.bind("S", lambda *_: self.save_handler())

    def save_handler(self):
        file_path = self.file_input.value
        self.status.value = "[bold]Loading...[/bold]"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            self.status.value = "[red]File not found"
            return
        except Exception as e:
            self.status.value = f"[red]Error: {e}"
            return

        words = [w.lower() for w in strip_punctuation(content)]
        unique_words = list(set(words))

        session = Session()
        loaded_count = 0
        for word in unique_words:
            if not word or not word.isalpha():
                continue
            if session.query(Card).filter_by(word=word).first():
                continue
            try:
                translation = translate(
                    word,
                    SETTINGS['learning_lang']['code'],
                    SETTINGS['native_lang']['code']
                )
                if translation.lower() == word or len(strip_punctuation(translation)) == 0:
                    self.status.value = f"Skipping '{word}'"
                    continue
                card = Card(
                    word=word,
                    translation=translation,
                    source_lang=SETTINGS['learning_lang']['code'],
                    target_lang=SETTINGS['native_lang']['code']
                )
                session.add(card)
                loaded_count += 1
            except KeyboardInterrupt:
                session.rollback()
                session.close()
                self.status.value = "[red]Interrupted"
                return
            except Exception as e:
                self.status.value = f"[red]Failed: {word} - {e}"
        session.commit()
        session.close()
        self.status.value = f"[green]Loaded {loaded_count} words!"

 
def main() -> None:
    with ptg.WindowManager() as manager:
        game = Game()
        loader = TextLoader()
        manager.add(loader.window)

if __name__ == "__main__":
    sync_settings_to_db()
    main()
