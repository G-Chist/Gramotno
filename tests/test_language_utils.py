import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from language_logic.language_utils import translate, strip_punctuation


class TestTurkishTranslations(unittest.TestCase):

    def test_turkish_to_english(self):
        result = translate("Merhaba, bugun nasilsin?", "tr", "en")
        self.assertEqual(strip_punctuation(result), strip_punctuation("Hi, how are you today?"))


class TestStripPunctuation(unittest.TestCase):

    def test_strips_punctuation(self):
        text = "Hello, world! How is it going?"
        result = strip_punctuation(text)
        self.assertEqual(result, ["Hello", "world", "How", "is", "it", "going"])

    def test_empty_string(self):
        self.assertEqual(strip_punctuation("!!!"), [])

    def test_no_punctuation(self):
        self.assertEqual(strip_punctuation("hello world"), ["hello", "world"])


if __name__ == "__main__":
    unittest.main()
