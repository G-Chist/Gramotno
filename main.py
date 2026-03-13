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
left_container = None
right_container = None
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

def make_handler(word: str, container: 'ptg.Container | None', index: int):
    def handler(*args):
        write_word(word)
        if container is not None:
            container.select(index)
    return handler

def update_card_words():
    global all_cards, left_ids, right_ids, words_left, words_right
    
    session = Session()
    all_cards = session.query(Card).all()
    session.close()

    if not all_cards:
        words_left = [pad_string_with_spaces("N/A") for _ in range(5)]
        words_right = [pad_string_with_spaces("N/A") for _ in range(5)]
        left_ids = [None] * 5
        right_ids = [None] * 5
    else:
        selected_cards = random.sample(all_cards, min(5, len(all_cards)))

        left_pairs = [(card.id, card.translation) for card in selected_cards]
        random.shuffle(left_pairs)
        left_ids = [p[0] for p in left_pairs]
        translations_left = [p[1] for p in left_pairs]

        right_pairs = [(card.id, card.word) for card in selected_cards]
        random.shuffle(right_pairs)
        right_ids = [p[0] for p in right_pairs]
        words_right_orig = [p[1] for p in right_pairs]

        words_left = [pad_string_with_spaces(t) for t in translations_left]
        words_right = [pad_string_with_spaces(w) for w in words_right_orig]

    return words_left, words_right, left_ids, right_ids

def make_left_handler(idx: int):
    def handler(*args):
        global selected_left, selected_right
        selected_left = idx
        if left_container:
            left_container.select(idx)
        if selected_right is not None:
            if left_ids[idx] == right_ids[selected_right]:
                STATUS.value = "[green]SUCCESS![/]"
                selected_left = None
                selected_right = None
            else:
                STATUS.value = "[red]Try again![/]"
    return handler

def make_right_handler(idx: int):
    def handler(*args):
        global selected_left, selected_right
        selected_right = idx
        if right_container:
            right_container.select(idx)
        if selected_left is not None:
            if right_ids[idx] == left_ids[selected_left]:
                STATUS.value = "[green]SUCCESS![/]"
                selected_left = None
                selected_right = None
            else:
                STATUS.value = "[red]Try again![/]"
    return handler

def refresh_card_buttons():
    global cards_left, cards_right
    
    cards_left = []
    for i, word_left in enumerate(words_left):
        index_style = f'[{COLORS["left_index"]["foreground"]}]{COLORS["left_index"]["bold"] and "[bold]" or ""}{left_keys[i]}[/bold]'
        word_style = f'{word_left}'
        btn = ptg.Button(f"{index_style}: {word_style}", make_handler(word_left, left_container, i))
        cards_left.append(btn)

    cards_right = []
    for i, word_right in enumerate(words_right):
        index_style = f'[{COLORS["right_index"]["foreground"]}]{COLORS["right_index"]["bold"] and "[bold]" or ""}{right_keys[i]}[/bold]'
        word_style = f'{word_right}'
        btn = ptg.Button(f"{index_style}: {word_style}", make_handler(word_right, right_container, i))
        cards_right.append(btn)

    if left_container:
        for i, btn in enumerate(cards_left):
            left_container.bind(left_keys[i], make_left_handler(i))

    if right_container:
        for i, btn in enumerate(cards_right):
            right_container.bind(right_keys[i], make_right_handler(i))

def rebuild_containers():
    global left_container, right_container
    left_header = ptg.Label(f"[{COLORS['left_header']['foreground']}]{COLORS['left_header']['bold'] and '[bold]' or ''}Native[/bold]\n")
    right_header = ptg.Label(f"[{COLORS['right_header']['foreground']}]{COLORS['right_header']['bold'] and '[bold]' or ''}Learning[/bold]\n")
    left_container = ptg.Container(left_header, "",)
    right_container = ptg.Container(right_header, "",)
    for btn in cards_left:
        left_container += btn
    for btn in cards_right:
        right_container += btn
    left_container += ptg.Label("")
    right_container += ptg.Label("")
    refresh_card_buttons()

