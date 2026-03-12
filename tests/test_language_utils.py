import unittest
import string

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from language_logic.language_utils import translate


def strip_punctuation(text):
    return text.translate(str.maketrans("", "", string.punctuation))


class TestTurkishTranslations(unittest.TestCase):

    def test_turkish_to_english(self):
        result = translate("Merhaba, bugun nasilsin?", "tr", "en")
        self.assertEqual(strip_punctuation(result), strip_punctuation("Hi, how are you today?"))


if __name__ == "__main__":
    unittest.main()
