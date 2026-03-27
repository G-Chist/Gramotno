"""
Gramotno - Interactive Language Learning Card Game

This module is the main entry point for the flashcard application. It provides
interfaces for loading words from text files, matching words between languages,
and configuring application settings.

Key Components:
- WordPicker: Handles card selection and filtering logic
- Game: The main gameplay loop for matching words
- TextLoader: Loads and parses text files to create flashcards
- Settings: UI for configuring language and color preferences
- MainMenu: Primary navigation interface

The application persists data in a SQLite database (evolving_cards.db) and uses
TOML configuration files for settings management.
"""

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
from game.stats import GameStats

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
    """
    Synchronizes the settings from the TOML configuration file to the database.
    
    This function reads the current settings from the SETTINGS global variable
    (loaded from settings.toml) and persists them to the UserSettings table
    in the database. If no settings exist in the database, it creates a new
    entry. If settings already exist, it updates them with the current values.
    
    The function handles both the native language and learning language settings,
    defaulting to English ('en') and Turkish ('tr') respectively if not specified
    in the configuration.
    
    Note: This function commits changes to the database and closes the session.
    """
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
    """
    Saves the current settings to both the TOML file and the database.
    
    This function serializes the SETTINGS global variable to the settings.toml
    file in the settings directory using the TOML format. After writing the file,
    it also synchronizes the settings to the database by calling sync_settings_to_db().
    
    This two-step process ensures that the configuration persists both in the
    human-readable configuration file and in the application database, allowing
    the application to restore settings even if the file format changes in future
    versions.
    
    Raises:
        IOError: If the settings file cannot be written.
    """
    with open("settings/settings.toml", "wb") as f:
        tomlwrite.dump(SETTINGS, f)
    sync_settings_to_db()


def reload_settings():
    """
    Reloads the settings from the TOML configuration file into memory.
    
    This function reads the settings.toml file from the settings directory
    and updates the global SETTINGS and COLORS variables with the new values.
    This is useful when the settings file has been modified externally or
    after a save operation to ensure the in-memory representation matches
    the persisted configuration.
    
    Note: This function modifies global variables and does not return any value.
    """
    global SETTINGS, COLORS
    with open("settings/settings.toml", "rb") as f:
        SETTINGS = tomllib.load(f)
    COLORS = SETTINGS


def get_cards_from_db():
    """
    Retrieves all flashcards from the database.
    
    This function queries the Card table and returns a list of all card objects
    currently stored in the database. Each card represents a word or phrase
    that the user is learning, including its translation and associated metadata.
    
    Returns:
        list: A list of Card objects representing all flashcards in the database.
              Returns an empty list if no cards exist.
    
    Note: The session is closed after the query to release database resources.
    """
    session = Session()
    cards = session.query(Card).all()
    session.close()
    return cards


def get_random_card():
    """
    Selects a random flashcard from the database.
    
    This function retrieves all cards from the database and returns a single
    random card. This is primarily used for displaying a single word or phrase,
    such as in promotional displays or quick practice sessions.
    
    Returns:
        Card: A randomly selected Card object from the database.
        str: Returns "N/A" if no cards exist in the database.
    
    Note: Uses Python's random.choice() for selection, which provides uniform
          randomness across all available cards.
    """
    cards = get_cards_from_db()
    if not cards:
        return "N/A"
    return random.choice(cards)

def pad_string_with_spaces(string: str, max_len: int = 20) -> str:
    """
    Pads a string with trailing spaces to reach a specified maximum length.
    
    This utility function ensures that text displays consistently by adding
    spaces to the end of strings that are shorter than the specified maximum.
    Used for terminal-based UIs where alignment of
    columns and buttons matters.
    
    Args:
        string: The input string to pad.
        max_len: The desired length after padding. Defaults to 20 characters.
    
    Returns:
        str: The padded string, or the original string if it exceeds max_len.
    
    Example:
        >>> pad_string_with_spaces("hello", 10)
        'hello     '
    """
    return string + " " * (max_len - len(string))


