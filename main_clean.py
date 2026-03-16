import pytermgui as ptg
import random
import sys
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

def get_cards_from_db():
    session = Session()
    cards = session.query(Card).all()
    session.close()
    return cards

def get_random_card():
    cards = get_cards_from_db()
    if not cards:
        return "N/A"
    return random.choice(cards)

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

class WordPicker:

    def __init__(self):
        self.cards = []
        self.native_words = []
        self.learning_words = []
        self.five_cards = []

    def get_cards(self):
        self.cards = get_cards_from_db()

    def get_random_card(self):
        if not self.cards:
            self.get_cards()
        if not self.cards:
            return None
        return random.choice(self.cards)

    def get_random_5_cards(self):
        if not self.cards:
            self.get_cards()
        if not self.cards:
            return []
        self.five_cards = random.sample(self.cards, min(5, len(self.cards)))
    
    def fill_native_words(self):
        words = [(card.translation, card.id) for card in self.five_cards]
        random.shuffle(words)
        self.native_words = words

    def fill_learning_words(self):
        words = [(card.word, card.id) for card in self.five_cards]
        random.shuffle(words)
        self.learning_words = words

class Game:

    def __init__(self, return_to_menu=None):
        self.return_to_menu = return_to_menu
        
        self.wordpicker = WordPicker()
        self.wordpicker.get_cards()
        self.wordpicker.get_random_5_cards()
        self.wordpicker.fill_native_words()
        self.wordpicker.fill_learning_words()
       
        self.words_left = [card[0] for card in self.wordpicker.native_words] or []
        self.words_right = [card[0] for card in self.wordpicker.learning_words] or []
        self.ids_left = [card[1] for card in self.wordpicker.native_words] if self.wordpicker.native_words else []
        self.ids_right = [card[1] for card in self.wordpicker.learning_words] if self.wordpicker.learning_words else []
        
        self.selected_left = None
        self.selected_right = None

        has_cards = bool(self.wordpicker.cards)
        
        if not has_cards:
            self.status = ptg.Label("[dim]Please load words![/dim]") 
        else:
            self.status = ptg.Label("[dim]Start matching![/dim]")

        self.left_keys = [SETTINGS['left_keys'][f'key_{i}'] for i in range(1, 6)]
        self.right_keys = [SETTINGS['right_keys'][f'key_{i}'] for i in range(1, 6)]
        
        self.left_buttons = []
        for i in range(len(self.left_keys)):
            word = self.words_left[i] if i < len(self.words_left) else ""
            btn = ptg.Button(pad_string_with_spaces(f"{self.left_keys[i]}) {word}"))
            self.left_buttons.append(btn)

        self.right_buttons = []
        for i, key in enumerate(self.right_keys):
            word = self.words_right[i] if i < len(self.words_right) else ""
            btn = ptg.Button(pad_string_with_spaces(f"{key}) {word}"))
            self.right_buttons.append(btn)

        left_header = ptg.Label(f"[{COLORS['left_header']['foreground']}]{COLORS['left_header']['bold'] and '[bold]' or ''}Native[/bold]\n")
        right_header = ptg.Label(f"[{COLORS['right_header']['foreground']}]{COLORS['right_header']['bold'] and '[bold]' or ''}Learning[/bold]\n")
        
        left_container = ptg.Container(
            left_header,
            "",
            *self.left_buttons,
            "",
        )
        right_container = ptg.Container(
            right_header,
            "",
            *self.right_buttons,
            "",
        )
        
        splitter = ptg.Splitter(
            left_container,
            right_container,
        )
        splitter.chars["separator"] = ""

        self.window = ptg.Window(
            splitter,
            "",
            self.status,
            "",
            "[dim]Q: Quit to menu[/dim]",
            width=int(ptg.terminal.width),
            height=int(ptg.terminal.height*0.8),
            box="ROUNDED",
            is_noblur=True,
        ).center()
        self.window.styles.border = ""

        for i, btn in enumerate(self.left_buttons):
            self.window.bind(self.left_keys[i], lambda *_, idx=i: self.left_button_handler(idx))

        for i, btn in enumerate(self.right_buttons):
            self.window.bind(self.right_keys[i], lambda *_, idx=i: self.right_button_handler(idx))

        self.window.bind("q", lambda *_: self._close())
        self.window.bind("Q", lambda *_: self._close())
        self.window.bind("esc", lambda *_: self._close())

        with open("debug_game.txt", "w") as f:
            f.write("=== Game Initialization Debug ===\n")
            f.write(f"return_to_menu: {self.return_to_menu}\n")
            f.write(f"wordpicker.cards: {self.wordpicker.cards}\n")
            f.write(f"wordpicker.five_cards: {self.wordpicker.five_cards}\n")
            f.write(f"wordpicker.native_words: {self.wordpicker.native_words}\n")
            f.write(f"wordpicker.learning_words: {self.wordpicker.learning_words}\n")
            f.write(f"words_left: {self.words_left}\n")
            f.write(f"words_right: {self.words_right}\n")
            f.write(f"ids_left: {self.ids_left}\n")
            f.write(f"ids_right: {self.ids_right}\n")
            f.write(f"selected_left: {self.selected_left}\n")
            f.write(f"selected_right: {self.selected_right}\n")
            f.write(f"left_keys: {self.left_keys}\n")
            f.write(f"right_keys: {self.right_keys}\n")
            f.write(f"left_buttons: {len(self.left_buttons)}\n")
            f.write(f"right_buttons: {len(self.right_buttons)}\n")
            f.write("===\n")

    def left_button_handler(self, index):
        self.selected_left = self.ids_left[index]

    def right_button_handler(self, index):
        self.selected_right = self.ids_right[index]
        
        if self.selected_left is not None:
            if self.selected_left == self.selected_right:
                self.wordpicker.get_random_5_cards()
                self.wordpicker.fill_native_words()
                self.wordpicker.fill_learning_words()
                self.words_left = [card[0] for card in self.wordpicker.native_words] or []
                self.words_right = [card[0] for card in self.wordpicker.learning_words] or []
                self.ids_left = [card[1] for card in self.wordpicker.native_words] if self.wordpicker.native_words else []
                self.ids_right = [card[1] for card in self.wordpicker.learning_words] if self.wordpicker.learning_words else []
                for i, btn in enumerate(self.left_buttons):
                    btn.label = pad_string_with_spaces(f"{self.left_keys[i]}) {self.words_left[i]}")
                for i, btn in enumerate(self.right_buttons):
                    btn.label = pad_string_with_spaces(f"{self.right_keys[i]}) {self.words_right[i]}")
                self.status.value = "[green]Correct! Cards updated."
                self.selected_left = None
                self.selected_right = None
            else:
                self.status.value = "[red]Incorrect! Try again."
                self.selected_right = None 

    def _close(self):
        if self.return_to_menu:
            self.return_to_menu()


