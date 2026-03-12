import pytermgui as ptg
import random
import os
import tomli as tomllib
import tomli_w as tomlwrite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.schema import Base, UserSettings

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

engine = create_engine('sqlite:///evolving_cards.db')
Session = sessionmaker(bind=engine)

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

GOOFY_WORDS = [
    "chud", "huzz", "chopped", "clavicular", "mogging", "piss", "them", "polycule", "goy", "chad"
]

OUTPUT_FILE = "words.txt"

def pad_string_with_spaces(string: str, max_len: int = 20) -> str:
    return string + " " * (max_len - len(string)) 

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def invert_color(r: int, g: int, b: int) -> tuple[int, int, int]:
    return (255 - r, 255 - g, 255 - b)

def color_preview(hex_color: str, text: str = "Preview") -> str:
    r, g, b = hex_to_rgb(hex_color)
    ir, ig, ib = invert_color(r, g, b)
    return f"[{ir};{ig};{ib} @{r};{g};{b}]{text}[/]"

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
            "",
            f"[dim]Press ? to open settings[/dim]",
            "",
            width=int(ptg.terminal.width),
            height=int(ptg.terminal.height*0.8),
            is_noblur=True,
        ).center()
        window.styles.border = ""

        manager.add(window)

        def open_settings():
            native_input = ptg.InputField(SETTINGS['native_lang']['code'])
            learning_input = ptg.InputField(SETTINGS['learning_lang']['code'])
            
            left_idx_input = ptg.InputField(SETTINGS['left_index']['foreground'])
            right_idx_input = ptg.InputField(SETTINGS['right_index']['foreground'])
            left_hdr_input = ptg.InputField(SETTINGS['left_header']['foreground'])
            right_hdr_input = ptg.InputField(SETTINGS['right_header']['foreground'])

            left_idx_preview = ptg.Label(color_preview(SETTINGS['left_index']['foreground']))
            right_idx_preview = ptg.Label(color_preview(SETTINGS['right_index']['foreground']))
            left_hdr_preview = ptg.Label(color_preview(SETTINGS['left_header']['foreground']))
            right_hdr_preview = ptg.Label(color_preview(SETTINGS['right_header']['foreground']))

            def update_previews(*args):
                left_idx_preview.value = color_preview(left_idx_input.value)
                right_idx_preview.value = color_preview(right_idx_input.value)
                left_hdr_preview.value = color_preview(left_hdr_input.value)
                right_hdr_preview.value = color_preview(right_hdr_input.value)

            left_idx_input.bind("any", update_previews)
            right_idx_input.bind("any", update_previews)
            left_hdr_input.bind("any", update_previews)
            right_hdr_input.bind("any", update_previews)

            def save_all(*args):
                SETTINGS['native_lang']['code'] = native_input.value
                SETTINGS['learning_lang']['code'] = learning_input.value
                SETTINGS['left_index']['foreground'] = left_idx_input.value
                SETTINGS['right_index']['foreground'] = right_idx_input.value
                SETTINGS['left_header']['foreground'] = left_hdr_input.value
                SETTINGS['right_header']['foreground'] = right_hdr_input.value
                save_settings()
                reload_settings()
                manager.remove(settings_window)

            save_btn = ptg.Button("[bold]Save[/bold]", save_all)
            cancel_btn = ptg.Button("[dim]Cancel[/dim]", lambda *_: manager.remove(settings_window))

            ptg.Splitter.set_char("separator", "")

            settings_window = ptg.Window(
                "[bold]Settings[/bold]",
                "",
                ptg.Container("[bold]Languages[/bold]", box="EMPTY"),
                "",
                ptg.Splitter(ptg.Label(pad_string_with_spaces("Native", 15)), native_input),
                ptg.Splitter(ptg.Label(pad_string_with_spaces("Learning", 15)), learning_input),
                "",
                ptg.Container("[bold]Colors[/bold]", box="EMPTY"),
                "",
                ptg.Splitter(ptg.Label(pad_string_with_spaces("Left index", 15)), left_idx_input, left_idx_preview),
                ptg.Splitter(ptg.Label(pad_string_with_spaces("Right index", 15)), right_idx_input, right_idx_preview),
                ptg.Splitter(ptg.Label(pad_string_with_spaces("Left header", 15)), left_hdr_input, left_hdr_preview),
                ptg.Splitter(ptg.Label(pad_string_with_spaces("Right header", 15)), right_hdr_input, right_hdr_preview),
                "",
                ptg.Splitter(save_btn, cancel_btn),
                "",
                "[dim]Press Q to close[/dim]",
                width=70,
                is_noblur=True,
            ).center()
            
            settings_window.styles.border = ""
            
            settings_window.bind("Q", lambda *_: manager.remove(settings_window))
            
            manager.add(settings_window)

        window.bind("?", lambda *_: open_settings())


if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    sync_settings_to_db()
    main()