def hex_to_rgb(hex_color: str):
    """
    Converts a hexadecimal color code to RGB tuple values.
    
    This function parses a hex color string (with or without the '#' prefix)
    and returns the corresponding red, green, and blue component values as
    integers in the range 0-255.
    
    Args:
        hex_color: A string representing the hexadecimal color code.
                   Can optionally include the '#' prefix.
    
    Returns:
        tuple: A three-element tuple of integers (r, g, b) representing
               the RGB components of the color.
    
    Example:
        >>> hex_to_rgb("#FF0000")
        (255, 0, 0)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def invert_color(r: int, g: int, b: int):
    """
    Inverts an RGB color by subtracting each component from 255.
    
    This function calculates the inverse of a color, which can be used for
    creating text colors that contrast with a given background color.
    By inverting each RGB component, we get a color that will be visible
    on backgrounds of the original color.
    
    Args:
        r: The red component (0-255).
        g: The green component (0-255).
        b: The blue component (0-255).
    
    Returns:
        tuple: A three-element tuple (r, g, b) representing the inverted color.
    
    Example:
        >>> invert_color(255, 0, 0)
        (0, 255, 255)
    """
    return (255 - r, 255 - g, 255 - b)


def color_preview(hex_color: str, text: str = "Preview") -> str:
    """
    Creates a colored preview string for terminal display.
    
    This function generates a pytermgui-compatible markup string that
    displays the given text with the specified background color. This
    is used in the settings UI to show users how their color choices
    will appear in the application.
    
    Args:
        hex_color: The hexadecimal color code for the background.
        text: The text to display with the color. Defaults to "Preview".
    
    Returns:
        str: A pytermgui markup string that renders the colored preview.
    
    Example:
        >>> color_preview("#FF0000", "Sample")
        '[0;0;255 @255;0;0]Sample[/]'
    """
    r, g, b = hex_to_rgb(hex_color)
    ir, ig, ib = invert_color(r, g, b)
    return f"[{ir};{ig};{ib} @{r};{g};{b}]{text}[/]"


def write_word(word: str) -> None:
    """
    Appends a word to the output file for logging purposes.
    
    This function opens the output file in append mode and writes the
    given word followed by a newline character. This is used to track
    or log words that have been processed or reviewed during a session.
    
    Args:
        word: The word to write to the output file.
    
    Note:
        The output file path is defined by the global OUTPUT_FILE variable.
        The file is opened in append mode, so existing content is preserved.
    """
    with open(OUTPUT_FILE, "a") as f:
        f.write(word + "\n")

class WordPicker:
    """
    A class responsible for selecting and managing flashcards for the learning game.
    
    The WordPicker acts as the bridge between the database of flashcards and the
    game interface. It handles three main responsibilities:
    
    1. Basic card retrieval: Loading cards from the database for random selection
    2. Card organization: Preparing word lists for both the native and learning languages
    3. Spaced repetition: Implementing algorithms to prioritize cards based on
       user performance statistics
    
    The class maintains several internal state variables:
    - cards: All available cards from the database
    - five_cards: The current set of 5 cards being used in the game
    - native_words: Shuffled list of translations for the current cards
    - learning_words: Shuffled list of words being learned
    
    The selection methods include:
    - Random card selection for basic gameplay
    - Priority-based selection using performance metrics from the database
    - Cards can be sorted by success rate, error count, response time, or a combination
    """

    def __init__(self):
        """
        Initializes a new WordPicker instance with empty card collections.
        
        The constructor initializes all internal lists to empty states.
        Cards must be loaded explicitly by calling get_cards() or one of
        the selection methods that automatically load cards if needed.
        """
        self.cards = []
        self.native_words = []
        self.learning_words = []
        self.five_cards = []

    def get_cards(self):
        """
        Loads all flashcards from the database into the internal cards list.
        
        This method queries the database for all Card records and stores them
        in the self.cards attribute. After calling this method, the WordPicker
        has access to all available flashcards for selection operations.
        
        Note:
            This does not populate five_cards, native_words, or learning_words.
            Those must be populated separately using the appropriate methods.
        """
        self.cards = get_cards_from_db()

    def get_random_card(self):
        """
        Returns a single randomly selected card from the available cards.
        
        If no cards have been loaded yet, this method first loads all cards
        from the database. If no cards exist in the database, returns None.
        
        Returns:
            Card: A randomly selected Card object, or None if no cards exist.
        """
        if not self.cards:
            self.get_cards()
        if not self.cards:
            return None
        return random.choice(self.cards)

    def get_random_5_cards(self):
        """
        Selects a random sample of 5 cards for the current game round.
        
        If no cards have been loaded yet, this method first loads all cards
        from the database. If fewer than 5 cards exist, returns all available
        cards (up to 5). The selected cards are stored in the five_cards
        attribute for use in subsequent operations.
        
        Returns:
            list: A list of up to 5 Card objects randomly selected from
                  the available cards. Returns empty list if no cards exist.
        """
        if not self.cards:
            self.get_cards()
        if not self.cards:
            return []
        self.five_cards = random.sample(self.cards, min(5, len(self.cards)))

    def fill_native_words(self):
        """
        Populates the native_words list with shuffled translations from five_cards.
        
        This method extracts the translation (the native language word) and
        database ID from each card in five_cards, then shuffles them randomly.
        The resulting list is stored in native_words and used to populate
        the left side of the game interface.
        
        The output format is a list of tuples: (translation_string, card_id)
        
        Note:
            This method expects five_cards to be populated. If empty, the
            result will be an empty list.
        """
        words = [(card.translation, card.id) for card in self.five_cards]
        random.shuffle(words)
        self.native_words = words

    def fill_learning_words(self):
        """
        Populates the learning_words list with shuffled words from five_cards.
        
        This method extracts the word (in the learning language) and database
        ID from each card in five_cards, then shuffles them randomly. The
        resulting list is stored in learning_words and used to populate the
        right side of the game interface.
        
        The output format is a list of tuples: (word_string, card_id)
        
        Note:
            This method expects five_cards to be populated. If empty, the
            result will be an empty list.
        """
        words = [(card.word, card.id) for card in self.five_cards]
        random.shuffle(words)
        self.learning_words = words

    def _get_cards_with_progress(self):
        """
        Internal method that retrieves cards along with their progress statistics.
        
        This method queries both the Card and Progress tables from the database
        and creates a mapping of card IDs to their progress records. This is
        used by the spaced repetition methods to make decisions about card
        prioritization based on user performance.
        
        Returns:
            tuple: A two-element tuple containing:
                - list: All Card objects from the database
                - dict: A mapping of card_id -> Progress object
        
        Note:
            This is an internal method (prefixed with underscore) as it handles
            database operations and returns raw data that requires further
            processing by the public methods.
        """
        session = Session()
        cards = session.query(Card).all()
        card_ids = [c.id for c in cards]
        progress_records = session.query(Progress).filter(Progress.card_id.in_(card_ids)).all()
        progress_map = {p.card_id: p for p in progress_records}
        session.close()
        return cards, progress_map

    def get_worst_cards_by_success_rate(self, n=5):
        """
        Returns the n cards with the lowest success rates, prioritizing never-played cards.
        
        This method implements a spaced repetition algorithm that prioritizes:
        1. Cards that have never been played (no progress record) - highest priority
        2. Cards with the lowest ratio of correct answers to total attempts
        
        The sorting uses a tuple key (priority, success_rate) where:
        - Priority 0 = never played (sorted first)
        - Priority 1 = has been played (sorted by success rate ascending)
        
        Args:
            n: The number of cards to return. Defaults to 5.
        
        Returns:
            list: A list of up to n Card objects sorted by worst performance first.
        
        Example:
            If you have cards with success rates [0.8, 0.2, 0.5] and some never played,
            the output would be: [never_played, 0.2, 0.5, 0.8] (up to n cards)
        """
        cards, progress_map = self._get_cards_with_progress()
        scored_cards = []
        for card in cards:
            progress = progress_map.get(card.id)
            if progress is None:
                scored_cards.append((card, (0, 0.0)))
            elif progress.total_attempts and progress.total_attempts > 0:
                success_rate = progress.correct_count / progress.total_attempts
                scored_cards.append((card, (1, success_rate)))
            else:
                scored_cards.append((card, (0, 0.0)))
        scored_cards.sort(key=lambda x: x[1])
        return [c[0] for c in scored_cards[:n]]

    def get_worst_cards_by_errors(self, n=5):
        """
        Returns the n cards with the most incorrect answers.
        
        This method prioritizes cards that users have gotten wrong most frequently.
        Cards without any progress records (never played) are given infinite
        error counts, placing them first. This also places cards without
        progress at the top of the list.
        
        Args:
            n: The number of cards to return. Defaults to 5.
        
        Returns:
            list: A list of up to n Card objects sorted by highest error count first.
        
        Note:
            Cards with no progress (never played) will always appear before
            cards that have been played, regardless of their error counts.
        """
        cards, progress_map = self._get_cards_with_progress()
        scored_cards = []
        for card in cards:
            progress = progress_map.get(card.id)
            if progress is None:
                error_count = float('inf')
            else:
                error_count = progress.incorrect_count
            scored_cards.append((card, error_count))
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored_cards[:n]]

    def get_worst_cards_by_response_time(self, n=5):
        """
        Returns the n cards with the slowest average response times.
        
        This method prioritizes cards where users take the longest to answer,
        which may indicate difficulty or unfamiliarity with the material.
        Cards without response time data (never played or no recorded times)
        are given infinite time, placing them first.
        
        Args:
            n: The number of cards to return. Defaults to 5.
        
        Returns:
            list: A list of up to n Card objects sorted by slowest response time first.
        
        Note:
            Response time is measured in milliseconds. Cards without recorded
            times are given infinite time, placing them first.
        """
        cards, progress_map = self._get_cards_with_progress()
        scored_cards = []
        for card in cards:
            progress = progress_map.get(card.id)
            if progress is None:
                avg_time = float('inf')
            elif progress.avg_response_time_ms is not None:
                avg_time = progress.avg_response_time_ms
            else:
                avg_time = float('inf')
            scored_cards.append((card, avg_time))
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored_cards[:n]]

    def get_worst_cards_combined(self, n=5):
        """
        Returns the n worst cards using a weighted combination of all metrics.
        
        This method implements a comprehensive spaced repetition algorithm that
        combines multiple performance indicators into a single score:
        - Error count: Number of incorrect answers (higher = worse)
        - Success rate: Ratio of correct to total attempts (lower = worse)
        - Response time: Average time to answer in ms (slower = worse)
        
        The combined score formula is:
        score = errors + (1 - success_rate) * 10 + (avg_time_ms / 1000)
        
        Cards with no progress records receive infinite scores to ensure
        they are prioritized for learning.
        
        Args:
            n: The number of cards to return. Defaults to 5.
        
        Returns:
            list: A list of up to n Card objects sorted by worst combined score.
        
        Note:
            This is the most comprehensive way to select cards for practice,
            as it considers all aspects of user performance.
        """
        cards, progress_map = self._get_cards_with_progress()
        scored_cards = []
        for card in cards:
            progress = progress_map.get(card.id)
            if progress is None:
                score = float('inf')
            elif progress.total_attempts and progress.total_attempts > 0:
                success_rate = progress.correct_count / progress.total_attempts
                error_count = progress.incorrect_count
                avg_time = progress.avg_response_time_ms if progress.avg_response_time_ms is not None else 0
                score = error_count + (1 - success_rate) * 10 + (avg_time / 1000)
            else:
                score = float('inf')
            scored_cards.append((card, score))
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored_cards[:n]]

    def get_worst_5_cards(self):
        """
        Convenience method that retrieves the 5 worst cards using combined scoring.
        
        This is a shorthand method that calls get_worst_cards_combined(5) and
        stores the result in both the five_cards attribute and returns it.
        
        Returns:
            list: A list of 5 Card objects selected by combined worst performance.
        
        Side effect:
            Sets self.five_cards to the returned list of cards.
        """
        self.five_cards = self.get_worst_cards_combined(5)
        return self.five_cards

class Game:
    """
    The main game interface where users match words between languages.
    
    This class manages the interactive flashcard matching game where users
    see words in their native language on the left side and words in the
    language they're learning on the right side. The goal is to correctly
    match pairs of related words.
    
    Game Flow:
    1. Initialize with 5 random cards from the database
    2. Display native words on left, learning words on right (both shuffled)
    3. User selects a word from each side using keyboard shortcuts
    4. If selections match (same card ID), record success and get new cards
    5. If selections don't match, record failure and prompt to try again
    
    Key Features:
    - Timer tracking: Starts when user selects a left-side word
    - Progress tracking: Records correct/incorrect answers in database
    - Dynamic updates: Refreshes card sets after each correct match
    - Debug output: Writes game state to debug_game.txt on init
    
    The class uses the WordPicker to manage card selection, with options for
    random selection or spaced-repetition-based selection through the
    get_worst_5_cards method.
    """

    def __init__(self, return_to_menu=None):
        """
        Initializes a new game session with random cards and UI setup.
        
        Args:
            return_to_menu: Optional callback function that returns to the
                           main menu. If provided, the game will show a menu
                           option to quit back to the main screen.
        
        The constructor performs several initialization steps:
        1. Creates a WordPicker and loads 5 random cards
        2. Prepares shuffled word lists for both language sides
        3. Initializes game statistics tracking
        4. Creates the pytermgui UI with buttons and status display
        5. Binds keyboard shortcuts for word selection and navigation
        6. Writes debug information to debug_game.txt
        
        The game window is centered on the terminal and uses a rounded box
        style for visual appeal.
        """
        self.return_to_menu = return_to_menu
        
        self.wordpicker = WordPicker()
        self.wordpicker.get_cards()
        self.wordpicker.get_worst_5_cards()
        self.wordpicker.fill_native_words()
        self.wordpicker.fill_learning_words()
       
        self.words_left = [card[0] for card in self.wordpicker.native_words] or []
        self.words_right = [card[0] for card in self.wordpicker.learning_words] or []
        self.ids_left = [card[1] for card in self.wordpicker.native_words] if self.wordpicker.native_words else []
        self.ids_right = [card[1] for card in self.wordpicker.learning_words] if self.wordpicker.learning_words else []
        
        self.selected_left = None
        self.selected_right = None

        self.stats = GameStats()
        self.stats.load_from_db(Session())

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
        """
        Handles user selection of a word from the left (native language) side.
        
        This method is called when the user presses a key corresponding to
        one of the native language words displayed on the left side of the
        game interface. It records which card was selected and starts a
        timer to track how long the user takes to make their selection.
        
        Args:
            index: The index of the selected button (0-4) corresponding to
                   the position in the left_buttons list.
        
        Side effects:
            - Sets self.selected_left to the card ID of the chosen word
            - Starts a timer in self.stats for response time tracking
        """
        self.selected_left = self.ids_left[index]
        self.stats.start_card_timer(self.selected_left)

    def right_button_handler(self, index):
        """
        Handles user selection of a word from the right (learning language) side.
        
        This method is called when the user presses a key corresponding to
        one of the learning language words displayed on the right side. If
        a left-side word has already been selected, this performs the match
        check to determine if the two selections correspond to the same card.
        
        Matching logic:
        - If both sides select the same card ID: Correct match! Load new cards
        - If different card IDs selected: Incorrect match, record failure
        
        Args:
            index: The index of the selected button (0-4) corresponding to
                   the position in the right_buttons list.
        
        Side effects:
            - May update self.selected_right
            - May call self.stats.record_result() to save the outcome
            - May refresh the card display with new words
            - Updates self.status with result message (green/red)
        """
        self.selected_right = self.ids_right[index]
        
        if self.selected_left is not None:
            if self.selected_left == self.selected_right:
                self.stats.record_result(self.selected_left, correct=True)
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
                self.stats.record_result(self.selected_left, correct=False)
                self.status.value = "[red]Incorrect! Try again."
                self.selected_right = None 

    def _close(self):
        """
        Closes the game and returns to the main menu (or exits).
        
        This method is called when the user presses Q, q, or ESC to exit
        the game. It performs cleanup by persisting any accumulated game
        statistics to the database, then either returns to the main menu
        if a callback was provided, or does nothing if this was the main
        view.
        
        The statistics are saved because they track user progress and are
        used by the WordPicker selection methods to order cards.
        
        Side effects:
            - Calls self.stats.persist_to_db() to save progress
            - May call self.return_to_menu() if callback was provided
        """
        self.stats.persist_to_db(Session())
        if self.return_to_menu:
            self.return_to_menu()


class TextLoader:
    """
    A text file loader interface for importing flashcards into the database.
    
    This class provides a UI for users to load text files containing words
    in the language they're learning. The loader processes the text, extracts
    unique words, translates them to the user's native language, and creates
    new flashcards in the database.
    
    Processing Pipeline:
    1. Read the file content as text
    2. Strip punctuation and normalize to lowercase
    3. Extract unique words (removing duplicates)
    4. Filter out non-alphabetic entries
    5. Skip words already in the database
    6. Translate each word using the language service
    7. Create and save new Card records
    
    The UI displays progress through the status label, showing the number
    of words successfully loaded, or error messages if something goes wrong.
    """

    def __init__(self, return_to_menu=None):
        """
        Initializes the text loader interface with input field and buttons.
        
        Args:
            return_to_menu: Optional callback function to return to main menu
                            after closing this interface.
        
        Creates:
            - An input field for entering the file path
            - A status label showing current state or results
            - A Save button to trigger the file loading process
            - A pytermgui Window with keyboard bindings
        
        Key bindings:
            - S: Trigger the save_handler to load the file
            - q/Q: Close and return to menu
        """
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
        """
        Processes the input file and creates flashcards from the text content.
        
        This method performs the core functionality of the TextLoader class:
        reading a file, processing its contents, translating words, and saving
        them to the database as flashcards.
        
        Processing steps:
        1. Opens and reads the specified file (UTF-8 encoding)
        2. Strips punctuation from content and converts to lowercase
        3. Extracts unique words (set eliminates duplicates)
        4. Filters out empty strings and non-alphabetic entries
        5. Skips words already present in the database
        6. Translates each word using the configured language service
        7. Validates that translation differs from the original word
        8. Creates Card records and adds them to the database
        9. Commits all changes and reports the count of loaded words
        
        The status label updates throughout the process to show:
        - "Loading..." at the start
        - "Skipping 'word'" for invalid translations
        - "Failed: word - error" for translation errors
        - "Loaded N words!" on successful completion
        
        The method handles KeyboardInterrupt gracefully, rolling back any
        partial changes and closing the session properly.
        
        Note:
            Uses the global SETTINGS to determine source and target languages
            for translation. The translation service is called from the
            language_utils module.
        """
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
        """
        Closes the text loader interface and returns to the main menu.
        
        This method is called when the user presses Q or q to exit the
        text loader screen. If a return_to_menu callback was provided
        during initialization, it is called to navigate back to the
        main menu.
        
        Side effects:
            - May call self.return_to_menu() if callback was provided
        """
        if self.return_to_menu:
            self.return_to_menu()


class Settings:
    """
    A settings configuration interface for customizing the application.
    
    This class provides a UI for users to modify application settings
    including language preferences and color schemes for the interface.
    
    Configurable Options:
    - Native language code (e.g., 'en' for English)
    - Learning language code (e.g., 'tr' for Turkish)
    - Color for left-side indices (native language)
    - Color for right-side indices (learning language)
    - Color for left header
    - Color for right header
    
    The interface includes live color previews that show how the chosen
    colors will appear in the actual application interface. Users can
    update previews without saving, then save when satisfied with the
    look.
    
    Settings are persisted to both the TOML configuration file and the
    database so they're available to other parts of the application.
    """

    def __init__(self, return_to_menu=None):
        """
        Initializes the settings interface with input fields and previews.
        
        Args:
            return_to_menu: Optional callback function to return to main menu.
        
        Creates input fields populated with current settings from the global
        SETTINGS variable. For colors, creates preview labels showing the
        actual color appearance.
        
        Key bindings:
            - Enter: Update previews when pressed in any input field
            - U: Update previews manually
            - S: Save settings to file and database
            - q/Q: Close and return to menu
        """
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
        """
        Updates the color preview labels to match the current input values.
        
        This method is called when the user wants to see how their chosen
        colors will actually appear in the application interface. It reads
        the hex color codes from each input field and generates preview
        labels using the color_preview utility function.
        
        The preview shows the inverted color (for text) on the original
        color (for background), giving users an accurate representation
        of their color choices.
        
        Args:
            _: Unused parameter that accepts optional argument from bound keys.
        
        Side effects:
            - Updates the value property of all four preview labels
        """
        self.left_idx_preview.value = color_preview(self.left_idx_input.value)
        self.right_idx_preview.value = color_preview(self.right_idx_input.value)
        self.left_hdr_preview.value = color_preview(self.left_hdr_input.value)
        self.right_hdr_preview.value = color_preview(self.right_hdr_input.value)

    def save_handler(self):
        """
        Saves the current settings to file and database, then reloads them.
        
        This method updates the global SETTINGS dictionary with the current
        values from all input fields, then persists those changes by calling:
        1. save_settings() - writes to TOML file and database
        2. reload_settings() - reloads from file to ensure in-memory state matches
        
        After saving, updates the status label to confirm success to the user.
        
        Side effects:
            - Updates global SETTINGS dictionary
            - Writes settings to settings/settings.toml file
            - Updates UserSettings table in database
            - Updates status label with success message
        """
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
        """
        Closes the settings interface and returns to the main menu.
        
        This method is called when the user presses Q or q to exit the
        settings screen. If a return_to_menu callback was provided
        during initialization, it is called to navigate back to the
        main menu.
        
        Side effects:
            - May call self.return_to_menu() if callback was provided
        """
        if self.return_to_menu:
            self.return_to_menu()


class MainMenu:
    """
    The main navigation menu that provides access to all application features.
    
    This class creates the primary user interface that users see when they
    first launch the application. It presents a menu with options to:
    - Start the matching game (P)
    - Open the text file loader (T)
    - Access settings configuration (S)
    - Quit the application (Q)
    
    The menu displays the application logo and uses keyboard shortcuts
    for navigation. Each option opens its respective interface within
    the window manager, allowing users to seamlessly transition between
    different parts of the application.
    
    Key Features:
    - Keyboard-driven navigation (no mouse required)
    - Central hub for all application functions
    - Handles window management transitions
    - Clean exit handling for the application
    """

    def __init__(self, manager):
        """
        Initializes the main menu with buttons and keyboard bindings.
        
        Args:
            manager: A pytermgui WindowManager instance that handles
                     the creation and removal of application windows.
        
        Creates:
            - Four buttons: Play Game, Text Loader, Settings, Quit
            - A Window with the application logo and button container
            - Keyboard bindings for each menu option
        
        The logo is displayed using a pre-defined ASCII art string that
        shows when the application starts. After the logo, the menu
        presents options in a rounded container box.
        
        Key bindings:
            - P: Open the game interface
            - T: Open the text loader
            - S: Open settings
            - Q: Exit the application
        """
        self.manager = manager

        self.game_btn = ptg.Button(f"[bold]P[/bold]{pad_string_with_spaces('lay Game')}")
        self.loader_btn = ptg.Button(f"[bold]T[/bold]{pad_string_with_spaces('ext Loader')}")
        self.settings_btn = ptg.Button(f"[bold]S[/bold]{pad_string_with_spaces('ettings')}")
        self.help_btn = ptg.Button(f"[bold]H[/bold]{pad_string_with_spaces('elp')}")
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
                self.help_btn,
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
        self.window.bind("?", lambda *_: self.open_help())
        self.window.bind("h", lambda *_: self.open_help())
        self.window.bind("H", lambda *_: self.open_help())
        self.window.bind("q", lambda *_: self.quit())
        self.window.bind("Q", lambda *_: self.quit())

    def open_game(self):
        """
        Opens the flashcard matching game interface.
        
        This method creates a new Game instance with a callback that returns
        to the main menu when the game is closed. The game window is then
        added to the window manager, which displays it to the user.
        
        The callback ensures that when the user exits the game (by pressing
        Q), they return to the main menu rather than having the application
        close entirely.
        
        Side effects:
            - Creates a new Game instance
            - Adds the game window to the window manager
        """
        game = Game(return_to_menu=lambda: self._return_to_menu())
        self.manager.add(game.window)

    def open_loader(self):
        """
        Opens the text file loader interface.
        
        This method creates a new TextLoader instance with a callback that
        returns to the main menu when closed. The loader window is added
        to the window manager for display.
        
        Users can use this to import new vocabulary from text files to
        create flashcards for the learning game.
        
        Side effects:
            - Creates a new TextLoader instance
            - Adds the loader window to the window manager
        """
        loader = TextLoader(return_to_menu=lambda: self._return_to_menu())
        self.manager.add(loader.window)

    def open_settings(self):
        """
        Opens the settings configuration interface.
        
        This method creates a new Settings instance with a callback that
        returns to the main menu when closed. The settings window is added
        to the window manager for display.
        
        Users can modify language preferences and color schemes through
        this interface.
        
        Side effects:
            - Creates a new Settings instance
            - Adds the settings window to the window manager
        """
        settings = Settings(return_to_menu=lambda: self._return_to_menu())
        self.manager.add(settings.window)

    def open_help(self):
        """
        Opens the help/information window.
        
        Displays information about the application including controls
        and basic usage instructions.
        
        Side effects:
            - Creates a new window with help content
            - Adds the window to the window manager
        """
        help_text = '\n'.join(pad_string_with_spaces(line, 250) for line in """
