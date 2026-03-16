import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.insert(0, '/home/matvei/EvolvingCards')

from main_clean import WordPicker, get_cards_from_db

class MockCard:
    def __init__(self, id, word, translation):
        self.id = id
        self.word = word
        self.translation = translation

class TestWordPicker(unittest.TestCase):
    
    def setUp(self):
        self.mock_cards = [
            MockCard(1, "hello", "hola"),
            MockCard(2, "world", "mundo"),
            MockCard(3, "foo", "bar"),
            MockCard(4, "test", "prueba"),
            MockCard(5, "code", "codigo"),
            MockCard(6, "bug", "error"),
            MockCard(7, "feature", "caracteristica"),
        ]
    
    @patch('main_clean.get_cards_from_db')
    def test_get_cards(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards
        
        picker = WordPicker()
        picker.get_cards()
        
        self.assertEqual(picker.cards, self.mock_cards)
        mock_get_cards.assert_called_once()
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_card(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards
        
        picker = WordPicker()
        result = picker.get_random_card()
        
        self.assertIsNotNone(result)
        self.assertIn(result, self.mock_cards)
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_5_cards(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards
        
        picker = WordPicker()
        picker.get_cards()
        picker.get_random_5_cards()
        
        self.assertEqual(len(picker.five_cards), 5)
        self.assertTrue(all(card in self.mock_cards for card in picker.five_cards))
    
    @patch('main_clean.get_cards_from_db')
    def test_fill_native_words(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards[:5]
        
        picker = WordPicker()
        picker.cards = self.mock_cards[:5]
        picker.five_cards = self.mock_cards[:5]
        picker.fill_native_words()
        
        self.assertEqual(len(picker.native_words), 5)
        words = [w[0] for w in picker.native_words]
        ids = [w[1] for w in picker.native_words]
        self.assertCountEqual(words, ["hola", "mundo", "bar", "prueba", "codigo"])
        self.assertCountEqual(ids, [1, 2, 3, 4, 5])
    
    @patch('main_clean.get_cards_from_db')
    def test_fill_learning_words(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards[:5]
        
        picker = WordPicker()
        picker.cards = self.mock_cards[:5]
        picker.five_cards = self.mock_cards[:5]
        picker.fill_learning_words()
        
        self.assertEqual(len(picker.learning_words), 5)
        words = [w[0] for w in picker.learning_words]
        ids = [w[1] for w in picker.learning_words]
        self.assertCountEqual(words, ["hello", "world", "foo", "test", "code"])
        self.assertCountEqual(ids, [1, 2, 3, 4, 5])
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_card_empty_db(self, mock_get_cards):
        mock_get_cards.return_value = []
        
        picker = WordPicker()
        result = picker.get_random_card()
        
        self.assertIsNone(result)
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_5_cards_empty_db(self, mock_get_cards):
        mock_get_cards.return_value = []
        
        picker = WordPicker()
        picker.cards = []
        picker.get_random_5_cards()
        
        self.assertEqual(picker.five_cards, [])

if __name__ == '__main__':
    unittest.main()
