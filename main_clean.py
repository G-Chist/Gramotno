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

STATUS = ptg.Label("[dim]Please load words![/dim]")

FILE_TO_LOAD = "enter .txt file path"

engine = create_engine('sqlite:///evolving_cards.db')
Session = sessionmaker(bind=engine)

OUTPUT_FILE = "words.txt"

all_cards = []
left_ids = []
right_ids = []
words_left = []
words_right = []
left_keys = []
right_keys = []
cards_left = []
cards_right = []
selected_left = None
selected_right = None

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
        self.clicks = 0
        self.clicks_label = ptg.Label(f"Clicks: {self.clicks}")
        self.button = ptg.Button(f"Click me!", lambda *_: self.button_handler()) 
        
        left_header = ptg.Label(f"[{COLORS['left_header']['foreground']}]{COLORS['left_header']['bold'] and '[bold]' or ''}Native[/bold]\n")
        right_header = ptg.Label(f"[{COLORS['right_header']['foreground']}]{COLORS['right_header']['bold'] and '[bold]' or ''}Learning[/bold]\n")
        
        left_container = ptg.Container(
            left_header,
            "",
            STATUS,
            "",
            get_random_word(),
        )
        right_container = ptg.Container(
            right_header,
            "",
            self.button,
            "",
            self.clicks_label,
        )
        
        splitter = ptg.Splitter(
            left_container,
            right_container,
        )
        splitter.chars["separator"] = ""
        
        self.window = ptg.Window(
            logo_string,
            "",
            splitter,
            "",
            width=int(ptg.terminal.width),
            height=int(ptg.terminal.height*0.8),
            is_noblur=True,
        ).center()
        self.window.styles.border = ""
        
        right_container.bind("1", lambda *_: self.button_handler())

    def button_handler(self):
        self.clicks += 1
        self.button.label = f"Dude {self.clicks}"
        self.clicks_label.value = f"Clicks: {self.clicks}" 
 
def main() -> None:
    with ptg.WindowManager() as manager:
        game = Game()
        manager.add(game.window)

if __name__ == "__main__":
    sync_settings_to_db()
    main()