[bold]Gramotno Help[/bold]

A language learning flashcard app that helps you
learn new words by matching them with your native language.

[bold]Main Menu Controls:[/bold]
[bold]P[/bold] - Play Game (start a matching session)
[bold]T[/bold] - Text Loader (load words from a file)
[bold]S[/bold] - Settings (configure languages, colors)
[bold]H[/bold] - Help (show this menu)
[bold]Q[/bold] - Quit application

[bold]In Game:[/bold]
- You see 5 words in your native language on the left
- And 5 words in the language you're learning on the right
- Press number keys (1-5) to select a word from each side
- If they match, you get a correct point and new cards appear
- If they don't match, try again
- Your progress is automatically saved
- Press [bold]Q[/bold] to quit and return to menu

[bold]Tips:[/bold]
- Load words using the Text Loader (T)
- Go to Settings (S) to choose your native and learning languages
- The game tracks your response time and accuracy
- Use Q anytime to gracefully exit and save progress
""".split('\n'))
        help_window = ptg.Window(
            help_text.strip(),
            "",
            "[dim]Press Q to close[/dim]",
            width=int(ptg.terminal.width*0.8),
            height=int(ptg.terminal.height*0.8),
            box="ROUNDED",
        ).center()
        help_window.styles.border = ""
        
        def close_help(*args):
            self.manager.remove(help_window)
            self.manager.add(self.window)
            self.window.focus()
        
        help_window.bind("q", close_help)
        help_window.bind("Q", close_help)
        
        self.manager.add(help_window)
        help_window.focus()

    def quit(self):
        """
        Exits the application cleanly.
        
        This method is called when the user presses Q to exit from the
        main menu. It uses sys.exit() to terminate the Python process
        with a success status code.
        
        Note:
            This is the only way to fully exit the application. Other
            views return to the menu rather than quitting.
        """
        sys.exit(0)

    def _return_to_menu(self):
        """
        Returns focus to the main menu by removing all other windows.
        
        This method is used as a callback by other interfaces (Game,
        TextLoader, Settings) to return to the main menu. It iterates
        through all windows in the window manager and removes any that
        are not the main menu window, then brings the menu into focus.
        
        This creates a clean transition back to the main menu without
        having to recreate it, preserving the user's state in the menu.
        
        Side effects:
            - Removes all windows except the main menu from the manager
            - Sets focus to the main menu window
        """
        for window in list(self.manager._windows):
            if window != self.window:
                self.manager.remove(window)
        self.window.focus()
  

def main() -> None:
    """
    The main entry point for the Gramotno application.
    
    This function initializes the pytermgui WindowManager, creates the
    main menu, adds it to the manager, and gives it focus to begin the
    application. It uses a context manager to ensure proper cleanup
    of the WindowManager resources when the application exits.
    
    Before showing the menu, it calls sync_settings_to_db() to ensure
    the database has the correct user settings from the configuration
    file. This allows the application to use stored preferences even
    on first run.
    
    The function runs the application's main event loop implicitly
    through the WindowManager, which blocks until all windows are
    closed or the application exits.
    
    Side effects:
        - Initializes the WindowManager
        - Creates and displays the MainMenu
        - Syncs settings to database on startup
    """
    with ptg.WindowManager() as manager:
        menu = MainMenu(manager)
        manager.add(menu.window)
        menu.window.focus()

if __name__ == "__main__":
    sync_settings_to_db()
    main()