class TextLoader:

    def __init__(self, return_to_menu=None):
        self.return_to_menu = return_to_menu
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
            "[dim]S: Save | Q: Quit to menu[/dim]",
            width=int(ptg.terminal.width),
            box="ROUNDED",
            is_noblur=True,
        ).center()
        self.window.styles.border = ""

        self.window.bind("S", lambda *_: self.save_handler())
        self.window.bind("q", lambda *_: self._close())
        self.window.bind("Q", lambda *_: self._close())

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

    def _close(self):
        if self.return_to_menu:
            self.return_to_menu()

class Settings:

    def __init__(self, return_to_menu=None):
        self.return_to_menu = return_to_menu
        self.native_input = ptg.InputField(SETTINGS['native_lang']['code'])
        self.learning_input = ptg.InputField(SETTINGS['learning_lang']['code'])
        
        self.left_idx_input = ptg.InputField(SETTINGS['left_index']['foreground'])
        self.right_idx_input = ptg.InputField(SETTINGS['right_index']['foreground'])
        self.left_hdr_input = ptg.InputField(SETTINGS['left_header']['foreground'])
        self.right_hdr_input = ptg.InputField(SETTINGS['right_header']['foreground'])

        self.left_idx_preview = ptg.Label(color_preview(SETTINGS['left_index']['foreground']))
        self.right_idx_preview = ptg.Label(color_preview(SETTINGS['right_index']['foreground']))
        self.left_hdr_preview = ptg.Label(color_preview(SETTINGS['left_header']['foreground']))
        self.right_hdr_preview = ptg.Label(color_preview(SETTINGS['right_header']['foreground']))

        self.status = ptg.Label("[dim]See settings/settings.toml for more[/dim]")

        self.update_btn = ptg.Button("Update Preview", lambda *_: self.update_previews())
        self.save_btn = ptg.Button("[bold]Save[/bold]", lambda *_: self.save_handler())

        self.left_idx_input.bind("enter", lambda *_: self.update_previews())
        self.right_idx_input.bind("enter", lambda *_: self.update_previews())
        self.left_hdr_input.bind("enter", lambda *_: self.update_previews())
        self.right_hdr_input.bind("enter", lambda *_: self.update_previews())

        ptg.Splitter.set_char("separator", "")

        self.window = ptg.Window(
            "[bold]Settings[/bold]",
            "",
            ptg.Container("[bold]Languages[/bold]", box="ROUNDED"),
            "",
            ptg.Splitter(ptg.Label(pad_string_with_spaces("Native", 15)), self.native_input),
            ptg.Splitter(ptg.Label(pad_string_with_spaces("Learning", 15)), self.learning_input),
            "",
            ptg.Container("[bold]Colors[/bold]", box="ROUNDED"),
            "",
            ptg.Splitter(ptg.Label(pad_string_with_spaces("Left index", 15)), self.left_idx_input, self.left_idx_preview),
            ptg.Splitter(ptg.Label(pad_string_with_spaces("Right index", 15)), self.right_idx_input, self.right_idx_preview),
            ptg.Splitter(ptg.Label(pad_string_with_spaces("Left header", 15)), self.left_hdr_input, self.left_hdr_preview),
            ptg.Splitter(ptg.Label(pad_string_with_spaces("Right header", 15)), self.right_hdr_input, self.right_hdr_preview),
            "",
            ptg.Splitter(self.update_btn, self.save_btn),
            "",
            self.status,
            "",
            "[dim]U: Update preview | S: Save | Q: Quit to menu[/dim]",
            width=int(ptg.terminal.width),
            box="ROUNDED",
            is_noblur=True,
        ).center()
        
        self.window.styles.border = ""
        
        self.window.bind("U", lambda *_: self.update_previews())
        self.window.bind("S", lambda *_: self.save_handler())
        self.window.bind("q", lambda *_: self._close())
        self.window.bind("Q", lambda *_: self._close())

    def update_previews(self, _=None):
        self.left_idx_preview.value = color_preview(self.left_idx_input.value)
        self.right_idx_preview.value = color_preview(self.right_idx_input.value)
        self.left_hdr_preview.value = color_preview(self.left_hdr_input.value)
        self.right_hdr_preview.value = color_preview(self.right_hdr_input.value)

    def save_handler(self):
        SETTINGS['native_lang']['code'] = self.native_input.value
        SETTINGS['learning_lang']['code'] = self.learning_input.value
        SETTINGS['left_index']['foreground'] = self.left_idx_input.value
        SETTINGS['right_index']['foreground'] = self.right_idx_input.value
        SETTINGS['left_header']['foreground'] = self.left_hdr_input.value
        SETTINGS['right_header']['foreground'] = self.right_hdr_input.value
        save_settings()
        reload_settings()
        self.status.value = "[green]Settings saved!"

    def _close(self):
        if self.return_to_menu:
            self.return_to_menu()

