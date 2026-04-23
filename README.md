```
    ▄▄▄▄                                                                        
  ██▀▀▀▀█                                            ██                         
 ██         ██▄████   ▄█████▄  ████▄██▄   ▄████▄   ███████   ██▄████▄   ▄████▄  
 ██  ▄▄▄▄   ██▀       ▀ ▄▄▄██  ██ ██ ██  ██▀  ▀██    ██      ██▀   ██  ██▀  ▀██ 
 ██  ▀▀██   ██       ▄██▀▀▀██  ██ ██ ██  ██    ██    ██      ██    ██  ██    ██ 
  ██▄▄▄██   ██       ██▄▄▄███  ██ ██ ██  ▀██▄▄██▀    ██▄▄▄   ██    ██  ▀██▄▄██▀ 
    ▀▀▀▀    ▀▀        ▀▀▀▀ ▀▀  ▀▀ ▀▀ ▀▀    ▀▀▀▀       ▀▀▀▀   ▀▀    ▀▀    ▀▀▀▀   
                                                                                   
```

# How to Play

**Gramotno** is a language learning flashcard game. Match words between your native language and the language you're learning.

## Quick Start

1. Press **T** to load words from a text file (creates flashcards)
2. Press **P** to play the matching game
3. Press **S** to configure languages and colors

## Controls

### Main Menu
| Key | Action |
|-----|--------|
| P | Play Game |
| T | Text Loader |
| S | Settings |
| H | Help |
| Q | Quit |

### In Game
| Key | Action |
|-----|--------|
| 1-5 | Select word from left (native language) |
| a-e | Select word from right (learning language) |
| Q | Quit to menu |

## Gameplay
1. You see 5 words in your native language on the **left**
2. And 5 words in the language you're learning on the **right**
3. Press a number key to select a word from each side
4. If the pair matches (same word translated), you get a point and new cards appear
5. If they don't match, try again!
6. Your progress is automatically saved

## Install

```bash
git clone https://github.com/G-Chist/EvolvingCards.git
cd EvolvingCards
git lfs install
git lfs pull
pip install -r requirements.txt
```

## Run

```bash
python main_clean.py
```