def main() -> None:
    global left_keys, right_keys, left_container, right_container, selected_left, selected_right
    
    with ptg.WindowManager() as manager:
        update_card_words()
        
        left_keys = [SETTINGS["left_keys"][f"key_{i}"] for i in range(1, 6)]
        right_keys = [SETTINGS["right_keys"][f"key_{i}"] for i in range(1, 6)]

        selected_left = None
        selected_right = None

        left_header = ptg.Label(f"[{COLORS['left_header']['foreground']}]{COLORS['left_header']['bold'] and '[bold]' or ''}Native[/bold]\n")
        right_header = ptg.Label(f"[{COLORS['right_header']['foreground']}]{COLORS['right_header']['bold'] and '[bold]' or ''}Learning[/bold]\n")
        left_container = ptg.Container(left_header, "",)
        right_container = ptg.Container(right_header, "",)
        
        refresh_card_buttons()
        
        for btn in cards_left:
            left_container += btn
        for btn in cards_right:
            right_container += btn
        left_container += ptg.Label("")
        right_container += ptg.Label("")

        splitter = ptg.Splitter(
            left_container,
            right_container,
        )
        splitter.chars["separator"] = ""

        window = ptg.Window(
            logo_string,
            splitter,
            "",
            STATUS,
            "",
            f"[dim]Press ? to open settings, L to open text loader, Ctrl-c to quit[/dim]",
            "",
            width=int(ptg.terminal.width),
            height=int(ptg.terminal.height*0.8),
            is_noblur=True,
        ).center()
        window.styles.border = ""

        manager.add(window)

        def open_text_loader():
            text_file_input = ptg.InputField(FILE_TO_LOAD)

            def save_text_loader(*args):
                file_path = text_file_input.value
                loading_status.value = "[bold]Loading...[/bold]"

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                words = [w.lower() for w in strip_punctuation(content)]
                unique_words = list(set(words))

                session = Session()
                for word in unique_words:
                    if not word or not word.isalpha():
                        continue
                    if session.query(Card).filter_by(word=word).first():
                        continue
                    try:
                        translation = translate(word, SETTINGS['learning_lang']['code'], SETTINGS['native_lang']['code'])
                        if translation.lower() == word or len(strip_punctuation(translation)) == 0:
                            loading_status.value=f"Skipping '{word}'"
                            continue
                        card = Card(
                            word=word,
                            translation=translation,
                            source_lang=SETTINGS['learning_lang']['code'],
                            target_lang=SETTINGS['native_lang']['code']
                        )
                        session.add(card)
                    except KeyboardInterrupt:
                        session.rollback()
                        session.close()
                        loading_status.value = "[red]Interrupted"
                        return
                    except Exception as e:
                        loading_status.value=f"Failed to translate '{word}': {e}"
                session.commit()
                session.close()
                loading_status.value = f"[green]Loaded {len(unique_words)} words!"
                
                update_card_words()
                refresh_card_buttons()
                rebuild_containers()
                
                manager.remove(text_loader_window)

            save_btn = ptg.Button("[bold]Save[/bold]", save_text_loader)
            cancel_btn = ptg.Button("[dim]Cancel[/dim]", lambda *_: manager.remove(text_loader_window))

            loading_status = ptg.Label("[dim]Ready[/dim]")

            ptg.Splitter.set_char("separator", "")

            text_loader_window = ptg.Window(
                "[bold]Load text into flashcards[/bold]",
                "",
                ptg.Splitter(ptg.Label(pad_string_with_spaces("File to load", 20)), text_file_input),
                "",
                ptg.Splitter(save_btn, cancel_btn),
                "",
                loading_status,
                "",
                "[dim]S: Save | Q: Close[/dim]",
                width=70,
                is_noblur=True,
            ).center()
            
            text_loader_window.styles.border = ""
            
            text_loader_window.bind("Q", lambda *_: manager.remove(text_loader_window))
            text_loader_window.bind("S", lambda *_: save_text_loader())

            manager.add(text_loader_window)

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

            def update_previews(_=None):
                left_idx_preview.value = color_preview(left_idx_input.value)
                right_idx_preview.value = color_preview(right_idx_input.value)
                left_hdr_preview.value = color_preview(left_hdr_input.value)
                right_hdr_preview.value = color_preview(right_hdr_input.value)

            update_btn = ptg.Button("Update Preview", update_previews)

            left_idx_input.bind("enter", update_previews)
            right_idx_input.bind("enter", update_previews)
            left_hdr_input.bind("enter", update_previews)
            right_hdr_input.bind("enter", update_previews)

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
                ptg.Splitter(update_btn, save_btn, cancel_btn),
                "",
                "[dim]U: Update preview | S: Save | Q: Close[/dim]",
                width=70,
                is_noblur=True,
            ).center()
            
            settings_window.styles.border = ""
            
            settings_window.bind("Q", lambda *_: manager.remove(settings_window))
            settings_window.bind("U", lambda *_: update_previews())
            settings_window.bind("S", lambda *_: save_all())
            
            manager.add(settings_window)

        window.bind("?", lambda *_: open_settings())
        window.bind("L", lambda *_: open_text_loader())

if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    sync_settings_to_db()
    main()