class MainMenu:

    def __init__(self, manager):
        self.manager = manager

        self.game_btn = ptg.Button(f"[bold]P[/bold]{pad_string_with_spaces('lay Game')}")
        self.loader_btn = ptg.Button(f"[bold]T[/bold]{pad_string_with_spaces('ext Loader')}")
        self.settings_btn = ptg.Button(f"[bold]S[/bold]{pad_string_with_spaces('ettings')}")
        self.quit_btn = ptg.Button(f"[bold]Q[/bold]{pad_string_with_spaces('uit')}")

        self.window = ptg.Window(
            logo_string,
            "",
            ptg.Container(
                "[bold]Main Menu[/bold]",
                "",
                self.game_btn,
                self.loader_btn,
                self.settings_btn,
                "",
                self.quit_btn,
                box="ROUNDED",
            ),
            "",
            "[dim]Made by G-Chist[/dim]",
            width=int(ptg.terminal.width),
            height=int(ptg.terminal.height),
            is_noblur=True,
        ).center()
        self.window.styles.border = ""

        self.window.bind("p", lambda *_: self.open_game())
        self.window.bind("P", lambda *_: self.open_game())
        self.window.bind("t", lambda *_: self.open_loader())
        self.window.bind("T", lambda *_: self.open_loader())
        self.window.bind("s", lambda *_: self.open_settings())
        self.window.bind("S", lambda *_: self.open_settings())
        self.window.bind("q", lambda *_: self.quit())
        self.window.bind("Q", lambda *_: self.quit())

    def open_game(self):
        game = Game(return_to_menu=lambda: self._return_to_menu())
        self.manager.add(game.window)

    def open_loader(self):
        loader = TextLoader(return_to_menu=lambda: self._return_to_menu())
        self.manager.add(loader.window)

    def open_settings(self):
        settings = Settings(return_to_menu=lambda: self._return_to_menu())
        self.manager.add(settings.window)

    def quit(self):
        sys.exit(0)

    def _return_to_menu(self):
        for window in list(self.manager._windows):
            if window != self.window:
                self.manager.remove(window)
        self.window.focus()
  
def main() -> None:
    with ptg.WindowManager() as manager:
        menu = MainMenu(manager)
        manager.add(menu.window)
        menu.window.focus()

if __name__ == "__main__":
    sync_settings_to_db()
    main()
